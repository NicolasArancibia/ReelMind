@echo off
powershell.exe -NoProfile -File "%~dp0scripts\maintenance-window.ps1"
if errorlevel 1 pause
