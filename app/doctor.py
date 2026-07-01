from __future__ import annotations

import compileall
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import db
from app.config import DB_PATH, UPLOAD_DIR
from app.extractors import is_ocr_available
from app.ollama_client import is_ollama_available
from app.planner import complete_matching_tasks, generate_daily_plan, get_daily_plan, next_pending_task
from app.question_bank import get_question_count, seed_question_bank
from app.seed_data import seed_real_edital


def main() -> int:
    print("== Diagnostico da Plataforma de Estudos ==")
    ok = True

    print("\n[1/7] Compilacao Python")
    compiled = compileall.compile_dir(PROJECT_ROOT / "app", quiet=1)
    print("OK" if compiled else "FALHA")
    ok = ok and compiled

    print("\n[2/7] Banco SQLite")
    db.init_db()
    print(f"Banco: {DB_PATH}")
    print(f"Existe: {'sim' if DB_PATH.exists() else 'nao'}")
    ok = ok and DB_PATH.exists()

    print("\n[3/7] Seed SEDES DF Pedagogia")
    concurso_id = seed_real_edital()
    topics = db.fetch_one("SELECT COUNT(*) AS qtd FROM topics WHERE concurso_id = ?", (concurso_id,))
    materials = db.fetch_one("SELECT COUNT(*) AS qtd FROM materials WHERE concurso_id = ?", (concurso_id,))
    print(f"Concurso ID: {concurso_id}")
    print(f"Topicos: {int(topics['qtd']) if topics else 0}")
    print(f"Materiais: {int(materials['qtd']) if materials else 0}")
    ok = ok and bool(topics and int(topics["qtd"]) >= 40)

    print("\n[4/7] Banco local de questoes")
    created = seed_question_bank(concurso_id)
    total_questions = get_question_count(concurso_id)
    print(f"Novas questoes sincronizadas: {created}")
    print(f"Questoes locais: {total_questions}")
    ok = ok and total_questions >= 25

    print("\n[5/7] Fluxo diario integrado")
    flow_ok = _check_daily_flow(concurso_id)
    print("OK" if flow_ok else "FALHA")
    ok = ok and flow_ok

    print("\n[6/7] OCR de imagens")
    ocr_ok = is_ocr_available()
    print("OK - Tesseract encontrado" if ocr_ok else "AVISO - Tesseract nao encontrado")

    print("\n[7/7] IA local")
    ai_ok = is_ollama_available()
    print("OK - Ollama respondeu" if ai_ok else "AVISO - Ollama indisponivel")

    print("\nUploads:", UPLOAD_DIR)
    print("\nResultado geral:", "OK" if ok else "FALHA OPERACIONAL")
    if not ok:
        print("Corrija os itens com FALHA antes de usar como rotina principal de estudos.")
        return 1
    return 0


def _check_daily_flow(concurso_id: int) -> bool:
    today = date.today()
    created = generate_daily_plan(concurso_id, today, 40)
    plan = get_daily_plan(concurso_id, today)
    focus = next_pending_task(concurso_id, today)
    if plan.empty or not focus:
        return False
    closed = complete_matching_tasks(
        concurso_id=concurso_id,
        topic_id=int(focus["topic_id"]),
        task_date=today,
        task_types=(str(focus["task_type"]),),
    )
    # The doctor must not leave artificial plan rows in the user's study history.
    db.execute("DELETE FROM study_tasks WHERE concurso_id = ? AND task_date = ?", (concurso_id, today.isoformat()))
    print(f"Tarefas criadas no teste: {created}")
    print(f"Proxima tarefa detectada: {focus['task_type']} - {focus['topic']}")
    print(f"Tarefas fechadas automaticamente: {closed}")
    return created >= 0 and closed >= 1


if __name__ == "__main__":
    raise SystemExit(main())
