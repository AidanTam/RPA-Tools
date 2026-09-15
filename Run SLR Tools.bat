@echo off
cd /d "%~dp0"
title SLR Tools (local runner)
echo(
echo    SLR Tools  (local runner)
echo(

where python >nul 2>nul || (
  echo    Python was not found on PATH.
  echo    Install Python 3.13 from https://www.python.org/downloads/ and tick
  echo    "Add python.exe to PATH", then run this again.
  echo(
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo    First run: setting up a private Python environment in .venv
  echo    This happens once and takes a few minutes. Later runs start straight up.
  echo(
  python -m venv .venv
  if errorlevel 1 (
    echo    Could not create the environment. Check that Python installed correctly.
    echo(
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
  echo    Installing dependencies from requirements.txt...
  echo(
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo(
    echo    Dependency install failed. You need an internet connection for this
    echo    first run. Delete the .venv folder and try again.
    echo(
    pause
    exit /b 1
  )
  echo(
)

rem Streamlit asks for an email on first run and blocks until it gets one.
rem Writing its credentials file up front skips that prompt entirely.
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
  > "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
  >> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

echo    Starting the app. Your browser opens at http://localhost:8501
echo    If it does not, paste that address into your browser yourself.
echo(
echo    Leave this window open while you work.
echo    Press Ctrl+C here, or close this window, to stop the app.
echo(

".venv\Scripts\python.exe" -m streamlit run "pyrpa\UI\rpa_tools.py"

echo(
echo    The app has stopped.
pause
