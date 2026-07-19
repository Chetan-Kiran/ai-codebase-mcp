import sqlite3
import os

# Always resolve to the project root regardless of where the MCP host
# launches the server from (Claude Desktop sets an arbitrary cwd).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
DB_PATH = os.path.join(_DATA_DIR, "project_data.db")

def init_db():
    # Ensure the data directory exists before SQLite tries to create the file.
    os.makedirs(_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Example table for storing repository analysis history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT,
            analysis_type TEXT,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def query_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def execute_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return "Query executed successfully."

# Initialize on import — directory is created inside init_db()
if not os.path.exists(DB_PATH):
    init_db()
