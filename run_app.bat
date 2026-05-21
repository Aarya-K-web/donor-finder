@echo off
title LifeLine Link - Local Server Runner
cls
echo =====================================================================
echo    LifeLine Link - Blood and Organ Donor Finder Server Runner (Root)
echo =====================================================================
echo.

:: Ask user for MySQL credentials
set /p DB_PASS="Enter your MySQL root password (leave blank and press Enter if none): "
set DB_USER=root
set DB_HOST=localhost
set DB_NAME=blood_organ_donor_db

:: Configure environment variables for python executions
set DB_PASSWORD=%DB_PASS%
set DB_HOST=localhost
set DB_USER=root
set DB_NAME=blood_organ_donor_db

echo Server is launching!
echo Open http://127.0.0.1:5000 in your browser to view the application.
echo Press Ctrl+C inside this window to stop the server at any time.
echo =====================================================================
echo.

python app.py
pause
