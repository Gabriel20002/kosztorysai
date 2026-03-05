import requests
r = requests.post('http://localhost:11434/api/generate', 
    json={'model':'qwen3:8b','prompt':'Powiedz tylko: TAK','stream':False}, 
    timeout=30)
data = r.json()
resp = data.get('response', 'BRAK')
# Bezpieczne wyświetlenie
print(f"Status: {r.status_code}")
print(f"Response length: {len(resp)}")
print(f"First 100 chars: {resp[:100].encode('ascii', 'replace').decode()}")
