@echo off
cd /d "%~dp0"
echo Starting Basic Backend Server...
start "Basic Backend Server" cmd /k "call .venv\Scripts\activate && python src\api\basic_backend_server.py"
echo Starting Expose Server...
start "Expose Server" cmd /k "call .venv\Scripts\activate && python src\api\expose_server.py"
echo Servers started.
