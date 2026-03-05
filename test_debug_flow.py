"""Debug flow matchera"""
from knr_matcher import KNRMatcher

matcher = KNRMatcher(use_ai=True, use_embeddings=True)

test = {'opis': 'Wykopy jamiste o glebokosci do 1.5m ze skarpami', 'podstawa': ''}

# 1. Znajdz kandydatow
candidates = matcher.find_candidates(test['opis'], test['podstawa'])
print(f"Kandydatow: {len(candidates)}")

for i, c in enumerate(candidates[:5]):
    print(f"  {i+1}. {c['position']['code']} | dist: {c['distance']:.3f} | src: {c['source']}")
    print(f"     {c['position']['description'][:60]}")

# 2. Sprawdz czy AI sie wywola
if candidates:
    top_dist = candidates[0]['distance']
    print(f"\nTop distance: {top_dist:.3f}")
    print(f"Czy embedding-high? {top_dist < 0.2}")
    print(f"Czy AI? {top_dist >= 0.2}")
