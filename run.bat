@echo off
setlocal
rem ── Westwood MarketPulse — one-click local launch ─────────────────────────
rem Backend (FastAPI):  http://127.0.0.1:8210   (API docs at /docs)
rem Frontend (built):   http://127.0.0.1:4175/MarketPulse/
rem
rem The frontend is a production build with the API base baked in
rem (frontend2: VITE_API_BASE_URL=http://127.0.0.1:8210 npx vite build).
rem If the backend is down the UI degrades gracefully to bundled data.

set "ROOT=%~dp0"
set "API_PORT=8210"
set "WEB_PORT=4175"
set "URL=http://127.0.0.1:%WEB_PORT%/MarketPulse/"

where python >nul 2>nul || (
  echo Python 3.11+ is required. Run "Setup Westwood Platform.bat" first.
  pause & exit /b 1
)
where node >nul 2>nul || (
  echo Node.js 20+ is required to serve the frontend.
  pause & exit /b 1
)

rem Backend — skip if already serving
netstat -ano | findstr /C:":%API_PORT% " | findstr LISTENING >nul
if not errorlevel 1 (
  echo MarketPulse API already running on :%API_PORT%
) else (
  echo Starting MarketPulse API on :%API_PORT% ...
  start "MarketPulse API" /min cmd /c "cd /d "%ROOT%" && python -m uvicorn backend.main:app --host 127.0.0.1 --port %API_PORT%"
)

rem Frontend — build once if dist is missing, then serve
if not exist "%ROOT%frontend2\dist\index.html" (
  echo First run - building the frontend...
  cd /d "%ROOT%frontend2"
  call npm.cmd ci || ( echo Dependency install failed. & pause & exit /b 1 )
  set "VITE_API_BASE_URL=http://127.0.0.1:%API_PORT%"
  call npx.cmd vite build || ( echo Build failed. & pause & exit /b 1 )
)

rem Frontend — bind to 127.0.0.1 explicitly (vite otherwise binds IPv6 ::1
rem only on Windows, and http://127.0.0.1 refuses to connect)
netstat -ano | findstr /C:":%WEB_PORT% " | findstr LISTENING >nul
if not errorlevel 1 (
  echo Frontend already serving on :%WEB_PORT%
) else (
  start "MarketPulse Web" /min cmd /c "cd /d "%ROOT%frontend2" && npx.cmd vite preview --host 127.0.0.1 --port %WEB_PORT% --strictPort"
)

timeout /t 3 /nobreak >nul
start "" "%URL%"
echo.
echo MarketPulse is up:  %URL%
echo Close the "MarketPulse API" and "MarketPulse Web" windows to stop.
endlocal
