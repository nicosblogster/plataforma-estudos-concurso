from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SCREEN_EXPECTATIONS = {
    "Planejamento": ["Planejamento"],
    "Questões": ["Registrar simulado ou questões"],
    "Estudo": ["Registrar estudo"],
    "Configurações": ["Saúde do ambiente", "Novo concurso"],
    "Revisões": ["Fila de revisões"],
    "Desempenho": ["Desempenho e relatório"],
}


def main() -> int:
    ok = True
    for nav_fragment, expected_texts in SCREEN_EXPECTATIONS.items():
        app = AppTest.from_file(str(PROJECT_ROOT / "app" / "main.py"))
        app.run(timeout=60)
        if app.exception:
            ok = False
            print(f"{nav_fragment}: FALHA na abertura inicial")
            for exc in app.exception:
                print(exc)
            continue

        if not app.radio:
            ok = False
            print(f"{nav_fragment}: FALHA - navegacao lateral nao encontrada")
            continue

        radio = app.radio[0]
        target = next((option for option in radio.options if nav_fragment in option), None)
        if not target:
            ok = False
            print(f"{nav_fragment}: FALHA - opcao nao encontrada")
            continue

        radio.set_value(target)
        app.run(timeout=60)
        values = []
        for collection_name in ["title", "header", "subheader", "markdown", "info", "warning", "success"]:
            for item in getattr(app, collection_name):
                values.append(str(getattr(item, "value", item)))
        joined = "\n".join(values)
        missing = [text for text in expected_texts if text not in joined]
        if app.exception or missing:
            ok = False
            print(f"{nav_fragment}: FALHA")
            if missing:
                print("Textos ausentes:", ", ".join(missing))
            for exc in app.exception:
                print(exc)
        else:
            print(f"{nav_fragment}: OK")

    print("Resultado:", "OK" if ok else "FALHA")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
