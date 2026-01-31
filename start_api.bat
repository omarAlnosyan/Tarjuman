@echo off
cd /d "%~dp0"
echo Starting Tarjuman API on http://localhost:8000 ...
if defined CONDA_EXE (
  call conda activate base
)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
pause
