from services.indexer_service import search_repo

def semantic_search(repo_path, query, top_k=10):
    """
    Semantic vector search over the codebase.
    Replaces the old case-insensitive string match with dense vector retrieval
    powered by sentence-transformers + FAISS.
    """
    results = search_repo(repo_path, query, top_k=top_k)

    if not results:
        return "No semantically relevant matches found."

    output_lines = [f"Top {len(results)} semantic matches for: \"{query}\"\n"]

    for i, r in enumerate(results, 1):
        output_lines.append(
            f"[{i}] {r['file_path']}  (lines {r['start_line']}-{r['end_line']})  score={r['score']:.4f}"
        )
        # Show a snippet (first 5 lines of the chunk)
        snippet = "\n".join(r["content"].splitlines()[:5])
        output_lines.append(f"  {snippet}\n")

    return "\n".join(output_lines)