"""
Minimálny AI agent s tool-callingom (ReAct pattern)
Zadanie: Lekcia 1 - AI Agenti
"""

import os
import json
from typing import Dict, Any, Callable
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Validácia konfigurácie
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("❌ Chýba GEMINI_API_KEY v .env súbore")

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ============================================================
# NÁSTROJE
# ============================================================

def calculate(operation: str, a: float, b: float) -> Dict[str, Any]:
    """Vykonáva základné matematické operácie s error handlingom."""
    
    ops: Dict[str, Callable[[float, float], float]] = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y,
    }
    
    # Validácia vstupov
    if operation not in ops:
        return {"error": f"Neznáma operácia: {operation}"}
    if operation == "divide" and b == 0:
        return {"error": "Delenie nulou nie je možné"}
    
    try:
        result = ops[operation](a, b)
        return {"result": result, "operation": operation, "a": a, "b": b}
    except Exception as e:
        return {"error": str(e)}


# Registry dostupných funkcií a ich schém
AVAILABLE_FUNCTIONS: Dict[str, Callable] = {"calculate": calculate}

TOOLS = [
    types.Tool(
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
                        "a": types.Schema(type=types.Type.NUMBER, description="Prvé číslo"),
                        "b": types.Schema(type=types.Type.NUMBER, description="Druhé číslo"),
                    },
                    required=["operation", "a", "b"],
                ),
            )
        ]
    )
]


# ============================================================
# REACT AGENT
# ============================================================

class GeminiReActAgent:
    """ReAct (Reason and Act) agent pre Gemini API."""
    
    def __init__(self, model: str = MODEL, api_key: str = API_KEY, max_iterations: int = 10):
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.max_iterations = max_iterations
        self.tools = TOOLS
    
    def _execute_tool_call(self, fn_name: str, fn_args: Dict[str, Any]) -> Dict[str, Any]:
        """Vykoná jeden tool call s error handlingom."""
        print(f"\n🛠️  Vykonávam: {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")
        
        if fn_name not in AVAILABLE_FUNCTIONS:
            result = {"error": f"Neznámy nástroj: {fn_name}"}
            print(f"   ❌ {result['error']}")
            return result
        
        try:
            result = AVAILABLE_FUNCTIONS[fn_name](**fn_args)
            print(f"   ✅ Výsledok: {json.dumps(result, ensure_ascii=False)}")
            return result
        except Exception as e:
            result = {"error": str(e)}
            print(f"   ❌ Chyba: {e}")
            return result
    
    def _process_function_calls(self, parts: list) -> list[types.Part]:
        """Spracuje všetky function calls z odpovede a vráti results."""
        function_calls = [p for p in parts if hasattr(p, 'function_call') and p.function_call]
        
        if not function_calls:
            return []
        
        print(f"🔧 Našiel som {len(function_calls)} tool call(s)")
        
        # Vykonaj všetky tool calls paralelne (v budúcnosti môže byť async)
        tool_results = []
        for fc_part in function_calls:
            fc = fc_part.function_call
            result = self._execute_tool_call(fc.name, dict(fc.args or {}))
            
            tool_results.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response=result
                    )
                )
            )
        
        return tool_results
    
    def _call_llm(self, contents: list[types.Content]) -> Any:
        """Wrapper pre LLM call s error handlingom."""
        try:
            return self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(tools=self.tools, temperature=0.0)
            )
        except Exception as e:
            print(f"❌ Chyba pri volaní API: {e}")
            raise
    
    def run(self, user_message: str, system_prompt: str = "Si užitočný AI asistent. Keď potrebuješ vykonať výpočet, použi dostupné nástroje.") -> str:
        """Spustí ReAct loop až kým nedostane finálnu odpoveď."""
        
        print(f"\n{'='*70}\n🤖 GEMINI REACT AGENT\n{'='*70}\n")
        print(f"👤 Používateľ: {user_message}\n")
        
        # Inicializácia histórie s prvou user message
        contents_history = [
            types.Content(
                role="user",
                parts=[types.Part(text=f"{system_prompt}\n\nOtázka: {user_message}")]
            )
        ]
        
        # ReAct loop
        for iteration in range(1, self.max_iterations + 1):
            print(f"--- Iterácia {iteration} ---")
            print("📡 Volám Gemini API...")
            
            try:
                response = self._call_llm(contents_history)
            except Exception as e:
                return f"Chyba: {str(e)}"
            
            # Validácia odpovede
            if not response.candidates or not response.candidates[0].content.parts:
                print("⚠️ Prázdna odpoveď od LLM")
                return "Chyba: Prázdna odpoveď"
            
            parts = response.candidates[0].content.parts
            
            # Spracovanie function calls (ak existujú)
            tool_results = self._process_function_calls(parts)
            
            if tool_results:
                # Pridaj assistant odpoveď a tool results do histórie
                contents_history.extend([
                    response.candidates[0].content,
                    types.Content(role="user", parts=tool_results)
                ])
                print("")
                continue
            
            # Žiadne function calls - hľadaj finálnu textovú odpoveď
            final_text = "\n".join(p.text for p in parts if hasattr(p, 'text') and p.text)
            
            if final_text:
                contents_history.append(response.candidates[0].content)
                print(f"\n💬 Finálna odpoveď:\n{'='*70}\n{final_text}\n{'='*70}\n")
                return final_text
            
            # Fallback pri neočakávanej odpovedi
            print("⚠️ Neočakávaná odpoveď od LLM")
            return "Chyba: Neočakávaná odpoveď"
        
        # Max iterácií dosiahnutých
        error_msg = "⚠️ Dosiahnutý maximálny počet iterácií bez finálnej odpovede"
        print(error_msg)
        return error_msg


# ============================================================
# MAIN
# ============================================================

def main():
    """Demo príklady použitia agenta."""
    agent = GeminiReActAgent()
    
    examples = [
        ("PRÍKLAD 1: Jednoduchý výpočet", "Koľko je 25 krát 4?"),
        ("PRÍKLAD 2: Komplexný výpočet", "Vypočítaj (150 + 50) deleno 4, potom výsledok vynásob 2"),
    ]
    
    for title, query in examples:
        print(f"\n{'='*70}\n{title}\n{'='*70}")
        agent.run(query)


if __name__ == "__main__":
    main()
