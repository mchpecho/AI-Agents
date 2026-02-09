# AI Agent s Tool-Calling

**Praktické cvičení - Lekce 1 AI Agenti**

## 📋 Popis

Minimálny AI agent, ktorý demonštruje základy tool-callingu:
- Zavolá Gemini LLM API
- LLM si vyžiada nástroj `calculate` 
- Skript nástroj vykoná
- Výsledok pošle späť LLM
- Vypíše finálnu odpoveď

## 🚀 Inštalácia a spustenie

### 1. Klonovanie repozitára

```bash
git clone <your-repo-url>
cd <repo-name>
```

### 2. Vytvorenie virtuálneho prostredia

```bash
python -m venv .venv
```

### 3. Aktivácia virtuálneho prostredia

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 4. Inštalácia závislostí

```bash
pip install -r requirements.txt
```

### 5. Konfigurácia API kľúča

```bash
cp .env.example .env
```

Potom upravte `.env` súbor a doplňte váš Gemini API kľúč:
```
GEMINI_API_KEY=your_actual_api_key_here
```

**Ako získať Gemini API kľúč:**
1. Navštívte: https://aistudio.google.com/app/apikey
2. Prihláste sa s Google účtom
3. Kliknite na "Create API Key"
4. Skopírujte vygenerovaný kľúč do `.env` súboru

**🎉 Free Tier Info:**
- ✅ **Úplne ZADARMO** - žiadna kreditná karta potrebná
- ✅ **Gemini 2.5 Flash** - 5 RPM, 20 RPD, 250k TPM
- ✅ **Dostatočné pre testovanie a učenie**
- 💡 Pre produkciu môžete neskôr upgradovať na platený tier

### 6. Spustenie

```bash
python agent.py
```
```bash
python agent_react.py
```
```bash
python agent_advanced.py
```

## 🔧 Ako to funguje

### Architektúra

```
Používateľ
    ↓
[AI Agent]
    ↓
[LLM API - Gemini] ←→ [Tool: calculate]
    ↓
Finálna odpoveď
```

## 📁 Štruktúra projektu

```
.
├── agent.py              # ⭐ Základný AI agent (hlavné zadanie)
├── agent_react.py        # ⭐ Základný AI agent ReAct (hlavné zadanie)
├── agent_advanced.py     # 🚀 Rozšírená verzia s viacerými nástrojmi
├── agent_ollama.py       # 🦙 Alternatíva s lokálnym LLM (Ollama)
├── list_models.py        # 🤖 Zoznam dostupných gemini modelov pre api
├── requirements.txt      # Python závislosti
├── .env.example          # Šablóna pre environment premenné
├── .env                  # Vaše API kľúče (nie v gite!)
├── .gitignore            # Git ignore súbor
└── README.md             # Tento súbor
```
## ▶️ Použitie (agent_react.py)

### Jednoduchý výpočet:
<img width="670" height="457" alt="image" src="https://github.com/user-attachments/assets/f5a61314-290f-4e52-9e11-174c5c4f4849" />

### Komplexný výpočet
<img width="677" height="721" alt="image" src="https://github.com/user-attachments/assets/6ba2f2a1-0ce1-4276-ae1f-bea9a3c8ae82" />

