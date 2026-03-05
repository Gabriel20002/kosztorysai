# -*- coding: utf-8 -*-
import pdfplumber
import sys

pdf_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Gabriel\Downloads\przedmiar-zwanowice-remiza-2 (1).pdf'

with pdfplumber.open(pdf_path) as pdf:
    print(f'Stron: {len(pdf.pages)}')
    for i, page in enumerate(pdf.pages[:3], 1):
        text = page.extract_text() or ""
        tables = page.extract_tables()
        images = page.images
        chars = page.chars
        print(f'\nStrona {i}:')
        print(f'  Tekst: {len(text)} znakow')
        print(f'  Tabele: {len(tables)}')
        print(f'  Obrazy: {len(images)}')
        print(f'  Znaki (chars): {len(chars)}')
        if text:
            print(f'  Fragment: {text[:500]}')
        if tables:
            print(f'  Tabela 0: {tables[0][:2] if tables[0] else "pusta"}')
