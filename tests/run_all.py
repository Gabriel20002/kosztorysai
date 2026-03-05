# -*- coding: utf-8 -*-
"""
Runner dla wszystkich testów kosztorysAI

Uruchomienie:
    cd kosztorysAI
    python tests/run_all.py
"""

import sys
import os

# Dodaj katalog nadrzędny do path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def run_all_tests():
    """Uruchamia wszystkie testy"""
    print("=" * 60)
    print("TESTY KOSZTORYSAI")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    # Lista modułów testowych
    test_modules = [
        ('TextFixer', 'test_text_fixer'),
        ('PDF Parser', 'test_pdf_parser'),
        ('ATH Generator', 'test_ath_generator'),
    ]
    
    for name, module_name in test_modules:
        print(f"\n{'='*60}")
        print(f"Modul: {name}")
        print(f"{'='*60}")
        
        try:
            module = __import__(module_name)
            if hasattr(module, 'run_tests'):
                success = module.run_tests()
                if success:
                    total_passed += 1
                else:
                    total_failed += 1
            else:
                print(f"  [!] Brak funkcji run_tests w {module_name}")
                total_failed += 1
        except Exception as e:
            print(f"  [ERROR] Nie mozna zaladowac {module_name}: {e}")
            total_failed += 1
    
    # Podsumowanie
    print(f"\n{'='*60}")
    print("PODSUMOWANIE")
    print(f"{'='*60}")
    print(f"Moduly OK: {total_passed}")
    print(f"Moduly FAIL: {total_failed}")
    
    if total_failed == 0:
        print("\n[OK] Wszystkie testy przeszly!")
        return True
    else:
        print(f"\n[!] {total_failed} modul(ow) ma bledy!")
        return False


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    success = run_all_tests()
    sys.exit(0 if success else 1)
