from pathlib import Path
import shutil

import fitz
import pandas as pd
import pytesseract
from docx import Document
from PIL import Image


MAX_TEXT_CHARS = 80_000


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix in {".xlsx", ".xls"}:
        return _extract_excel(path)
    if suffix == ".csv":
        return _extract_csv(path)
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")[:MAX_TEXT_CHARS]
    if suffix in {".jpg", ".jpeg", ".png"}:
        return _extract_image_ocr(path)
    raise ValueError(f"Formato não suportado: {suffix}")


def _extract_pdf(path: Path) -> str:
    chunks: list[str] = []
    with fitz.open(path) as doc:
        for page in doc:
            chunks.append(page.get_text("text"))
            if sum(len(chunk) for chunk in chunks) >= MAX_TEXT_CHARS:
                break
    return "\n".join(chunks)[:MAX_TEXT_CHARS].strip()


def _extract_docx(path: Path) -> str:
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)[:MAX_TEXT_CHARS].strip()


def _extract_excel(path: Path) -> str:
    frames = pd.read_excel(path, sheet_name=None)
    lines: list[str] = []
    for sheet, df in frames.items():
        lines.append(f"Planilha: {sheet}")
        lines.append(df.fillna("").astype(str).head(200).to_csv(index=False))
    return "\n".join(lines)[:MAX_TEXT_CHARS].strip()


def _extract_csv(path: Path) -> str:
    df = pd.read_csv(path)
    return df.fillna("").astype(str).head(500).to_csv(index=False)[:MAX_TEXT_CHARS]


def _extract_image_ocr(path: Path) -> str:
    tesseract_path = _find_tesseract()
    with Image.open(path) as image:
        width, height = image.size
        mode = image.mode
        prepared = image.convert("L")

    if not tesseract_path:
        return (
            "Imagem recebida, mas o motor OCR Tesseract não foi encontrado no Windows.\n"
            f"Arquivo: {path.name}\nDimensões: {width}x{height}\nModo: {mode}\n\n"
            "Para ativar OCR de imagem, instale o Tesseract OCR e execute novamente o upload.\n"
            "Comando sugerido no Windows: winget install UB-Mannheim.TesseractOCR"
        )

    pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
    try:
        text = pytesseract.image_to_string(prepared, lang="por+eng")
    except pytesseract.TesseractError:
        text = pytesseract.image_to_string(prepared, lang="eng")

    cleaned = text.strip()
    if not cleaned:
        return (
            "OCR executado, mas nenhum texto legível foi identificado.\n"
            f"Arquivo: {path.name}\nDimensões: {width}x{height}\nModo: {mode}"
        )
    return cleaned[:MAX_TEXT_CHARS]


def is_ocr_available() -> bool:
    return _find_tesseract() is not None


def _find_tesseract() -> Path | None:
    command = shutil.which("tesseract")
    if command:
        return Path(command)

    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Users\acer\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
