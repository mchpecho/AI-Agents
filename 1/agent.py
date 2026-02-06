"""
Minimálny AI agent s tool-callingom
Zadanie: Lekcia 1 - AI Agenti
"""

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Načítanie environment premenných
load_dotenv()

# Konfigurácia Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY nie je nastavený v .env súbore")

# Inicializácia klienta
client = genai.Client(api_key=GEMINI_API_KEY)


def calculate(operation: str, a: float, b: float) -> float:
    """
    Výpočetná funkcia - nástroj pre AI agenta.
    
    Args:
        operation: Typ operácie (add, subtract, multiply, divide)
        a: Prvé číslo
        b: Druhé číslo
        
    Returns:
        Výsledok výpočtu
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Chyba: delenie nulou"
    }
    
    if operation not in operations:
        return f"Chyba: neznáma operácia '{operation}'"
    
    result = operations[operation](a, b)
    print(f"🔧 Nástroj 'calculate' vykonaný: {operation}({a}, {b}) = {result}")
    return result


# Definícia nástroja pre nové Gemini API
calculate_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="calculate",
            description="Vykonáva základné matematické operácie (sčítanie, odčítanie, násobenie, delenie)",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "operation": types.Schema(
                        type=types.Type.STRING,
                        description="Typ operácie: 'add', 'subtract', 'multiply', alebo 'divide'",
                        enum=["add", "subtract", "multiply", "divide"]
                    ),
                    "a": types.Schema(
                        type=types.Type.NUMBER,
                        description="Prvé číslo"
                    ),
                    "b": types.Schema(
                        type=types.Type.NUMBER,
                        description="Druhé číslo"
                    )
                },
                required=["operation", "a", "b"]
            )
        )
    ]
)


def run_agent(user_prompt: str):
    """
    Hlavná funkcia AI agenta s tool-callingom.
    
    Args:
        user_prompt: Otázka/príkaz od používateľa
    """
    print(f"\n{'='*60}")
    print(f"🤖 AI AGENT - Tool Calling Demo")
    print(f"{'='*60}")
    print(f"\n👤 Používateľ: {user_prompt}\n")
    
    # Prvé volanie LLM
    print("📡 Volám LLM API...\n")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # Aktuálny dostupný model
            contents=user_prompt,
            config=types.GenerateContentConfig(
                tools=[calculate_tool],
                temperature=0.0
            )
        )
        
        # Spracovanie odpovede
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Kontrola function calls
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Ak je to function call
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        function_name = function_call.name
                        function_args = dict(function_call.args)
                        
                        print(f"🤖 LLM požaduje nástroj: {function_name}")
                        print(f"   Argumenty: {json.dumps(function_args, indent=2, ensure_ascii=False)}\n")
                        
                        # Vykonanie nástroja
                        if function_name == "calculate":
                            result = calculate(
                                operation=function_args["operation"],
                                a=function_args["a"],
                                b=function_args["b"]
                            )
                        else:
                            result = f"Chyba: neznámy nástroj '{function_name}'"
                        
                        # Poslanie výsledku späť LLM
                        print(f"\n📤 Posielam výsledok späť LLM: {result}\n")
                        print("📡 Volám LLM API s výsledkom nástroja...\n")
                        
                        # Vytvorenie function response a pokračovanie konverzácie
                        function_response = types.Part(
                            function_response=types.FunctionResponse(
                                name=function_name,
                                response={"result": result}
                            )
                        )
                        
                        # Ďalšie volanie s výsledkom
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[
                                types.Content(role="user", parts=[types.Part(text=user_prompt)]),
                                response.candidates[0].content,
                                types.Content(role="user", parts=[function_response])
                            ],
                            config=types.GenerateContentConfig(
                                tools=[calculate_tool],
                                temperature=0.0
                            )
                        )
                    
                    # Ak je to textová odpoveď
                    elif hasattr(part, 'text') and part.text:
                        print(f"💬 Finálna odpoveď LLM:")
                        print(f"{'='*60}")
                        print(f"{part.text}")
                        print(f"{'='*60}\n")
                        return
            else:
                break
        
        if iteration >= max_iterations:
            print("⚠️  Dosiahnutý maximálny počet iterácií")
            
    except Exception as e:
        print(f"❌ Chyba pri volaní API: {e}")
        print("\n💡 Tipy na riešenie:")
        print("1. Skontrolujte API kľúč v .env súbore")
        print("2. Overte internetové pripojenie")
        print("3. Spustite skript list_models pre zobrazenie dostupných modelov")


def main():
    """Hlavná funkcia s demo príkladmi"""
    
    # Príklad 1: Jednoduchý výpočet
    run_agent("Koľko je 25 krát 4?")
    
    # Príklad 2: Zložitejší výpočet
    run_agent("Vypočítaj (150 + 50) deleno 4")
    


if __name__ == "__main__":
    main()
