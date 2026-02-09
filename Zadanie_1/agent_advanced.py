"""
Rozšírený AI Agent s viacerými nástrojmi (viac RPM - potrebné platené API)
Demonštruje pokročilé použitie tool-callingu
"""

import os
import random
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("❌ Chýba GEMINI_API_KEY v .env súbore")

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY)

# ============================================================
# NÁSTROJE
# ============================================================

def calculate(operation: str, a: float, b: float) -> float:
    ops = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y,
    }
    if operation not in ops:
        raise ValueError(f"Neznáma operácia: {operation}")
    if operation == "divide" and b == 0:
        raise ZeroDivisionError("Delenie nulou")
    result = ops[operation](a, b)
    print(f"🔧 calculate({operation}, {a}, {b}) = {result}")
    return result

def get_current_time(timezone: str = "UTC") -> str:
    # Pozn.: timezone tu len “echo-ujeme”, pre demo stačí.
    now = datetime.now()
    result = f"{now:%Y-%m-%d %H:%M:%S} ({timezone})"
    print(f"🔧 get_current_time({timezone}) = {result}")
    return result

def roll_dice(num_dice: int = 1, num_sides: int = 6) -> dict:
    if num_dice < 1 or num_sides < 2:
        raise ValueError("num_dice >= 1, num_sides >= 2")
    rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(rolls)
    result = {"rolls": rolls, "total": total}
    print(f"🔧 roll_dice({num_dice}d{num_sides}) = {result}")
    return result

AVAILABLE_FUNCTIONS = {
    "calculate": calculate,
    "get_current_time": get_current_time,
    "roll_dice": roll_dice,
}

# ===== DEFINÍCIE NÁSTROJOV PRE GEMINI (types.*) =====

tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="calculate",
            description="Základné matematické operácie nad dvoma číslami.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["operation", "a", "b"],
            },
        ),
        types.FunctionDeclaration(
            name="get_current_time",
            description="Vráti aktuálny dátum a čas.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Časové pásmo (default: UTC)"},
                },
            },
        ),
        types.FunctionDeclaration(
            name="roll_dice",
            description="Hodí kockami a vráti hody aj súčet.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "num_dice": {"type": "integer", "description": "Počet kociek (default: 1)"},
                    "num_sides": {"type": "integer", "description": "Počet strán (default: 6)"},
                },
            },
        ),
    ]
)

cfg = types.GenerateContentConfig(tools=[tools], temperature=0.0)


def run_advanced_agent(user_prompt: str) -> None:
    prompt = (
        "Používaj nástroje keď to pomôže. "
        "Pri viac-krokových úlohách volaj nástroje opakovane. "
        f"Otázka: {user_prompt}"
    )

    history = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    for _ in range(10):
        resp = client.models.generate_content(model=MODEL, contents=history, config=cfg)

        if not resp.candidates:
            print(resp.text or "")
            return

        content = resp.candidates[0].content
        parts = content.parts or []
        history.append(content)

        # nájdi function_call (ak existuje)
        fc_part = next((p for p in parts if getattr(p, "function_call", None)), None)
        if fc_part:
            fc = fc_part.function_call
            name = fc.name
            args = dict(fc.args or {})

            print(f"🤖 Tool call: {name} args={args}")

            fn = AVAILABLE_FUNCTIONS.get(name)
            if not fn:
                tool_payload = {"error": f"Neznámy nástroj: {name}"}
            else:
                try:
                    result = fn(**args)
                    tool_payload = {"result": result}
                except Exception as e:
                    tool_payload = {"error": str(e)}

            tool_part = types.Part.from_function_response(name=name, response=tool_payload)
            history.append(types.Content(role="tool", parts=[tool_part]))
            continue

        # inak je to text
        text = resp.text
        if text:
            print(text)
        else:
            # fallback: vypíš čo sa dá
            for p in parts:
                if getattr(p, "text", None):
                    print(p.text)
        return

    print("⚠️ Dosiahnutý max počet iterácií.")

# ============================================================
# MAIN
# ============================================================

def main():
    examples = [
        "Koľko je 15 plus 25?",
        "Aký je teraz čas?",
        "Hoď tromi kockami",
    ]
    for ex in examples:
        print("\n" + "=" * 70)
        print("👤", ex)
        run_advanced_agent(ex)


if __name__ == "__main__":
    main()