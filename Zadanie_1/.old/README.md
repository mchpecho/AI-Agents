## Praktické cvičení - Lekce 1
AI Agenti, Počet bodů: 100,
Deadline: 12.2.2026

---

### Zadání:
Napiš Python skript, který zavolá LLM API, použije nástroj (např. výpočetní funkci) a
vrátí odpověď zpět LLM.
### Forma odevzdání:
Vypracovaný úkol odevzdejte ve formě zdrojového kódu. Projekt ideálně nahrajte na
Github a odevzdejte link do Github repositáře. Link odevzdejte v Google Classroom.


### Riešenie:

# Minimal AI agent (tool-calling)

Skript:
- zavolá Gemini LLM
- LLM si vyžiada nástroj `calculate`
- skript nástroj vykoná
- výsledok pošle späť LLM
- vypíše finálnu odpoveď

## Inštalácia
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# doplň GEMINI_API_KEY

