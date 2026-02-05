@echo off
cd /d "%~dp0"
title Tarjuman - تشغيل كامل
echo ============================================
echo   ترجمان - تحرير المنافذ وتشغيل API والواجهة
echo ============================================
echo.

echo [1/4] تحرير المنفذ 8000 (API)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
  taskkill /PID %%a /F >nul 2>&1
  echo       تم إيقاف العملية %%a
)
echo [2/4] تحرير المنفذ 3000 (الواجهة)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
  taskkill /PID %%a /F >nul 2>&1
  echo       تم إيقاف العملية %%a
)
echo [3/4] إزالة قفل Next.js إن وُجد...
if exist "tarjuman-ui\.next\dev\lock" (
  del /f "tarjuman-ui\.next\dev\lock"
  echo       تم حذف ملف القفل
) else (
  echo       لا يوجد قفل
)

echo [4/4] تشغيل الـ API في نافذة جديدة...
start "Tarjuman API" cmd /k "cd /d "%~dp0" && echo انتظر حتى تظهر: [*] Tarjuman API ready. && echo. && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul

echo تشغيل الواجهة في نافذة جديدة...
start "Tarjuman UI" cmd /k "cd /d "%~dp0tarjuman-ui" && set NODE_OPTIONS=--max-old-space-size=2048 && echo انتظر حتى تظهر Ready ثم افتح http://localhost:3000 && echo. && npm run dev"

echo.
echo ============================================
echo   تم. نافذتان مفتوحتان:
echo   - API:  انتظر Tarjuman API ready ثم افتح المتصفح
echo   - UI:   انتظر Ready ثم افتح http://localhost:3000
echo ============================================
pause
