from __future__ import annotations

import json
from typing import Any

import requests

from app.config import OLLAMA_HOST, OLLAMA_MODEL


def is_ollama_available() -> bool:
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        response.raise_for_status()
        models = response.json().get("models", [])
        return any(model.get("name") == OLLAMA_MODEL for model in models)
    except requests.RequestException:
        return False


def generate(prompt: str, temperature: float = 0.2) -> str:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=120)
    response.raise_for_status()
    return str(response.json().get("response", "")).strip()


def summarize_material(text: str, category: str) -> str:
    if not text.strip():
        return "Não foi possível extrair texto útil do arquivo."
    prompt = f"""
Você é um analista de estudos para concursos públicos brasileiros.
Analise o conteúdo abaixo e devolva em português, com objetividade:
1. Resumo do material.
2. Disciplinas ou assuntos prováveis.
3. Pontos que devem virar revisão.
4. Observações de risco para o candidato.

Tipo de arquivo: {category}
Conteúdo:
{text[:12000]}
"""
    return generate(prompt)


def extract_topics_from_edital(text: str) -> list[dict[str, Any]]:
    prompt = f"""
Extraia possíveis disciplinas e tópicos de um edital de concurso público.
Responda APENAS em JSON válido no formato:
[
  {{"discipline": "Nome da disciplina", "topic": "Tópico do edital", "priority": 1}}
]
Prioridade deve ser de 1 a 5, sendo 5 o mais importante.

Texto do edital:
{text[:14000]}
"""
    raw = generate(prompt)
    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
        parsed = json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        return []
    valid: list[dict[str, Any]] = []
    for item in parsed:
        discipline = str(item.get("discipline", "")).strip()
        topic = str(item.get("topic", "")).strip()
        if not discipline or not topic:
            continue
        try:
            priority = max(1, min(5, int(item.get("priority", 3))))
        except (TypeError, ValueError):
            priority = 3
        valid.append({"discipline": discipline, "topic": topic, "priority": priority})
    return valid[:80]


def generate_quadrrix_question(topic: str, mode: str = "multipla_escolha") -> dict[str, Any]:
    if mode == "certo_errado":
        prompt = f"""
Atue como professor especialista em concursos da banca Instituto Quadrix.
Crie UMA questão inédita no estilo CERTO ou ERRADO sobre o tópico abaixo.
Use cobrança literal, lei seca, conceito direto ou pegadinha sutil de troca de palavras.

Responda APENAS em JSON válido:
{{
  "mode": "certo_errado",
  "statement": "enunciado da questão",
  "answer": "Certo",
  "justification": "justificativa detalhada com artigo de lei ou conceito teórico quando aplicável"
}}

Tópico: {topic}
"""
    else:
        prompt = f"""
Atue como professor especialista em concursos da banca Instituto Quadrix.
O edital SEDES/DF Pedagogia prevê prova objetiva de múltipla escolha, com cinco opções A, B, C, D e E, e uma única correta.
Crie UMA questão inédita nesse estilo sobre o tópico abaixo.
Use cobrança literal, lei seca, conceito direto ou pegadinha sutil de troca de palavras.

Responda APENAS em JSON válido:
{{
  "mode": "multipla_escolha",
  "statement": "enunciado da questão",
  "options": {{"A": "alternativa A", "B": "alternativa B", "C": "alternativa C", "D": "alternativa D", "E": "alternativa E"}},
  "answer": "A",
  "justification": "justificativa detalhada com artigo de lei ou conceito teórico quando aplicável"
}}

Tópico: {topic}
"""
    raw = generate(prompt, temperature=0.35)
    parsed = _parse_json_object(raw)
    if not parsed:
        raise ValueError("A IA não retornou uma questão em JSON válido.")
    return parsed


def _parse_json_object(raw: str) -> dict[str, Any]:
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, json.JSONDecodeError):
        return {}
    return {}
