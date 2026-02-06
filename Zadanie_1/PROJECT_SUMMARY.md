# 🤖 AI Agent s Tool-Calling - Súhrn projektu

## 📋 Základné informácie

**Názov:** AI Agent s Tool-Calling  
**Predmet:** Praktické cvičenie - Lekcia 1 AI Agenti  
**Bodov:** 100  
**Deadline:** 12.2.2026  
**Jazyk:** Python 3.8+  
**LLM API:** Google Gemini 1.5 Flash  

---

## 📁 Obsah projektu

### Kľúčové súbory

| Súbor | Veľkosť | Popis |
|-------|---------|-------|
| **agent.py** | 5.3 KB | ⭐ Hlavný skript - základná implementácia |
| **agent_advanced.py** | 8.1 KB | 🚀 Rozšírená verzia s viacerými nástrojmi |
| **agent_ollama.py** | 4.6 KB | 🦙 Alternatíva s lokálnym LLM (Ollama) |
| **requirements.txt** | 65 B | 📦 Python závislosti |
| **.env.example** | 120 B | 🔑 Šablóna pre API kľúče |
| **.gitignore** | 210 B | 🚫 Ignorované súbory pre Git |

### Dokumentácia

| Súbor | Veľkosť | Popis |
|-------|---------|-------|
| **README.md** | 5.1 KB | 📖 Hlavná dokumentácia projektu |
| **ODOVZDANIE.md** | 4.7 KB | 📝 Návod na odovzdanie úlohy |
| **ARCHITECTURE.md** | 8.6 KB | 🏗️ Architektúra a diagramy |
| **EXAMPLE_OUTPUT.md** | 2.5 KB | 📊 Ukážka výstupu programu |

### Setup skripty

| Súbor | Veľkosť | Popis |
|-------|---------|-------|
| **setup.sh** | 2.0 KB | 🐧 Automatická inštalácia (Linux/Mac) |
| **setup.bat** | 1.9 KB | 🪟 Automatická inštalácia (Windows) |

**Celková veľkosť:** ~41 KB  
**Počet súborov:** 11

---

## 🎯 Splnené požiadavky

✅ **Python skript** - tri verzie (basic, advanced, ollama)  
✅ **Volanie LLM API** - Google Gemini API  
✅ **Použitie nástroja** - funkcia `calculate()`  
✅ **Návrat odpovede do LLM** - kompletný tool-calling flow  
✅ **Zdrojový kód** - čitateľný, komentovaný  
✅ **Dokumentácia** - README, návody, príklady  
✅ **Github ready** - .gitignore, setup skripty  

---

## 🚀 Rýchly štart

### Linux/Mac
```bash
git clone <your-repo-url>
cd <repo-name>
chmod +x setup.sh
./setup.sh
# Upravte .env súbor
python agent.py
```

### Windows
```batch
git clone <your-repo-url>
cd <repo-name>
setup.bat
REM Upravte .env súbor
python agent.py
```

---

## 🔧 Technická špecifikácia

### Použité technológie
- **Python 3.8+**
- **google-generativeai** - Gemini API klient
- **python-dotenv** - Environment premenné
- **requests** - HTTP komunikácia (pre Ollama verziu)

### Architektúra
```
Používateľ → Agent → LLM API ⟷ Nástroje
                  ↓
            Finálna odpoveď
```

### Podporované nástroje

#### Základná verzia (`agent.py`)
- `calculate(operation, a, b)` - matematické operácie

#### Rozšírená verzia (`agent_advanced.py`)
- `calculate()` - matematické operácie
- `get_current_time()` - aktuálny čas
- `roll_dice()` - hádzanie kockami
- `get_weather()` - počasie (simulované)

---

## 📚 Vzdelávacie ciele

Tento projekt demonštruje:

1. **LLM API integrácia** - pripojenie na Gemini API
2. **Tool-calling** - definícia a použitie nástrojov
3. **Function calling** - spracovanie function calls od LLM
4. **Multi-turn konverzácia** - posielanie výsledkov späť do LLM
5. **Error handling** - ošetrenie chýb a výnimiek
6. **Best practices** - čitateľný kód, dokumentácia, Git workflow

---

## 🎓 Čo som sa naučil

- ✅ Ako zavolať LLM API (Gemini)
- ✅ Ako definovať nástroje pre LLM
- ✅ Ako spracovať tool calls
- ✅ Ako implementovať kompletný agent flow
- ✅ Ako dokumentovať projekt
- ✅ Ako pripraviť projekt na Github

---

## 🔮 Možnosti rozšírenia

### Jednoduché rozšírenia
- [ ] Viac matematických funkcií (mocnina, odmocnina, sin, cos)
- [ ] História konverzácií
- [ ] Logovanie do súboru
- [ ] Unit testy

### Stredne pokročilé
- [ ] Integrácia s reálnym Weather API
- [ ] Databázové operácie
- [ ] Webové rozhranie (Flask/FastAPI)
- [ ] Caching výsledkov

### Pokročilé
- [ ] Multi-agent systém
- [ ] RAG (Retrieval-Augmented Generation)
- [ ] Fine-tuning vlastného modelu
- [ ] Production deployment

---

## 📊 Štatistiky kódu

### Riadky kódu (LOC)

| Súbor | Riadky | Komentáre | Blank | Total |
|-------|--------|-----------|-------|-------|
| agent.py | ~120 | ~40 | ~20 | ~180 |
| agent_advanced.py | ~200 | ~50 | ~30 | ~280 |
| agent_ollama.py | ~120 | ~30 | ~20 | ~170 |

**Celkom:** ~630 riadkov

### Funkcie

- **Základná verzia:** 3 funkcie (1 nástroj)
- **Rozšírená verzia:** 6 funkcií (4 nástroje)
- **Ollama verzia:** 4 funkcie (1 nástroj)

---

## 💡 Tipy pre vyučujúcich

### Hodnotenie

**Odporúčané kritériá:**

1. **Funkcionalita (40 bodov)**
   - Agent korektne volá LLM API (10b)
   - Tool-calling implementovaný správne (15b)
   - Výsledok sa vracia do LLM (15b)

2. **Kvalita kódu (30 bodov)**
   - Čitateľnosť a štruktúra (10b)
   - Komentáre a dokumentácia (10b)
   - Error handling (10b)

3. **Dokumentácia (20 bodov)**
   - README je prehľadný (10b)
   - Návod na spustenie (5b)
   - Príklady použitia (5b)

4. **Github (10 bodov)**
   - Správna štruktúra repozitára (5b)
   - .gitignore funguje (3b)
   - Commit messages (2b)

### Časté chyby študentov

- ❌ Zabudnutý .env v .gitignore
- ❌ Chýbajúce komentáre
- ❌ Nefunkčný requirements.txt
- ❌ Chýbajúci README
- ❌ Neošetrené výnimky

---

## 📞 Podpora

Ak narazíte na problémy:

1. Skontrolujte **README.md** pre základné návody
2. Pozrite **ODOVZDANIE.md** pre Github workflow
3. Prečítajte **ARCHITECTURE.md** pre pochopenie architektúry
4. Kontaktujte vyučujúceho

---

## 📜 Licencia

Tento projekt je vytvorený pre vzdelávacie účely.  
Študenti môžu voľne používať a upravovať kód pre učebné účely.

---

## ✅ Checklist pred odovzdaním

- [ ] Kód funguje a bol otestovaný
- [ ] Všetky súbory sú v repozitári
- [ ] .env NIE JE v repozitári
- [ ] README je aktuálny
- [ ] Commit messages sú zmysluplné
- [ ] Repozitár je verejný (alebo podľa pokynov)
- [ ] Link bol odovzdaný v Google Classroom

---

**Verzia dokumentácie:** 1.0  
**Dátum vytvorenia:** 6. február 2026  
**Autor:** Claude (Anthropic AI)

---

🎉 **Veľa úspechov s projektom!**
