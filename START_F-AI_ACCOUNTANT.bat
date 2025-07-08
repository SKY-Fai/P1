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

echo [INFO] Starting F-AI Accountant Server...
echo.
echo [ACCESS] Application URL: http://localhost:5000
echo [LOGIN]  Username: admin
echo [LOGIN]  Password: test
echo.
echo [STATUS] Server is starting... Please wait
echo [INFO]   Press Ctrl+C to stop the server
echo.

python main.py

echo.
echo [INFO] Server stopped
pause