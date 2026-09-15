@echo off
cd /d "%~dp0"
title SLR Tools (local runner)
echo(
echo    SLR Tools  (local runner)
echo(

rem Opening this file from inside a zip extracts it alone to a temp folder,
rem leaving none of the app next to it. Catch that before anything else.
if not exist "requirements.txt" goto :notextracted
if not exist "pyrpa\UI\rpa_tools.py" goto :notextracted
goto :extracted

:notextracted
echo    This file is not sitting with the rest of the app.
echo(
echo    If you opened it from inside the .zip, Windows copied just this one
echo    file to a temporary folder. Close this window, right-click the .zip,
echo    choose "Extract All", and run this file from the extracted folder.
echo(
echo    Current folder: %CD%
echo(
pause
exit /b 1

:extracted
rem This app needs Python 3.12 or newer: the pinned numpy/pandas versions
rem refuse to install on anything older. The "python" on PATH is often an
rem older install, so prefer the py launcher, which can pick a newer one.
set "PYCMD="
py -3.13 -c "pass" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3.13"
if not defined PYCMD (
  py -3.14 -c "pass" >nul 2>nul
  if not errorlevel 1 set "PYCMD=py -3.14"
)
if not defined PYCMD (
  py -3.12 -c "pass" >nul 2>nul
  if not errorlevel 1 set "PYCMD=py -3.12"
)
if not defined PYCMD (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
  if not errorlevel 1 set "PYCMD=python"
)

if not defined PYCMD (
  echo    This app needs Python 3.12 or newer, and none was found.
  echo(
  echo    Detected on this machine:
  py --list 2>nul
  python -c "import sys; print('     python on PATH: ' + sys.version.split()[0])" 2>nul
  echo(
  echo    Install Python 3.13 from https://www.python.org/downloads/ and tick
  echo    "Add python.exe to PATH", then run this again.
  echo(
  pause
  exit /b 1
)

rem A .venv left over from an older Python cannot run this app either.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
  if errorlevel 1 (
    echo    The existing .venv folder was built with a Python older than 3.12,
    echo    so the dependencies cannot install into it.
    echo(
    echo    Delete the .venv folder next to this file, then run this again.
    echo(
    pause
    exit /b 1
  )
)

echo    Using %PYCMD%
echo(

if not exist ".venv\Scripts\python.exe" (
  echo    First run: setting up a private Python environment in .venv
  echo    This happens once and takes a few minutes. Later runs start straight up.
  echo(
  %PYCMD% -m venv .venv
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
    echo    Dependency install failed. The first run needs an internet connection.
    echo    Delete the .venv folder and try again.
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
