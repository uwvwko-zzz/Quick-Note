@echo off
chcp 65001 >nul
title Quick Note
cd /d "%~dp0"
python quick_note.py
pause