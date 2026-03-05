# -*- coding: utf-8 -*-
"""
Łączy starą i nową bazę nakładów
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).parent / "learned_kosztorysy"

# Załaduj obie bazy
old = json.load(open(BASE / 'naklady_rms.json', 'r', encoding='utf-8'))
new = json.load(open(BASE / 'naklady_extracted.json', 'r', encoding='utf-8'))

print(f'Stara baza: {len(old)} pozycji')
print(f'Nowa baza: {len(new)} pozycji')

# Normalizuj i połącz
def norm_knr(knr):
    return knr.upper().replace(' ', '')

knr_dict = {}

# Najpierw stara (ma pełne nakłady R/M/S)
for p in old:
    knr = norm_knr(p.get('knr', ''))
    if knr:
        knr_dict[knr] = p

# Dodaj nowe (tylko jeśli nie ma w starej lub ma lepsze dane)
added = 0
updated = 0
for p in new:
    knr = norm_knr(p.get('knr', ''))
    if not knr:
        continue
    
    existing = knr_dict.get(knr)
    if not existing:
        knr_dict[knr] = p
        added += 1
    else:
        # Porównaj - zachowaj ten z większymi danymi
        new_sum = p.get('R', 0) + p.get('M', 0) + p.get('S', 0)
        old_sum = existing.get('R', 0) + existing.get('M', 0) + existing.get('S', 0)
        if new_sum > old_sum:
            knr_dict[knr] = p
            updated += 1

merged = list(knr_dict.values())

print(f'\nPołączona baza: {len(merged)} pozycji')
print(f'  Dodano nowych: {added}')
print(f'  Zaktualizowano: {updated}')

# Zapisz
output = BASE / 'naklady_merged.json'
json.dump(merged, open(output, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'\nZapisano do: {output}')

# Statystyki katalogów
catalogs = {}
for n in merged:
    knr = n.get('knr', '')
    match = re.match(r'(K[NS]?N?R(?:-[A-Z])?\s*[\d]+(?:-[\d]+)?)', knr, re.I)
    if match:
        cat = match.group(1).upper()
        catalogs[cat] = catalogs.get(cat, 0) + 1

print(f'\nKatalogi ({len(catalogs)}):')
for cat, count in sorted(catalogs.items(), key=lambda x: -x[1])[:15]:
    print(f'  {cat}: {count}')
