@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Falta el entorno de Python. Sigue la instalacion del archivo README.md.
  pause
  exit /b 1
)
if not exist ".env" (
  echo Falta .env. Copia .env.example y configura tu clave de Django.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" manage.py check
if errorlevel 1 (
  echo No se pudo iniciar. Revisa el mensaje anterior y README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 (
  pause
  exit /b 1
)
echo.
echo Mesa Viva - Abre http://127.0.0.1:8000/ en tu navegador.
echo Para detener el servidor presiona Ctrl+C.
echo.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
pause
