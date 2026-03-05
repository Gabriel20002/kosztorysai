# -*- coding: utf-8 -*-
"""
CalcValidator - weryfikacja matematyczna kosztorysów
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class ValidationStatus(Enum):
    OK = "OK"
    CALC_MISMATCH = "CALC_MISMATCH"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class ValidationResult:
    status: ValidationStatus
    message: str = ""
    expected: float = 0.0
    actual: float = 0.0
    difference_percent: float = 0.0

class CalcValidator:
    """Walidator kalkulacji kosztorysowych"""
    
    # Domyślne parametry narzutów
    DEFAULT_PARAMS = {
        'kp_procent': 70.0,      # Koszty pośrednie % od R+S
        'z_procent': 12.0,       # Zysk % od R+S+Kp
        'kz_procent': 8.0,       # Koszty zakupu % od M
        'vat_procent': 23.0,     # VAT
        'stawka_rg': 35.0,       # Stawka roboczogodziny
        'tolerance': 0.02,       # Tolerancja błędu (2%)
    }
    
    def __init__(self, params=None):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
    
    def validate_cena_jednostkowa(self, pozycja, params=None) -> ValidationResult:
        """
        Sprawdza zgodność ceny jednostkowej z modelem narzutów
        
        Model:
        Cj = (R × (1+Kp) × (1+Z)) + (M × (1+Kz)) + (S × (1+Kp) × (1+Z)) / ilość
        """
        p = {**self.params, **(params or {})}
        
        R = pozycja.get('R', 0)
        M = pozycja.get('M', 0)
        S = pozycja.get('S', 0)
        ilosc = pozycja.get('ilosc', 1)
        cena_pdf = pozycja.get('cena_jednostkowa', 0)
        
        if ilosc == 0:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message="Ilość = 0, nie można obliczyć ceny jednostkowej"
            )
        
        if cena_pdf == 0:
            # Brak ceny do weryfikacji - oblicz ją
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Brak ceny jednostkowej do weryfikacji"
            )
        
        # Oblicz cenę według modelu
        Kp = p['kp_procent'] / 100
        Z = p['z_procent'] / 100
        Kz = p['kz_procent'] / 100
        
        # Robocizna z narzutami
        R_narz = R * (1 + Kp) * (1 + Z)
        
        # Materiały z kosztami zakupu
        M_narz = M * (1 + Kz)
        
        # Sprzęt z narzutami
        S_narz = S * (1 + Kp) * (1 + Z)
        
        wartosc_model = R_narz + M_narz + S_narz
        cena_model = wartosc_model / ilosc
        
        # Porównaj
        if cena_pdf == 0:
            diff_pct = 100
        else:
            diff_pct = abs(cena_model - cena_pdf) / cena_pdf * 100
        
        tolerance = p['tolerance'] * 100
        
        if diff_pct <= tolerance:
            return ValidationResult(
                status=ValidationStatus.OK,
                expected=cena_model,
                actual=cena_pdf,
                difference_percent=diff_pct
            )
        else:
            return ValidationResult(
                status=ValidationStatus.CALC_MISMATCH,
                message=f"Rozbieżność {diff_pct:.1f}% (tolerancja {tolerance:.0f}%)",
                expected=cena_model,
                actual=cena_pdf,
                difference_percent=diff_pct
            )
    
    def validate_wartosc(self, pozycja) -> ValidationResult:
        """
        Sprawdza zgodność wartości pozycji
        Wartość = Ilość × (R+M+S) [koszty bezpośrednie]
        """
        R = pozycja.get('R', 0)
        M = pozycja.get('M', 0)
        S = pozycja.get('S', 0)
        ilosc = pozycja.get('ilosc', 1)
        wartosc_pdf = pozycja.get('wartosc', 0)
        
        # Suma kosztów bezpośrednich
        suma_bezp = R + M + S
        
        # Wartość może być liczona na dwa sposoby:
        # A) Ilość × suma_bezp_jednostkowa
        # B) Ilość × cena_jednostkowa_z_narzutami
        
        # Sprawdź wariant A (bez narzutów)
        if ilosc > 0:
            wartosc_model_A = suma_bezp  # suma bezpośrednia całkowita
            wartosc_model_B = ilosc * pozycja.get('cena_jednostkowa', 0)
        else:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message="Ilość = 0"
            )
        
        # Porównaj z obiema możliwościami
        if wartosc_pdf == 0:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Brak wartości do weryfikacji"
            )
        
        diff_A = abs(wartosc_model_A - wartosc_pdf) / wartosc_pdf * 100 if wartosc_pdf else 100
        diff_B = abs(wartosc_model_B - wartosc_pdf) / wartosc_pdf * 100 if wartosc_pdf else 100
        
        tolerance = self.params['tolerance'] * 100
        
        if diff_A <= tolerance:
            return ValidationResult(
                status=ValidationStatus.OK,
                message="Wartość = koszty bezpośrednie (zgodne z Norma PRO)",
                expected=wartosc_model_A,
                actual=wartosc_pdf,
                difference_percent=diff_A
            )
        elif diff_B <= tolerance:
            return ValidationResult(
                status=ValidationStatus.OK,
                message="Wartość = ilość × cena jednostkowa",
                expected=wartosc_model_B,
                actual=wartosc_pdf,
                difference_percent=diff_B
            )
        else:
            return ValidationResult(
                status=ValidationStatus.CALC_MISMATCH,
                message=f"Wartość nie pasuje do żadnego modelu (diff A: {diff_A:.1f}%, B: {diff_B:.1f}%)",
                expected=wartosc_model_A,
                actual=wartosc_pdf,
                difference_percent=min(diff_A, diff_B)
            )
    
    def validate_podsumowanie(self, podsumowanie, pozycje) -> ValidationResult:
        """
        Sprawdza poprawność podsumowania kosztorysu
        """
        # Oblicz sumy z pozycji
        suma_R = sum(p.get('R', 0) for p in pozycje)
        suma_M = sum(p.get('M', 0) for p in pozycje)
        suma_S = sum(p.get('S', 0) for p in pozycje)
        
        # Porównaj z podsumowaniem
        pdf_R = podsumowanie.get('suma_R', 0)
        pdf_M = podsumowanie.get('suma_M', 0)
        pdf_S = podsumowanie.get('suma_S', 0)
        
        errors = []
        
        if pdf_R and abs(suma_R - pdf_R) / max(pdf_R, 1) > self.params['tolerance']:
            errors.append(f"R: obliczone {suma_R:.2f}, PDF {pdf_R:.2f}")
        
        if pdf_M and abs(suma_M - pdf_M) / max(pdf_M, 1) > self.params['tolerance']:
            errors.append(f"M: obliczone {suma_M:.2f}, PDF {pdf_M:.2f}")
        
        if pdf_S and abs(suma_S - pdf_S) / max(pdf_S, 1) > self.params['tolerance']:
            errors.append(f"S: obliczone {suma_S:.2f}, PDF {pdf_S:.2f}")
        
        if errors:
            return ValidationResult(
                status=ValidationStatus.CALC_MISMATCH,
                message="; ".join(errors)
            )
        
        # Sprawdź narzuty
        Kp = self.params['kp_procent'] / 100
        Z = self.params['z_procent'] / 100
        
        kp_expected = (suma_R + suma_S) * Kp
        kp_pdf = podsumowanie.get('koszty_posrednie', 0)
        
        if kp_pdf and abs(kp_expected - kp_pdf) / max(kp_pdf, 1) > self.params['tolerance']:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"Kp: oczekiwane {kp_expected:.2f}, PDF {kp_pdf:.2f} (może inny %)"
            )
        
        return ValidationResult(
            status=ValidationStatus.OK,
            message="Podsumowanie zgodne"
        )
    
    def recalculate_pozycja(self, pozycja, params=None):
        """
        Przelicza pozycję z poprawnymi wartościami
        Zwraca nową pozycję ze zaktualizowanymi wartościami
        """
        p = {**self.params, **(params or {})}
        
        R = pozycja.get('R', 0)
        M = pozycja.get('M', 0)
        S = pozycja.get('S', 0)
        ilosc = pozycja.get('ilosc', 1) or 1
        
        Kp = p['kp_procent'] / 100
        Z = p['z_procent'] / 100
        Kz = p['kz_procent'] / 100
        
        # Koszty bezpośrednie
        suma_bezp = R + M + S
        
        # Z narzutami
        R_narz = R * (1 + Kp) * (1 + Z)
        M_narz = M * (1 + Kz)
        S_narz = S * (1 + Kp) * (1 + Z)
        
        wartosc_z_narz = R_narz + M_narz + S_narz
        cena_jedn = wartosc_z_narz / ilosc
        
        return {
            **pozycja,
            'suma_bezposrednia': suma_bezp,
            'wartosc': wartosc_z_narz,
            'cena_jednostkowa': cena_jedn,
            'R_z_narzutami': R_narz,
            'M_z_narzutami': M_narz,
            'S_z_narzutami': S_narz,
        }
    
    def recalculate_kosztorys(self, pozycje, params=None):
        """
        Przelicza cały kosztorys i generuje podsumowanie
        
        POPRAWNA FORMUŁA (zgodna z Norma PRO):
        1. Koszty bezpośrednie = R + M + S
        2. Kp (koszty pośrednie) = (R + S) × Kp%
        3. Kz (koszty zakupu) = M × Kz%  [opcjonalnie]
        4. Z (zysk) = (R + S + Kp) × Z%  [UWAGA: M wyłączone!]
        5. Netto = R + M + S + Kp + Kz + Z
        6. VAT = Netto × VAT%
        7. Brutto = Netto + VAT
        """
        p = {**self.params, **(params or {})}
        
        # Przelicz pozycje
        przeliczone = [self.recalculate_pozycja(poz, p) for poz in pozycje]
        
        # Sumy kosztów bezpośrednich
        suma_R = sum(poz.get('R', 0) for poz in przeliczone)
        suma_M = sum(poz.get('M', 0) for poz in przeliczone)
        suma_S = sum(poz.get('S', 0) for poz in przeliczone)
        
        suma_bezposrednia = suma_R + suma_M + suma_S
        
        Kp_proc = p['kp_procent'] / 100
        Z_proc = p['z_procent'] / 100
        Kz_proc = p.get('kz_procent', 0) / 100
        VAT_proc = p['vat_procent'] / 100
        
        # Koszty pośrednie od R+S (NIE od M!)
        kp = (suma_R + suma_S) * Kp_proc
        
        # Koszty zakupu od M (opcjonalne)
        kz = suma_M * Kz_proc if Kz_proc > 0 else 0
        
        # Zysk od R+S+Kp (M wyłączone z podstawy!)
        zysk = (suma_R + suma_S + kp) * Z_proc
        
        # NETTO = wszystkie składniki
        netto = suma_R + suma_M + suma_S + kp + kz + zysk
        
        # Walidacja wewnętrzna
        skladniki = suma_R + suma_M + suma_S + kp + kz + zysk
        if abs(netto - skladniki) > 0.01:
            print(f"⚠ BŁĄD WEWNĘTRZNY: netto={netto:.2f} != składniki={skladniki:.2f}")
        
        vat = netto * VAT_proc
        brutto = netto + vat
        
        podsumowanie = {
            'suma_R': suma_R,
            'suma_M': suma_M,
            'suma_S': suma_S,
            'suma_bezposrednia': suma_bezposrednia,
            'koszty_posrednie': kp,
            'koszty_zakupu': kz,
            'zysk': zysk,
            'wartosc_netto': netto,
            'vat': vat,
            'wartosc_brutto': brutto,
            'kp_procent': p['kp_procent'],
            'z_procent': p['z_procent'],
            'kz_procent': p.get('kz_procent', 0),
            'vat_procent': p['vat_procent'],
            # Breakdown dla weryfikacji
            '_breakdown': {
                'R': suma_R,
                'M': suma_M,
                'S': suma_S,
                'Kp': kp,
                'Kz': kz,
                'Z': zysk,
                'suma_skladnikow': suma_R + suma_M + suma_S + kp + kz + zysk,
            }
        }
        
        return przeliczone, podsumowanie
    
    def validate_netto_sum(self, podsumowanie) -> ValidationResult:
        """
        Sprawdza czy NETTO = R + M + S + Kp + Kz + Z
        """
        R = podsumowanie.get('suma_R', 0)
        M = podsumowanie.get('suma_M', 0)
        S = podsumowanie.get('suma_S', 0)
        Kp = podsumowanie.get('koszty_posrednie', 0)
        Kz = podsumowanie.get('koszty_zakupu', 0)
        Z = podsumowanie.get('zysk', 0)
        netto = podsumowanie.get('wartosc_netto', 0)
        
        expected = R + M + S + Kp + Kz + Z
        diff = abs(netto - expected)
        diff_pct = diff / max(netto, 1) * 100
        
        if diff_pct > 1:  # >1% różnicy
            return ValidationResult(
                status=ValidationStatus.CALC_MISMATCH,
                message=f"NETTO ({netto:.2f}) != R+M+S+Kp+Kz+Z ({expected:.2f}). Różnica: {diff:.2f} zł ({diff_pct:.1f}%)",
                expected=expected,
                actual=netto,
                difference_percent=diff_pct
            )
        
        return ValidationResult(
            status=ValidationStatus.OK,
            message=f"Suma NETTO poprawna: {netto:.2f} = R({R:.0f})+M({M:.0f})+S({S:.0f})+Kp({Kp:.0f})+Z({Z:.0f})"
        )


# ============ TEST ============
if __name__ == "__main__":
    validator = CalcValidator()
    
    # Test pozycji
    poz = {
        'ilosc': 28.89,
        'R': 22.50,
        'M': 520.00,
        'S': 42.00,
        'cena_jednostkowa': 683.31,
        'wartosc': 16886.21,
    }
    
    print("=== Test walidacji ceny jednostkowej ===")
    result = validator.validate_cena_jednostkowa(poz)
    print(f"Status: {result.status.value}")
    print(f"Oczekiwana: {result.expected:.2f}")
    print(f"Aktualna: {result.actual:.2f}")
    print(f"Różnica: {result.difference_percent:.1f}%")
    print(f"Komunikat: {result.message}")
    
    print("\n=== Test przeliczenia ===")
    przeliczona = validator.recalculate_pozycja(poz)
    print(f"Suma bezpośrednia: {przeliczona['suma_bezposrednia']:.2f}")
    print(f"Wartość z narzutami: {przeliczona['wartosc']:.2f}")
    print(f"Cena jednostkowa: {przeliczona['cena_jednostkowa']:.2f}")
    
    print("\n✓ CalcValidator OK")
