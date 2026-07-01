import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from app.config import DB_PATH


@contextmanager
def connect() -> Iterable[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS concursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        banca TEXT,
        orgao TEXT,
        exam_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'material',
        topic TEXT,
        extracted_text TEXT,
        ai_summary TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(concurso_id) REFERENCES concursos(id)
    );

    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        discipline TEXT NOT NULL,
        topic TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 3,
        status TEXT NOT NULL DEFAULT 'nao_iniciado',
        difficulty INTEGER NOT NULL DEFAULT 3,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(concurso_id, discipline, topic),
        FOREIGN KEY(concurso_id) REFERENCES concursos(id)
    );

    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        topic_id INTEGER,
        minutes INTEGER NOT NULL,
        notes TEXT,
        studied_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(concurso_id) REFERENCES concursos(id),
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );

    CREATE TABLE IF NOT EXISTS simulations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        simulation_date TEXT NOT NULL,
        mode TEXT NOT NULL DEFAULT 'simulado_parcial',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(concurso_id) REFERENCES concursos(id)
    );

    CREATE TABLE IF NOT EXISTS question_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        topic_id INTEGER,
        simulation_id INTEGER,
        total_questions INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        difficulty INTEGER NOT NULL DEFAULT 3,
        feedback TEXT,
        answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(concurso_id) REFERENCES concursos(id),
        FOREIGN KEY(topic_id) REFERENCES topics(id),
        FOREIGN KEY(simulation_id) REFERENCES simulations(id)
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        review_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pendente',
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(concurso_id) REFERENCES concursos(id),
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );

    CREATE TABLE IF NOT EXISTS study_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        task_date TEXT NOT NULL,
        task_type TEXT NOT NULL,
        target_minutes INTEGER NOT NULL DEFAULT 40,
        status TEXT NOT NULL DEFAULT 'pendente',
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(concurso_id, topic_id, task_date, task_type),
        FOREIGN KEY(concurso_id) REFERENCES concursos(id),
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );

    CREATE TABLE IF NOT EXISTS question_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        source TEXT NOT NULL DEFAULT 'local',
        mode TEXT NOT NULL DEFAULT 'multipla_escolha',
        statement TEXT NOT NULL,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        option_e TEXT,
        correct_answer TEXT NOT NULL,
        justification TEXT NOT NULL,
        difficulty INTEGER NOT NULL DEFAULT 3,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(concurso_id) REFERENCES concursos(id),
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );

    CREATE TABLE IF NOT EXISTS question_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concurso_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        selected_answer TEXT,
        is_correct INTEGER NOT NULL,
        skipped INTEGER NOT NULL DEFAULT 0,
        score_delta REAL NOT NULL DEFAULT 0,
        attempted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(concurso_id) REFERENCES concursos(id),
        FOREIGN KEY(question_id) REFERENCES question_bank(id),
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );
    """
    with connect() as conn:
        conn.executescript(schema)
        _ensure_column(conn, "topics", "question_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "question_results", "simulation_id", "INTEGER")
        conn.execute(
            "INSERT OR IGNORE INTO users (id, name, email) VALUES (1, 'Usuário Local', 'local@app')"
        )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def execute(query: str, params: tuple[Any, ...] = ()) -> int:
    with connect() as conn:
        cur = conn.execute(query, params)
        return int(cur.lastrowid)


def fetch_df(query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(query, params).fetchone()


def save_uploaded_file(file_name: str, payload: bytes, upload_dir: Path) -> Path:
    safe_name = Path(file_name).name.replace(" ", "_")
    target = upload_dir / safe_name
    suffix = 1
    while target.exists():
        target = upload_dir / f"{target.stem}_{suffix}{target.suffix}"
        suffix += 1
    target.write_bytes(payload)
    return target
