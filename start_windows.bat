@echo off
title F-AI Accountant Enterprise Server
color 0A

echo.
echo ========================================
echo  F-AI ACCOUNTANT ENTERPRISE v2.0.0
echo ========================================
echo  Complete Enterprise Accounting SaaS
echo ========================================
echo.

echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo [INFO] Starting F-AI Accountant Server...
echo.
echo [ACCESS] Application URL: http://localhost:5000
echo [LOGIN]  Username: admin
echo [LOGIN]  Password: test
echo.
echo [STATUS] Server is starting... Please wait
echo [INFO]   Press Ctrl+C to stop the server
echo.

REM Start the application with enhanced configuration
python -m gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 --worker-class sync --max-requests 1000 --preload main:app

echo.
echo [INFO] Server stopped
pause