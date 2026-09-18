@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pdf-to-web.exe" (
  echo PDF to Web is not set up in this folder.
  echo.
  echo Follow the Development setup steps in README.md, then launch this file again.
  echo.
  pause
  exit /b 1
)

echo Starting PDF to Web...
echo Leave this window open while using the application.
echo.

".venv\Scripts\pdf-to-web.exe" serve
if errorlevel 1 pause
