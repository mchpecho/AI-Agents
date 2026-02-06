# Ukážkový výstup agenta

Toto je príklad toho, ako vyzerá výstup pri spustení `agent.py`:

```
============================================================
🤖 AI AGENT - Tool Calling Demo
============================================================

👤 Používateľ: Koľko je 25 krát 4?

📡 Volám LLM API...

🤖 LLM požaduje nástroj: calculate
   Argumenty: {
     "operation": "multiply",
     "a": 25,
     "b": 4
   }

🔧 Nástroj 'calculate' vykonaný: multiply(25, 4) = 100

📤 Posielam výsledok späť LLM: 100

📡 Volám LLM API s výsledkom nástroja...

💬 Finálna odpoveď LLM:
============================================================
25 krát 4 je 100.
============================================================


============================================================
🤖 AI AGENT - Tool Calling Demo
============================================================

👤 Používateľ: Vypočítaj (150 + 50) deleno 4

📡 Volám LLM API...

🤖 LLM požaduje nástroj: calculate
   Argumenty: {
     "operation": "add",
     "a": 150,
     "b": 50
   }

🔧 Nástroj 'calculate' vykonaný: add(150, 50) = 200

📤 Posielam výsledok späť LLM: 200

📡 Volám LLM API s výsledkom nástroja...

🤖 LLM požaduje nástroj: calculate
   Argumenty: {
     "operation": "divide",
     "a": 200,
     "b": 4
   }

🔧 Nástroj 'calculate' vykonaný: divide(200, 4) = 50.0

📤 Posielam výsledok späť LLM: 50.0

📡 Volám LLM API s výsledkom nástroja...

💬 Finálna odpoveď LLM:
============================================================
(150 + 50) deleno 4 je 50.
============================================================
```

## Vysvetlenie procesu:

1. **Používateľ zadá otázku** - matematická úloha v prirodzenom jazyku

2. **LLM analyzuje** - rozpozná potrebu použiť nástroj `calculate`

3. **LLM vygeneruje tool call** - špecifikuje funkciu a parametre v JSON formáte

4. **Agent vykoná nástroj** - zavolá Python funkciu `calculate()` 

5. **Agent vráti výsledok** - pošle číslo späť LLM

6. **LLM vytvorí odpoveď** - sformuluje výsledok v prirodzenom jazyku

## Kľúčové komponenty:

- **Tool Definition** - popis nástroja v Gemini API formáte
- **Function Call Detection** - detekcia požiadavky na nástroj z LLM
- **Function Execution** - vykonanie Python funkcie
- **Result Forwarding** - odoslanie výsledku späť LLM
- **Response Generation** - finálna odpoveď v prirodzenom jazyku
