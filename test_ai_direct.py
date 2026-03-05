"""Test bezpośredniego wywołania AI"""
import requests
import json
import re

prompt = """Ktora pozycja KNR najlepiej pasuje do opisu?

Opis: Wykopy jamiste glebokosci 1.5m ze skarpami gruncie kat III

1. KNR 2-01 0301 - wyrowywanie skarp
2. KNR 2-01 0310 - wykopy jamiste ze skarpami
3. KNR 2-01 0320 - wykopy liniowe

Odpowiedz jednym slowem: 1, 2 lub 3"""

print("Wysylam do Ollama...")
response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'qwen3:8b', 
        'prompt': prompt, 
        'stream': False, 
        'options': {'temperature': 0.3, 'num_predict': 300}
    },
    timeout=30
)

print(f"Status: {response.status_code}")
result = response.json()
response_text = result.get('response', '')
print(f"Response: {response_text}")

# Parsuj JSON
json_match = re.search(r'\{[^}]+\}', response_text)
if json_match:
    try:
        ai_result = json.loads(json_match.group())
        print(f"Parsed: {ai_result}")
    except:
        print("JSON parse failed")
else:
    print("No JSON found")
