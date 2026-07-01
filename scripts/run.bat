@echo off
setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Execute scripts\install.bat primeiro.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
set "PYTHONPATH=%CD%"
streamlit run app\main.py
