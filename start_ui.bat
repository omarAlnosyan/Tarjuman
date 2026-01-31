@echo off
cd /d "%~dp0\tarjuman-ui"
echo Starting Tarjuman UI on http://localhost:3000 ...
call npm run dev
pause
