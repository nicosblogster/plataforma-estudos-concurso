from __future__ import annotations

import shutil
from pathlib import Path

from app import db
from app.config import UPLOAD_DIR
from app.extractors import extract_text
from app.question_bank import seed_question_bank


REAL_EDITAL = Path(r"C:\Users\acer\Downloads\edital-sedes-df-2026.pdf")
PEDAGOGY_POST_EDITAL = Path(r"C:\Users\acer\Downloads\sedes df-pedagogia-pos-edital.pdf")
ADMIN_VERTICALIZED_XLSX = Path(
    r"C:\Users\acer\Downloads\edital-verticalizado-sedes-df-secretaria-de-estado-de-desenvolvimento-social-administrativo.xlsx"
)


STUDY_MAP_TOPICS = [
    ("Língua Portuguesa", "Compreensão e interpretação de textos de gêneros variados", 5, 3608),
    ("Língua Portuguesa", "Domínio da ortografia oficial - emprego das letras", 4, 3608),
    ("Língua Portuguesa", "Domínio da ortografia oficial - emprego da acentuação gráfica", 4, 3608),
    ("Língua Portuguesa", "Concordância verbal e nominal", 5, 3608),
    ("Língua Portuguesa", "Colocação dos pronomes átonos", 4, 3608),
    ("Língua Portuguesa", "Emprego do sinal indicativo de crase", 5, 3608),
    ("Língua Portuguesa", "Emprego dos sinais de pontuação", 5, 3608),
    ("Língua Portuguesa", "Coordenação e subordinação entre orações e termos da oração", 5, 3608),
    ("Língua Portuguesa", "Reconhecimento de tipos e gêneros textuais", 4, 3608),
    ("Língua Portuguesa", "Reescrita de frases e parágrafos do texto", 5, 3608),
    ("Língua Portuguesa", "Significação, substituição, reorganização e reescrita textual", 5, 3608),
    ("Língua Portuguesa", "Coesão textual: referenciação, substituição, repetição, conectores e sequenciação", 5, 3608),
    ("Língua Portuguesa", "Emprego e correlação de tempos e modos verbais", 4, 3608),
    ("Fundamentos, Organização, Gestão e Marcos Normativos da Assistência Social", "LOAS, PNAS/2004 e SUAS", 5, 81),
    ("Fundamentos, Organização, Gestão e Marcos Normativos da Assistência Social", "Princípios, diretrizes, objetivos e organização da Assistência Social", 5, 81),
    ("Fundamentos, Organização, Gestão e Marcos Normativos da Assistência Social", "Proteção Social Básica e Especial", 5, 81),
    ("Fundamentos, Organização, Gestão e Marcos Normativos da Assistência Social", "Seguranças socioassistenciais, matricialidade sociofamiliar, territorialização e intersetorialidade", 5, 81),
    ("Fundamentos, Organização, Gestão e Marcos Normativos da Assistência Social", "NOB/SUAS: responsabilidades dos entes, cofinanciamento, gestão do trabalho e rede", 5, 81),
    ("Fundamentos, Organização, Gestão e Marcos Normativos da Assistência Social", "CadÚnico e Protocolo de Gestão Integrada de Serviços, Benefícios e Transferências de Renda", 4, 81),
    ("Direitos, Violações de Direitos e Vulnerabilidades Sociais", "Crianças, adolescentes e juventude", 5, 259),
    ("Direitos, Violações de Direitos e Vulnerabilidades Sociais", "ECA e Estatuto Digital da Criança e do Adolescente", 5, 259),
    ("Direitos, Violações de Direitos e Vulnerabilidades Sociais", "Convivência familiar e comunitária, acolhimento, adoção e SINASE", 5, 259),
    ("Direitos, Violações de Direitos e Vulnerabilidades Sociais", "Violência contra crianças e adolescentes", 5, 259),
    ("Direitos, Violações de Direitos e Vulnerabilidades Sociais", "Pessoa idosa e pessoa com deficiência: Estatuto da Pessoa Idosa, Política Nacional do Idoso e LBI", 5, 259),
    ("Direitos, Violações de Direitos e Vulnerabilidades Sociais", "População em situação de rua, pobreza e exclusão social", 5, 259),
    ("Direitos, Violações de Direitos e Vulnerabilidades Sociais", "Desproteção social e Política Nacional para a População em Situação de Rua", 4, 259),
    ("Conhecimentos do DF, Política para Mulheres, Legislação e Primeiros Socorros", "Realidade étnica, social, histórica, geográfica, cultural, política e econômica do DF e RIDE", 4, 185),
    ("Conhecimentos do DF, Política para Mulheres, Legislação e Primeiros Socorros", "Plano Distrital de Política para Mulheres - PDPM", 4, 185),
    ("Conhecimentos do DF, Política para Mulheres, Legislação e Primeiros Socorros", "Lei Orgânica do Distrito Federal - Título VI", 4, 185),
    ("Conhecimentos do DF, Política para Mulheres, Legislação e Primeiros Socorros", "Lei Complementar 840/2011 - disposições preliminares, deveres, regime disciplinar e processos", 5, 185),
    ("Conhecimentos do DF, Política para Mulheres, Legislação e Primeiros Socorros", "Lei Maria da Penha - Lei Federal 11.340/2006", 5, 185),
    ("Conhecimentos Específicos - Pedagogia", "O Pedagogo no SUAS: planejamento e prática socioeducativa", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Planejamento participativo: elaboração, execução, registro, monitoramento e avaliação de projetos socioeducativos", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Metodologias participativas e educação em grupo: oficinas, atividades socioeducativas e práticas coletivas", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Educação, comunidade e território: fortalecimento de vínculos familiares e comunitários", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Interdisciplinaridade, multidisciplinaridade, trabalho em rede e articulação intersetorial", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Intervenção pedagógica nas situações de vulnerabilidade e violência", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Processos educativos com famílias e indivíduos em negligência, abandono, institucionalização e exclusão social", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Atuação pedagógica com adolescentes em conflito com a lei", 4, 297),
    ("Conhecimentos Específicos - Pedagogia", "Educação para cidadania, autonomia e protagonismo social", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Fundamentos da Educação e Pedagogia Social", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Formação do pedagogo no Brasil e atuação em contextos não escolares", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Desafios contemporâneos da educação em contextos de vulnerabilidade", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Educação social e pedagogia social como inclusão e garantia de direitos", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Concepções críticas, histórico-dialéticas e emancipatórias; educação popular, formal, não formal e informal", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Direito Educacional", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Educação na Constituição Federal de 1988", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "LDB - Lei Federal 9.394/1996 e alterações", 5, 297),
    ("Conhecimentos Específicos - Pedagogia", "Princípios e organização da educação brasileira e gestão democrática", 5, 297),
]


def seed_real_edital(user_id: int = 1) -> int:
    db.init_db()
    existing = db.fetch_one(
        "SELECT id FROM concursos WHERE user_id = ? AND name = ?",
        (user_id, "Pedagoga/Pedagogia - SEDES DF 2026"),
    )
    if existing:
        concurso_id = int(existing["id"])
    else:
        concurso_id = db.execute(
            """
            INSERT INTO concursos (user_id, name, banca, orgao, exam_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                "Pedagoga/Pedagogia - SEDES DF 2026",
                "Instituto Quadrix",
                "SEDES/DF",
                "2026-09-06",
            ),
        )

    _replace_study_map(concurso_id)

    if REAL_EDITAL.exists():
        existing_material = db.fetch_one(
            "SELECT id FROM materials WHERE concurso_id = ? AND original_name = ? AND category = 'edital'",
            (concurso_id, REAL_EDITAL.name),
        )
        if not existing_material:
            target = UPLOAD_DIR / REAL_EDITAL.name
            if not target.exists():
                shutil.copy2(REAL_EDITAL, target)
            text = extract_text(target)
            db.execute(
                """
                INSERT INTO materials
                (concurso_id, filename, original_name, file_type, category, topic, extracted_text, ai_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    concurso_id,
                    target.name,
                    REAL_EDITAL.name,
                    ".pdf",
                    "edital",
                    "Edital completo",
                    text,
                    "Edital real carregado para o cargo de Pedagoga/Pedagogia - SEDES DF 2026.",
                ),
            )

    _add_reference_material(
        concurso_id=concurso_id,
        source=PEDAGOGY_POST_EDITAL,
        category="material",
        topic="Vade mecum pós-edital - Pedagogia",
        summary="Material pós-edital de Pedagogia carregado como referência de estudo.",
    )

    _add_reference_material(
        concurso_id=concurso_id,
        source=ADMIN_VERTICALIZED_XLSX,
        category="material",
        topic="Planilha verticalizada recebida - Administrativo",
        summary=(
            "Arquivo recebido, mas identificado como verticalizado de Administrativo. "
            "Não foi usado para substituir o mapa do cargo de Pedagoga."
        ),
    )

    seed_question_bank(concurso_id)

    return concurso_id


def _replace_study_map(concurso_id: int) -> None:
    activity = db.fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM study_sessions WHERE concurso_id = ?) AS sessions,
            (SELECT COUNT(*) FROM question_results WHERE concurso_id = ?) AS results,
            (SELECT COUNT(*) FROM reviews WHERE concurso_id = ?) AS reviews
        """,
        (concurso_id, concurso_id, concurso_id),
    )
    has_activity = bool(activity and (activity["sessions"] or activity["results"] or activity["reviews"]))

    if not has_activity:
        db.execute("DELETE FROM study_tasks WHERE concurso_id = ?", (concurso_id,))
        db.execute("DELETE FROM topics WHERE concurso_id = ?", (concurso_id,))

    for discipline, topic, priority, question_count in STUDY_MAP_TOPICS:
        db.execute(
            """
            INSERT OR IGNORE INTO topics (concurso_id, discipline, topic, priority, question_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (concurso_id, discipline, topic, priority, question_count),
        )
        db.execute(
            """
            UPDATE topics
            SET priority = ?, question_count = ?
            WHERE concurso_id = ? AND discipline = ? AND topic = ?
            """,
            (priority, question_count, concurso_id, discipline, topic),
        )


def _add_reference_material(
    concurso_id: int,
    source: Path,
    category: str,
    topic: str,
    summary: str,
) -> None:
    if not source.exists():
        return
    existing = db.fetch_one(
        "SELECT id FROM materials WHERE concurso_id = ? AND original_name = ?",
        (concurso_id, source.name),
    )
    if existing:
        return
    target = UPLOAD_DIR / source.name
    if not target.exists():
        shutil.copy2(source, target)
    try:
        text = extract_text(target)
    except Exception as exc:
        text = f"Arquivo recebido, mas a extração automática falhou: {exc}"
    db.execute(
        """
        INSERT INTO materials
        (concurso_id, filename, original_name, file_type, category, topic, extracted_text, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concurso_id,
            target.name,
            source.name,
            source.suffix.lower(),
            category,
            topic,
            text,
            summary,
        ),
    )
