# -*- coding: utf-8 -*-
import json

data = json.load(open('learned_kosztorysy/naklady_rms.json','r',encoding='utf-8'))

# Szukaj KNR 4-01
knr401 = [n for n in data if 'KNR 4-01' in n.get('knr','').upper() or 'KNR4-01' in n.get('knr','').upper()]
print(f'KNR 4-01 w bazie: {len(knr401)}')
for n in knr401[:10]:
    knr = n.get('knr','')
    r = n.get('R',0)
    m = n.get('M',0)
    opis = n.get('opis','')[:60]
    print(f"  {knr}: R={r:.2f}, M={m:.2f} - {opis}")

# Sprawdź konkretny: KNR 4-01 0354-03
exact = [n for n in data if '0354-03' in n.get('knr','')]
print(f'\nKNR 4-01 0354-03: {len(exact)}')
if exact:
    for e in exact:
        print(f"  {e}")

# Sprawdź jakie katalogi mamy
catalogs = set()
for n in data:
    knr = n.get('knr', '')
    # Wyciągnij katalog (np. KNR 4-01)
    import re
    m = re.match(r'(K[NS]?N?R(?:-[A-Z])?\s*[\d]+-[\d]+)', knr, re.I)
    if m:
        catalogs.add(m.group(1).upper())

print(f'\nKatalogi w bazie ({len(catalogs)}):')
for c in sorted(catalogs):
    count = len([n for n in data if c in n.get('knr','').upper()])
    print(f"  {c}: {count} pozycji")
