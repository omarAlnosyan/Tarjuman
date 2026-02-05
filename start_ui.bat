@echo off
cd /d "%~dp0\tarjuman-ui"
echo Starting Tarjuman UI on http://localhost:3000 ...
echo (زيادة حد الذاكرة لتفادي خطأ Out of Memory)
set NODE_OPTIONS=--max-old-space-size=2048
call npm run dev
pause
