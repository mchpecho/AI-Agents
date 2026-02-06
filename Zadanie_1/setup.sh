#!/bin/bash

# Setup script pre AI Agent projekt
# Autor: Prakticke cvicenie - Lekcia 1 AI Agenti

echo "======================================"
echo "AI Agent Setup Script"
echo "======================================"
echo ""

# Kontrola Python verzie
echo "Kontrolujem Python instalaciu..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 nie je nainstalovany!"
    echo "Nainstalujte Python 3.8 alebo novsi"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[OK] Najdeny: $PYTHON_VERSION"
echo ""

# Vytvorenie virtualneho prostredia
echo "Vytvaram virtualne prostredie..."
python3 -m venv .venv
echo "[OK] Virtualne prostredie vytvorene"
echo ""

# Aktivacia virtualneho prostredia
echo "Aktivujem virtualne prostredie..."
source .venv/bin/activate
echo "[OK] Virtualne prostredie aktivovane"
echo ""

# Instalacia zavislosti
echo "Instalujem zavislosti..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "[OK] Zavislosti nainstalovane"
echo ""

# Vytvorenie .env suboru ak neexistuje
if [ ! -f .env ]; then
    echo "Vytvaram .env subor..."
    cp .env.example .env
    echo "[OK] .env subor vytvoreny"
    echo ""
    echo "DOLEZITE: Upravte .env subor a doplnte vas GEMINI_API_KEY"
    echo "Ziskajte API kluc na: https://aistudio.google.com/app/apikey"
else
    echo "[ERROR] .env subor uz existuje"
fi
echo ""

echo "======================================"
echo "Setup dokonceny!"
echo "======================================"
echo ""
echo "Dalsie kroky:"
echo "   1. Upravte .env subor a doplnte GEMINI_API_KEY"
echo "   2. Spustite: python agent.py"
echo ""
echo "Tipy:"
echo "   - Zakladna verzia: python agent.py"
echo "   - Pokrocila verzia: python agent_advanced.py"
echo "   - Ollama verzia: python agent_ollama.py"
echo ""
echo "Viac info v README.md"
echo ""
