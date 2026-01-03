
@echo off
echo Running MSU
set PYTHONPATH=%CD%\app
call venv\Scripts\activate
python run.py
pause