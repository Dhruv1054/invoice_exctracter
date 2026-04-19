@echo off
title Invoice Extraction Portal

echo.
echo ==========================================
echo   Invoice Extraction Portal - Starting
echo ==========================================
echo.

REM Start Streamlit in a new window
echo [1/2] Starting Streamlit app on port 8501...
start "Streamlit App" cmd /k "cd /d %~dp0 && streamlit run app.py"

REM Wait for Streamlit to boot
timeout /t 4 /nobreak >nul

REM Start ngrok tunnel in a new window
echo [2/2] Starting ngrok tunnel...
start "ngrok Tunnel" cmd /k "ngrok http 8501"

echo.
echo ==========================================
echo   Both windows are now open.
echo   Copy the https://xxxx.ngrok-free.app
echo   URL from the ngrok window and share it.
echo ==========================================
echo.
pause
