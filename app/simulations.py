from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from app import db


def create_simulation(concurso_id: int, title: str, mode: str, notes: str = "") -> int:
    return db.execute(
        """
        INSERT INTO simulations (concurso_id, title, simulation_date, mode, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (concurso_id, title.strip(), date.today().isoformat(), mode, notes.strip()),
    )


def add_simulation_result(
    concurso_id: int,
    simulation_id: int,
    topic_id: int,
    total_questions: int,
    correct_answers: int,
    difficulty: int,
) -> None:
    accuracy = correct_answers / total_questions if total_questions else 0
    if accuracy < 0.6:
        feedback = "Simulado crítico: revisão imediata, teoria e nova bateria de questões."
    elif accuracy < 0.8:
        feedback = "Simulado intermediário: revisar erros e repetir em até 7 dias."
    else:
        feedback = "Simulado bom: manter revisão espaçada e aumentar dificuldade."
    db.execute(
        """
        INSERT INTO question_results
        (concurso_id, topic_id, simulation_id, total_questions, correct_answers, difficulty, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (concurso_id, topic_id, simulation_id, total_questions, correct_answers, difficulty, feedback),
    )
    if accuracy < 0.8:
        db.execute(
            """
            INSERT INTO reviews (concurso_id, topic_id, review_date, reason)
            VALUES (?, ?, ?, ?)
            """,
            (
                concurso_id,
                topic_id,
                (date.today() + timedelta(days=2)).isoformat(),
                f"Desempenho abaixo de 80% no simulado #{simulation_id}",
            ),
        )


def get_simulations(concurso_id: int) -> pd.DataFrame:
    return db.fetch_df(
        """
        SELECT s.id, s.title, s.simulation_date, s.mode, s.notes,
               COALESCE(SUM(q.total_questions), 0) AS total_questions,
               COALESCE(SUM(q.correct_answers), 0) AS correct_answers
        FROM simulations s
        LEFT JOIN question_results q ON q.simulation_id = s.id
        WHERE s.concurso_id = ?
        GROUP BY s.id, s.title, s.simulation_date, s.mode, s.notes
        ORDER BY s.simulation_date DESC, s.id DESC
        """,
        (concurso_id,),
    )


def simulation_details(simulation_id: int) -> pd.DataFrame:
    return db.fetch_df(
        """
        SELECT q.id, q.total_questions, q.correct_answers, q.difficulty, q.feedback,
               t.discipline, t.topic
        FROM question_results q
        JOIN topics t ON t.id = q.topic_id
        WHERE q.simulation_id = ?
        ORDER BY t.discipline, t.topic
        """,
        (simulation_id,),
    )
