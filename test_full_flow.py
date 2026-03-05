# -*- coding: utf-8 -*-
"""Test pełnego flow: parser v2 + KNR matcher z AI"""

import sys
import time
from test_parser_v2 import parse_przedmiar_v2
from knr_matcher import KNRMatcher

def test_full_flow(pdf_path, max_positions=10):
    """Test parsowania + matchowania KNR"""
    
    print("=" * 80)
    print("TEST: Parser v2 + KNR Matcher z AI")
    print("=" * 80)
    
    # 1. Parsuj przedmiar
    print("\n[1] Parsowanie przedmiaru...")
    start = time.time()
    positions = parse_przedmiar_v2(pdf_path)
    parse_time = time.time() - start
    print(f"    Znaleziono {len(positions)} pozycji w {parse_time:.2f}s")
    
    # 2. Inicjalizuj matcher
    print("\n[2] Inicjalizacja KNR Matcher...")
    matcher = KNRMatcher(use_ai=True, use_embeddings=True)
    
    # 3. Testuj matching dla pierwszych N pozycji
    print(f"\n[3] Matching dla {min(max_positions, len(positions))} pozycji...\n")
    print(f"{'Lp':>3} | {'KNR z przedmiaru':<20} | {'Dopasowany KNR':<25} | {'Conf':>5} | {'Metoda':<10}")
    print("-" * 95)
    
    total_time = 0
    matched = 0
    for pos in positions[:max_positions]:
        start = time.time()
        result = matcher.match(pos['opis'], pos['knr'])
        elapsed = time.time() - start
        total_time += elapsed
        
        if result.confidence >= 0.5:
            matched += 1
            status = "OK"
        else:
            status = "--"
        
        print(f"{pos['lp']:3} | {pos['knr']:<20} | {result.knr_code:<25} | {result.confidence:5.2f} | {result.source:<10} {status}")
    
    print("-" * 95)
    print(f"Dopasowano: {matched}/{min(max_positions, len(positions))} ({100*matched/min(max_positions, len(positions)):.0f}%)")
    print(f"Średni czas: {total_time/min(max_positions, len(positions)):.2f}s/pozycję")
    print(f"Łączny czas matchingu: {total_time:.1f}s")


if __name__ == '__main__':
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Gabriel\Downloads\06. Zał. nr 2 do SWZ - Przedmiar robót.pdf'
    max_pos = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    test_full_flow(pdf_path, max_pos)
