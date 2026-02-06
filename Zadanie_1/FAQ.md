# Často kladené otázky (FAQ)

## 💰 Platenie a API kľúč

### Q: Musím zaplatiť za Gemini API?
**A:** NIE! Gemini API má **úplne zadarmo free tier** bez potreby kreditnej karty. Stačí si vytvoriť Google účet a vygenerovať API kľúč na https://aistudio.google.com/app/apikey

### Q: Koľko requestov môžem urobiť zadarmo?
**A:** S free tier máte k dispozícii (január 2026):

| Model | Requests/min | Requests/deň |
|-------|--------------|--------------|
| Gemini 1.5 Flash | 10 RPM | 250 RPD |
| Gemini 2.5 Flash | 10 RPM | 250 RPD |
| Gemini 2.5 Flash-Lite | 15 RPM | 1,000 RPD |

Pre toto cvičenie je **Gemini 1.5 Flash** ideálny.

### Q: Stačí to na vypracovanie úlohy?
**A:** ÁNO, rozhodne! Pre testovanie a učenie je to viac než dosť. Tento projekt spraví cca 3-10 requestov pri spustení, čo je len zlomok denného limitu.

### Q: Čo ak prekročím free limity?
**A:** Dostanete HTTP 429 chybu (rate limit error). Stačí chvíľu počkať a skúsiť znova. Pre produkciu môžete upgradovať na platený tier.

### Q: Ako dlho funguje free tier?
**A:** **Navždy!** Free tier nie je časovo obmedzený. Môžete ho používať neobmedzene dlho s uvedenými rate limitmi.

---

## 🔧 Technické problémy

### Q: "ModuleNotFoundError: No module named 'google'"
**A:** Potrebujete nainštalovať závislosti:
```bash
pip install -r requirements.txt
```

### Q: "ValueError: GEMINI_API_KEY nie je nastavený"
**A:** Musíte vytvoriť `.env` súbor a doplniť API kľúč:
```bash
cp .env.example .env
# Potom upravte .env a doplňte váš API kľúč
```

### Q: "Rate limit exceeded (429)"
**A:** Prekročili ste free tier limity. Riešenia:
1. Počkajte pár minút a skúste znova
2. Použite model s vyššími limitmi (Flash-Lite)
3. Upgradujte na platený tier (nie je nutné pre cvičenie)

### Q: Agent sa zasekne a nič nevypíše
**A:** Skontrolujte:
1. Je váš API kľúč správny?
2. Máte internetové pripojenie?
3. Pozrite sa na chybové hlášky v konzole

---

## 🤖 Ollama alternatíva

### Q: Môžem to spustiť úplne offline?
**A:** ÁNO! Použite `agent_ollama.py` verziu:
1. Nainštalujte Ollama: https://ollama.ai
2. Stiahnite model: `ollama pull llama3.2`
3. Spustite server: `ollama serve`
4. Spustite: `python agent_ollama.py`

### Q: Ktorý model z Ollama použiť?
**A:** Odporúčané modely:
- **llama3.2** (3GB) - rýchly a dobrý
- **llama3.1** (4.7GB) - silnejší
- **gemma2** (5GB) - od Google
- **mistral** (4GB) - efektívny

### Q: Ollama vs Gemini API - čo je lepšie?
**A:** 
- **Gemini API**: Lepšia kvalita, jednoduchšie, ale vyžaduje internet
- **Ollama**: Offline, súkromie, ale slabšie modely a pomalšie

Pre toto cvičenie odporúčam **Gemini API** kvôli jednoduchosti.

---

## 📊 Rozdiely medzi verziami

### Q: Ktorú verziu mám použiť pre cvičenie?
**A:** **agent.py** - základná verzia plne spĺňa zadanie.

### Q: Prečo sú tam 3 verzie?
**A:**
- **agent.py** - základná verzia (POŽADOVANÁ pre cvičenie) ⭐
- **agent_advanced.py** - demo rozšírenia s viacerými nástrojmi 🚀
- **agent_ollama.py** - alternatíva pre lokálny LLM 🦙

### Q: Môžem odovzdať advanced verziu?
**A:** ÁNO, ale základná verzia stačí. Advanced je len bonus na ukázanie možností.

---

## 🐙 Github

### Q: Musím používať Git cez príkazový riadok?
**A:** NIE! Môžete použiť:
1. **GitHub Desktop** - grafické rozhranie
2. **VS Code** - integrovaný Git
3. **Webové rozhranie** - upload priamo na github.com

Pozrite `ODOVZDANIE.md` pre detailné návody.

### Q: Čo ak som omylom uploadol .env súbor?
**A:** Ihneď ho odstráňte:
```bash
git rm --cached .env
git commit -m "Remove .env from repository"
git push
```
A vytvorte si **nový API kľúč** (starý už nie je bezpečný).

### Q: Môže byť repozitár súkromný?
**A:** Závisí od požiadaviek vyučujúceho. Väčšinou je požadovaný **verejný** repozitár.

---

## 📝 Hodnotenie

### Q: Na čo sa pozerá vyučujúci?
**A:** Pravdepodobne:
1. ✅ Fungujúci kód (40%)
2. ✅ Správna implementácia tool-callingu (30%)
3. ✅ Dokumentácia a komentáre (20%)
4. ✅ Github štruktúra (10%)

### Q: Musím mať komentáre v kóde?
**A:** ÁNO, odporúčam pridať komentáre. Ukazujú, že rozumiete čo robíte.

### Q: Stačí len agent.py?
**A:** ÁNO, ale odporúčam pridať:
- README.md - popis projektu
- requirements.txt - závislosti
- .env.example - šablóna
- .gitignore - bezpečnosť

Všetko to máte už pripravené v tomto projekte! ✅

---

## ⏰ Deadline

### Q: Kedy je deadline?
**A:** 12.2.2026 (pozri zadanie)

### Q: Môžem odovzdať skôr?
**A:** ÁNO! Odporúčam odovzdať skôr pre istotu.

### Q: Čo ak nestihnem?
**A:** Kontaktujte vyučujúceho vopred.

---

## 💡 Ďalšie tipy

### Q: Ako môžem projekt rozšíriť?
**A:** Nápady:
1. Pridajte viac nástrojov (get_time, weather, atď.)
2. Web rozhranie (Flask/FastAPI)
3. Logovanie do súboru
4. Unit testy
5. Databáza pre históriu

Pozrite `agent_advanced.py` pre inšpiráciu.

### Q: Kde sa môžem dozvedieť viac?
**A:** Užitočné zdroje:
- **Gemini API Docs**: https://ai.google.dev/docs
- **Tool Calling Guide**: https://ai.google.dev/docs/function_calling
- **Python SDK**: https://github.com/google/generative-ai-python
- **Tento README**: obsahuje všetko potrebné

---

## 📞 Pomoc

### Q: Kde získam pomoc ak niečo nefunguje?
**A:**
1. Prečítajte si README.md
2. Skontrolujte ODOVZDANIE.md
3. Pozrite si chybové hlášky
4. Kontaktujte vyučujúceho
5. Spýtajte sa spolužiakov

---

**Posledná aktualizácia FAQ:** 6. február 2026

🎓 **Veľa úspechov s projektom!**
