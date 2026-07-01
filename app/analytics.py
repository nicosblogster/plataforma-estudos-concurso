import pandas as pd


def topic_performance(results: pd.DataFrame, topics: pd.DataFrame) -> pd.DataFrame:
    if results.empty or topics.empty:
        return pd.DataFrame(
            columns=["topic_id", "discipline", "topic", "total_questions", "correct_answers", "accuracy"]
        )
    grouped = (
        results.groupby("topic_id", dropna=True)[["total_questions", "correct_answers"]]
        .sum()
        .reset_index()
    )
    grouped["accuracy"] = (grouped["correct_answers"] / grouped["total_questions"]).fillna(0)
    return grouped.merge(
        topics[["id", "discipline", "topic", "priority", "question_count"]],
        left_on="topic_id",
        right_on="id",
        how="left",
    ).drop(columns=["id"])


def weak_topics(performance: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    if performance.empty:
        return performance
    return performance.sort_values(["accuracy", "total_questions"], ascending=[True, False]).head(limit)


def progress_percent(topics: pd.DataFrame) -> float:
    if topics.empty:
        return 0.0
    done = topics["status"].isin(["concluido", "revisao"]).sum()
    return round((done / len(topics)) * 100, 1)


def discipline_performance(results: pd.DataFrame, topics: pd.DataFrame) -> pd.DataFrame:
    if results.empty or topics.empty:
        return pd.DataFrame(columns=["discipline", "total_questions", "correct_answers", "accuracy"])
    merged = results.merge(
        topics[["id", "discipline"]],
        left_on="topic_id",
        right_on="id",
        how="left",
    )
    grouped = merged.groupby("discipline", dropna=False)[["total_questions", "correct_answers"]].sum().reset_index()
    grouped["accuracy"] = (grouped["correct_answers"] / grouped["total_questions"]).fillna(0)
    return grouped.sort_values("accuracy")


def readiness_score(topics: pd.DataFrame, results: pd.DataFrame, sessions: pd.DataFrame, reviews: pd.DataFrame) -> dict[str, float]:
    progress = progress_percent(topics)
    performance = topic_performance(results, topics)
    avg_accuracy = 0.0 if performance.empty else float(performance["accuracy"].mean() * 100)
    reviewed = 0.0
    if not reviews.empty:
        reviewed = float((reviews["status"] != "pendente").mean() * 100)
    hours = 0.0 if sessions.empty else float(sessions["minutes"].sum() / 60)
    hours_score = min(100.0, hours / 120 * 100)
    score = float(round(progress * 0.30 + avg_accuracy * 0.35 + reviewed * 0.15 + hours_score * 0.20, 1))
    return {
        "score": score,
        "progress": float(round(progress, 1)),
        "accuracy": float(round(avg_accuracy, 1)),
        "reviewed": float(round(reviewed, 1)),
        "hours": float(round(hours, 1)),
    }


def recommendations(topics: pd.DataFrame, results: pd.DataFrame, reviews: pd.DataFrame) -> list[str]:
    output: list[str] = []
    perf = topic_performance(results, topics)
    if not reviews.empty:
        pending = reviews[reviews["status"] == "pendente"]
        if len(pending) > 0:
            output.append(f"Zerar {len(pending)} revisão(ões) pendente(s) antes de conteúdo novo.")
    if not perf.empty:
        weak = weak_topics(perf, limit=3)
        for _, row in weak.iterrows():
            output.append(
                f"Reforçar {row['discipline']} - {row['topic']} ({round(float(row['accuracy']) * 100, 1)}% de acerto)."
            )
    if not topics.empty:
        untouched = topics[topics["status"] == "nao_iniciado"].sort_values(["question_count", "priority"], ascending=False)
        for _, row in untouched.head(2).iterrows():
            output.append(f"Iniciar tópico prioritário: {row['discipline']} - {row['topic']}.")
    return output[:6]
