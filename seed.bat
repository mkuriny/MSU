@echo off
chcp 65001 > nul

echo === Создание администратора ===

if exist venv\Scripts\python.exe (
    echo Используется venv
    venv\Scripts\python -m app.scripts.seed_admin
) else (
    echo Используется системный Python
    python -m app.scripts.seed_admin
)

echo === Готово ===
pause