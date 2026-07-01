@echo off
setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Execute scripts\install.bat primeiro.
  if /I not "%~1"=="/nopause" pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
set "PYTHONPATH=%CD%"
python -m app.smoke
set EXITCODE=%ERRORLEVEL%
echo.
if not "%EXITCODE%"=="0" (
  echo Smoke test encontrou falhas.
) else (
  echo Smoke test concluido com sucesso.
)
if /I not "%~1"=="/nopause" pause
exit /b %EXITCODE%
