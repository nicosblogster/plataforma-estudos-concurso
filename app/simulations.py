from __future__ import annotations

from datetime import date, timedelta
from typing import Any

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


def record_simulation_answer(
    concurso_id: int,
    simulation_id: int,
    question: dict[str, Any],
    selected_answer: str,
    elapsed_seconds: int,
) -> dict[str, Any]:
    skipped = selected_answer == "Pular"
    expected = str(question["correct_answer"]).upper()
    chosen = "" if skipped else selected_answer.upper()
    is_correct = (chosen == expected) and not skipped
    score_delta = 0.0 if skipped else (1.0 if is_correct else -0.5)
    feedback = (
        f"Simulado interativo #{simulation_id}: resposta={selected_answer}; "
        f"gabarito={expected}; tempo={elapsed_seconds}s"
    )

    db.execute(
        """
        INSERT INTO question_attempts
        (concurso_id, question_id, topic_id, selected_answer, is_correct, skipped, score_delta)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concurso_id,
            int(question["id"]),
            int(question["topic_id"]),
            selected_answer,
            1 if is_correct else 0,
            1 if skipped else 0,
            score_delta,
        ),
    )
    db.execute(
        """
        INSERT INTO question_results
        (concurso_id, topic_id, simulation_id, total_questions, correct_answers, difficulty, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concurso_id,
            int(question["topic_id"]),
            simulation_id,
            0 if skipped else 1,
            1 if is_correct else 0,
            int(question.get("difficulty", 3)),
            feedback,
        ),
    )
    if not is_correct and not skipped:
        db.execute(
            """
            INSERT INTO reviews (concurso_id, topic_id, review_date, reason)
            VALUES (?, ?, ?, ?)
            """,
            (
                concurso_id,
                int(question["topic_id"]),
                (date.today() + timedelta(days=2)).isoformat(),
                f"Erro no simulado interativo #{simulation_id}",
            ),
        )
    return {
        "expected": expected,
        "selected": selected_answer,
        "is_correct": is_correct,
        "skipped": skipped,
        "score_delta": score_delta,
    }


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


def simulation_discipline_summary(simulation_id: int) -> pd.DataFrame:
    return db.fetch_df(
        """
        SELECT t.discipline,
               COUNT(q.id) AS entries,
               COALESCE(SUM(q.total_questions), 0) AS total_questions,
               COALESCE(SUM(q.correct_answers), 0) AS correct_answers,
               ROUND(
                   100.0 * COALESCE(SUM(q.correct_answers), 0) /
                   NULLIF(COALESCE(SUM(q.total_questions), 0), 0),
                   1
               ) AS accuracy,
               SUM(CASE WHEN q.total_questions > q.correct_answers THEN 1 ELSE 0 END) AS errors
        FROM question_results q
        JOIN topics t ON t.id = q.topic_id
        WHERE q.simulation_id = ?
        GROUP BY t.discipline
        ORDER BY accuracy ASC, total_questions DESC, t.discipline
        """,
        (simulation_id,),
    )
