@echo off
title LifeLine Link - Aiven Cloud Server Runner
cls
echo =====================================================================
echo    LifeLine Link - Blood and Organ Donor Finder (Aiven Cloud DB)
echo =====================================================================
echo.

if exist .env (
    echo Loading configuration from .env file...
    for /f "usebackq delims=" %%x in (".env") do (
        set "%%x"
    )
) else (
    echo [WARNING] .env file not found!
    echo Please make sure your .env file is present or manually enter password.
    echo.
    set /p DB_PASSWORD="Enter Aiven MySQL Password: "
    set DB_HOST=donor-finder-db-aaryak418-a818.i.aivencloud.com
    set DB_PORT=10208
    set DB_USER=avnadmin
    set DB_NAME=blood_organ_donor_db
)

echo.
echo Connecting to Aiven Cloud MySQL database...
echo Host: %DB_HOST%
echo Port: %DB_PORT%
echo Database: %DB_NAME%
echo.

echo Server is launching on Aiven Cloud database!
echo Open http://127.0.0.1:5000 in your browser to view the application.
echo Press Ctrl+C inside this window to stop the server at any time.
echo =====================================================================
echo.

python app.py
pause
