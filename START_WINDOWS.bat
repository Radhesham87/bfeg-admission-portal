@echo off
title BFEG Admission Portal - Local Preview
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Python is not installed, or not on your PATH.
  echo   Install it from https://www.python.org/downloads/
  echo   IMPORTANT: tick "Add Python to PATH" during install.
  echo.
  pause
  exit /b 1
)

python run_local.py
pause
