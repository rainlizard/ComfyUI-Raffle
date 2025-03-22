@echo off
echo Batch file received: "%~1"
python "%~dp0extract_categories.py" "%~f1"
pause