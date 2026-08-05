import os
import sqlite3
import hashlib

# numpy, faiss, and sentence_transformers are imported LAZILY inside the
# functions that actually use them. This means the MCP server can start up
# cleanly with any Python/mcp-dev invocation — the heavy ML deps are only
# loaded the first time a search is actually requested.

# Absolute paths anchored to the project root so they work regardless of
# what working directory the MCP host (Claude Desktop) happens to use.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
DB_PATH = os.path.join(_DATA_DIR, "project_data.db")
FAISS_INDEX_PATH = os.path.join(_DATA_DIR, "project_data.faiss")
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # lazy import
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def init_db():
    # Ensure the data directory exists before SQLite tries to create the file.
    os.makedirs(_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for storing file sync states (hashing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_sync_state (
            repo_path TEXT,
            file_path TEXT,
            file_hash TEXT,
            last_modified REAL,
            PRIMARY KEY (repo_path, file_path)
        )
    ''')

    # Table for storing vector chunk metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vector_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_path TEXT,
            file_path TEXT,
            content TEXT,
            start_line INTEGER,
            end_line INTEGER,
            faiss_id INTEGER
        )
    ''')

    conn.commit()
    conn.close()


def compute_file_hash(file_path):
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception:
        return None


def chunk_file_content(file_path, content, chunk_size=20, overlap=5):
    """
    Chunks a file line-by-line using a sliding window.
    Returns list of dicts with 'content', 'start_line', 'end_line'.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    chunks = []

    if total_lines == 0:
        return chunks

    i = 0
    while i < total_lines:
        start_line = i + 1
        end_line = min(i + chunk_size, total_lines)
        chunk_lines = lines[i:end_line]
        chunk_text = "\n".join(chunk_lines)

        chunks.append({
            "content": chunk_text,
            "start_line": start_line,
            "end_line": end_line
        })

        # Advance by chunk_size - overlap
        i += (chunk_size - overlap)
        if i >= total_lines or (chunk_size - overlap) <= 0:
            break

    return chunks


def index_repo(repo_path):
    """
    Scans the repository, detects changed/new files, extracts chunks,
    generates embeddings, and saves metadata + FAISS index.
    """
    import numpy as np   # lazy
    import faiss         # lazy

    init_db()

    from services.parser_service import get_all_files
    files = get_all_files(repo_path)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read existing sync state
    cursor.execute("SELECT file_path, file_hash FROM file_sync_state WHERE repo_path = ?", (repo_path,))
    sync_states = dict(cursor.fetchall())

    current_files = set(files)

    # Remove deleted files
    deleted_files = set(sync_states.keys()) - current_files
    for df in deleted_files:
        cursor.execute("DELETE FROM file_sync_state WHERE repo_path = ? AND file_path = ?", (repo_path, df))
        cursor.execute("DELETE FROM vector_metadata WHERE repo_path = ? AND file_path = ?", (repo_path, df))

    model = None
    changes_made = False

    for relative_path in files:
        full_path = os.path.join(repo_path, relative_path)
        if not os.path.isfile(full_path):
            continue

        current_hash = compute_file_hash(full_path)
        last_modified = os.path.getmtime(full_path)

        if relative_path not in sync_states or sync_states[relative_path] != current_hash:
            changes_made = True

            cursor.execute("DELETE FROM vector_metadata WHERE repo_path = ? AND file_path = ?", (repo_path, relative_path))

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue

            chunks = chunk_file_content(relative_path, content)
            if not chunks:
                cursor.execute(
                    "INSERT OR REPLACE INTO file_sync_state (repo_path, file_path, file_hash, last_modified) VALUES (?, ?, ?, ?)",
                    (repo_path, relative_path, current_hash, last_modified)
                )
                continue

            if model is None:
                model = get_model()

            texts = [f"File: {relative_path}\nLines {c['start_line']}-{c['end_line']}\n\n{c['content']}" for c in chunks]
            embeddings = model.encode(texts, show_progress_bar=False)

            for chunk, _ in zip(chunks, embeddings):
                cursor.execute(
                    "INSERT INTO vector_metadata (repo_path, file_path, content, start_line, end_line, faiss_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (repo_path, relative_path, chunk['content'], chunk['start_line'], chunk['end_line'], -1)
                )

            cursor.execute(
                "INSERT OR REPLACE INTO file_sync_state (repo_path, file_path, file_hash, last_modified) VALUES (?, ?, ?, ?)",
                (repo_path, relative_path, current_hash, last_modified)
            )

    conn.commit()

    # Rebuild FAISS index if changes were made or index file is missing
    if changes_made or not os.path.exists(FAISS_INDEX_PATH):
        cursor.execute(
            "SELECT id, file_path, content, start_line, end_line FROM vector_metadata WHERE repo_path = ?",
            (repo_path,)
        )
        records = cursor.fetchall()

        if records:
            if model is None:
                model = get_model()

            texts_to_embed = [f"File: {r[1]}\nLines {r[3]}-{r[4]}\n\n{r[2]}" for r in records]
            embeddings = model.encode(texts_to_embed, show_progress_bar=False)

            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings).astype('float32'))
            faiss.write_index(index, FAISS_INDEX_PATH)

            for faiss_idx, record in enumerate(records):
                cursor.execute("UPDATE vector_metadata SET faiss_id = ? WHERE id = ?", (faiss_idx, record[0]))
            conn.commit()
        else:
            if os.path.exists(FAISS_INDEX_PATH):
                os.remove(FAISS_INDEX_PATH)

    conn.close()


def search_repo(repo_path, query, top_k=10):
    """
    Indexes the repo (ensuring updates), generates query embedding,
    searches FAISS index, and retrieves metadata records.
    """
    import numpy as np   # lazy
    import faiss         # lazy

    index_repo(repo_path)

    if not os.path.exists(FAISS_INDEX_PATH):
        return []

    model = get_model()
    query_vector = model.encode([query]).astype('float32')

    index = faiss.read_index(FAISS_INDEX_PATH)
    distances, indices = index.search(query_vector, min(top_k, index.ntotal))

    results = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for distance, faiss_idx in zip(distances[0], indices[0]):
        if faiss_idx == -1:
            continue
        cursor.execute(
            "SELECT file_path, content, start_line, end_line FROM vector_metadata WHERE repo_path = ? AND faiss_id = ?",
            (repo_path, int(faiss_idx))
        )
        row = cursor.fetchone()
        if row:
            results.append({
                "file_path": row[0],
                "content": row[1],
                "start_line": row[2],
                "end_line": row[3],
                "score": float(distance)
            })

    conn.close()
    return results
