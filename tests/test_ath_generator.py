# -*- coding: utf-8 -*-
"""
Testy dla ATHGenerator v3.0

Testuje format Norma PRO z RMS ZEST dla R, M, S.

Uruchomienie:
    python tests/test_ath_generator.py
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ath_generator import ATHGenerator


class TestATHGenerator:
    """Testy dla generatora ATH"""
    
    def setup_method(self):
        """Przygotowanie przed każdym testem"""
        self.generator = ATHGenerator()
        self.temp_dir = tempfile.mkdtemp()
        
        # Przykładowe dane testowe
        self.pozycje = [
            {'lp': 1, 'podstawa': 'KNR 2-31 0703-03', 'opis': 'Rozbiórka nawierzchni',
             'jm': 'm2', 'ilosc': 150.0, 'R': 450.0, 'M': 200.0, 'S': 75.0},
            {'lp': 2, 'podstawa': 'KNR 4-01 0354-09', 'opis': 'Betonowanie',
             'jm': 'm3', 'ilosc': 10.0, 'R': 350.0, 'M': 1500.0, 'S': 100.0},
        ]
        
        self.podsumowanie = {
            'suma_R': 800.0, 'suma_M': 1700.0, 'suma_S': 175.0,
            'koszty_posrednie': 1872.5, 'zysk': 545.70,
            'wartosc_netto': 5093.20, 'vat': 1171.44, 'wartosc_brutto': 6264.64,
        }
        
        self.dane_tytulowe = {
            'nazwa_inwestycji': 'Test Inwestycja',
            'wykonawca': 'KLONEKS',
        }
    
    # ===== Testy DEFAULT_PARAMS =====
    
    def test_default_params_exist(self):
        """Test że DEFAULT_PARAMS ma wszystkie wymagane pola"""
        required = ['stawka_rg', 'stawka_sprzetu', 'kp_procent', 'z_procent', 'vat_procent']
        
        for param in required:
            assert param in self.generator.params, f"Brak parametru: {param}"
    
    def test_default_params_values(self):
        """Test domyślnych wartości parametrów"""
        assert self.generator.params['stawka_rg'] == 35.00
        assert self.generator.params['stawka_sprzetu'] == 100.00
        assert self.generator.params['kp_procent'] == 70.0
        assert self.generator.params['z_procent'] == 12.0
        assert self.generator.params['vat_procent'] == 23.0
    
    def test_custom_params(self):
        """Test nadpisywania parametrów"""
        gen = ATHGenerator({'stawka_rg': 50.0, 'kp_procent': 80.0})
        
        assert gen.params['stawka_rg'] == 50.0
        assert gen.params['kp_procent'] == 80.0
        # Pozostałe domyślne
        assert gen.params['stawka_sprzetu'] == 100.00
    
    # ===== Testy struktury pliku =====
    
    def test_generate_creates_file(self):
        """Test że generate() tworzy plik"""
        output_path = os.path.join(self.temp_dir, 'test.ath')
        result = self.generator.generate(
            self.pozycje, self.podsumowanie, self.dane_tytulowe, output_path
        )
        
        assert os.path.exists(result)
        assert os.path.getsize(result) > 100
    
    def test_generate_encoding_cp1250(self):
        """Test że plik jest w kodowaniu cp1250"""
        dane = {'nazwa_inwestycji': 'Żółć', 'wykonawca': 'KŁONEKS'}
        output_path = os.path.join(self.temp_dir, 'test_encoding.ath')
        
        self.generator.generate(self.pozycje, self.podsumowanie, dane, output_path)
        
        # Plik powinien być odczytywalny jako cp1250
        with open(output_path, 'r', encoding='cp1250') as f:
            content = f.read()
        
        assert len(content) > 100
    
    def test_generate_has_header(self):
        """Test że plik ma nagłówek Athenasoft"""
        output_path = os.path.join(self.temp_dir, 'test.ath')
        self.generator.generate(self.pozycje, self.podsumowanie, self.dane_tytulowe, output_path)
        
        with open(output_path, 'r', encoding='cp1250') as f:
            content = f.read()
        
        assert '[KOSZTORYS ATHENASOFT]' in content
        assert 'pr=NORMA' in content
    
    def test_generate_has_rms_zest_for_r_m_s(self):
        """Test że plik ma 3 globalne RMS ZEST (R, M, S)"""
        output_path = os.path.join(self.temp_dir, 'test.ath')
        self.generator.generate(self.pozycje, self.podsumowanie, self.dane_tytulowe, output_path)
        
        with open(output_path, 'r', encoding='cp1250') as f:
            content = f.read()
        
        # Musi być RMS ZEST 1 (robocizna)
        assert '[RMS ZEST 1]' in content
        assert 'ty=R' in content
        
        # Musi być RMS ZEST 2 (materiały)
        assert '[RMS ZEST 2]' in content
        assert 'ty=M' in content
        
        # Musi być RMS ZEST 3 (sprzęt)
        assert '[RMS ZEST 3]' in content
        assert 'ty=S' in content
    
    def test_generate_has_pozycje(self):
        """Test że plik ma sekcje POZYCJA"""
        output_path = os.path.join(self.temp_dir, 'test.ath')
        self.generator.generate(self.pozycje, self.podsumowanie, self.dane_tytulowe, output_path)
        
        with open(output_path, 'r', encoding='cp1250') as f:
            content = f.read()
        
        assert '[POZYCJA]' in content
        assert 'Rozbiórka nawierzchni' in content or 'Rozbiorka' in content
    
    def test_generate_has_rms_references(self):
        """Test że pozycje mają referencje do RMS ZEST"""
        output_path = os.path.join(self.temp_dir, 'test.ath')
        self.generator.generate(self.pozycje, self.podsumowanie, self.dane_tytulowe, output_path)
        
        with open(output_path, 'r', encoding='cp1250') as f:
            content = f.read()
        
        # Referencje do RMS ZEST
        assert 'nz=1' in content  # robocizna
        assert 'nz=2' in content  # materiały
        assert 'nz=3' in content  # sprzęt
    
    def test_generate_pozycja_only_r(self):
        """Test pozycji z samą robocizną (bez M i S) - nie generuje nz=2/nz=3"""
        pozycje = [
            {'lp': 1, 'podstawa': 'KNR 1-01', 'opis': 'Roboty pomocnicze',
             'jm': 'r-g', 'ilosc': 10.0, 'R': 350.0, 'M': 0, 'S': 0},
        ]
        podsumowanie = {'suma_R': 350, 'suma_M': 0, 'suma_S': 0,
                        'koszty_posrednie': 245, 'zysk': 71.4,
                        'wartosc_netto': 666.4, 'vat': 153.27, 'wartosc_brutto': 819.67}
        
        output_path = os.path.join(self.temp_dir, 'test_r.ath')
        self.generator.generate(pozycje, podsumowanie, self.dane_tytulowe, output_path)
        
        with open(output_path, 'r', encoding='cp1250') as f:
            content = f.read()
        
        # Pozycja bez M i S nie powinna mieć referencji nz=2 i nz=3
        assert 'nz=1' in content, "Brak referencji do robocizny (nz=1)"
        assert 'nz=2' not in content, "Nie powinno być nz=2 dla pozycji bez M"
        assert 'nz=3' not in content, "Nie powinno być nz=3 dla pozycji bez S"
    
    def test_generate_narzuty(self):
        """Test że plik ma sekcje narzutów (Kp, Z)"""
        output_path = os.path.join(self.temp_dir, 'test.ath')
        self.generator.generate(self.pozycje, self.podsumowanie, self.dane_tytulowe, output_path)
        
        with open(output_path, 'r', encoding='cp1250') as f:
            content = f.read()
        
        assert '[NARZUTY NORMA 2]' in content
        assert 'Koszty posrednie' in content or 'Kp' in content
        assert 'Zysk' in content


def run_tests():
    """Uruchamia testy bez pytest"""
    test = TestATHGenerator()
    
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
    print("Testy ATH Generator v3.0")
    print("=" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
