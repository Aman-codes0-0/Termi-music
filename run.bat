@echo off
setlocal

:: Termi-music Run Script for Windows

:: Check if virtual environment exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate

:: Check if requirements are installed
python -c "import textual" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

:: Run the application
python main.py

if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error.
    pause
)
