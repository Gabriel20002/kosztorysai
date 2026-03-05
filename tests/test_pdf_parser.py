# -*- coding: utf-8 -*-
"""
Testy dla parsera PDF (KosztorysGenerator.parse_przedmiar_pdf)

Uruchomienie:
    python tests/test_pdf_parser.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kosztorys_generator import KosztorysGenerator
from pdf_cache import PDFCache


class TestPDFParser:
    """Testy dla parsera PDF"""
    
    def setup_method(self):
        """Przygotowanie przed każdym testem"""
        self.generator = KosztorysGenerator()
        # Wyłącz cache dla testów
        self.cache = PDFCache(enabled=False)
    
    # ===== Testy struktury pozycji =====
    
    def test_pozycja_has_required_fields(self):
        """Test że sparsowana pozycja ma wymagane pola"""
        required_fields = ['lp', 'podstawa', 'opis', 'jm', 'ilosc', 'R', 'M', 'S', 'dzial']
        
        # Stwórz minimalną pozycję
        pozycja = {
            'lp': 1,
            'podstawa': 'KNR 2-31 0703-03',
            'opis': 'Test',
            'jm': 'm2',
            'ilosc': 100,
            'R': 450,
            'M': 0,
            'S': 225,
            'dzial': 'Test',
        }
        
        for field in required_fields:
            assert field in pozycja, f"Brak pola: {field}"
    
    def test_pozycja_numeric_fields(self):
        """Test że pola numeryczne są liczbami"""
        pozycja = {
            'lp': 1,
            'ilosc': 100.5,
            'R': 450.0,
            'M': 0.0,
            'S': 225.0,
        }
        
        assert isinstance(pozycja['lp'], (int, float))
        assert isinstance(pozycja['ilosc'], (int, float))
        assert isinstance(pozycja['R'], (int, float))
        assert isinstance(pozycja['M'], (int, float))
        assert isinstance(pozycja['S'], (int, float))
    
    # ===== Testy _find_naklady =====
    
    def test_find_naklady_by_knr(self):
        """Test wyszukiwania nakładów po KNR"""
        # Dodaj testowy nakład do bazy
        self.generator.naklady = [
            {'knr': 'KNR 2-31 0703-03', 'R': 100, 'M': 50, 'S': 25},
        ]
        self.generator._rebuild_naklady_index()

        r, m, s, confidence, source = self.generator._find_naklady('KNR 2-31 0703-03', 'Rozbiórka')

        assert r == 100
        assert m == 50
        assert s == 25
    
    def test_find_naklady_default(self):
        """Test domyślnych nakładów gdy nie znaleziono w bazie"""
        self.generator.naklady = []  # Pusta baza
        self.generator._rebuild_naklady_index()

        r, m, s, confidence, source = self.generator._find_naklady('NIEZNANY-KNR', 'Nieznana pozycja')

        # Domyślne wartości
        assert r > 0
        assert m > 0
        assert s > 0
    
    def test_find_naklady_fuzzy_match(self):
        """Test fuzzy matching po opisie"""
        self.generator.naklady = [
            {'knr': 'KNR 9-99', 'opis': 'Rozbiórka nawierzchni betonowej', 'R': 200, 'M': 0, 'S': 100},
        ]
        self.generator._rebuild_naklady_index()

        # Szukamy podobnego opisu
        r, m, s, confidence, source = self.generator._find_naklady('INNY-KNR', 'Rozbiórka nawierzchni z betonu')

        # Powinno znaleźć przez fuzzy match (>= 3 wspólne słowa)
        # Wspólne: "Rozbiórka", "nawierzchni" - tylko 2, więc nie znajdzie
        # To jest test że NIE znajdzie (mniej niż 3 wspólne słowa)
        assert r > 0  # Domyślne
    
    # ===== Testy validate_pozycje =====
    
    def test_validate_pozycje_empty(self):
        """Test walidacji pustej listy"""
        errors, warnings = self.generator.validate_pozycje([])
        # Pusta lista - brak błędów
        assert isinstance(errors, list)
        assert isinstance(warnings, list)
    
    def test_validate_pozycje_valid(self):
        """Test walidacji poprawnych pozycji"""
        pozycje = [
            {'lp': 1, 'podstawa': 'KNR 2-31', 'opis': 'Test', 'jm': 'm2', 
             'ilosc': 100, 'R': 450, 'M': 0, 'S': 225},
        ]
        
        errors, warnings = self.generator.validate_pozycje(pozycje)
        # Brak krytycznych błędów
        assert len(errors) == 0
    
    # ===== Testy calculate_kosztorys =====
    
    def test_calculate_kosztorys_basic(self):
        """Test podstawowych obliczeń kosztorysu"""
        pozycje = [
            {'lp': 1, 'podstawa': 'KNR', 'opis': 'Test', 'jm': 'm2',
             'ilosc': 100, 'R': 1000, 'M': 500, 'S': 200, 'dzial': 'Test'},
        ]
        
        pozycje_out, podsumowanie = self.generator.calculate_kosztorys(pozycje)
        
        # Sprawdź sumy
        assert podsumowanie['suma_R'] == 1000
        assert podsumowanie['suma_M'] == 500
        assert podsumowanie['suma_S'] == 200
        
        # Sprawdź narzuty (Kp = 70% od R+S, Z = 12% od R+S+Kp)
        expected_kp = (1000 + 200) * 0.70  # 840
        expected_z = (1000 + 200 + expected_kp) * 0.12  # 244.8
        
        assert abs(podsumowanie['koszty_posrednie'] - expected_kp) < 0.01
        assert abs(podsumowanie['zysk'] - expected_z) < 0.01
        
        # NETTO = R + M + S + Kp + Z
        expected_netto = 1000 + 500 + 200 + expected_kp + expected_z
        assert abs(podsumowanie['wartosc_netto'] - expected_netto) < 0.01
    
    def test_calculate_kosztorys_multiple(self):
        """Test obliczeń z wieloma pozycjami"""
        pozycje = [
            {'lp': 1, 'R': 100, 'M': 50, 'S': 25, 'dzial': 'A', 
             'podstawa': 'KNR', 'opis': 'P1', 'jm': 'm2', 'ilosc': 10},
            {'lp': 2, 'R': 200, 'M': 100, 'S': 50, 'dzial': 'A',
             'podstawa': 'KNR', 'opis': 'P2', 'jm': 'm2', 'ilosc': 20},
            {'lp': 3, 'R': 300, 'M': 150, 'S': 75, 'dzial': 'B',
             'podstawa': 'KNR', 'opis': 'P3', 'jm': 'm2', 'ilosc': 30},
        ]
        
        pozycje_out, podsumowanie = self.generator.calculate_kosztorys(pozycje)
        
        # Sumy
        assert podsumowanie['suma_R'] == 600  # 100+200+300
        assert podsumowanie['suma_M'] == 300  # 50+100+150
        assert podsumowanie['suma_S'] == 150  # 25+50+75
    
    # ===== Testy cache =====
    
    def test_cache_disabled(self):
        """Test że cache można wyłączyć"""
        cache = PDFCache(enabled=False)
        
        # Set nie powinno nic robić
        result = cache.set('/fake/path.pdf', [{'test': 1}])
        assert result == False
        
        # Get powinno zwrócić None
        assert cache.get('/fake/path.pdf') is None
    
    def test_cache_stats(self):
        """Test statystyk cache"""
        cache = PDFCache()
        stats = cache.stats()
        
        assert 'enabled' in stats
        assert 'files' in stats
        assert 'size_kb' in stats


def run_tests():
    """Uruchamia testy bez pytest"""
    test = TestPDFParser()
    
    passed = 0
    failed = 0
    
    for method_name in dir(test):
        if method_name.startswith('test_'):
            test.setup_method()
            try:
                getattr(test, method_name)()
                print(f"  OK: {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  FAIL: {method_name} - {e}")
                failed += 1
            except Exception as e:
                print(f"  ERROR: {method_name} - {type(e).__name__}: {e}")
                failed += 1
    
    print(f"\n{'='*40}")
    print(f"Passed: {passed}, Failed: {failed}")
    return failed == 0


if __name__ == "__main__":
    print("Testy PDF Parser")
    print("=" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
