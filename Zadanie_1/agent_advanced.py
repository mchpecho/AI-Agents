"""
Rozšírený AI Agent s viacerými nástrojmi
Demonštruje pokročilé použitie tool-callingu
"""

import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv
from google import genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ===== NÁSTROJE =====

def calculate(operation: str, a: float, b: float) -> float:
    """Matematické operácie"""
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Chyba: delenie nulou"
    }
    result = operations.get(operation, lambda x, y: "Neznáma operácia")(a, b)
    print(f"🔧 calculate({operation}, {a}, {b}) = {result}")
    return result


def get_current_time(timezone: str = "UTC") -> str:
    """Vráti aktuálny čas"""
    current_time = datetime.now().strftime("%H:%M:%S")
    current_date = datetime.now().strftime("%Y-%m-%d")
    result = f"{current_date} {current_time} ({timezone})"
    print(f"🔧 get_current_time({timezone}) = {result}")
    return result


def roll_dice(num_dice: int = 1, num_sides: int = 6) -> dict:
    """Hodí kockami"""
    rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(rolls)
    result = {"rolls": rolls, "total": total}
    print(f"🔧 roll_dice({num_dice}d{num_sides}) = {rolls} (suma: {total})")
    return result


def get_weather(city: str) -> dict:
    """Simulovaná predpoveď počasia"""
    # V reálnej aplikácii by sa volalo Weather API
    weather_conditions = ["slnečno", "zamračené", "dážď", "sneh", "hmla"]
    result = {
        "city": city,
        "temperature": random.randint(-5, 30),
        "condition": random.choice(weather_conditions),
        "humidity": random.randint(30, 90)
    }
    print(f"🔧 get_weather({city}) = {result}")
    return result


# ===== DEFINÍCIE NÁSTROJOV PRE GEMINI =====

tools = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="calculate",
            description="Vykonáva matematické operácie",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "operation": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        enum=["add", "subtract", "multiply", "divide"]
                    ),
                    "a": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                    "b": genai.protos.Schema(type=genai.protos.Type.NUMBER)
                },
                required=["operation", "a", "b"]
            )
        ),
        genai.protos.FunctionDeclaration(
            name="get_current_time",
            description="Vráti aktuálny dátum a čas",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "timezone": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="Časové pásmo (default: UTC)"
                    )
                }
            )
        ),
        genai.protos.FunctionDeclaration(
            name="roll_dice",
            description="Hodí kockami a vráti výsledky",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "num_dice": genai.protos.Schema(
                        type=genai.protos.Type.INTEGER,
                        description="Počet kociek (default: 1)"
                    ),
                    "num_sides": genai.protos.Schema(
                        type=genai.protos.Type.INTEGER,
                        description="Počet strán kocky (default: 6)"
                    )
                }
            )
        ),
        genai.protos.FunctionDeclaration(
            name="get_weather",
            description="Získa informácie o počasí pre dané mesto",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "city": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="Názov mesta"
                    )
                },
                required=["city"]
            )
        )
    ]
)


# Mapovanie názvov funkcií na reálne funkcie
AVAILABLE_FUNCTIONS = {
    "calculate": calculate,
    "get_current_time": get_current_time,
    "roll_dice": roll_dice,
    "get_weather": get_weather
}


def run_advanced_agent(user_prompt: str):
    """Pokročilý AI agent s viacerými nástrojmi"""
    print(f"\n{'='*70}")
    print(f"🤖 POKROČILÝ AI AGENT - Multi-Tool Demo")
    print(f"{'='*70}")
    print(f"\n👤 Používateľ: {user_prompt}\n")
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=[tools]
    )
    
    chat = model.start_chat(enable_automatic_function_calling=False)
    
    print("📡 Volám LLM API...\n")
    response = chat.send_message(user_prompt)
    
    iteration = 0
    max_iterations = 10  # Ochrana pred nekonečnou slučkou
    
    while iteration < max_iterations:
        iteration += 1
        
        if not response.candidates[0].content.parts:
            break
            
        part = response.candidates[0].content.parts[0]
        
        # Tool call
        if hasattr(part, 'function_call') and part.function_call:
            function_call = part.function_call
            function_name = function_call.name
            function_args = dict(function_call.args)
            
            print(f"🤖 LLM požaduje nástroj #{iteration}: {function_name}")
            print(f"   Argumenty: {json.dumps(function_args, indent=2, ensure_ascii=False)}\n")
            
            # Vykonanie nástroja
            if function_name in AVAILABLE_FUNCTIONS:
                try:
                    result = AVAILABLE_FUNCTIONS[function_name](**function_args)
                except Exception as e:
                    result = f"Chyba: {str(e)}"
            else:
                result = f"Chyba: neznámy nástroj '{function_name}'"
            
            print(f"\n📤 Posielam výsledok späť LLM\n")
            
            # Vytvorenie function response
            function_response = genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=function_name,
                    response={"result": result}
                )
            )
            
            # Ďalšie volanie LLM
            print("📡 Volám LLM API s výsledkom...\n")
            response = chat.send_message(function_response)
        
        # Textová odpoveď
        elif hasattr(part, 'text') and part.text:
            print(f"💬 Finálna odpoveď LLM:")
            print(f"{'='*70}")
            print(f"{part.text}")
            print(f"{'='*70}\n")
            break
        
        else:
            break
    
    if iteration >= max_iterations:
        print("⚠️  Dosiahnutý maximálny počet iterácií")


def main():
    """Hlavná funkcia s rôznymi príkladmi"""
    
    examples = [
        "Koľko je 15 plus 25?",
        "Aký je teraz čas?",
        "Hoď tromi kockami",
        "Aké je počasie v Bratislave?",
        "Vypočítaj 100 deleno 5, potom výsledok vynásob 3, a hoď toľkými kockami",
    ]
    
    print("\n" + "="*70)
    print("🎯 DEMO: Rozšírený AI Agent s viacerými nástrojmi")
    print("="*70)
    print("\nDostupné nástroje:")
    print("  • calculate - matematické operácie")
    print("  • get_current_time - aktuálny čas")
    print("  • roll_dice - hádzanie kockami")
    print("  • get_weather - predpoveď počasia (simulovaná)")
    print()
    
    # Spusť všetky príklady
    for i, example in enumerate(examples, 1):
        print(f"\n{'#'*70}")
        print(f"# Príklad {i}/{len(examples)}")
        print(f"{'#'*70}")
        run_advanced_agent(example)
        
        if i < len(examples):
            input("Stlač Enter pre ďalší príklad...")


if __name__ == "__main__":
    main()
