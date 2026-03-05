# -*- coding: utf-8 -*-
import json

data = json.load(open('learned_kosztorysy/naklady_rms.json','r',encoding='utf-8'))

# Szukaj konkretnych pozycji
to_find = ['0430-10', '0411-08', '1017-02', '0511-13', '0307-02']
for f in to_find:
    matches = [n for n in data if f in n.get('knr','')]
    print(f'=== {f} ===')
    for m in matches:
        knr = m.get('knr','')
        r = m.get('R', 0)
        mval = m.get('M', 0)
        s = m.get('S', 0)
        opis = m.get('opis', '')[:80]
        print(f"  {knr}: R={r}, M={mval}, S={s}")
        print(f"    {opis}")
    print()
