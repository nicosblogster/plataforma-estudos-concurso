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
python -m app.doctor
set EXITCODE=%ERRORLEVEL%
echo.
if not "%EXITCODE%"=="0" (
  echo Diagnostico encontrou falhas operacionais.
) else (
  echo Diagnostico concluido com sucesso.
)
pause
exit /b %EXITCODE%
