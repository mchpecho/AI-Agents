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

### 6. Spustenie

```bash
python agent.py
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

### Proces:

1. **Používateľ zadá otázku**: Napríklad "Koľko je 25 krát 4?"

2. **Agent zavolá LLM**: Pošle otázku Gemini API s definíciou dostupných nástrojov

3. **LLM analyzuje a požiada o nástroj**: 
   ```json
   {
     "function_name": "calculate",
     "arguments": {
       "operation": "multiply",
       "a": 25,
       "b": 4
     }
   }
   ```

4. **Agent vykoná nástroj**: Zavolá funkciu `calculate("multiply", 25, 4)`

5. **Nástroj vráti výsledok**: `100`

6. **Agent pošle výsledok späť LLM**: LLM dostane výsledok výpočtu

7. **LLM vygeneruje finálnu odpoveď**: "Výsledok je 100."

## 📁 Štruktúra projektu

```
.
├── agent.py              # ⭐ Základný AI agent (hlavné zadanie)
├── agent_advanced.py     # 🚀 Rozšírená verzia s viacerými nástrojmi
├── agent_ollama.py       # 🦙 Alternatíva s lokálnym LLM (Ollama)
├── requirements.txt      # Python závislosti
├── .env.example         # Šablóna pre environment premenné
├── .env                 # Vaše API kľúče (nie v gite!)
├── .gitignore           # Git ignore súbor
└── README.md            # Tento súbor
```

## 📝 Verzie skriptov

### `agent.py`
Spĺňa zadanie cvičenia. Jednoduchý agent s jedným nástrojom `calculate`.

### `list_models.py`
Vypíše zoznam dostupných gemini modelov pre free API.

**Spustenie:**
```bash
python agent.py
```

### `agent_advanced.py` - Pokročilá verzia 🚀
Rozšírený agent s viacerými nástrojmi:
- `calculate` - matematické operácie
- `get_current_time` - aktuálny čas
- `roll_dice` - hádzanie kockami
- `get_weather` - predpoveď počasia (simulovaná)

**Spustenie:**
```bash
python agent_advanced.py
```

### `agent_ollama.py` - Lokálny LLM 🦙
Alternatívne riešenie s Ollama (open-source lokálny LLM).

**Prerekvizity:**
1. Nainštalujte Ollama: https://ollama.ai
2. Stiahnite model: `ollama pull llama3.2`
3. Spustite server: `ollama serve`

**Spustenie:**
```bash
python agent_ollama.py
```

## 🛠️ Nástroje

### `calculate`
Matematická kalkulačka s podporou operácií:
- `add` - sčítanie
- `subtract` - odčítanie  
- `multiply` - násobenie
- `divide` - delenie

**Parametre:**
- `operation` (string): Typ operácie
- `a` (float): Prvé číslo
- `b` (float): Druhé číslo

**Návratová hodnota:** Výsledok výpočtu (float)

## 📚 Použité technológie

- **Python 3.8+**
- **Google Gemini API** - LLM pre tool-calling
- **python-dotenv** - Správa environment premenných

## 🔐 Bezpečnosť

- `.env` súbor je v `.gitignore` - nikdy necommitujte API kľúče!
- Používajte `.env.example` ako šablónu 

## 👨‍💻 Autor
Michal Pecho

