"""Sprawdzenie formatów PDF katalogów KNR"""
import pdfplumber
import os

folder = r'C:\Users\Gabriel\Desktop\knr_sources'
results = []

for f in sorted(os.listdir(folder)):
    if f.endswith('.pdf'):
        path = os.path.join(folder, f)
        try:
            pdf = pdfplumber.open(path)
            # Sprawdź kilka stron
            text_total = 0
            for i in range(min(3, len(pdf.pages))):
                text = pdf.pages[i].extract_text() or ''
                text_total += len(text)
            
            results.append({
                'file': f,
                'pages': len(pdf.pages),
                'text_len': text_total,
                'type': 'TEXT' if text_total > 300 else 'SCAN'
            })
            pdf.close()
        except Exception as e:
            results.append({
                'file': f,
                'pages': 0,
                'text_len': 0,
                'type': f'ERROR: {e}'
            })

print(f"{'Plik':<60} | {'Str':>4} | {'Znaki':>6} | Typ")
print("-" * 85)
for r in results:
    short_name = r['file'][:57] + '...' if len(r['file']) > 60 else r['file']
    print(f"{short_name:<60} | {r['pages']:>4} | {r['text_len']:>6} | {r['type']}")

scans = sum(1 for r in results if r['type'] == 'SCAN')
texts = sum(1 for r in results if r['type'] == 'TEXT')
print(f"\nPodsumowanie: {texts} z tekstem, {scans} skanów, {len(results)} razem")
