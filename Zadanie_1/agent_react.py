"""
Minimálny AI agent s tool-callingom (ReAct)
Zadanie: Lekcia 1 - AI Agenti
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Načítanie environment premenných
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("❌ Chýba GEMINI_API_KEY v .env súbore")

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ============================================================
# NÁSTROJE (TOOLS)
# ============================================================

def calculate(operation: str, a: float, b: float) -> Dict[str, Any]:
    """
    Vykonáva základné matematické operácie.
    
    Args:
        operation: Typ operácie (add, subtract, multiply, divide)
        a: Prvé číslo
        b: Druhé číslo
        
    Returns:
        Dict s výsledkom alebo chybou
    """
    ops = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y,
    }
    
    if operation not in ops:
        return {"error": f"Neznáma operácia: {operation}"}
    
    if operation == "divide" and b == 0:
        return {"error": "Delenie nulou nie je možné"}
    
    try:
        result = ops[operation](a, b)
        return {"result": result, "operation": operation, "a": a, "b": b}
    except Exception as e:
        return {"error": str(e)}


# Mapovanie dostupných nástrojov
available_functions = {
    "calculate": calculate,
}


# Tool schema pre Gemini
calculate_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="calculate",
            description="Vykonáva základné matematické operácie (sčítanie, odčítanie, násobenie, delenie) nad dvoma číslami.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "operation": types.Schema(
                        type=types.Type.STRING,
                        enum=["add", "subtract", "multiply", "divide"],
                        description="Typ matematickej operácie",
                    ),
                    "a": types.Schema(
                        type=types.Type.NUMBER,
                        description="Prvé číslo"
                    ),
                    "b": types.Schema(
                        type=types.Type.NUMBER,
                        description="Druhé číslo"
                    ),
                },
                required=["operation", "a", "b"],
            ),
        )
    ]
)


# ============================================================
# REACT AGENT
# ============================================================

class GeminiReActAgent:
    """
    ReAct (Reason and Act) agent pre Gemini API.
    Podobný workflow ako Anthropic agent.
    """
    
    def __init__(self, model: str = MODEL, api_key: str = API_KEY):
        """
        Inicializácia agenta.
        
        Args:
            model: Názov Gemini modelu
            api_key: Gemini API kľúč
        """
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.max_iterations = 10
        self.tools = [calculate_tool]
    
    def run(
        self,
        user_message: str,
        system_prompt: str = "Si užitočný AI asistent. Keď potrebuješ vykonať výpočet, použi dostupné nástroje."
    ) -> str:
        """
        Spustí ReAct loop až kým nedostane finálnu odpoveď.
        
        Args:
            user_message: Používateľská otázka
            system_prompt: Systémový prompt (opcional)
            
        Returns:
            Finálna odpoveď od LLM
        """
        print(f"\n{'='*70}")
        print(f"🤖 GEMINI REACT AGENT")
        print(f"{'='*70}")
        print(f"\n👤 Používateľ: {user_message}\n")
        
        # História konverzácie (podobne ako v Anthropic)
        contents_history: List[types.Content] = []
        
        # Prvá user message
        initial_prompt = f"{system_prompt}\n\nOtázka: {user_message}"
        contents_history.append(
            types.Content(
                role="user",
                parts=[types.Part(text=initial_prompt)]
            )
        )
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            print(f"--- Iterácia {iteration} ---")
            
            # Volanie LLM
            print("📡 Volám Gemini API...")
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents_history,
                    config=types.GenerateContentConfig(
                        tools=self.tools,
                        temperature=0.0
                    )
                )
            except Exception as e:
                print(f"❌ Chyba pri volaní API: {e}")
                return f"Chyba: {str(e)}"
            
            # Kontrola odpovede
            if not response.candidates or not response.candidates[0].content.parts:
                print("⚠️ Prázdna odpoveď od LLM")
                return "Chyba: Prázdna odpoveď"
            
            parts = response.candidates[0].content.parts
            
            # Extrahovanie všetkých function calls (môže byť viac naraz!)
            function_calls = [
                p for p in parts 
                if hasattr(p, 'function_call') and p.function_call
            ]
            
            # Ak sú function calls, vykonaj ich
            if function_calls:
                print(f"🔧 Našiel som {len(function_calls)} tool call(s)")
                
                # Pridaj assistant odpoveď s function calls do histórie
                contents_history.append(response.candidates[0].content)
                
                # Vykonaj všetky tool calls a zbieraj výsledky
                tool_results_parts = []
                
                for fc_part in function_calls:
                    fc = fc_part.function_call
                    fn_name = fc.name
                    fn_args = dict(fc.args or {})
                    
                    print(f"\n🛠️  Vykonávam: {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")
                    
                    # Vykonaj funkciu
                    if fn_name in available_functions:
                        try:
                            function_to_call = available_functions[fn_name]
                            function_response = function_to_call(**fn_args)
                            print(f"   ✅ Výsledok: {json.dumps(function_response, ensure_ascii=False)}")
                        except Exception as e:
                            function_response = {"error": str(e)}
                            print(f"   ❌ Chyba: {e}")
                    else:
                        function_response = {"error": f"Neznámy nástroj: {fn_name}"}
                        print(f"   ❌ Neznámy nástroj: {fn_name}")
                    
                    # Vytvor function response part
                    tool_result_part = types.Part(
                        function_response=types.FunctionResponse(
                            name=fn_name,
                            response=function_response
                        )
                    )
                    tool_results_parts.append(tool_result_part)
                
                # Pridaj všetky tool results ako "user" message
                # (podobne ako Anthropic: tool results idú ako user content)
                contents_history.append(
                    types.Content(
                        role="user",
                        parts=tool_results_parts
                    )
                )
                
                print("")
                # Pokračuj na ďalšiu iteráciu
                continue
            
            # Ak nie sú function calls, skontroluj text odpoveď
            text_parts = [p for p in parts if hasattr(p, 'text') and p.text]
            
            if text_parts:
                final_text = "\n".join(p.text for p in text_parts)
                
                # Pridaj finálnu odpoveď do histórie
                contents_history.append(response.candidates[0].content)
                
                print(f"\n💬 Finálna odpoveď:")
                print(f"{'='*70}")
                print(final_text)
                print(f"{'='*70}\n")
                
                return final_text
            
            # Fallback
            print("⚠️ Neočakávaná odpoveď od LLM")
            return "Chyba: Neočakávaná odpoveď"
        
        # Ak sme dosiahli max iterácií
        error_msg = "⚠️ Dosiahnutý maximálny počet iterácií bez finálnej odpovede"
        print(error_msg)
        return error_msg


# ============================================================
# MAIN
# ============================================================

def main():
    """Hlavná funkcia s demo príkladmi"""
    
    # Vytvor agenta
    agent = GeminiReActAgent()
    
    # Príklad 1: Jednoduchý výpočet (single tool call)
    print("\n" + "="*70)
    print("PRÍKLAD 1: Jednoduchý výpočet")
    print("="*70)
    result1 = agent.run("Koľko je 25 krát 4?")
    
    # Príklad 2: Komplexný výpočet
    print("\n" + "="*70)
    print("PRÍKLAD 2: Komplexný výpočet")
    print("="*70)
    result2 = agent.run("Vypočítaj (150 + 50) deleno 4, potom výsledok vynásob 2")

if __name__ == "__main__":
    main()
