# -*- coding: utf-8 -*-
"""
Calculator Engine v2.0
Single Source of Truth - ZAWSZE oblicza od zera, NIGDY nie ufa danym wejściowym

Zasada: Pozycje → Sumy → Narzuty → NETTO (w tej kolejności, zawsze)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json

from formatters import fmt_summary
from exceptions import KosztorysError


@dataclass
class Pozycja:
    """Pojedyncza pozycja kosztorysowa"""
    lp: int
    podstawa: str
    opis: str
    jm: str
    ilosc: float
    R: float  # Robocizna (koszty bezpośrednie)
    M: float  # Materiały (koszty bezpośrednie)
    S: float  # Sprzęt (koszty bezpośrednie)
    dzial: str = "Kosztorys"
    
    @property
    def suma_bezposrednia(self) -> float:
        """R + M + S"""
        return self.R + self.M + self.S
    
    @property
    def R_jednostkowe(self) -> float:
        return self.R / self.ilosc if self.ilosc else 0
    
    @property
    def M_jednostkowe(self) -> float:
        return self.M / self.ilosc if self.ilosc else 0
    
    @property
    def S_jednostkowe(self) -> float:
        return self.S / self.ilosc if self.ilosc else 0


@dataclass
class Dzial:
    """Dział kosztorysu (suma pozycji)"""
    nazwa: str
    pozycje: List[Pozycja] = field(default_factory=list)
    
    @property
    def suma_R(self) -> float:
        return sum(p.R for p in self.pozycje)
    
    @property
    def suma_M(self) -> float:
        return sum(p.M for p in self.pozycje)
    
    @property
    def suma_S(self) -> float:
        return sum(p.S for p in self.pozycje)
    
    @property
    def suma_bezposrednia(self) -> float:
        """R + M + S dla działu"""
        return self.suma_R + self.suma_M + self.suma_S


@dataclass
class Podsumowanie:
    """Podsumowanie kosztorysu - OBLICZONE, nie deklarowane"""
    # Koszty bezpośrednie
    suma_R: float
    suma_M: float
    suma_S: float
    
    # Parametry narzutów
    kp_procent: float
    z_procent: float
    vat_procent: float
    
    # Obliczone narzuty
    koszty_posrednie: float  # Kp od (R+S)
    zysk: float              # Z od (R+S+Kp)
    
    # Wartości końcowe
    wartosc_netto: float
    vat: float
    wartosc_brutto: float
    
    @property
    def suma_bezposrednia(self) -> float:
        return self.suma_R + self.suma_M + self.suma_S
    
    def validate(self) -> bool:
        """Sprawdza wewnętrzną spójność"""
        expected_netto = self.suma_R + self.suma_M + self.suma_S + self.koszty_posrednie + self.zysk
        return abs(self.wartosc_netto - expected_netto) < 0.01


class CalculatorEngine:
    """
    Silnik obliczeniowy kosztorysów
    
    ZASADA: Single Source of Truth
    - ZAWSZE oblicza od pozycji
    - NIGDY nie używa wartości z danych wejściowych
    - Gwarantuje spójność sum
    """
    
    DEFAULT_PARAMS = {
        'stawka_rg': 35.00,      # zł/r-g (roboczogodzina)
        'stawka_sprzetu': 100.00, # zł/m-g (maszynogodzina)
        'kp_procent': 70.0,       # Koszty pośrednie od R+S
        'z_procent': 12.0,        # Zysk od R+S+Kp (M wyłączone!)
        'vat_procent': 23.0,
    }
    
    def __init__(self, params: Dict = None):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
    
    def calculate(self, pozycje: List[Dict]) -> tuple:
        """
        Główna funkcja - oblicza WSZYSTKO od zera
        
        Args:
            pozycje: lista słowników z pozycjami
            
        Returns:
            (dzialy, podsumowanie) - obliczone, spójne dane
        """
        # KROK 1: Konwertuj na obiekty Pozycja
        pozycje_obj = []
        for p in pozycje:
            pozycje_obj.append(Pozycja(
                lp=p.get('lp', len(pozycje_obj) + 1),
                podstawa=p.get('podstawa', ''),
                opis=p.get('opis', ''),
                jm=p.get('jm', 'szt.'),
                ilosc=p.get('ilosc', 0),
                R=p.get('R', 0),
                M=p.get('M', 0),
                S=p.get('S', 0),
                dzial=p.get('dzial', 'Kosztorys'),
            ))
        
        # KROK 2: Grupuj w działy
        dzialy_dict = {}
        for poz in pozycje_obj:
            if poz.dzial not in dzialy_dict:
                dzialy_dict[poz.dzial] = Dzial(nazwa=poz.dzial)
            dzialy_dict[poz.dzial].pozycje.append(poz)
        
        dzialy = list(dzialy_dict.values())
        
        # KROK 3: Oblicz sumy (ZAWSZE od pozycji!)
        suma_R = sum(d.suma_R for d in dzialy)
        suma_M = sum(d.suma_M for d in dzialy)
        suma_S = sum(d.suma_S for d in dzialy)
        
        # Weryfikacja: suma działów == suma pozycji
        suma_R_poz = sum(p.R for p in pozycje_obj)
        suma_M_poz = sum(p.M for p in pozycje_obj)
        suma_S_poz = sum(p.S for p in pozycje_obj)
        
        if abs(suma_R - suma_R_poz) >= 0.01:
            raise KosztorysError(f"Błąd sumy R: działy={suma_R:.2f}, pozycje={suma_R_poz:.2f}")
        if abs(suma_M - suma_M_poz) >= 0.01:
            raise KosztorysError(f"Błąd sumy M: działy={suma_M:.2f}, pozycje={suma_M_poz:.2f}")
        if abs(suma_S - suma_S_poz) >= 0.01:
            raise KosztorysError(f"Błąd sumy S: działy={suma_S:.2f}, pozycje={suma_S_poz:.2f}")
        
        # KROK 4: Oblicz narzuty (FORMUŁA NORMA PRO)
        kp_proc = self.params['kp_procent'] / 100
        z_proc = self.params['z_procent'] / 100
        vat_proc = self.params['vat_procent'] / 100
        
        # Kp od (R+S) - materiały wyłączone!
        koszty_posrednie = (suma_R + suma_S) * kp_proc
        
        # Zysk od (R+S+Kp) - materiały wyłączone!
        zysk = (suma_R + suma_S + koszty_posrednie) * z_proc
        
        # KROK 5: NETTO = R + M + S + Kp + Z (ZAWSZE suma składników!)
        wartosc_netto = suma_R + suma_M + suma_S + koszty_posrednie + zysk
        
        # VAT i Brutto
        vat = wartosc_netto * vat_proc
        wartosc_brutto = wartosc_netto + vat
        
        # KROK 6: Stwórz podsumowanie
        podsumowanie = Podsumowanie(
            suma_R=suma_R,
            suma_M=suma_M,
            suma_S=suma_S,
            kp_procent=self.params['kp_procent'],
            z_procent=self.params['z_procent'],
            vat_procent=self.params['vat_procent'],
            koszty_posrednie=koszty_posrednie,
            zysk=zysk,
            wartosc_netto=wartosc_netto,
            vat=vat,
            wartosc_brutto=wartosc_brutto,
        )
        
        # KROK 7: Walidacja wewnętrzna
        if not podsumowanie.validate():
            raise KosztorysError("Błąd wewnętrznej spójności podsumowania!")
        
        return dzialy, podsumowanie
    
    def to_dict(self, dzialy: List[Dzial], podsumowanie: Podsumowanie) -> Dict:
        """Konwertuje na słownik do generatorów PDF/ATH"""
        return {
            'dzialy': [
                {
                    'nazwa': d.nazwa,
                    'R': d.suma_R,
                    'M': d.suma_M,
                    'S': d.suma_S,
                    'razem': d.suma_bezposrednia,  # TYLKO koszty bezpośrednie!
                    'pozycje': [
                        {
                            'lp': p.lp,
                            'podstawa': p.podstawa,
                            'opis': p.opis,
                            'jm': p.jm,
                            'ilosc': p.ilosc,
                            'R': p.R,
                            'M': p.M,
                            'S': p.S,
                            'wartosc': p.suma_bezposrednia,  # koszty bezpośrednie
                        }
                        for p in d.pozycje
                    ]
                }
                for d in dzialy
            ],
            'podsumowanie': {
                'suma_R': podsumowanie.suma_R,
                'suma_M': podsumowanie.suma_M,
                'suma_S': podsumowanie.suma_S,
                'suma_bezposrednia': podsumowanie.suma_bezposrednia,
                'koszty_posrednie': podsumowanie.koszty_posrednie,
                'zysk': podsumowanie.zysk,
                'wartosc_netto': podsumowanie.wartosc_netto,
                'vat': podsumowanie.vat,
                'wartosc_brutto': podsumowanie.wartosc_brutto,
                'kp_procent': podsumowanie.kp_procent,
                'z_procent': podsumowanie.z_procent,
                'vat_procent': podsumowanie.vat_procent,
            }
        }
    
    def print_summary(self, podsumowanie: Podsumowanie):
        """Drukuje podsumowanie w czytelnej formie"""
        fmt = fmt_summary
        lines = [
            "=" * 50,
            "PODSUMOWANIE (Calculator Engine v2.0)",
            "=" * 50,
            "Koszty bezposrednie:",
            f"  R (Robocizna):    {fmt(podsumowanie.suma_R):>15} zl",
            f"  M (Materialy):    {fmt(podsumowanie.suma_M):>15} zl",
            f"  S (Sprzet):       {fmt(podsumowanie.suma_S):>15} zl",
            "  " + "-" * 40,
            f"  RAZEM (R+M+S):    {fmt(podsumowanie.suma_bezposrednia):>15} zl",
            "",
            "Narzuty:",
            f"  Kp {podsumowanie.kp_procent}% od (R+S): {fmt(podsumowanie.koszty_posrednie):>12} zl",
            f"  Z  {podsumowanie.z_procent}% od (R+S+Kp):{fmt(podsumowanie.zysk):>12} zl",
            "",
            "Wartosci koncowe:",
            "  " + "-" * 40,
            f"  NETTO:            {fmt(podsumowanie.wartosc_netto):>15} zl",
            f"  VAT {podsumowanie.vat_procent}%:         {fmt(podsumowanie.vat):>15} zl",
            "  " + "=" * 40,
            f"  BRUTTO:           {fmt(podsumowanie.wartosc_brutto):>15} zl",
            "=" * 50,
            f"Walidacja: {'OK' if podsumowanie.validate() else 'BLAD!'}",
        ]
        print("\n".join(lines))


# ============ TEST ============
if __name__ == "__main__":
    engine = CalculatorEngine({
        'kp_procent': 70,
        'z_procent': 12,
        'vat_procent': 23,
    })
    
    # Dane testowe
    pozycje = [
        {'lp': 1, 'podstawa': 'KNR 2-31', 'opis': 'Rozbiórka', 'jm': 'm2', 'ilosc': 150, 
         'R': 450, 'M': 0, 'S': 225, 'dzial': 'Roboty przygotowawcze'},
        {'lp': 2, 'podstawa': 'KNR 2-31', 'opis': 'Podbudowa', 'jm': 'm2', 'ilosc': 200,
         'R': 1400, 'M': 6200, 'S': 800, 'dzial': 'Podbudowy'},
        {'lp': 3, 'podstawa': 'KNR 2-33', 'opis': 'Beton', 'jm': 'm2', 'ilosc': 200,
         'R': 5600, 'M': 26000, 'S': 2800, 'dzial': 'Nawierzchnie'},
        {'lp': 4, 'podstawa': 'KNR 2-31', 'opis': 'Obrzeża', 'jm': 'm', 'ilosc': 60,
         'R': 504, 'M': 1260, 'S': 180, 'dzial': 'Nawierzchnie'},
    ]
    
    dzialy, podsumowanie = engine.calculate(pozycje)
    engine.print_summary(podsumowanie)
    
    # Weryfikacja ręczna
    print("WERYFIKACJA RĘCZNA:")
    R = 450 + 1400 + 5600 + 504
    M = 0 + 6200 + 26000 + 1260
    S = 225 + 800 + 2800 + 180
    print(f"R = {R}, M = {M}, S = {S}")
    Kp = (R + S) * 0.70
    Z = (R + S + Kp) * 0.12
    NETTO = R + M + S + Kp + Z
    print(f"Kp = {Kp:.2f}, Z = {Z:.2f}")
    print(f"NETTO = R+M+S+Kp+Z = {NETTO:.2f}")
