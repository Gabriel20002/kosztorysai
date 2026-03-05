"""Test szybkości KNR Matcher - tryb hybrydowy"""
from knr_matcher import KNRMatcher
import time

matcher = KNRMatcher(use_ai=True, use_embeddings=True)

tests = [
    {'opis': 'Wykopy jamiste o glebokosci do 1.5m ze skarpami', 'podstawa': 'KNR 2-01 0310-03'},
    {'opis': 'Sciany budynkow z cegiel pelnych grubosci 1 cegly', 'podstawa': ''},
    {'opis': 'Ocieplenie scian styropianem gr. 15cm', 'podstawa': ''},
    {'opis': 'Tynki wewnetrzne zwykle kat III', 'podstawa': ''},
    {'opis': 'Malowanie scian farba emulsyjna', 'podstawa': ''},
    {'opis': 'Posadzki betonowe gr 10cm zatarte na gladko', 'podstawa': ''},
    {'opis': 'Izolacje przeciwwilgociowe z papy', 'podstawa': ''},
    {'opis': 'Stolarka okienna PCV', 'podstawa': ''},
]

print('=== TEST HYBRYDOWY ===\n')
total_time = 0
ai_count = 0

for t in tests:
    start = time.time()
    r = matcher.match(t['opis'], t['podstawa'])
    elapsed = time.time() - start
    total_time += elapsed
    
    if 'ai' in r.source:
        ai_count += 1
    
    opis_short = t['opis'][:35].ljust(35)
    print(f"{opis_short} | {r.knr_code:20} | {r.confidence:.2f} | {r.source:15} | {elapsed:.1f}s")

print(f"\n=== PODSUMOWANIE ===")
print(f"Pozycji: {len(tests)}")
print(f"Czas: {total_time:.1f}s (avg: {total_time/len(tests):.1f}s)")
print(f"AI calls: {ai_count}/{len(tests)}")
