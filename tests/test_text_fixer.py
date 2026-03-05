# -*- coding: utf-8 -*-
"""
Testy dla TextFixer

Uruchomienie:
    cd kosztorysAI
    python -m pytest tests/test_text_fixer.py -v
    
Lub bez pytest:
    python tests/test_text_fixer.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from validators.text_fixer import TextFixer


class TestTextFixer:
    """Testy dla klasy TextFixer"""
    
    def setup_method(self):
        """Przygotowanie przed każdym testem"""
        self.fixer = TextFixer()
    
    # ===== fix_number =====
    
    def test_fix_number_double_dot(self):
        """Test naprawy liczb z podwójną kropką"""
        assert self.fixer.fix_number('0.428.89') == '28.89'
        assert self.fixer.fix_number('0.4123.45') == '23.45'
    
    def test_fix_number_thousands(self):
        """Test formatu tysięcy"""
        assert self.fixer.fix_number('1.234.56') == '1234.56'
    
    def test_fix_number_normal(self):
        """Test normalnych liczb (bez zmian)"""
        assert self.fixer.fix_number('123.45') == '123.45'
        assert self.fixer.fix_number('100') == '100'
    
    # ===== extract_number =====
    
    def test_extract_number_with_unit(self):
        """Test wyciągania liczby z jednostką"""
        assert self.fixer.extract_number('28,89 m2') == 28.89
        assert self.fixer.extract_number('150.5 szt.') == 150.5
    
    def test_extract_number_polish_format(self):
        """Test formatu polskiego (przecinek)"""
        assert self.fixer.extract_number('1 234,56') == 1234.56
    
    def test_extract_number_invalid(self):
        """Test dla nieprawidłowych danych"""
        assert self.fixer.extract_number('brak') == 0.0
        assert self.fixer.extract_number('') == 0.0
        assert self.fixer.extract_number(None) == 0.0
    
    # ===== fix_jednostka =====
    
    def test_fix_jednostka_superscript(self):
        """Test jednostek z indeksem górnym"""
        # Unicode superscript
        m2_super = 'm' + chr(178)  # m²
        m3_super = 'm' + chr(179)  # m³
        assert self.fixer.fix_jednostka(m2_super) == 'm2'
        assert self.fixer.fix_jednostka(m3_super) == 'm3'
    
    def test_fix_jednostka_variations(self):
        """Test różnych wariantów jednostek"""
        assert self.fixer.fix_jednostka('mb') == 'm'
        assert self.fixer.fix_jednostka('mb.') == 'm'
        assert self.fixer.fix_jednostka('szt') == 'szt.'
        assert self.fixer.fix_jednostka('kpl') == 'kpl.'
    
    def test_fix_jednostka_hybrid_ocr(self):
        """Test hybrydowych błędów OCR (r-g/m2)"""
        assert self.fixer.fix_jednostka('r-g/m2') == 'm2'
        assert self.fixer.fix_jednostka('m-g/m3') == 'm3'
    
    def test_fix_jednostka_empty(self):
        """Test pustej jednostki"""
        assert self.fixer.fix_jednostka('') == 'm2'
        assert self.fixer.fix_jednostka(None) == 'm2'
    
    # ===== fix_podstawa =====
    
    def test_fix_podstawa_standard(self):
        """Test standardowego formatu KNR"""
        assert self.fixer.fix_podstawa('KNR 2-31 0703-03') == 'KNR 2-31 0703-03'
    
    def test_fix_podstawa_no_dash(self):
        """Test KNR bez myślnika w numerze"""
        assert self.fixer.fix_podstawa('KNR 2-31 070303') == 'KNR 2-31 0703-03'
    
    def test_fix_podstawa_lowercase(self):
        """Test małych liter"""
        result = self.fixer.fix_podstawa('knr 2-31 0703-03')
        assert 'KNR' in result
    
    def test_fix_podstawa_spaces(self):
        """Test różnych formatów spacji"""
        result = self.fixer.fix_podstawa('KNR2 31 070303')
        assert 'KNR' in result
        assert '0703-03' in result or '0703' in result
    
    # ===== fix_encoding =====
    
    def test_fix_encoding_cp1250(self):
        """Test naprawy znaków cp1250"""
        # Replacement char powinien być usunięty
        assert self.fixer.fix_encoding('\ufffd') == ''  # Unicode replacement
        # Normalne polskie znaki powinny zostać
        assert 'a' in self.fixer.fix_encoding('ala ma kota')
    
    def test_fix_encoding_normal(self):
        """Test normalnego tekstu (bez zmian)"""
        text = 'Rozbiórka nawierzchni betonowej'
        assert self.fixer.fix_encoding(text) == text
    
    # ===== fix_opis =====
    
    def test_fix_opis_ocr_patterns(self):
        """Test naprawy wzorców OCR"""
        # cermentow -> cementow
        result = self.fixer.fix_opis('betonu cermentowego')
        assert 'cementow' in result.lower()
    
    def test_fix_opis_normal(self):
        """Test normalnego opisu (bez zmian)"""
        opis = 'Rozbiórka nawierzchni z kostki brukowej'
        result = self.fixer.fix_opis(opis)
        assert 'Rozbiórka' in result or 'rozbiórka' in result.lower()
    
    # ===== normalize_rms_separator =====
    
    def test_normalize_rms_separator(self):
        """Test normalizacji separatorów R/M/S"""
        assert '-- R --' in self.fixer.normalize_rms_separator('--R-')
        assert '-- R --' in self.fixer.normalize_rms_separator('- R --')
        assert '-- M --' in self.fixer.normalize_rms_separator('--M--')
        assert '-- S --' in self.fixer.normalize_rms_separator('-S-')
    
    # ===== fix_pozycja (integration) =====
    
    def test_fix_pozycja_complete(self):
        """Test naprawy kompletnej pozycji"""
        pozycja = {
            'podstawa': 'knr 2-31 070303',
            'opis': 'Rozbiórka cermentowej nawierzchni',
            'jm': 'm²',
            'ilosc': '150,5',
            'R': '450.00',
            'M': 0,
            'S': '225',
        }
        
        result = self.fixer.fix_pozycja(pozycja)
        
        assert 'KNR' in result['podstawa']
        assert result['jm'] == 'm2'
        assert result['ilosc'] == 150.5
        assert result['R'] == 450.0
        assert result['S'] == 225.0


def run_tests():
    """Uruchamia testy bez pytest"""
    test = TestTextFixer()
    
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
                print(f"  ERROR: {method_name} - {e}")
                failed += 1
    
    print(f"\n{'='*40}")
    print(f"Passed: {passed}, Failed: {failed}")
    return failed == 0


if __name__ == "__main__":
    print("Testy TextFixer")
    print("=" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
