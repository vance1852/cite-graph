import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "citation_graph.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    year INTEGER NOT NULL,
    venue TEXT,
    abstract TEXT,
    doi TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper_id INTEGER NOT NULL,
    cited_paper_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citing_paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FOREIGN KEY (cited_paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    UNIQUE(citing_paper_id, cited_paper_id)
);
"""


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)
