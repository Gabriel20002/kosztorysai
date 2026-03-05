import requests

prompt = """Ktora pozycja KNR najlepiej pasuje do opisu roboty budowlanej?

Opis: Wykopy jamiste glebokosci 1.5m

1. KNR 2-01 0525 - Darniowanie skarp
2. KNR 2-01 0124 - Reczne wykonanie rowkow
3. KNR 2-01 0530 - plantowanej skarpy
4. KNR 2-01 0220 - Reczne wyrownanie skarp wykopu
5. KNR 2-01 0518 - Zasypanie tluczniem

Odpowiedz TYLKO numerem (1-5) lub 0 jesli zadna nie pasuje."""

print("Prompt:", prompt[:100])
print("Wysylam...")

r = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'qwen3:8b',
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.1, 'num_predict': 150}
    },
    timeout=30
)

print(f"Status: {r.status_code}")
data = r.json()
resp = data.get('response', 'BRAK')
print(f"Response: '{resp}'")
print(f"Thinking: {data.get('thinking', 'brak')[:100] if data.get('thinking') else 'brak'}")
