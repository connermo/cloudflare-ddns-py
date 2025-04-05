@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.6 or later
    pause
    exit /b 1
)

:: Check if pip is installed
pip --version > nul 2>&1
if errorlevel 1 (
    echo pip is not installed
    echo Please install pip
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install or upgrade requirements
echo Installing/upgrading requirements...
pip install -r requirements.txt

:: Check if config file exists
if not exist config.ini (
    echo Config file not found
    echo Copying example config...
    copy config.ini.example config.ini
    echo Please edit config.ini with your settings
    notepad config.ini
    pause
    exit /b 1
)

:: Run the script
echo Starting Cloudflare DDNS client...
python cloudflare_ddns.py -i 300

:: Keep the window open if there's an error
if errorlevel 1 (
    echo An error occurred
    pause
)

endlocal