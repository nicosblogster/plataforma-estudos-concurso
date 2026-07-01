@echo off
setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Execute scripts\install.bat primeiro.
  if /I not "%~1"=="/nopause" pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
python -c "from app.extractors import _find_tesseract; p=_find_tesseract(); print('Tesseract encontrado em:', p if p else 'NAO ENCONTRADO'); print('Instale com: winget install UB-Mannheim.TesseractOCR' if not p else 'OCR pronto para imagens.')"
if /I not "%~1"=="/nopause" pause
