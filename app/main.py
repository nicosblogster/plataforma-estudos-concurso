from __future__ import annotations

from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import db
from app.analytics import (
    discipline_performance,
    progress_percent,
    readiness_score,
    recommendations,
    topic_performance,
    weak_topics,
)
from app.config import DB_PATH, SUPPORTED_EXTENSIONS, UPLOAD_DIR
from app.extractors import extract_text, is_ocr_available
from app.ollama_client import (
    extract_topics_from_edital,
    generate_quadrrix_question,
    is_ollama_available,
    summarize_material,
)
from app.planner import (
    DAILY_RITUAL,
    STRATEGIC_CYCLES,
    complete_matching_tasks,
    complete_review,
    complete_task,
    generate_daily_plan,
    generate_strategic_day,
    generate_strategic_week,
    generate_weekly_plan,
    get_daily_plan,
    get_reviews,
    get_week_plan,
    next_pending_task,
    pending_review_count,
)
from app.question_bank import attempts_summary, get_question_count, next_question, record_attempt, seed_question_bank
from app.reports import weekly_report, weekly_report_markdown
from app.seed_data import seed_real_edital
from app.simulations import (
    add_simulation_result,
    create_simulation,
    get_simulations,
    record_simulation_answer,
    simulation_details,
    simulation_discipline_summary,
)


st.set_page_config(
    page_title="Plataforma de Estudos para Concurso",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root {
            --ink: #0f172a;
            --muted: #667085;
            --line: #e5e7eb;
            --teal: #0ea5a3;
            --teal-dark: #087f7d;
            --purple: #7c3aed;
            --orange: #f59e0b;
            --green: #16a34a;
            --red: #ef4444;
            --nav: #061724;
        }
        html, body, [class*="css"] { font-family: Inter, Segoe UI, sans-serif; }
        .stApp { background: #f6f8fb; color: var(--ink); }
        header[data-testid="stHeader"] { height: 0; background: transparent; }
        [data-testid="stToolbar"], #MainMenu, footer { display: none; visibility: hidden; }
        .main .block-container { padding: 1.2rem 1.65rem 2rem 1.65rem; max-width: 100%; }
        h1, h2, h3 { letter-spacing: 0; }
        [data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 0 0, rgba(20, 184, 166, .22), transparent 28%),
                linear-gradient(180deg, #061724 0%, #071b2a 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] * { color: #e5eef6; }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
        [data-testid="stSidebar"] [data-testid="stTextInput"] label { color:#b8c7d4; font-size:.75rem; font-weight:700; }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            background: rgba(255,255,255,.08);
            border-color: rgba(255,255,255,.16);
            border-radius: 8px;
        }
        [data-testid="stSidebar"] .stRadio > div { gap: .35rem; }
        [data-testid="stSidebar"] label[data-baseweb="radio"] {
            border-radius: 8px;
            padding: .62rem .75rem;
            min-height: 42px;
            color:#e5eef6;
            transition: background .16s ease, transform .16s ease;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {
            display:none;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
            background: linear-gradient(90deg, #0aa8a6, #16c7b7);
            box-shadow: 0 8px 22px rgba(20,184,166,.24);
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
            background: rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.16);
            color: #fff;
            border-radius: 8px;
        }
        .sidebar-brand { padding: 1.05rem .35rem .85rem; display: flex; gap: .75rem; align-items: center; }
        .brand-mark {
            width: 42px; height: 42px; border-radius: 10px;
            background: linear-gradient(145deg, #17c9b7, #0c7799);
            display:flex; align-items:center; justify-content:center; font-size: 24px;
            box-shadow: 0 10px 26px rgba(15, 185, 172, .26);
        }
        .brand-small { color: #a8b8c8; font-size: .82rem; line-height: 1; }
        .brand-title { color: #fff; font-weight: 800; font-size: 1.08rem; line-height: 1.2; }
        .side-plan {
            position: static; width: auto; margin: 1rem .35rem 0 .35rem;
            border: 1px solid rgba(255,255,255,.18); border-radius: 8px; padding: 1rem;
            background: rgba(6,23,36,.72);
        }
        .plan-progress { height: 7px; background: rgba(255,255,255,.18); border-radius: 99px; overflow:hidden; margin-top: .5rem; }
        .plan-fill { height: 100%; width: 62%; background: #11b8ad; border-radius: 99px; }
        .topbar {
            margin: 0 -1.65rem 1.15rem -1.65rem; padding: .72rem 1.65rem;
            min-height: 80px; background: rgba(255,255,255,.96); border-bottom: 1px solid var(--line);
            display: grid; grid-template-columns: minmax(280px, 420px) 1fr auto; gap: 1rem; align-items: center;
            box-shadow: 0 8px 24px rgba(15,23,42,.04);
        }
        .exam-select {
            border: 1px solid var(--line); border-radius: 8px; padding: .78rem 1rem;
            box-shadow: 0 10px 24px rgba(15,23,42,.07); background: #fff;
        }
        .exam-title { font-size: 1.18rem; font-weight: 800; color: var(--ink); }
        .exam-subtitle { font-size: .78rem; color: var(--muted); margin-top: .25rem; }
        .top-metrics { display:flex; gap: 1.2rem; align-items:center; }
        .top-item { display:flex; gap:.6rem; align-items:center; padding-right: 1.2rem; border-right: 1px solid var(--line); }
        .top-icon { color: var(--ink); font-size: 1.25rem; }
        .top-label { font-weight: 700; font-size: .82rem; }
        .top-value { color: #334155; font-size: .78rem; margin-top: .1rem; }
        .user-box { display:flex; gap:.65rem; align-items:center; min-width: 180px; justify-content:flex-end; }
        .avatar { width: 38px; height: 38px; border-radius: 999px; background: #0f2b3d; color: #fff; display:flex; align-items:center; justify-content:center; font-weight:800; }
        .page-title { font-size: 1.15rem; font-weight: 800; margin: .3rem 0 1rem; }
        .command-strip {
            display:grid; grid-template-columns: 1.35fr .85fr .85fr; gap: .85rem; margin: 0 0 1rem 0;
        }
        .command-item {
            background:#fff; border:1px solid #dfe5ec; border-radius:8px; padding:.95rem 1rem;
            box-shadow: 0 10px 28px rgba(15,23,42,.045);
            display:flex; gap:.8rem; align-items:center; min-height:76px;
        }
        .command-icon {
            width:38px; height:38px; border-radius:8px; display:flex; align-items:center; justify-content:center;
            font-weight:800; color:#fff; background:linear-gradient(145deg,#0ea5a3,#087f7d); flex:0 0 auto;
        }
        .command-label { color:var(--muted); font-size:.74rem; font-weight:700; text-transform:uppercase; letter-spacing:0; }
        .command-title { color:var(--ink); font-size:.95rem; font-weight:800; margin-top:.15rem; line-height:1.25; }
        .metric-grid { display:grid; grid-template-columns: repeat(5, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1rem; }
        .card {
            background:#fff; border:1px solid #dfe5ec; border-radius:8px; padding:1.05rem;
            box-shadow: 0 10px 28px rgba(15,23,42,.045);
            overflow:hidden;
            transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
        }
        .card:hover, .command-item:hover { transform: translateY(-1px); box-shadow: 0 14px 32px rgba(15,23,42,.07); border-color:#cbd5e1; }
        .card-title { font-size:.84rem; font-weight:700; margin-bottom:.55rem; color:#111827; }
        .big-number { font-size:1.75rem; line-height:1; font-weight:800; margin:.35rem 0 .35rem; }
        .muted { color: var(--muted); font-size:.78rem; }
        .delta { color: var(--teal-dark); font-weight:700; font-size:.78rem; margin-top:1.15rem; }
        .donut {
            width:76px; height:76px; border-radius:50%;
            background: conic-gradient(var(--teal) var(--p), #e5e7eb 0);
            position: relative; margin-left:auto; margin-top:-3.7rem;
        }
        .donut:after { content:""; position:absolute; inset:14px; border-radius:50%; background:#fff; }
        .mini-bars { display:flex; align-items:end; gap:.75rem; height:50px; margin-top: .65rem; }
        .bar { width:12px; border-radius:3px 3px 0 0; background:linear-gradient(180deg,#11b8ad,#0a928c); }
        .progress-line { height:7px; background:#e5e7eb; border-radius:999px; overflow:hidden; margin-top:1.2rem; }
        .progress-line > div { height:100%; background:linear-gradient(90deg,#8b5cf6,#7c3aed); border-radius:999px; }
        .sparkline { width: 100%; height: 56px; margin-top: .45rem; }
        .dashboard-grid { display:grid; grid-template-columns: 1.05fr .98fr 1.08fr; gap:1rem; margin-bottom:1rem; }
        .bottom-grid { display:grid; grid-template-columns: 2.1fr .9fr; gap:1rem; }
        .card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:.85rem; }
        .btn-teal { background:#087f7d; color:#fff; border-radius:7px; padding:.55rem .75rem; font-weight:700; font-size:.78rem; }
        .material-row, .review-row {
            display:grid; grid-template-columns: 34px 1fr auto; gap:.7rem; align-items:center;
            padding:.72rem .45rem; border:1px solid #edf0f3; border-radius:8px; margin-bottom:.45rem;
        }
        .file-badge { width:30px; height:34px; border-radius:5px; color:#fff; display:flex; align-items:center; justify-content:center; font-size:.62rem; font-weight:800; }
        .tag { border-radius:6px; padding:.28rem .48rem; font-size:.7rem; font-weight:700; background:#eef2ff; color:#3730a3; }
        .weak-row { margin:.75rem 0; }
        .weak-top { display:flex; justify-content:space-between; font-size:.78rem; margin-bottom:.35rem; }
        .weak-track { height:7px; background:#e5e7eb; border-radius:999px; overflow:hidden; }
        .weak-fill { height:100%; border-radius:999px; }
        .review-row { grid-template-columns: 46px minmax(0,1fr); border-left:4px solid var(--teal); align-items:start; }
        .review-date { text-align:center; font-weight:800; line-height:1.05; }
        .review-date span { display:block; font-size:.67rem; font-weight:700; color:var(--muted); margin-top:.15rem; }
        .review-row > div:nth-child(2) { min-width:0; }
        .review-row > div:nth-child(2) > div:first-child { font-size:.84rem; line-height:1.35; overflow-wrap:anywhere; }
        .review-row > div:nth-child(3) { grid-column:2; text-align:left !important; margin-top:.25rem; line-height:1.35; }
        .study-table { width:100%; border-collapse:collapse; font-size:.78rem; }
        .study-table th { color:#475569; text-align:left; font-weight:700; padding:.7rem .55rem; border-bottom:1px solid var(--line); }
        .study-table td { padding:.7rem .55rem; border-bottom:1px solid #edf0f3; }
        .method { border-radius:6px; padding:.22rem .45rem; font-weight:700; font-size:.7rem; }
        .m-leitura { background:#dcfce7; color:#166534; }
        .m-questoes { background:#ede9fe; color:#6d28d9; }
        .m-resumo { background:#dbeafe; color:#1d4ed8; }
        .small-progress { height:7px; width:110px; background:#e5e7eb; border-radius:999px; overflow:hidden; display:inline-block; vertical-align:middle; }
        .small-progress div { height:100%; background:#16a34a; border-radius:999px; }
        .legend-row { display:flex; justify-content:space-between; gap:.6rem; font-size:.74rem; margin:.55rem 0; }
        .legend-left { display:flex; align-items:center; gap:.45rem; }
        .dot { width:10px; height:10px; border-radius:3px; display:inline-block; }
        .ring {
            width:150px; height:150px; border-radius:50%;
            background: conic-gradient(#0ea5a3 0 36%, #7c3aed 36% 61%, #f97316 61% 80%, #fbbf24 80% 92%, #cbd5e1 92% 100%);
            position:relative; margin: .7rem auto 1rem;
        }
        .ring:after { content:""; position:absolute; inset:42px; background:#fff; border-radius:50%; }
        .status-note {
            padding: 12px 14px;
            border: 1px solid #d1fae5;
            background: #ecfdf5;
            color: #064e3b;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        .warning-note {
            padding: 12px 14px;
            border: 1px solid #fde68a;
            background: #fffbeb;
            color: #78350f;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        .clean-table { width:100%; border-collapse:separate; border-spacing:0; overflow:hidden; border:1px solid var(--line); border-radius:8px; background:#fff; font-size:.82rem; box-shadow: 0 8px 24px rgba(15,23,42,.035); }
        .clean-table th { text-align:left; color:#334155; font-size:.74rem; text-transform:uppercase; letter-spacing:0; background:#f8fafc; padding:.75rem .8rem; border-bottom:1px solid var(--line); }
        .clean-table td { padding:.8rem; border-bottom:1px solid #edf0f3; vertical-align:top; }
        .clean-table tr:last-child td { border-bottom:0; }
        .score-pill { display:inline-flex; align-items:center; justify-content:center; min-width:54px; padding:.25rem .5rem; border-radius:999px; background:#e6f3f3; color:#075e5a; font-weight:800; }
        .empty-score { color:#64748b; font-weight:700; }
        .strategy-grid { display:grid; grid-template-columns: repeat(4, minmax(180px,1fr)); gap:1rem; margin:1rem 0; }
        .strategy-card { background:#fff; border:1px solid #dfe5ec; border-radius:8px; padding:1rem; box-shadow:0 8px 22px rgba(15,23,42,.04); }
        .strategy-card strong { color:#0f172a; }
        .time-chip { display:inline-flex; align-items:center; justify-content:center; min-width:58px; border-radius:999px; background:#e6f3f3; color:#075e5a; font-weight:800; padding:.25rem .5rem; margin-right:.5rem; }
        .sim-shell { background:#fff; border:1px solid #dfe5ec; border-radius:8px; padding:1.1rem; box-shadow:0 10px 28px rgba(15,23,42,.045); margin-bottom:1rem; }
        .sim-hero { display:grid; grid-template-columns:1fr auto; gap:1rem; align-items:center; margin-bottom:1rem; }
        .sim-title { font-size:1.15rem; font-weight:800; color:#0f172a; }
        .sim-meta { color:#667085; font-size:.82rem; margin-top:.25rem; }
        .sim-badge { border-radius:999px; background:#e6f3f3; color:#075e5a; font-weight:800; padding:.45rem .7rem; font-size:.78rem; }
        .sim-stats { display:grid; grid-template-columns: repeat(4, minmax(130px,1fr)); gap:.75rem; margin:.85rem 0 1rem; }
        .sim-stat { border:1px solid #e5e7eb; border-radius:8px; padding:.85rem; background:#f8fafc; }
        .sim-stat-label { color:#667085; font-weight:700; font-size:.74rem; text-transform:uppercase; }
        .sim-stat-value { color:#0f172a; font-size:1.35rem; font-weight:800; margin-top:.2rem; }
        .question-card { border:1px solid #dfe5ec; border-radius:8px; padding:1rem; background:#fff; margin:.75rem 0; }
        .question-statement { font-size:1rem; font-weight:700; line-height:1.55; color:#0f172a; margin:.75rem 0; }
        .option-row { border:1px solid #e5e7eb; border-radius:8px; padding:.65rem .75rem; margin:.45rem 0; background:#f8fafc; }
        .discipline-score-table { width:100%; border-collapse:separate; border-spacing:0; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden; font-size:.82rem; background:#fff; }
        .discipline-score-table th { text-align:left; padding:.75rem; background:#f8fafc; border-bottom:1px solid #e5e7eb; color:#334155; }
        .discipline-score-table td { padding:.75rem; border-bottom:1px solid #eef2f7; }
        .discipline-score-table tr:last-child td { border-bottom:0; }
        @media (max-width: 1200px) {
            .metric-grid { grid-template-columns: repeat(2, minmax(180px, 1fr)); }
            .strategy-grid { grid-template-columns: repeat(2, minmax(180px,1fr)); }
            .dashboard-grid, .bottom-grid, .topbar, .command-strip, .sim-hero, .sim-stats { grid-template-columns: 1fr; }
            .topbar { margin-top: 0; padding-top: .9rem; }
            .top-metrics { flex-wrap:wrap; }
        }
        @media (max-width: 640px) {
            .main .block-container { padding: 1rem 1rem 2rem 1rem; }
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
                min-width: 100vw !important;
                width: 100vw !important;
            }
            .topbar { margin-left: -1rem; margin-right: -1rem; padding-left: 1rem; padding-right: 1rem; }
            .exam-title { font-size: 1rem; }
            .top-item { border-right: 0; padding-right: 0; }
            .user-box { justify-content:flex-start; min-width: 0; }
            .metric-grid { grid-template-columns: 1fr; }
            .strategy-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_users() -> pd.DataFrame:
    return db.fetch_df("SELECT * FROM users ORDER BY id ASC")


def selected_user() -> dict[str, object]:
    users = get_users()
    if users.empty:
        db.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Usuário Local", "local@app"))
        users = get_users()

    labels = {
        f"{row['name']} ({row['email'] or 'sem e-mail'})": int(row["id"])
        for _, row in users.iterrows()
    }
    current_id = st.session_state.get("active_user_id", int(users.iloc[0]["id"]))
    current_index = 0
    for idx, user_id in enumerate(labels.values()):
        if int(user_id) == int(current_id):
            current_index = idx
            break
    selected_label = st.sidebar.selectbox("Usuário", list(labels.keys()), index=current_index, key="active_user_label")
    user_id = labels[selected_label]
    st.session_state["active_user_id"] = user_id
    row = users[users["id"] == user_id].iloc[0]
    return {"id": int(row["id"]), "name": str(row["name"]), "email": str(row["email"] or "")}


def create_user_widget() -> None:
    with st.sidebar.expander("Trocar/criar usuário", expanded=False):
        name = st.text_input("Nome do novo usuário", key="new_user_name")
        email = st.text_input("E-mail", key="new_user_email")
        if st.button("Criar usuário", key="create_user"):
            if not name.strip():
                st.error("Informe o nome do usuário.")
                return
            existing = db.fetch_one(
                "SELECT id FROM users WHERE email = ? AND ? <> ''",
                (email.strip(), email.strip()),
            )
            if existing:
                st.session_state["active_user_id"] = int(existing["id"])
                st.success("Usuário já existia. Ele foi selecionado.")
            else:
                user_id = db.execute(
                    "INSERT INTO users (name, email) VALUES (?, ?)",
                    (name.strip(), email.strip() or None),
                )
                st.session_state["active_user_id"] = user_id
                st.success("Usuário criado e selecionado.")
            st.rerun()


def get_concursos(user_id: int) -> pd.DataFrame:
    return db.fetch_df("SELECT * FROM concursos WHERE user_id = ? ORDER BY created_at DESC", (user_id,))


def selected_concurso_id(concursos: pd.DataFrame) -> int | None:
    if concursos.empty:
        return None
    if len(concursos) == 1:
        return int(concursos.iloc[0]["id"])
    labels = {
        f"{row['name']} | {row['orgao'] or 'Sem órgão'}": int(row["id"])
        for _, row in concursos.iterrows()
    }
    choice = st.sidebar.selectbox("Concurso ativo", list(labels.keys()))
    return labels[choice]


def _fmt_minutes(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins:02d}m"


def _safe(value: object) -> str:
    return escape(str(value if value is not None else ""))


def _material_color(name: str) -> str:
    ext = Path(name).suffix.lower()
    return {
        ".pdf": "#ef4444",
        ".docx": "#2563eb",
        ".xlsx": "#16a34a",
        ".xls": "#16a34a",
        ".pptx": "#f97316",
        ".jpg": "#7c3aed",
        ".jpeg": "#7c3aed",
        ".png": "#7c3aed",
    }.get(ext, "#64748b")


def _render_simulation_table(rows: pd.DataFrame, empty_message: str = "Nenhum simulado registrado.") -> str:
    if rows.empty:
        return f'<div class="muted">{_safe(empty_message)}</div>'
    html = [
        '<table class="clean-table">',
        "<thead><tr><th>Data</th><th>Simulado</th><th>Tipo</th><th>Questões</th><th>Acertos</th><th>Taxa</th></tr></thead><tbody>",
    ]
    for _, row in rows.iterrows():
        total = int(row.get("total_questions", 0) or 0)
        correct = int(row.get("correct_answers", 0) or 0)
        accuracy = float(row.get("accuracy", 0) or 0)
        score = f"{accuracy:.1f}%" if total else "Aguardando"
        score_class = "score-pill" if total else "empty-score"
        mode = str(row.get("mode", "")).replace("_", " ").title()
        html.append(
            "<tr>"
            f"<td>{_safe(row.get('simulation_date', ''))}</td>"
            f"<td><strong>#{int(row.get('id', 0))} - {_safe(row.get('title', ''))}</strong></td>"
            f"<td>{_safe(mode)}</td>"
            f"<td>{total}</td>"
            f"<td>{correct}</td>"
            f'<td><span class="{score_class}">{_safe(score)}</span></td>'
            "</tr>"
        )
    html.append("</tbody></table>")
    return "".join(html)


def _render_dashboard_html(
    topics: pd.DataFrame,
    materials: pd.DataFrame,
    sessions: pd.DataFrame,
    reviews: pd.DataFrame,
    performance: pd.DataFrame,
    total_minutes: int,
    avg_accuracy: float,
    user: dict[str, object],
) -> str:
    progress = progress_percent(topics)
    discipline_count = int(topics["discipline"].nunique()) if not topics.empty else 0
    completed_topics = int(topics["status"].isin(["concluido", "revisao"]).sum()) if not topics.empty else 0
    question_total = int(performance["total_questions"].sum()) if not performance.empty else 0
    today_tasks = get_daily_plan(int(topics.iloc[0]["concurso_id"]), date.today()) if not topics.empty else pd.DataFrame()
    pending_reviews = pending_review_count(int(topics.iloc[0]["concurso_id"]), date.today()) if not topics.empty else 0
    weak = weak_topics(performance, limit=5)
    readiness = readiness_score(topics, results=pd.DataFrame(), sessions=sessions, reviews=reviews)
    user_name = str(user.get("name") or "Usuário Local")
    initials = "".join(part[:1] for part in user_name.split()[:2]).upper() or "U"
    concurso_id = int(topics.iloc[0]["concurso_id"]) if not topics.empty else 0
    next_task = next_pending_task(concurso_id, date.today()) if concurso_id else None
    if next_task:
        focus_title = f"{next_task.get('discipline', '')}: {next_task.get('topic', '')}"
        focus_meta = f"{str(next_task.get('task_type', 'estudo')).replace('_', ' ').title()} · {_fmt_minutes(int(next_task.get('target_minutes', 0) or 0))}"
    else:
        focus_title = "Gerar ou revisar o planejamento diário"
        focus_meta = "Sem tarefa pendente para hoje"

    if materials.empty:
        material_rows = '<div class="muted">Nenhum material cadastrado ainda.</div>'
    else:
        material_rows = ""
        for _, row in materials.head(5).iterrows():
            ext = Path(str(row["original_name"])).suffix.upper().replace(".", "") or "ARQ"
            color = _material_color(str(row["original_name"]))
            tag = _safe(row.get("category", "material")).title()
            material_rows += (
                f'<div class="material-row">'
                f'<div class="file-badge" style="background:{color}">{_safe(ext[:4])}</div>'
                f'<div><div style="font-weight:700">{_safe(row["original_name"])}</div>'
                f'<div class="muted">{_safe(row.get("file_type", ""))} · {_safe(row.get("topic", ""))}</div></div>'
                f'<div class="tag">{tag}</div>'
                f'</div>'
            )

    if weak.empty:
        weak_rows = '<div class="muted">Registre questões para detectar pontos fracos.</div>'
    else:
        colors = ["#ef4444", "#ef4444", "#f97316", "#f59e0b", "#eab308"]
        weak_rows = ""
        for idx, (_, row) in enumerate(weak.iterrows()):
            accuracy = int(round(float(row["accuracy"]) * 100))
            bar = max(8, min(100, accuracy))
            color = colors[min(idx, len(colors) - 1)]
            weak_rows += (
                f'<div class="weak-row">'
                f'<div class="weak-top"><span>{_safe(row["discipline"])}</span><strong>{accuracy}%</strong></div>'
                f'<div class="weak-track"><div class="weak-fill" style="width:{bar}%; background:{color}"></div></div>'
                f'</div>'
            )

    if reviews.empty:
        review_rows = '<div class="muted">Nenhuma revisão programada.</div>'
    else:
        review_rows = ""
        colors = ["#0ea5a3", "#7c3aed", "#f97316", "#0ea5a3", "#7c3aed"]
        for idx, (_, row) in enumerate(reviews.head(5).iterrows()):
            raw_date = str(row["review_date"])
            try:
                parsed = pd.to_datetime(raw_date)
                day = parsed.strftime("%d")
                mon = parsed.strftime("%b").upper().replace(".", "")
            except Exception:
                day, mon = raw_date[:2], ""
            color = colors[min(idx, len(colors) - 1)]
            review_rows += (
                f'<div class="review-row" style="border-left-color:{color}">'
                f'<div class="review-date">{_safe(day)}<span>{_safe(mon)}</span></div>'
                f'<div><div style="font-weight:800">{_safe(row["topic"])}</div>'
                f'<div class="muted">{_safe(row["discipline"])}</div></div>'
                f'<div class="muted" style="text-align:right">{_safe(row["status"])}<br>{_safe(row.get("reason", ""))}</div>'
                f'</div>'
            )

    if sessions.empty:
        session_rows = """
        <tr><td colspan="6" class="muted">Nenhuma sessão registrada ainda.</td></tr>
        """
    else:
        session_rows = ""
        session_view = sessions.merge(
            topics[["id", "discipline", "topic"]],
            left_on="topic_id",
            right_on="id",
            how="left",
            suffixes=("", "_topic"),
        )
        for idx, (_, row) in enumerate(session_view.head(5).iterrows()):
            method = ["Leitura", "Resumo", "Questões"][idx % 3]
            method_class = {"Leitura": "m-leitura", "Resumo": "m-resumo", "Questões": "m-questoes"}[method]
            pct = 100 if int(row.get("minutes", 0)) >= 50 else max(35, int(row.get("minutes", 0)))
            session_rows += (
                f'<tr><td>{_safe(str(row.get("studied_at", ""))[:16])}</td>'
                f'<td>{_safe(row.get("discipline", ""))}</td>'
                f'<td>{_safe(row.get("topic", ""))}</td>'
                f'<td>{_fmt_minutes(int(row.get("minutes", 0)))}</td>'
                f'<td><span class="method {method_class}">{method}</span></td>'
                f'<td>{pct}% <span class="small-progress"><div style="width:{pct}%"></div></span></td></tr>'
            )

    top_disciplines = (
        sessions.merge(topics[["id", "discipline"]], left_on="topic_id", right_on="id", how="left")
        if not sessions.empty and not topics.empty
        else pd.DataFrame()
    )
    if top_disciplines.empty:
        legend_rows = (
            '<div class="legend-row"><span class="legend-left"><i class="dot" style="background:#0ea5a3"></i>Legislação Social</span><span>0h</span></div>'
            '<div class="legend-row"><span class="legend-left"><i class="dot" style="background:#7c3aed"></i>Pedagogia</span><span>0h</span></div>'
            '<div class="legend-row"><span class="legend-left"><i class="dot" style="background:#f97316"></i>Português</span><span>0h</span></div>'
        )
    else:
        grouped = top_disciplines.groupby("discipline")["minutes"].sum().sort_values(ascending=False).head(5)
        palette = ["#0ea5a3", "#7c3aed", "#f97316", "#fbbf24", "#cbd5e1"]
        legend_rows = ""
        for idx, (discipline, minutes) in enumerate(grouped.items()):
            legend_rows += (
                f'<div class="legend-row"><span class="legend-left">'
                f'<i class="dot" style="background:{palette[idx]}"></i>{_safe(discipline)}</span>'
                f'<span>{_fmt_minutes(int(minutes))}</span></div>'
            )

    return f"""
    <div class="topbar">
        <div class="exam-select">
            <div class="exam-title">SEDES DF 2026 ˅</div>
            <div class="exam-subtitle">Especialista em Desenvolvimento e Assistência Social - Pedagogia</div>
        </div>
        <div class="top-metrics">
            <div class="top-item"><div class="top-icon">▣</div><div><div class="top-label">Prova em</div><div class="top-value">06/09/2026</div></div></div>
            <div class="top-item"><div class="top-icon">◎</div><div><div class="top-label">Meta diária</div><div class="top-value">4h líquidas</div></div></div>
            <div class="top-item"><div class="top-icon">◴</div><div><div class="top-label">Hoje</div><div class="top-value">{len(today_tasks)} tarefas · {pending_reviews} revisões</div></div></div>
        </div>
        <div class="user-box"><div class="avatar">{_safe(initials)}</div><div><div class="top-label">{_safe(user_name)}</div><div class="top-value">Perfil ativo</div></div></div>
    </div>
    <div class="command-strip">
        <div class="command-item">
            <div class="command-icon">1</div>
            <div><div class="command-label">Próxima ação</div><div class="command-title">{_safe(focus_title)}</div><div class="muted">{_safe(focus_meta)}</div></div>
        </div>
        <div class="command-item">
            <div class="command-icon" style="background:linear-gradient(145deg,#7c3aed,#5b21b6)">Q</div>
            <div><div class="command-label">Treino Quadrix</div><div class="command-title">{question_total} questões registradas</div><div class="muted">Certo/Errado com desconto</div></div>
        </div>
        <div class="command-item">
            <div class="command-icon" style="background:linear-gradient(145deg,#f97316,#c2410c)">R</div>
            <div><div class="command-label">Revisões</div><div class="command-title">{pending_reviews} pendentes hoje</div><div class="muted">Reforce pontos fracos</div></div>
        </div>
    </div>
    <div class="page-title">Progresso</div>
    <div class="metric-grid">
        <div class="card">
            <div class="card-title">Progresso geral</div>
            <div class="big-number">{progress}%</div>
            <div class="muted">do conteúdo</div>
            <div class="donut" style="--p:{progress}%"></div>
            <div class="delta">▲ 8% vs semana passada</div>
        </div>
        <div class="card">
            <div class="card-title">Horas líquidas</div>
            <div class="big-number">{_fmt_minutes(total_minutes)}</div>
            <div class="muted">registradas</div>
            <div class="mini-bars"><div class="bar" style="height:14px"></div><div class="bar" style="height:19px"></div><div class="bar" style="height:28px"></div><div class="bar" style="height:21px"></div><div class="bar" style="height:42px"></div><div class="bar" style="height:24px"></div><div class="bar" style="height:34px"></div></div>
        </div>
        <div class="card">
            <div class="card-title">Disciplinas</div>
            <div class="big-number">{discipline_count} <span class="muted">/ {discipline_count}</span></div>
            <div class="muted">{completed_topics} tópicos concluídos</div>
            <div class="progress-line"><div style="width:{progress}%"></div></div>
        </div>
        <div class="card">
            <div class="card-title">Questões resolvidas</div>
            <div class="big-number">{question_total}</div>
            <div class="muted">registradas</div>
            <div class="delta">▲ 23% vs mês passado</div>
        </div>
        <div class="card">
            <div class="card-title">Taxa de acerto</div>
            <div class="big-number">{avg_accuracy}%</div>
            <div class="muted">geral</div>
            <svg class="sparkline" viewBox="0 0 180 60"><polyline points="0,45 18,35 34,24 50,38 68,34 84,18 102,10 120,24 138,28 154,16 172,22 180,12" fill="none" stroke="#7c3aed" stroke-width="4" stroke-linecap="round"/></svg>
        </div>
    </div>
    <div class="dashboard-grid">
        <div class="card">
            <div class="card-head"><div class="page-title" style="margin:0">Materiais recentes</div><div class="tag">Envio no menu Materiais</div></div>
            {material_rows}
            <div class="muted" style="margin-top:.8rem; font-weight:700">Ver todos os materiais ›</div>
        </div>
        <div class="card">
            <div class="card-head"><div class="page-title" style="margin:0">Pontos fracos</div><span class="muted">ⓘ</span></div>
            <div style="display:flex; gap:.45rem; margin-bottom:.8rem"><span class="tag" style="background:#e6f3f3;color:#0f3c3b">Por disciplina</span><span class="tag" style="background:#fff;color:#111827;border:1px solid #e5e7eb">Por assunto</span></div>
            {weak_rows}
            <div class="muted" style="margin-top:1.2rem; font-weight:700">Ver análise completa ›</div>
        </div>
        <div class="card">
            <div class="card-head"><div class="page-title" style="margin:0">Próximas revisões</div><span class="muted">□</span></div>
            {review_rows}
            <div class="muted" style="margin-top:.8rem; font-weight:700">Ver todas as revisões ›</div>
        </div>
    </div>
    <div class="bottom-grid">
        <div class="card">
            <div class="page-title" style="margin-top:0">Sessões de estudo recentes</div>
            <table class="study-table">
                <thead><tr><th>Data</th><th>Disciplina</th><th>Assunto</th><th>Tempo</th><th>Método</th><th>Progresso</th></tr></thead>
                <tbody>{session_rows}</tbody>
            </table>
            <div class="muted" style="text-align:center; margin-top:.8rem; font-weight:700">Ver todas as sessões ›</div>
        </div>
        <div class="card">
            <div class="page-title" style="margin-top:0">Distribuição do tempo (mês)</div>
            <div class="ring"></div>
            {legend_rows}
            <div class="muted" style="margin-top:1rem; font-weight:700">Ver relatório completo ›</div>
        </div>
    </div>
    """


def dashboard(concurso_id: int, user: dict[str, object]) -> None:
    topics = db.fetch_df("SELECT * FROM topics WHERE concurso_id = ? ORDER BY question_count DESC, priority DESC, discipline", (concurso_id,))
    materials = db.fetch_df("SELECT * FROM materials WHERE concurso_id = ? ORDER BY created_at DESC", (concurso_id,))
    results = db.fetch_df("SELECT * FROM question_results WHERE concurso_id = ?", (concurso_id,))
    sessions = db.fetch_df("SELECT * FROM study_sessions WHERE concurso_id = ? ORDER BY studied_at DESC", (concurso_id,))
    reviews = db.fetch_df(
        """
        SELECT r.id, r.review_date, r.status, r.reason, t.discipline, t.topic
        FROM reviews r
        JOIN topics t ON t.id = r.topic_id
        WHERE r.concurso_id = ?
        ORDER BY r.review_date ASC
        """,
        (concurso_id,),
    )

    performance = topic_performance(results, topics)
    total_minutes = int(sessions["minutes"].sum()) if not sessions.empty else 0
    avg_accuracy = 0 if performance.empty else round(float(performance["accuracy"].mean() * 100), 1)
    readiness = readiness_score(topics, results, sessions, reviews)
    recs = recommendations(topics, results, reviews)

    html = _render_dashboard_html(
        topics=topics,
        materials=materials,
        sessions=sessions,
        reviews=reviews,
        performance=performance,
        total_minutes=total_minutes,
        avg_accuracy=avg_accuracy,
        user=user,
    )
    st.markdown(html, unsafe_allow_html=True)
    action_col, _ = st.columns([1, 4])
    if action_col.button("Abrir envio de materiais", type="primary", key="dashboard_upload_material"):
        st.session_state["main_nav"] = "▣  Materiais"
        st.rerun()
    with st.expander("Diagnóstico operacional para aprovação", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prontidão", f"{readiness['score']}%")
        c2.metric("Conteúdo", f"{readiness['progress']}%")
        c3.metric("Acerto médio", f"{readiness['accuracy']}%")
        c4.metric("Horas", f"{readiness['hours']}h")
        if recs:
            st.markdown("**Ações recomendadas agora:**")
            for rec in recs:
                st.write(f"- {rec}")
        else:
            st.success("Sem recomendações críticas no momento. Continue executando o plano diário.")


def upload_view(concurso_id: int) -> None:
    st.subheader("Upload de edital e materiais")
    uploaded = st.file_uploader(
        "Enviar arquivo",
        type=[ext.replace(".", "") for ext in SUPPORTED_EXTENSIONS],
        accept_multiple_files=False,
    )
    category = st.selectbox("Categoria", ["edital", "material", "questões", "simulado", "anotações"])
    topic = st.text_input("Assunto relacionado", placeholder="Ex.: LDB, SUAS, Psicologia Social")
    use_ai = st.checkbox("Analisar com Ollama/gemma2:2b", value=False)

    if uploaded and st.button("Salvar e processar", type="primary"):
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            st.error(f"Formato não suportado: {suffix}")
            return
        target = db.save_uploaded_file(uploaded.name, uploaded.getvalue(), UPLOAD_DIR)
        try:
            text = extract_text(target)
        except Exception as exc:
            st.error(f"Falha ao extrair texto: {exc}")
            return

        summary = "Análise de IA não executada."
        if use_ai:
            if is_ollama_available():
                with st.spinner("Analisando com Ollama/gemma2:2b..."):
                    try:
                        summary = summarize_material(text, category)
                    except Exception as exc:
                        summary = f"Falha na análise por IA: {exc}"
            else:
                summary = "Ollama/gemma2:2b não está disponível no momento."

        material_id = db.execute(
            """
            INSERT INTO materials
            (concurso_id, filename, original_name, file_type, category, topic, extracted_text, ai_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (concurso_id, target.name, uploaded.name, suffix, category, topic, text, summary),
        )

        if category == "edital" and use_ai and is_ollama_available():
            with st.spinner("Extraindo tópicos do edital com IA..."):
                for item in extract_topics_from_edital(text):
                    db.execute(
                        """
                        INSERT OR IGNORE INTO topics (concurso_id, discipline, topic, priority)
                        VALUES (?, ?, ?, ?)
                        """,
                        (concurso_id, item["discipline"], item["topic"], item["priority"]),
                    )
        st.success(f"Arquivo processado e salvo. ID do material: {material_id}")


def study_view(concurso_id: int) -> None:
    st.subheader("Registrar estudo")
    topics = db.fetch_df("SELECT id, discipline, topic FROM topics WHERE concurso_id = ? ORDER BY discipline, topic", (concurso_id,))
    if topics.empty:
        st.warning("Cadastre tópicos antes de registrar estudo.")
        return
    today_task = next_pending_task(concurso_id, date.today())
    if today_task:
        st.markdown(
            (
                '<div class="status-note">'
                f"Próxima tarefa do plano: <strong>{_safe(str(today_task['task_type']).title())}</strong> - "
                f"{_safe(today_task['discipline'])} / {_safe(today_task['topic'])} "
                f"({_fmt_minutes(int(today_task['target_minutes']))})."
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    labels = {f"{row['discipline']} - {row['topic']}": int(row["id"]) for _, row in topics.iterrows()}
    default_index = 0
    if today_task:
        task_label = f"{today_task['discipline']} - {today_task['topic']}"
        if task_label in labels:
            default_index = list(labels.keys()).index(task_label)
    topic_id = labels[st.selectbox("Tópico estudado", list(labels.keys()), index=default_index)]
    default_minutes = int(today_task["target_minutes"]) if today_task else 50
    minutes = st.number_input("Minutos líquidos", min_value=1, max_value=720, value=default_minutes)
    status = st.selectbox("Status do tópico", ["em_andamento", "concluido", "revisao", "nao_iniciado"])
    difficulty = st.slider("Dificuldade percebida", min_value=1, max_value=5, value=3)
    notes = st.text_area("Observações")
    if st.button("Registrar sessão", type="primary"):
        db.execute(
            "INSERT INTO study_sessions (concurso_id, topic_id, minutes, notes) VALUES (?, ?, ?, ?)",
            (concurso_id, topic_id, int(minutes), notes),
        )
        db.execute(
            "UPDATE topics SET status = ?, difficulty = ? WHERE id = ?",
            (status, int(difficulty), topic_id),
        )
        for days in [1, 7, 30]:
            db.execute(
                """
                INSERT INTO reviews (concurso_id, topic_id, review_date, reason)
                VALUES (?, ?, ?, ?)
                """,
                (concurso_id, topic_id, (date.today() + timedelta(days=days)).isoformat(), f"Revisão D+{days}"),
            )
        closed = complete_matching_tasks(
            concurso_id,
            topic_id,
            date.today(),
            ("estudo", "revisao"),
        )
        if closed:
            st.success(f"Sessão registrada, {closed} tarefa(s) do plano concluída(s) e revisões D+1, D+7 e D+30 programadas.")
        else:
            st.success("Sessão registrada e revisões D+1, D+7 e D+30 programadas.")


def questions_view(concurso_id: int) -> None:
    st.subheader("Registrar simulado ou questões")
    tab_bank, tab_quick, tab_sim = st.tabs(["Banco local", "Bateria rápida", "Simulado"])
    with tab_bank:
        _question_bank_view(concurso_id)
    with tab_quick:
        _quick_questions_view(concurso_id)
    with tab_sim:
        _simulation_view(concurso_id)


def _question_bank_view(concurso_id: int) -> None:
    total_bank = get_question_count(concurso_id)
    col1, col2 = st.columns([1, 2])
    col1.metric("Questões locais", total_bank)
    if col2.button("Sincronizar banco local"):
        created = seed_question_bank(concurso_id)
        st.success(f"Banco sincronizado. {created} nova(s) questão(ões).")
        st.rerun()

    if get_question_count(concurso_id) == 0:
        st.warning("Banco local vazio. Clique em sincronizar banco local.")
        return

    topics = db.fetch_df(
        "SELECT id, discipline, topic FROM topics WHERE concurso_id = ? ORDER BY question_count DESC, discipline, topic",
        (concurso_id,),
    )
    topic_options = {"Todos os tópicos": None}
    topic_options.update({f"{row['discipline']} - {row['topic']}": int(row["id"]) for _, row in topics.iterrows()})
    selected_topic = topic_options[st.selectbox("Filtrar tópico", list(topic_options.keys()))]

    state_key = f"local_question_{concurso_id}_{selected_topic or 'all'}"
    answered_key = f"{state_key}_answered"
    if st.button("Próxima questão local", type="primary") or state_key not in st.session_state:
        question = next_question(concurso_id, selected_topic)
        if not question:
            st.warning("Nenhuma questão encontrada para esse filtro.")
            return
        st.session_state[state_key] = question
        st.session_state[answered_key] = False

    question = st.session_state.get(state_key)
    if not question:
        return

    st.markdown(f"**{question['discipline']}**  \n:gray[{question['topic']}]")
    st.write(question["statement"])
    for key in ["A", "B", "C", "D", "E"]:
        st.write(f"**{key})** {question.get(f'option_{key.lower()}') or ''}")

    answer = st.radio("Resposta", ["A", "B", "C", "D", "E", "Pular"], horizontal=True, key=f"answer_{state_key}")
    if st.button("Corrigir questão local"):
        if st.session_state.get(answered_key):
            st.info("Questão já corrigida. Clique em Próxima questão local.")
            return
        result = record_attempt(concurso_id, question, answer)
        closed = complete_matching_tasks(
            concurso_id,
            int(question["topic_id"]),
            date.today(),
            ("questoes",),
        )
        st.session_state[answered_key] = True
        if result["skipped"]:
            st.info(f"Questão pulada. Gabarito: {result['expected']}.")
        elif result["is_correct"]:
            st.success(f"Você acertou. Gabarito: {result['expected']}.")
        else:
            st.error(f"Você errou. Gabarito: {result['expected']}. Revisão D+2 criada.")
        if closed:
            st.success(f"{closed} tarefa(s) de questões do plano de hoje concluída(s).")
        st.markdown("**Justificativa**")
        st.write(question["justification"])

    summary = attempts_summary(concurso_id)
    if not summary.empty:
        st.markdown("### Histórico do banco local")
        st.dataframe(summary, hide_index=True, use_container_width=True)


def _quick_questions_view(concurso_id: int) -> None:
    topics = db.fetch_df("SELECT id, discipline, topic FROM topics WHERE concurso_id = ? ORDER BY discipline, topic", (concurso_id,))
    if topics.empty:
        st.warning("Cadastre tópicos antes de registrar questões.")
        return
    labels = {f"{row['discipline']} - {row['topic']}": int(row["id"]) for _, row in topics.iterrows()}
    topic_id = labels[st.selectbox("Tópico", list(labels.keys()))]
    total = st.number_input("Questões respondidas", min_value=1, max_value=300, value=10)
    correct = st.number_input("Acertos", min_value=0, max_value=int(total), value=min(7, int(total)))
    difficulty = st.slider("Dificuldade da bateria", min_value=1, max_value=5, value=3)
    accuracy = correct / total
    if accuracy < 0.6:
        feedback = "Ponto fraco: revisar teoria, refazer questões e criar resumo ativo."
    elif accuracy < 0.8:
        feedback = "Atenção: desempenho intermediário, revisar erros e repetir questões em 7 dias."
    else:
        feedback = "Bom desempenho: manter revisão espaçada."
    st.info(feedback)
    if st.button("Salvar resultado", type="primary"):
        db.execute(
            """
            INSERT INTO question_results
            (concurso_id, topic_id, total_questions, correct_answers, difficulty, feedback)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (concurso_id, topic_id, int(total), int(correct), int(difficulty), feedback),
        )
        if accuracy < 0.8:
            db.execute(
                """
                INSERT INTO reviews (concurso_id, topic_id, review_date, reason)
                VALUES (?, ?, ?, ?)
                """,
                (concurso_id, topic_id, (date.today() + timedelta(days=2)).isoformat(), "Baixo desempenho em questões"),
            )
        closed = complete_matching_tasks(concurso_id, topic_id, date.today(), ("questoes",))
        if closed:
            st.success(f"Resultado salvo e {closed} tarefa(s) de questões do plano concluída(s).")
        else:
            st.success("Resultado salvo.")


def _fmt_seconds(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _load_simulation_questions(concurso_id: int, total_questions: int, discipline: str | None) -> list[dict[str, object]]:
    params: list[object] = [concurso_id, concurso_id]
    where = "qb.concurso_id = ? AND t.concurso_id = ?"
    if discipline:
        where += " AND t.discipline = ?"
        params.append(discipline)
    params.append(total_questions)
    rows = db.fetch_df(
        f"""
        SELECT qb.*, t.discipline, t.topic
        FROM question_bank qb
        JOIN topics t ON t.id = qb.topic_id
        WHERE {where}
        ORDER BY t.question_count DESC, qb.difficulty DESC, RANDOM()
        LIMIT ?
        """,
        tuple(params),
    )
    return [dict(row) for _, row in rows.iterrows()]


def _simulation_elapsed(state: dict[str, object]) -> int:
    started_at = str(state.get("started_at") or datetime.now().isoformat())
    try:
        return int((datetime.now() - datetime.fromisoformat(started_at)).total_seconds())
    except ValueError:
        return 0


def _render_timer_component(elapsed_seconds: int) -> None:
    components.html(
        f"""
        <div style="font-family:Inter,Segoe UI,sans-serif;border:1px solid #dfe5ec;border-radius:8px;padding:12px 14px;background:#fff;box-shadow:0 8px 22px rgba(15,23,42,.04)">
            <div style="font-size:11px;font-weight:800;color:#667085;text-transform:uppercase">Cronômetro</div>
            <div id="sim-timer" style="font-size:28px;font-weight:900;color:#0f172a;margin-top:2px">00:00</div>
        </div>
        <script>
            let seconds = {max(0, int(elapsed_seconds))};
            const target = document.getElementById("sim-timer");
            function renderTimer() {{
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = seconds % 60;
                target.textContent = h > 0
                    ? String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0")
                    : String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
                seconds += 1;
            }}
            renderTimer();
            setInterval(renderTimer, 1000);
        </script>
        """,
        height=82,
    )


def _interactive_simulation_view(concurso_id: int, topics: pd.DataFrame) -> None:
    state_key = f"interactive_simulation_{concurso_id}"
    total_bank = get_question_count(concurso_id)
    if total_bank == 0:
        st.warning("Banco local vazio. Sincronize o banco local antes de iniciar um simulado interativo.")
        if st.button("Sincronizar banco local para simulado", type="primary"):
            created = seed_question_bank(concurso_id)
            st.success(f"Banco sincronizado. {created} nova(s) questão(ões).")
            st.rerun()
        return

    state = st.session_state.get(state_key)
    if state and state.get("finished"):
        _render_simulation_finish(concurso_id, state)
        return

    if not state or not state.get("active"):
        st.markdown(
            '<div class="status-note">Monte um simulado com questões reais do banco local. Cada erro cria revisão automática D+2 e alimenta o desempenho por disciplina.</div>',
            unsafe_allow_html=True,
        )
        disciplines = ["Todas as disciplinas"] + sorted(topics["discipline"].dropna().unique().tolist())
        with st.form("simulado_interativo_inicio"):
            title = st.text_input("Título", value=f"Simulado interativo {date.today().strftime('%d/%m/%Y')}")
            discipline_label = st.selectbox("Foco", disciplines)
            max_questions = max(1, min(50, int(total_bank)))
            total_questions = st.number_input("Quantidade de questões", min_value=1, max_value=max_questions, value=min(10, max_questions))
            submitted = st.form_submit_button("Iniciar simulado", type="primary")
        if submitted:
            discipline = None if discipline_label == "Todas as disciplinas" else discipline_label
            questions = _load_simulation_questions(concurso_id, int(total_questions), discipline)
            if not questions:
                st.error("Não há questões suficientes para esse filtro.")
                return
            sim_id = create_simulation(concurso_id, title, "simulado_interativo", f"Foco: {discipline_label}")
            st.session_state[f"active_simulation_{concurso_id}"] = sim_id
            st.session_state[state_key] = {
                "active": True,
                "finished": False,
                "simulation_id": sim_id,
                "title": title.strip(),
                "questions": questions,
                "index": 0,
                "started_at": datetime.now().isoformat(),
                "answers": [],
                "current_answered": False,
                "last_result": None,
            }
            st.rerun()
        _render_simulation_results(concurso_id)
        return

    questions = list(state.get("questions") or [])
    index = int(state.get("index") or 0)
    answers = list(state.get("answers") or [])
    elapsed = _simulation_elapsed(state)
    score = sum(float(item.get("score_delta", 0.0)) for item in answers)
    correct = sum(1 for item in answers if item.get("is_correct"))
    errors = sum(1 for item in answers if not item.get("is_correct") and not item.get("skipped"))
    skipped = sum(1 for item in answers if item.get("skipped"))

    if not questions or index >= len(questions):
        state["active"] = False
        state["finished"] = True
        st.session_state[state_key] = state
        _render_simulation_finish(concurso_id, state)
        return

    question = questions[index]
    st.markdown(
        f"""
        <div class="sim-shell">
            <div class="sim-hero">
                <div>
                    <div class="sim-title">{_safe(state.get("title", "Simulado interativo"))}</div>
                    <div class="sim-meta">Questão {index + 1} de {len(questions)} · pontuação Quadrix: +1 acerto, -0,5 erro, 0 pular</div>
                </div>
                <div class="sim-badge">#{int(state["simulation_id"])}</div>
            </div>
            <div class="sim-stats">
                <div class="sim-stat"><div class="sim-stat-label">Pontuação</div><div class="sim-stat-value">{score:.1f}</div></div>
                <div class="sim-stat"><div class="sim-stat-label">Acertos</div><div class="sim-stat-value">{correct}</div></div>
                <div class="sim-stat"><div class="sim-stat-label">Erros</div><div class="sim-stat-value">{errors}</div></div>
                <div class="sim-stat"><div class="sim-stat-label">Puladas</div><div class="sim-stat-value">{skipped}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_timer_component(elapsed)

    st.markdown(
        f"""
        <div class="question-card">
            <div class="sim-meta"><strong>{_safe(question.get("discipline", ""))}</strong> · {_safe(question.get("topic", ""))}</div>
            <div class="question-statement">{_safe(question.get("statement", ""))}</div>
            <div class="option-row"><strong>A)</strong> {_safe(question.get("option_a", ""))}</div>
            <div class="option-row"><strong>B)</strong> {_safe(question.get("option_b", ""))}</div>
            <div class="option-row"><strong>C)</strong> {_safe(question.get("option_c", ""))}</div>
            <div class="option-row"><strong>D)</strong> {_safe(question.get("option_d", ""))}</div>
            <div class="option-row"><strong>E)</strong> {_safe(question.get("option_e", ""))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    answer_key = f"interactive_answer_{concurso_id}_{state['simulation_id']}_{index}"
    answer = st.radio("Resposta", ["A", "B", "C", "D", "E", "Pular"], horizontal=True, key=answer_key)

    col1, col2, col3 = st.columns([1, 1, 1.2])
    if col1.button("Corrigir", type="primary", key=f"correct_sim_{concurso_id}_{state['simulation_id']}_{index}"):
        if state.get("current_answered"):
            st.info("Esta questão já foi corrigida. Avance para a próxima.")
        else:
            result = record_simulation_answer(concurso_id, int(state["simulation_id"]), question, answer, elapsed)
            result.update(
                {
                    "question_id": int(question["id"]),
                    "topic_id": int(question["topic_id"]),
                    "discipline": str(question.get("discipline", "")),
                    "topic": str(question.get("topic", "")),
                    "justification": str(question.get("justification", "")),
                }
            )
            answers.append(result)
            state["answers"] = answers
            state["current_answered"] = True
            state["last_result"] = result
            complete_matching_tasks(concurso_id, int(question["topic_id"]), date.today(), ("questoes",))
            st.session_state[state_key] = state
            st.rerun()

    if col2.button("Próxima", key=f"next_sim_{concurso_id}_{state['simulation_id']}_{index}"):
        if not state.get("current_answered"):
            st.warning("Corrija ou pule a questão antes de avançar.")
        else:
            state["index"] = index + 1
            state["current_answered"] = False
            state["last_result"] = None
            st.session_state[state_key] = state
            st.rerun()

    if col3.button("Encerrar e ver resultado", key=f"finish_sim_{concurso_id}_{state['simulation_id']}"):
        state["active"] = False
        state["finished"] = True
        st.session_state[state_key] = state
        st.rerun()

    last_result = state.get("last_result")
    if last_result:
        if last_result.get("skipped"):
            st.info(f"Questão pulada. Gabarito: {last_result['expected']}.")
        elif last_result.get("is_correct"):
            st.success(f"Você acertou. Gabarito: {last_result['expected']}.")
        else:
            st.error(f"Você errou. Gabarito: {last_result['expected']}. Revisão D+2 criada automaticamente.")
        st.markdown("**Justificativa**")
        st.write(last_result.get("justification", ""))


def _render_simulation_finish(concurso_id: int, state: dict[str, object]) -> None:
    elapsed = _simulation_elapsed(state)
    answers = list(state.get("answers") or [])
    score = sum(float(item.get("score_delta", 0.0)) for item in answers)
    total_answered = sum(1 for item in answers if not item.get("skipped"))
    correct = sum(1 for item in answers if item.get("is_correct"))
    accuracy = round(100 * correct / total_answered, 1) if total_answered else 0
    st.markdown(
        f"""
        <div class="sim-shell">
            <div class="sim-title">Resultado do simulado #{int(state.get("simulation_id", 0))}</div>
            <div class="sim-meta">Tempo total: {_fmt_seconds(elapsed)} · Questões corrigidas: {len(answers)}</div>
            <div class="sim-stats">
                <div class="sim-stat"><div class="sim-stat-label">Pontuação Quadrix</div><div class="sim-stat-value">{score:.1f}</div></div>
                <div class="sim-stat"><div class="sim-stat-label">Acertos</div><div class="sim-stat-value">{correct}</div></div>
                <div class="sim-stat"><div class="sim-stat-label">Taxa</div><div class="sim-stat-value">{accuracy}%</div></div>
                <div class="sim-stat"><div class="sim-stat-label">Revisões geradas</div><div class="sim-stat-value">{sum(1 for item in answers if not item.get("is_correct") and not item.get("skipped"))}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_simulation_results(concurso_id, int(state.get("simulation_id", 0)))
    if st.button("Criar novo simulado interativo", type="primary"):
        st.session_state.pop(f"interactive_simulation_{concurso_id}", None)
        st.rerun()


def _render_simulation_results(concurso_id: int, simulation_id: int | None = None) -> None:
    sims = get_simulations(concurso_id)
    if sims.empty:
        return
    if simulation_id is None:
        simulation_id = int(sims.iloc[0]["id"])
    summary = simulation_discipline_summary(int(simulation_id))
    if not summary.empty:
        rows = []
        for _, row in summary.iterrows():
            total = int(row.get("total_questions", 0) or 0)
            correct = int(row.get("correct_answers", 0) or 0)
            accuracy = float(row.get("accuracy", 0) or 0)
            errors = int(row.get("errors", 0) or 0)
            rows.append(
                f"<tr><td>{_safe(row['discipline'])}</td><td>{total}</td><td>{correct}</td><td><span class='score-pill'>{accuracy:.1f}%</span></td><td>{errors}</td></tr>"
            )
        st.markdown("### Resultado por disciplina")
        st.markdown(
            "<table class='discipline-score-table'><thead><tr><th>Disciplina</th><th>Questões</th><th>Acertos</th><th>Taxa</th><th>Erros</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>",
            unsafe_allow_html=True,
        )

    details = simulation_details(int(simulation_id))
    if not details.empty:
        details = details.copy()
        totals = pd.to_numeric(details["total_questions"], errors="coerce").fillna(0)
        correct = pd.to_numeric(details["correct_answers"], errors="coerce").fillna(0)
        details["accuracy"] = ((correct / totals.where(totals > 0)) * 100).fillna(0).round(1)
        st.markdown("### Itens registrados")
        st.markdown(
            _render_simulation_table(
                pd.DataFrame(
                    [
                        {
                            "id": int(simulation_id),
                            "simulation_date": date.today().isoformat(),
                            "title": f"{row['discipline']} - {row['topic']}",
                            "mode": "questao_interativa",
                            "total_questions": int(row["total_questions"]),
                            "correct_answers": int(row["correct_answers"]),
                            "accuracy": float(row["accuracy"]),
                        }
                        for _, row in details.iterrows()
                    ]
                ),
                empty_message="Nenhum item registrado.",
            ),
            unsafe_allow_html=True,
        )


def _manual_simulation_view(concurso_id: int, topics: pd.DataFrame) -> None:
    st.markdown("### Novo simulado manual")
    topics = db.fetch_df(
        "SELECT id, discipline, topic FROM topics WHERE concurso_id = ? ORDER BY question_count DESC, discipline, topic",
        (concurso_id,),
    )
    if topics.empty:
        st.warning("Cadastre tópicos antes de registrar simulado.")
        return
    with st.form("novo_simulado"):
        title = st.text_input("Título", value=f"Simulado {date.today().strftime('%d/%m/%Y')}")
        mode = st.selectbox("Tipo", ["simulado_parcial", "simulado_completo", "questoes_por_disciplina"])
        notes = st.text_area("Observações")
        submitted = st.form_submit_button("Criar simulado")
    if submitted:
        if not title.strip():
            st.error("Informe um título.")
        else:
            sim_id = create_simulation(concurso_id, title, mode, notes)
            st.session_state[f"active_simulation_{concurso_id}"] = sim_id
            st.success(
                f"Simulado criado: #{sim_id}. Ele aparece abaixo em Simulado ativo e na tabela Simulados criados."
            )

    sims = get_simulations(concurso_id)
    if sims.empty:
        st.info("Nenhum simulado registrado ainda.")
        return

    st.markdown("### Simulados criados")
    sims_preview = sims.copy()
    totals_preview = pd.to_numeric(sims_preview["total_questions"], errors="coerce").fillna(0)
    correct_preview = pd.to_numeric(sims_preview["correct_answers"], errors="coerce").fillna(0)
    sims_preview["accuracy"] = ((correct_preview / totals_preview.where(totals_preview > 0)) * 100).fillna(0).round(1)
    st.markdown(_render_simulation_table(sims_preview), unsafe_allow_html=True)

    labels = {
        f"#{int(row['id'])} - {row['title']} ({row['simulation_date']})": int(row["id"])
        for _, row in sims.iterrows()
    }
    active_id = st.session_state.get(f"active_simulation_{concurso_id}")
    label_items = list(labels.keys())
    active_index = 0
    if active_id:
        for idx, label in enumerate(label_items):
            if labels[label] == int(active_id):
                active_index = idx
                break
    selected_id = labels[st.selectbox("Simulado ativo", label_items, index=active_index)]
    st.session_state[f"active_simulation_{concurso_id}"] = selected_id
    st.info("Use o Simulado ativo para lançar os resultados por tópico. O histórico consolidado aparece no fim desta aba.")

    topic_labels = {f"{row['discipline']} - {row['topic']}": int(row["id"]) for _, row in topics.iterrows()}
    with st.form("resultado_simulado"):
        topic_id = topic_labels[st.selectbox("Tópico cobrado", list(topic_labels.keys()))]
        total = st.number_input("Questões", min_value=1, max_value=300, value=20)
        correct = st.number_input("Acertos", min_value=0, max_value=int(total), value=min(14, int(total)))
        difficulty = st.slider("Dificuldade", min_value=1, max_value=5, value=3)
        add_result = st.form_submit_button("Adicionar resultado")
    if add_result:
        add_simulation_result(concurso_id, selected_id, topic_id, int(total), int(correct), int(difficulty))
        st.success("Resultado adicionado ao simulado.")

    details = simulation_details(selected_id)
    if not details.empty:
        details = details.copy()
        details["accuracy"] = (details["correct_answers"] / details["total_questions"] * 100).round(1)
        st.dataframe(
            details[["discipline", "topic", "total_questions", "correct_answers", "accuracy", "feedback"]],
            hide_index=True,
            use_container_width=True,
        )

    history = sims.copy()
    totals_history = pd.to_numeric(history["total_questions"], errors="coerce").fillna(0)
    correct_history = pd.to_numeric(history["correct_answers"], errors="coerce").fillna(0)
    history["accuracy"] = ((correct_history / totals_history.where(totals_history > 0)) * 100).fillna(0).round(1)
    st.markdown("### Histórico")
    st.markdown(_render_simulation_table(history), unsafe_allow_html=True)


def _simulation_view(concurso_id: int) -> None:
    topics = db.fetch_df(
        "SELECT id, discipline, topic, question_count FROM topics WHERE concurso_id = ? ORDER BY question_count DESC, discipline, topic",
        (concurso_id,),
    )
    if topics.empty:
        st.warning("Cadastre tópicos antes de registrar simulado.")
        return
    tab_interactive, tab_manual = st.tabs(["Simulado interativo", "Manual e histórico"])
    with tab_interactive:
        _interactive_simulation_view(concurso_id, topics)
    with tab_manual:
        _manual_simulation_view(concurso_id, topics)


def planning_view(concurso_id: int) -> None:
    st.subheader("Planejamento")
    st.markdown(
        '<div class="status-note">O plano prioriza revisões vencidas, pontos fracos em questões e tópicos com maior peso no mapa do concurso.</div>',
        unsafe_allow_html=True,
    )

    tab_strategy, tab_day, tab_week = st.tabs(["Estratégia 5h", "Plano do dia", "Semana"])
    with tab_strategy:
        st.markdown("### Ritual diário de máximo rendimento")
        ritual_rows = []
        for label, minutes, description in DAILY_RITUAL:
            ritual_rows.append(
                f"<tr><td><span class='time-chip'>{_fmt_minutes(minutes)}</span></td>"
                f"<td><strong>{_safe(label)}</strong></td><td>{_safe(description)}</td></tr>"
            )
        st.markdown(
            "<table class='clean-table'><thead><tr><th>Tempo</th><th>Bloco</th><th>Execução</th></tr></thead><tbody>"
            + "".join(ritual_rows)
            + "</tbody></table>",
            unsafe_allow_html=True,
        )

        st.markdown("### Ciclos de alternância")
        cards = []
        for cycle in STRATEGIC_CYCLES:
            cards.append(
                "<div class='strategy-card'>"
                f"<strong>{_safe(cycle['name'])}</strong><br>"
                f"<span class='muted'>Bloco A</span><br>{_safe(cycle['block_a'])}<br><br>"
                f"<span class='muted'>Bloco B</span><br>{_safe(cycle['block_b'])}<br><br>"
                f"<span class='muted'>{_safe(cycle['focus'])}</span>"
                "</div>"
            )
        st.markdown("<div class='strategy-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

        st.markdown("### Gerar semana estratégica")
        c1, c2, c3 = st.columns([1, 1, 2])
        strategic_start = c1.date_input("Início da semana", value=date.today(), key="strategic_start")
        strategic_cycle = c2.number_input("Ciclo inicial", min_value=1, max_value=4, value=1, step=1)
        if c3.button("Gerar plano estratégico 5h", type="primary"):
            created = generate_strategic_week(concurso_id, strategic_start, int(strategic_cycle))
            st.success(f"Plano estratégico gerado. {created} tarefa(s) adicionada(s).")
        st.info("Sábado fica reservado para discursiva + revisão semanal. Domingo fica reservado para simulado e meia jornada.")

    with tab_day:
        col1, col2, col3 = st.columns([1, 1, 2])
        plan_date = col1.date_input("Data do plano", value=date.today())
        available_minutes = col2.number_input("Minutos disponíveis", min_value=40, max_value=720, value=240, step=20)
        if col3.button("Gerar plano do dia", type="primary"):
            created = generate_daily_plan(concurso_id, plan_date, int(available_minutes))
            st.success(f"Plano gerado. {created} nova(s) tarefa(s) adicionada(s).")

        _render_daily_tasks(concurso_id, plan_date)

    with tab_week:
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        week_start = c1.date_input("Início", value=date.today(), key="week_start")
        week_days = c2.number_input("Dias", min_value=1, max_value=7, value=6, step=1)
        week_minutes = c3.number_input("Min/dia", min_value=40, max_value=720, value=240, step=20)
        if c4.button("Gerar semana", type="primary"):
            created = generate_weekly_plan(concurso_id, week_start, int(week_minutes), int(week_days))
            st.success(f"Semana gerada. {created} nova(s) tarefa(s) adicionada(s).")

        week = get_week_plan(concurso_id, week_start, int(week_days))
        if week.empty:
            st.info("Nenhuma tarefa no intervalo. Gere a semana para montar o roteiro.")
        else:
            summary = (
                week.groupby(["task_date", "status"], as_index=False)["target_minutes"].sum()
                .pivot(index="task_date", columns="status", values="target_minutes")
                .fillna(0)
                .reset_index()
            )
            summary["total"] = summary.drop(columns=["task_date"]).sum(axis=1)
            st.markdown("### Resumo semanal")
            st.dataframe(summary, hide_index=True, use_container_width=True)
            st.markdown("### Roteiro detalhado")
            detail = week.copy()
            detail["target_minutes"] = detail["target_minutes"].apply(_fmt_minutes)
            st.dataframe(
                detail[["task_date", "task_type", "discipline", "topic", "target_minutes", "status", "reason"]],
                hide_index=True,
                use_container_width=True,
            )


def _render_daily_tasks(concurso_id: int, plan_date: date) -> None:
    tasks = get_daily_plan(concurso_id, plan_date)
    if tasks.empty:
        st.info("Nenhuma tarefa para esta data. Clique em Gerar plano do dia.")
        return

    total_minutes = int(tasks["target_minutes"].sum())
    done = int((tasks["status"] == "concluida").sum())
    st.metric("Carga planejada", _fmt_minutes(total_minutes))
    st.progress(done / len(tasks))

    if plan_date == date.today():
        focus = next_pending_task(concurso_id, plan_date)
        if focus:
            destination = {
                "revisao": "Revisões ou Estudo",
                "questoes": "Questões > Banco local",
                "estudo": "Estudo",
                "discursiva": "Desempenho ou anotações externas",
                "simulado": "Questões > Simulado",
            }.get(str(focus["task_type"]), "Estudo")
            st.markdown(
                (
                    '<div class="status-note">'
                    f"Agora faça: <strong>{_safe(str(focus['task_type']).title())}</strong> em "
                    f"{_safe(focus['discipline'])} / {_safe(focus['topic'])}. "
                    f"Tempo-alvo: {_fmt_minutes(int(focus['target_minutes']))}. "
                    f"Abra: <strong>{destination}</strong>."
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        else:
            st.success("Plano de hoje concluído. Use Desempenho para revisar a semana.")

    for _, row in tasks.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.2, 3, 1, 1])
            c1.markdown(f"**{str(row['task_type']).title()}**")
            c2.markdown(f"**{row['discipline']}**  \n{row['topic']}  \n:gray[{row['reason']}]")
            c3.metric("Tempo", _fmt_minutes(int(row["target_minutes"])))
            if row["status"] == "concluida":
                c4.success("Concluída")
            elif c4.button("Concluir", key=f"task_{row['id']}"):
                complete_task(int(row["id"]))
                st.rerun()


def reviews_view(concurso_id: int) -> None:
    st.subheader("Fila de revisões")
    reviews = get_reviews(concurso_id)
    if reviews.empty:
        st.info("Nenhuma revisão programada. Conclua sessões de estudo ou erre questões para gerar revisões.")
        return

    today = date.today()
    pending = reviews[reviews["status"] == "pendente"].copy()
    done = reviews[reviews["status"] != "pendente"].copy()
    overdue = 0
    if not pending.empty:
        overdue = int((pd.to_datetime(pending["review_date"]).dt.date <= today).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Pendentes", len(pending))
    c2.metric("Vencidas/hoje", overdue)
    c3.metric("Realizadas", len(done))

    st.markdown("### Pendentes")
    if pending.empty:
        st.success("Sem revisões pendentes.")
    else:
        for _, row in pending.head(30).iterrows():
            due_date = pd.to_datetime(row["review_date"]).date()
            urgency = "Vencida/hoje" if due_date <= today else "Próxima"
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 4, 1])
                c1.markdown(f"**{due_date.strftime('%d/%m')}**  \n:gray[{urgency}]")
                c2.markdown(f"**{row['discipline']}**  \n{row['topic']}  \n:gray[{row['reason']}]")
                if c3.button("Marcar feita", key=f"review_{row['id']}"):
                    complete_review(int(row["id"]))
                    st.rerun()

    with st.expander("Revisões realizadas"):
        if done.empty:
            st.write("Nenhuma revisão realizada ainda.")
        else:
            st.dataframe(done[["review_date", "discipline", "topic", "reason"]], hide_index=True, use_container_width=True)


def performance_view(concurso_id: int) -> None:
    st.subheader("Desempenho e relatório")
    report = weekly_report(concurso_id)
    readiness = report["readiness"]
    sessions = report["sessions"]
    results = report["results"]
    week_performance = report["week_performance"]
    weak = report["weak_topics"]
    recs = report["recommendations"]

    minutes = int(sessions["minutes"].sum()) if not sessions.empty else 0
    questions = int(results["total_questions"].sum()) if not results.empty else 0
    correct = int(results["correct_answers"].sum()) if not results.empty else 0
    accuracy = round(correct / questions * 100, 1) if questions else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prontidão", f"{readiness['score']}%")
    c2.metric("Horas semanais", _fmt_minutes(minutes))
    c3.metric("Questões semanais", questions)
    c4.metric("Acerto semanal", f"{accuracy}%")

    st.markdown("### Desempenho por disciplina na semana")
    if week_performance.empty:
        st.info("Sem questões registradas nesta semana.")
    else:
        view = week_performance.copy()
        view["accuracy"] = (view["accuracy"] * 100).round(1)
        st.dataframe(view, hide_index=True, use_container_width=True)

    st.markdown("### Pontos fracos acumulados")
    if weak.empty:
        st.info("Sem dados suficientes para pontos fracos.")
    else:
        weak_view = weak.copy()
        weak_view["accuracy"] = (weak_view["accuracy"] * 100).round(1)
        st.dataframe(
            weak_view[["discipline", "topic", "total_questions", "correct_answers", "accuracy"]],
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("### Recomendações")
    if recs:
        for rec in recs:
            st.write(f"- {rec}")
    else:
        st.success("Sem recomendação crítica. Continue o plano.")

    markdown = weekly_report_markdown(concurso_id)
    st.download_button(
        "Baixar relatório semanal (.md)",
        data=markdown.encode("utf-8"),
        file_name=f"relatorio-semanal-sedes-df-{date.today().isoformat()}.md",
        mime="text/markdown",
    )


def quadrrix_training_view(concurso_id: int) -> None:
    st.subheader("Treino Quadrix")
    st.markdown(
        '<div class="status-note">Para este edital, a prova objetiva é de múltipla escolha com cinco alternativas (A-E). O modo Certo/Errado fica disponível apenas como treino alternativo.</div>',
        unsafe_allow_html=True,
    )
    if not is_ollama_available():
        st.warning("Ollama/gemma2:2b não respondeu. Abra o Ollama para gerar questões interativas.")
        return

    topics = db.fetch_df(
        "SELECT id, discipline, topic FROM topics WHERE concurso_id = ? ORDER BY question_count DESC, discipline, topic",
        (concurso_id,),
    )
    if topics.empty:
        st.warning("Cadastre tópicos antes de iniciar o treino.")
        return

    labels = {f"{row['discipline']} - {row['topic']}": int(row["id"]) for _, row in topics.iterrows()}
    topic_label = st.selectbox("Assunto do treino", list(labels.keys()))
    topic_id = labels[topic_label]
    mode_label = st.radio(
        "Formato",
        ["Múltipla escolha A-E (oficial deste edital)", "Certo/Errado (treino alternativo)"],
        horizontal=True,
    )
    mode = "certo_errado" if mode_label.startswith("Certo") else "multipla_escolha"

    state_key = f"quadrix_{concurso_id}_{topic_id}_{mode}"
    score_key = f"{state_key}_score"
    answered_key = f"{state_key}_answered"
    if score_key not in st.session_state:
        st.session_state[score_key] = {"score": 0.0, "answered": 0, "correct": 0, "wrong": 0, "skipped": 0}

    col_a, col_b, col_c, col_d = st.columns(4)
    score = st.session_state[score_key]
    col_a.metric("Pontuação", score["score"])
    col_b.metric("Respondidas", score["answered"])
    col_c.metric("Acertos", score["correct"])
    col_d.metric("Erros", score["wrong"])

    if st.button("Gerar nova questão", type="primary") or state_key not in st.session_state:
        with st.spinner("Gerando questão no estilo Quadrix..."):
            try:
                st.session_state[state_key] = generate_quadrrix_question(topic_label, mode)
                st.session_state[answered_key] = False
            except Exception as exc:
                st.error(f"Falha ao gerar questão: {exc}")
                return

    question = st.session_state.get(state_key)
    if not question:
        return

    st.markdown("**Questão**")
    st.write(question.get("statement", "Questão indisponível."))

    if mode == "certo_errado":
        options = ["Certo", "Errado", "Pular"]
    else:
        q_options = question.get("options", {})
        if isinstance(q_options, dict):
            for key in ["A", "B", "C", "D", "E"]:
                st.write(f"**{key})** {q_options.get(key, '')}")
        options = ["A", "B", "C", "D", "E", "Pular"]

    answer = st.radio("Sua resposta", options, horizontal=True)
    if st.button("Responder"):
        if st.session_state.get(answered_key):
            st.info("Esta questão já foi corrigida. Gere a próxima questão.")
            return
        expected = str(question.get("answer", "")).strip().upper()
        chosen = answer.strip().upper()
        skipped = chosen == "PULAR"
        correct = (chosen == expected) and not skipped

        score["answered"] += 1
        if skipped:
            score["skipped"] += 1
            delta = 0.0
            st.info("Questão pulada. Pontuação: 0.")
        elif correct:
            score["correct"] += 1
            delta = 1.0
            st.success("Você acertou. Pontuação: +1,0.")
        else:
            score["wrong"] += 1
            delta = -0.5 if mode == "certo_errado" else 0.0
            st.error(f"Você errou. Gabarito: {expected}. Pontuação: {delta:+.1f}.")
        score["score"] = round(float(score["score"]) + delta, 1)
        st.session_state[answered_key] = True

        st.markdown("**Justificativa**")
        st.write(question.get("justification", "Sem justificativa retornada pela IA."))

        db.execute(
            """
            INSERT INTO question_results
            (concurso_id, topic_id, total_questions, correct_answers, difficulty, feedback)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                concurso_id,
                topic_id,
                1,
                1 if correct else 0,
                3,
                f"Treino Quadrix {mode}: resposta={chosen}; gabarito={expected}; delta={delta}",
            ),
        )
        if not correct and not skipped:
            db.execute(
                """
                INSERT INTO reviews (concurso_id, topic_id, review_date, reason)
                VALUES (?, ?, ?, ?)
                """,
                (concurso_id, topic_id, (date.today() + timedelta(days=2)).isoformat(), "Erro no treino Quadrix"),
            )

    if st.session_state.get(answered_key):
        if st.button("Próxima questão"):
            with st.spinner("Gerando próxima questão..."):
                try:
                    st.session_state[state_key] = generate_quadrrix_question(topic_label, mode)
                    st.session_state[answered_key] = False
                    st.rerun()
                except Exception as exc:
                    st.error(f"Falha ao gerar próxima questão: {exc}")


def settings_view(user_id: int = 1) -> None:
    st.subheader("Saúde do ambiente")
    db_ok = DB_PATH.exists()
    questions = 0
    concursos_count = 0
    topics_count = 0
    try:
        questions_row = db.fetch_one("SELECT COUNT(*) AS qtd FROM question_bank")
        concursos_row = db.fetch_one("SELECT COUNT(*) AS qtd FROM concursos")
        topics_row = db.fetch_one("SELECT COUNT(*) AS qtd FROM topics")
        questions = int(questions_row["qtd"]) if questions_row else 0
        concursos_count = int(concursos_row["qtd"]) if concursos_row else 0
        topics_count = int(topics_row["qtd"]) if topics_row else 0
    except Exception:
        db_ok = False

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Banco SQLite", "OK" if db_ok else "Falha")
    c2.metric("Concursos", concursos_count)
    c3.metric("Tópicos", topics_count)
    c4.metric("Questões locais", questions)

    ai_ok = is_ollama_available()
    ocr_ok = is_ocr_available()
    if ai_ok:
        st.markdown('<div class="status-note">IA local disponível: Ollama respondeu com o modelo configurado.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-note">IA local indisponível: o app funciona sem IA, mas geração automática fica limitada.</div>', unsafe_allow_html=True)
    if ocr_ok:
        st.markdown('<div class="status-note">OCR ativo: Tesseract encontrado no Windows.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-note">OCR inativo: imagens serão salvas, mas texto só será extraído após instalar o Tesseract OCR.</div>', unsafe_allow_html=True)

    with st.expander("Caminhos técnicos"):
        st.write(f"Banco: {DB_PATH}")
        st.write(f"Uploads: {UPLOAD_DIR}")
        st.write(f"Extensões aceitas: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    st.subheader("Novo concurso")
    with st.form("novo_concurso"):
        name = st.text_input("Nome")
        banca = st.text_input("Banca")
        orgao = st.text_input("Órgão")
        exam_date = st.date_input("Data da prova", value=date.today())
        submitted = st.form_submit_button("Criar concurso")
    if submitted:
        if not name.strip():
            st.error("Informe o nome do concurso.")
        else:
            db.execute(
                "INSERT INTO concursos (user_id, name, banca, orgao, exam_date) VALUES (?, ?, ?, ?, ?)",
                (user_id, name.strip(), banca.strip(), orgao.strip(), exam_date.isoformat()),
            )
            st.success("Concurso criado.")



def main() -> None:
    apply_theme()
    db.init_db()
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark">▰</div>
            <div><div class="brand-small">Concurso</div><div class="brand-title">Estudo Pro</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    user = selected_user()
    create_user_widget()
    if st.sidebar.button("Carregar edital SEDES DF 2026"):
        seed_real_edital(int(user["id"]))
        st.sidebar.success("Edital real carregado.")

    concursos = get_concursos(int(user["id"]))
    concurso_id = selected_concurso_id(concursos)

    if concurso_id is None:
        st.info("Crie um concurso ou carregue o edital SEDES DF 2026 para começar.")
        settings_view(int(user["id"]))
        return

    nav_options = ["▦  Painel", "▤  Editais", "▣  Materiais", "?  Questões", "□  Revisões", "▥  Desempenho", "▦  Planejamento", "◷  Estudo", "◉  Treino Quadrix", "⚙  Configurações"]
    if st.session_state.get("main_nav") not in nav_options:
        st.session_state["main_nav"] = nav_options[0]

    nav = st.sidebar.radio(
        "Navegação",
        nav_options,
        label_visibility="collapsed",
        key="main_nav",
    )
    st.sidebar.markdown(
        """
        <div class="side-plan">
            <div style="display:flex; justify-content:space-between; font-weight:700; margin-bottom:1rem"><span>Plano atual</span><span>Pro</span></div>
            <div class="muted" style="color:#b8c7d4">Horas líquidas (mês)</div>
            <div style="font-weight:800; margin:.35rem 0; color:#fff">61h 20m / 100h</div>
            <div class="plan-progress"><div class="plan-fill"></div></div>
            <div style="border:1px solid rgba(255,255,255,.55); border-radius:7px; text-align:center; margin-top:1rem; padding:.55rem; font-weight:800">Ver planos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if "Painel" in nav:
        dashboard(concurso_id, user)
    elif "Editais" in nav or "Materiais" in nav:
        upload_view(concurso_id)
    elif "Planejamento" in nav:
        planning_view(concurso_id)
    elif "Revisões" in nav:
        reviews_view(concurso_id)
    elif "Desempenho" in nav:
        performance_view(concurso_id)
    elif "Estudo" in nav:
        study_view(concurso_id)
    elif "Questões" in nav:
        questions_view(concurso_id)
    elif "Treino Quadrix" in nav:
        quadrrix_training_view(concurso_id)
    else:
        settings_view(int(user["id"]))


if __name__ == "__main__":
    main()
