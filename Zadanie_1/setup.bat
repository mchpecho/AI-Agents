@echo off
REM Setup script pre AI Agent projekt (Windows)
REM Autor: Prakticke cvicenie - Lekcia 1 AI Agenti

echo ======================================
echo AI Agent Setup Script (Windows)
echo ======================================
echo.

REM Kontrola Python verzie
echo Kontrolujem Python instalaciu...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python nie je nainstalovany!
    echo    Nainstalujte Python 3.8 alebo novsi z python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Najdeny: %PYTHON_VERSION%
echo.

REM Vytvorenie virtualneho prostredia
echo Vytvaram virtualne prostredie...
python -m venv .venv
echo Virtualne prostredie vytvorene
echo.

REM Aktivacia virtualneho prostredia
echo Aktivujem virtualne prostredie...
call .venv\Scripts\activate.bat
echo [OK] Virtualne prostredie aktivovane
echo.

REM Instalacia zavislosti
echo Instalujem zavislosti...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo [OK] Zavislosti nainstalovane
echo.

REM Vytvorenie .env suboru ak neexistuje
if not exist .env (
    echo Vytvaram .env subor...
    copy .env.example .env >nul
    echo [OK] .env subor vytvoreny
    echo.
    echo DOLEZITE: Upravte .env subor a doplnte vas GEMINI_API_KEY
    echo Ziskajte API kluc na: https://aistudio.google.com/app/apikey
) else (
    echo [ERROR] .env subor uz existuje
)
echo.

echo ======================================
echo Setup dokonceny!
echo ======================================
echo.
echo Dalsie kroky:
echo    1. Upravte .env subor a doplnte GEMINI_API_KEY
echo    2. Spustite: python agent.py
echo.
echo Tipy:
echo   - Zakladna verzia: python agent.py
echo   - Pokrocila verzia: python agent_advanced.py
echo   - Ollama verzia: python agent_ollama.py
echo.
echo Viac info v README.md
echo.
pause
