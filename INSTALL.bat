@echo off
title F-AI Accountant One-Click Installer
color 0B

echo.
echo ========================================
echo  F-AI ACCOUNTANT ONE-CLICK INSTALLER
echo ========================================
echo  Enterprise Accounting SaaS Platform
echo ========================================
echo.

echo [INFO] Starting automated installation...
echo [INFO] This will install all dependencies and setup the database
echo [INFO] Please wait while we configure everything for you...
echo.

REM Run the Python installer
python setup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Installation completed successfully!
    echo [INFO] You can now run F-AI Accountant using START_F-AI_ACCOUNTANT.bat
    echo.
    echo Would you like to start F-AI Accountant now?
    set /p choice="Enter Y to start or N to exit: "
    if /i "%choice%"=="Y" (
        echo [INFO] Starting F-AI Accountant...
        START_F-AI_ACCOUNTANT.bat
    )
) else (
    echo.
    echo [ERROR] Installation failed. Please check the errors above.
    echo [INFO] You may need to install Python 3.8+ first from python.org
)

pause