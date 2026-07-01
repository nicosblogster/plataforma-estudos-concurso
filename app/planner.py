from __future__ import annotations

from datetime import date
from datetime import timedelta

import pandas as pd

from app import db
from app.analytics import topic_performance


STRATEGIC_CYCLES = [
    {
        "name": "Ciclo 1 - Base e Fundamentos",
        "block_a": "Compreensão e interpretação",
        "block_b": "LOAS, PNAS/2004 e SUAS",
        "focus": "Interpretação, gramática aplicada e fundamentos do SUAS.",
    },
    {
        "name": "Ciclo 2 - Legislação e Específica I",
        "block_a": "Lei Maria da Penha",
        "block_b": "LDB - Lei Federal 9.394/1996",
        "focus": "Lei seca, Constituição de 1988, LDB e Direito Educacional.",
    },
    {
        "name": "Ciclo 3 - Normas do DF e Específica II",
        "block_a": "Lei Orgânica do Distrito Federal",
        "block_b": "O Pedagogo no SUAS",
        "focus": "LC 840/2011, deveres, regime disciplinar e prática socioeducativa.",
    },
    {
        "name": "Ciclo 4 - Realidade do DF e Vulnerabilidades",
        "block_a": "Realidade étnica, social, histórica, geográfica, cultural, política e econômica do DF e RIDE",
        "block_b": "Intervenção pedagógica nas situações de vulnerabilidade e violência",
        "focus": "DF/RIDE, violência, direitos humanos e intervenção pedagógica.",
    },
]


DAILY_RITUAL = [
    ("Revisão ativa", 30, "Flashcards, mapa mental ou gatilhos do dia anterior."),
    ("Bloco A", 105, "Teoria com produção de resumo próprio."),
    ("Intervalo", 15, "Descompressão total."),
    ("Bloco B", 105, "Segunda disciplina do ciclo com resumo próprio."),
    ("Questões Quadrix", 45, "10 a 15 questões dos temas estudados no dia."),
]


def generate_strategic_day(concurso_id: int, task_date: date, cycle_number: int) -> int:
    cycle = STRATEGIC_CYCLES[(cycle_number - 1) % len(STRATEGIC_CYCLES)]
    created = 0
    created += _insert_task_by_match(
        concurso_id,
        task_date,
        "revisao",
        30,
        "Ritual 5h: revisão ativa do dia anterior",
        cycle["block_a"],
    )
    created += _insert_task_by_match(
        concurso_id,
        task_date,
        "estudo",
        105,
        f"{cycle['name']} - Bloco A: teoria + resumo próprio",
        cycle["block_a"],
    )
    created += _insert_task_by_match(
        concurso_id,
        task_date,
        "estudo",
        105,
        f"{cycle['name']} - Bloco B: teoria + resumo próprio",
        cycle["block_b"],
    )
    created += _insert_task_by_match(
        concurso_id,
        task_date,
        "questoes",
        45,
        "Ritual 5h: 10 a 15 questões Quadrix dos temas do dia",
        cycle["block_b"],
    )
    return created


def generate_strategic_week(concurso_id: int, start_date: date, start_cycle: int = 1) -> int:
    created = 0
    for offset in range(5):
        created += generate_strategic_day(concurso_id, start_date + timedelta(days=offset), start_cycle + offset)
    saturday = start_date + timedelta(days=5)
    sunday = start_date + timedelta(days=6)
    created += _insert_task_by_match(
        concurso_id,
        saturday,
        "discursiva",
        120,
        "Sábado: estudo de caso discursivo de 20 a 30 linhas sobre SUAS/LDB",
        "O Pedagogo no SUAS",
    )
    created += _insert_task_by_match(
        concurso_id,
        saturday,
        "revisao",
        90,
        "Sábado: revisão semanal dos erros e resumos",
        "LDB",
    )
    created += _insert_task_by_match(
        concurso_id,
        sunday,
        "simulado",
        120,
        "Domingo: simulado de questões + benefícios/programas do DF",
        "Realidade étnica",
    )
    return created


def generate_weekly_plan(concurso_id: int, start_date: date, daily_minutes: int = 240, days: int = 6) -> int:
    created = 0
    for offset in range(max(1, min(days, 7))):
        created += generate_daily_plan(
            concurso_id=concurso_id,
            task_date=start_date + timedelta(days=offset),
            available_minutes=daily_minutes,
        )
    return created


def generate_daily_plan(concurso_id: int, task_date: date, available_minutes: int = 240) -> int:
    topics = db.fetch_df("SELECT * FROM topics WHERE concurso_id = ?", (concurso_id,))
    results = db.fetch_df("SELECT * FROM question_results WHERE concurso_id = ?", (concurso_id,))
    reviews = db.fetch_df(
        """
        SELECT r.*, t.discipline, t.topic, t.priority, t.question_count
        FROM reviews r
        JOIN topics t ON t.id = r.topic_id
        WHERE r.concurso_id = ? AND r.status = 'pendente' AND r.review_date <= ?
        ORDER BY r.review_date ASC, t.priority DESC
        """,
        (concurso_id, task_date.isoformat()),
    )
    performance = topic_performance(results, topics)
    created = 0
    remaining = max(40, available_minutes)

    for _, row in reviews.head(4).iterrows():
        if remaining <= 0:
            break
        minutes = min(35, remaining)
        created += _insert_task(
            concurso_id,
            int(row["topic_id"]),
            task_date,
            "revisao",
            minutes,
            f"Revisão vencida ou prevista para {row['review_date']}",
        )
        remaining -= minutes

    if not performance.empty and remaining > 0:
        weak = performance.sort_values(["accuracy", "total_questions"], ascending=[True, False]).head(4)
        for _, row in weak.iterrows():
            if remaining <= 0:
                break
            minutes = min(45, remaining)
            created += _insert_task(
                concurso_id,
                int(row["topic_id"]),
                task_date,
                "questoes",
                minutes,
                f"Ponto fraco: {round(float(row['accuracy']) * 100, 1)}% de acerto",
            )
            remaining -= minutes

    if remaining > 0 and not topics.empty:
        candidates = topics.copy()
        candidates["status_rank"] = candidates["status"].map(
            {"nao_iniciado": 0, "em_andamento": 1, "revisao": 2, "concluido": 3}
        ).fillna(0)
        candidates["score"] = (
            candidates["question_count"].fillna(0).astype(int)
            + candidates["priority"].fillna(3).astype(int) * 120
            - candidates["status_rank"] * 250
            + candidates["difficulty"].fillna(3).astype(int) * 40
        )
        discipline_counts: dict[str, int] = {}
        for _, row in candidates.sort_values("score", ascending=False).iterrows():
            if remaining <= 0:
                break
            discipline = str(row["discipline"])
            if discipline_counts.get(discipline, 0) >= 2:
                continue
            minutes = min(50, remaining)
            created += _insert_task(
                concurso_id,
                int(row["id"]),
                task_date,
                "estudo",
                minutes,
                "Alta prioridade pelo peso no mapa e status atual",
            )
            discipline_counts[discipline] = discipline_counts.get(discipline, 0) + 1
            remaining -= minutes

    return created


def get_daily_plan(concurso_id: int, task_date: date) -> pd.DataFrame:
    return db.fetch_df(
        """
        SELECT st.id, st.task_date, st.task_type, st.target_minutes, st.status, st.reason,
               t.discipline, t.topic, t.priority, t.question_count, t.difficulty
        FROM study_tasks st
        JOIN topics t ON t.id = st.topic_id
        WHERE st.concurso_id = ? AND st.task_date = ?
        ORDER BY
            CASE st.task_type WHEN 'revisao' THEN 0 WHEN 'questoes' THEN 1 WHEN 'estudo' THEN 2 WHEN 'discursiva' THEN 3 WHEN 'simulado' THEN 4 ELSE 5 END,
            t.question_count DESC,
            t.priority DESC
        """,
        (concurso_id, task_date.isoformat()),
    )


def get_week_plan(concurso_id: int, start_date: date, days: int = 7) -> pd.DataFrame:
    end_date = start_date + timedelta(days=max(1, min(days, 7)) - 1)
    return db.fetch_df(
        """
        SELECT st.id, st.task_date, st.task_type, st.target_minutes, st.status, st.reason,
               t.discipline, t.topic, t.priority, t.question_count, t.difficulty
        FROM study_tasks st
        JOIN topics t ON t.id = st.topic_id
        WHERE st.concurso_id = ? AND st.task_date BETWEEN ? AND ?
        ORDER BY st.task_date ASC,
            CASE st.task_type WHEN 'revisao' THEN 0 WHEN 'questoes' THEN 1 WHEN 'estudo' THEN 2 WHEN 'discursiva' THEN 3 WHEN 'simulado' THEN 4 ELSE 5 END,
            t.question_count DESC,
            t.priority DESC
        """,
        (concurso_id, start_date.isoformat(), end_date.isoformat()),
    )


def complete_task(task_id: int) -> None:
    db.execute("UPDATE study_tasks SET status = 'concluida' WHERE id = ?", (task_id,))


def complete_matching_tasks(
    concurso_id: int,
    topic_id: int,
    task_date: date,
    task_types: tuple[str, ...],
) -> int:
    if not task_types:
        return 0
    placeholders = ",".join("?" for _ in task_types)
    params = (concurso_id, topic_id, task_date.isoformat(), *task_types)
    before = db.fetch_one(
        f"""
        SELECT COUNT(*) AS qtd
        FROM study_tasks
        WHERE concurso_id = ? AND topic_id = ? AND task_date = ?
          AND task_type IN ({placeholders}) AND status <> 'concluida'
        """,
        params,
    )
    db.execute(
        f"""
        UPDATE study_tasks
        SET status = 'concluida'
        WHERE concurso_id = ? AND topic_id = ? AND task_date = ?
          AND task_type IN ({placeholders}) AND status <> 'concluida'
        """,
        params,
    )
    return int(before["qtd"]) if before else 0


def next_pending_task(concurso_id: int, task_date: date) -> dict | None:
    row = db.fetch_one(
        """
        SELECT st.id, st.task_date, st.task_type, st.target_minutes, st.status, st.reason,
               t.id AS topic_id, t.discipline, t.topic, t.priority, t.question_count
        FROM study_tasks st
        JOIN topics t ON t.id = st.topic_id
        WHERE st.concurso_id = ? AND st.task_date = ? AND st.status <> 'concluida'
        ORDER BY
            CASE st.task_type WHEN 'revisao' THEN 0 WHEN 'questoes' THEN 1 WHEN 'estudo' THEN 2 WHEN 'discursiva' THEN 3 WHEN 'simulado' THEN 4 ELSE 5 END,
            t.question_count DESC,
            t.priority DESC,
            st.id ASC
        LIMIT 1
        """,
        (concurso_id, task_date.isoformat()),
    )
    return dict(row) if row else None


def complete_review(review_id: int) -> None:
    review = db.fetch_one("SELECT * FROM reviews WHERE id = ?", (review_id,))
    if not review:
        return
    db.execute("UPDATE reviews SET status = 'feita' WHERE id = ?", (review_id,))
    topic_id = int(review["topic_id"])
    concurso_id = int(review["concurso_id"])
    for days in [7, 30]:
        db.execute(
            """
            INSERT OR IGNORE INTO reviews (concurso_id, topic_id, review_date, reason)
            VALUES (?, ?, ?, ?)
            """,
            (concurso_id, topic_id, (date.today() + timedelta(days=days)).isoformat(), f"Ciclo pós-revisão D+{days}"),
        )


def get_reviews(concurso_id: int) -> pd.DataFrame:
    return db.fetch_df(
        """
        SELECT r.id, r.review_date, r.status, r.reason, t.discipline, t.topic, t.priority
        FROM reviews r
        JOIN topics t ON t.id = r.topic_id
        WHERE r.concurso_id = ?
        ORDER BY
            CASE r.status WHEN 'pendente' THEN 0 ELSE 1 END,
            r.review_date ASC,
            t.priority DESC
        """,
        (concurso_id,),
    )


def pending_review_count(concurso_id: int, ref_date: date) -> int:
    row = db.fetch_one(
        "SELECT COUNT(*) AS qtd FROM reviews WHERE concurso_id = ? AND status = 'pendente' AND review_date <= ?",
        (concurso_id, ref_date.isoformat()),
    )
    return int(row["qtd"]) if row else 0


def _insert_task(
    concurso_id: int,
    topic_id: int,
    task_date: date,
    task_type: str,
    target_minutes: int,
    reason: str,
) -> int:
    before = db.fetch_one(
        """
        SELECT id FROM study_tasks
        WHERE concurso_id = ? AND topic_id = ? AND task_date = ? AND task_type = ?
        """,
        (concurso_id, topic_id, task_date.isoformat(), task_type),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO study_tasks
        (concurso_id, topic_id, task_date, task_type, target_minutes, reason)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (concurso_id, topic_id, task_date.isoformat(), task_type, target_minutes, reason),
    )
    return 0 if before else 1


def _insert_task_by_match(
    concurso_id: int,
    task_date: date,
    task_type: str,
    target_minutes: int,
    reason: str,
    match: str,
) -> int:
    topic = _find_topic(concurso_id, match)
    if not topic:
        return 0
    return _insert_task(concurso_id, int(topic["id"]), task_date, task_type, target_minutes, reason)


def _find_topic(concurso_id: int, match: str):
    topic = db.fetch_one(
        """
        SELECT id FROM topics
        WHERE concurso_id = ? AND lower(topic) LIKE '%' || lower(?) || '%'
        ORDER BY question_count DESC, priority DESC
        LIMIT 1
        """,
        (concurso_id, match),
    )
    if topic:
        return topic
    first_word = match.split()[0] if match.split() else match
    return db.fetch_one(
        """
        SELECT id FROM topics
        WHERE concurso_id = ? AND lower(discipline || ' ' || topic) LIKE '%' || lower(?) || '%'
        ORDER BY question_count DESC, priority DESC
        LIMIT 1
        """,
        (concurso_id, first_word),
    )
