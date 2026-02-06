# Návod na odovzdanie úlohy

## 📋 Zadanie
**Praktické cvičenie - Lekce 1 AI Agenti**  
**Počet bodov:** 100  
**Deadline:** 12.2.2026

### Požadovaná forma:
✅ Vypracovaný úkol vo forme zdrojového kódu  
✅ Projekt nahraný na Github  
✅ Link odevzdaný v Google Classroom

---

## 🚀 Kroky na odovzdanie

### 1. Nahrajte projekt na Github

#### A) Vytvorte nový repozitár na Github:
1. Choďte na https://github.com/new
2. Zadajte názov repozitára (napr. `ai-agent-tool-calling`)
3. Nastavte repozitár ako **Public** alebo **Private** (podľa pokynov vyučujúceho)
4. **NEKLIKAJTE** na "Add README" (už ho máte)
5. Kliknite "Create repository"

#### B) Nahrajte súbory:

**Spôsob 1 - Cez príkazový riadok (Git):**

```bash
# Prejdite do priečinka s projektom
cd cesta/k/projektu

# Inicializujte Git repozitár
git init

# Pridajte všetky súbory
git add .

# Vytvorte prvý commit
git commit -m "Initial commit: AI Agent s tool-calling"

# Pripojte vzdialený repozitár (zmeňte URL za váš)
git remote add origin https://github.com/vase-meno/ai-agent-tool-calling.git

# Nahrajte súbory
git branch -M main
git push -u origin main
```

**Spôsob 2 - Cez GitHub Desktop:**
1. Otvorte GitHub Desktop
2. File → Add Local Repository
3. Vyberte priečinok s projektom
4. Commit changes
5. Publish repository

**Spôsob 3 - Cez webové rozhranie:**
1. V repozitári kliknite "uploading an existing file"
2. Potiahnte všetky súbory (okrem `.env` súboru!)
3. Kliknite "Commit changes"

### 2. Overte obsah repozitára

Váš Github repozitár by mal obsahovať:

```
✅ agent.py              - hlavný skript (povinný)
✅ requirements.txt      - závislosti
✅ .env.example         - šablóna pre API kľúče
✅ .gitignore           - ignorované súbory
✅ README.md            - dokumentácia
✅ setup.sh             - setup script (Linux/Mac)
✅ setup.bat            - setup script (Windows)
✅ EXAMPLE_OUTPUT.md    - ukážka výstupu

⚠️  Bonusové súbory (nepovinné):
- agent_advanced.py     - rozšírená verzia
- agent_ollama.py       - Ollama verzia
```

**DÔLEŽITÉ:** 
- ❌ **NENAHRAJTE** `.env` súbor (obsahuje váš API kľúč!)
- ✅ Skontrolujte, že `.gitignore` funguje správne

### 3. Otestujte repozitár

Overte, že niekto iný dokáže váš projekt spustiť:

1. **Klonujte svoj repozitár** do nového priečinka:
   ```bash
   git clone https://github.com/vase-meno/ai-agent-tool-calling.git
   cd ai-agent-tool-calling
   ```

2. **Spustite setup:**
   ```bash
   # Linux/Mac
   chmod +x setup.sh
   ./setup.sh
   
   # Windows
   setup.bat
   ```

3. **Doplňte API kľúč** do `.env`

4. **Spustite agent:**
   ```bash
   python agent.py
   ```

Ak všetko funguje, môžete odovzdať! ✅

### 4. Skopírujte link a odevzdajte

1. Choďte na váš Github repozitár
2. Skopírujte URL z prehliadača (napr. `https://github.com/vase-meno/ai-agent-tool-calling`)
3. Otvorte Google Classroom
4. Nájdite zadanie "Praktické cvičení - Lekce 1 AI Agenti"
5. Vložte link a kliknite "Odevzdať"

---

## ✅ Kontrolný zoznam pred odovzdaním

Uistite sa, že:

- [ ] Repozitár je verejný (alebo súkromný podľa pokynov)
- [ ] Obsahuje všetky požadované súbory
- [ ] README.md je prehľadný a obsahuje návod
- [ ] `.env` súbor **NIE JE** v repozitári
- [ ] `.gitignore` správne ignoruje `.env`, `.venv`, atď.
- [ ] Kód funguje (otestovali ste ho)
- [ ] Sú prítomné komentáre v kóde
- [ ] Link na repozitár ste skopírovali správne

---

## 📊 Bodovanie (orientačne)

- **30 bodov** - Správna implementácia volania LLM API
- **30 bodov** - Správna implementácia tool-callingu
- **20 bodov** - Správne spracovanie výsledku a návrat do LLM
- **10 bodov** - Kvalita kódu a dokumentácie
- **10 bodov** - Funkčnosť a testovateľnosť

---

## 💡 Tipy

1. **Testujte včas** - nečakajte na deadline
2. **Používajte .gitignore** - ochránite svoje API kľúče
3. **Píšte README** - uľahčíte prácu vyučujúcemu
4. **Komentujte kód** - ukážete, že rozumiete čo robíte
5. **Commitujte postupne** - nie všetko naraz na poslednú chvíľu

---

## 🆘 Časté problémy

### Problém: "git: command not found"
**Riešenie:** Nainštalujte Git z https://git-scm.com/

### Problém: "Permission denied" pri pushu
**Riešenie:** Nastavte SSH kľúč alebo použite Personal Access Token

### Problém: ".env súbor je v repozitári"
**Riešenie:** 
```bash
git rm --cached .env
git commit -m "Remove .env from repository"
git push
```

### Problém: "ModuleNotFoundError: No module named 'google'"
**Riešenie:** 
```bash
pip install -r requirements.txt
```

---

## 📞 Kontakt

Ak máte problémy, kontaktujte vyučujúceho alebo použite fórum predmetu.

**Držím palce! 🍀**
