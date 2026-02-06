"""
AI Agent s Ollama (lokálny LLM) - alternatívne riešenie
Poznámka: Vyžaduje nainštalovaný Ollama a stiahnutý model
"""

import json
import requests
from typing import Any

OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"  # alebo iný model, ktorý máte stiahnutý


def calculate(operation: str, a: float, b: float) -> float:
    """
    Výpočetná funkcia - nástroj pre AI agenta.
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


# Definícia nástroja pre Ollama
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Vykonáva základné matematické operácie",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Typ operácie: add, subtract, multiply, divide",
                        "enum": ["add", "subtract", "multiply", "divide"]
                    },
                    "a": {
                        "type": "number",
                        "description": "Prvé číslo"
                    },
                    "b": {
                        "type": "number",
                        "description": "Druhé číslo"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        }
    }
]


def call_ollama(messages: list, tools: list = None) -> dict:
    """Zavolá Ollama API"""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }
    
    if tools:
        payload["tools"] = tools
    
    response = requests.post(OLLAMA_API_URL, json=payload)
    return response.json()


def run_agent_ollama(user_prompt: str):
    """
    AI agent s Ollama (lokálny LLM)
    """
    print(f"\n{'='*60}")
    print(f"🤖 AI AGENT - Ollama Tool Calling")
    print(f"{'='*60}")
    print(f"\n👤 Používateľ: {user_prompt}\n")
    
    messages = [
        {"role": "user", "content": user_prompt}
    ]
    
    # Prvé volanie LLM
    print("📡 Volám Ollama API...\n")
    response = call_ollama(messages, tools)
    
    # Kontrola tool calls
    message = response.get("message", {})
    
    if "tool_calls" in message:
        for tool_call in message["tool_calls"]:
            function = tool_call.get("function", {})
            function_name = function.get("name")
            function_args = function.get("arguments", {})
            
            print(f"🤖 LLM požaduje nástroj: {function_name}")
            print(f"   Argumenty: {json.dumps(function_args, indent=2, ensure_ascii=False)}\n")
            
            # Vykonanie nástroja
            if function_name == "calculate":
                result = calculate(
                    operation=function_args["operation"],
                    a=function_args["a"],
                    b=function_args["b"]
                )
            
            # Pridanie tool response do messages
            messages.append(message)
            messages.append({
                "role": "tool",
                "content": str(result)
            })
            
            # Druhé volanie LLM s výsledkom
            print(f"\n📤 Posielam výsledok späť LLM: {result}\n")
            print("📡 Volám Ollama API s výsledkom nástroja...\n")
            response = call_ollama(messages)
            message = response.get("message", {})
    
    # Finálna odpoveď
    final_text = message.get("content", "")
    print(f"💬 Finálna odpoveď LLM:")
    print(f"{'='*60}")
    print(f"{final_text}")
    print(f"{'='*60}\n")


def main():
    """Hlavná funkcia"""
    print("\n⚠️  POZNÁMKA: Tento skript vyžaduje:")
    print("   1. Nainštalovaný Ollama (https://ollama.ai)")
    print("   2. Stiahnutý model: ollama pull llama3.2")
    print("   3. Bežiaci Ollama server: ollama serve\n")
    
    try:
        run_agent_ollama("Koľko je 25 krát 4?")
    except requests.exceptions.ConnectionError:
        print("❌ Chyba: Nemôžem sa pripojiť k Ollama.")
        print("   Uistite sa, že Ollama server beží (ollama serve)")


if __name__ == "__main__":
    main()
