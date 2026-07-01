from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from app import db
from app.analytics import discipline_performance, readiness_score, recommendations, topic_performance, weak_topics


def weekly_report(concurso_id: int, end_date: date | None = None) -> dict[str, object]:
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)
    topics = db.fetch_df("SELECT * FROM topics WHERE concurso_id = ?", (concurso_id,))
    results = db.fetch_df(
        "SELECT * FROM question_results WHERE concurso_id = ? AND date(answered_at) BETWEEN ? AND ?",
        (concurso_id, start_date.isoformat(), end_date.isoformat()),
    )
    all_results = db.fetch_df("SELECT * FROM question_results WHERE concurso_id = ?", (concurso_id,))
    sessions = db.fetch_df(
        "SELECT * FROM study_sessions WHERE concurso_id = ? AND date(studied_at) BETWEEN ? AND ?",
        (concurso_id, start_date.isoformat(), end_date.isoformat()),
    )
    all_sessions = db.fetch_df("SELECT * FROM study_sessions WHERE concurso_id = ?", (concurso_id,))
    reviews = db.fetch_df("SELECT * FROM reviews WHERE concurso_id = ?", (concurso_id,))
    perf = topic_performance(all_results, topics)
    week_perf = discipline_performance(results, topics)
    weak = weak_topics(perf, limit=5)
    readiness = readiness_score(topics, all_results, all_sessions, reviews)
    recs = recommendations(topics, all_results, reviews)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "topics": topics,
        "results": results,
        "sessions": sessions,
        "reviews": reviews,
        "week_performance": week_perf,
        "weak_topics": weak,
        "readiness": readiness,
        "recommendations": recs,
    }


def weekly_report_markdown(concurso_id: int) -> str:
    report = weekly_report(concurso_id)
    sessions: pd.DataFrame = report["sessions"]  # type: ignore[assignment]
    results: pd.DataFrame = report["results"]  # type: ignore[assignment]
    weak: pd.DataFrame = report["weak_topics"]  # type: ignore[assignment]
    readiness: dict[str, float] = report["readiness"]  # type: ignore[assignment]
    recs: list[str] = report["recommendations"]  # type: ignore[assignment]

    minutes = int(sessions["minutes"].sum()) if not sessions.empty else 0
    questions = int(results["total_questions"].sum()) if not results.empty else 0
    correct = int(results["correct_answers"].sum()) if not results.empty else 0
    accuracy = round(correct / questions * 100, 1) if questions else 0

    lines = [
        "# Relatório semanal - SEDES DF Pedagogia",
        f"Período: {report['start_date']} a {report['end_date']}",
        "",
        "## Indicadores",
        f"- Prontidão estimada: {readiness['score']}%",
        f"- Horas líquidas na semana: {minutes // 60}h {minutes % 60:02d}m",
        f"- Questões na semana: {questions}",
        f"- Acertos na semana: {correct}",
        f"- Taxa de acerto semanal: {accuracy}%",
        "",
        "## Pontos fracos",
    ]
    if weak.empty:
        lines.append("- Ainda sem dados suficientes de questões.")
    else:
        for _, row in weak.iterrows():
            lines.append(f"- {row['discipline']} - {row['topic']}: {round(float(row['accuracy']) * 100, 1)}%")

    lines.extend(["", "## Próximas ações"])
    if recs:
        lines.extend([f"- {rec}" for rec in recs])
    else:
        lines.append("- Continuar executando o planejamento diário.")

    return "\n".join(lines)
