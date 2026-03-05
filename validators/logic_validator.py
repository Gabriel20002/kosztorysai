# -*- coding: utf-8 -*-
"""
LogicValidator - walidacja logiki budowlanej kosztorysów
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum

class LogicStatus(Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class LogicResult:
    status: LogicStatus
    message: str = ""
    details: Dict = None

class LogicValidator:
    """Walidator logiki budowlanej - bilans mas, spójność technologiczna"""
    
    # Słowa kluczowe dla kategoryzacji robót
    KEYWORDS = {
        'wykopy': ['wykop', 'przekop', 'korytowanie', 'zdejmowanie', 'usunięcie', 'rozbiórka'],
        'wypelnienia': ['podbudowa', 'podsypka', 'zasypka', 'beton', 'nawierzchnia', 'warstwa'],
        'rozbiorki': ['rozbiórka', 'demontaż', 'usunięcie', 'zerwanie', 'skucie'],
        'montaz': ['montaż', 'ułożenie', 'wykonanie', 'osadzenie', 'zamontowanie'],
    }
    
    # Jednostki objętościowe
    VOLUME_UNITS = ['m3', 'm³', 'm.sześć', 'm sześć']
    AREA_UNITS = ['m2', 'm²', 'mkw']
    LENGTH_UNITS = ['m', 'mb', 'm.b.']
    
    def __init__(self):
        pass
    
    def categorize_pozycja(self, pozycja) -> str:
        """Kategoryzuje pozycję według typu robót"""
        opis = pozycja.get('opis', '').lower()
        
        for kategoria, keywords in self.KEYWORDS.items():
            for kw in keywords:
                if kw in opis:
                    return kategoria
        
        return 'inne'
    
    def validate_bilans_mas(self, pozycje) -> LogicResult:
        """
        Sprawdza bilans mas - czy wykopy ≈ wypełnienia
        
        Zasada: objętość wykopanego gruntu powinna być zbliżona
        do objętości materiału który go zastępuje (z tolerancją na zagęszczenie)
        """
        wykopy_m3 = 0
        wypelnienia_m3 = 0
        
        for poz in pozycje:
            jm = poz.get('jm', '').lower()
            ilosc = poz.get('ilosc', 0)
            opis = poz.get('opis', '').lower()
            kategoria = self.categorize_pozycja(poz)
            
            # Tylko jednostki objętościowe
            if any(u in jm for u in self.VOLUME_UNITS):
                if kategoria == 'wykopy' or any(kw in opis for kw in ['wykop', 'korytowanie']):
                    wykopy_m3 += ilosc
                elif kategoria == 'wypelnienia' or any(kw in opis for kw in ['beton', 'podbudowa', 'zasypka']):
                    wypelnienia_m3 += ilosc
            
            # Przelicz m2 na m3 jeśli podana grubość
            elif any(u in jm for u in self.AREA_UNITS):
                grubosc = self._extract_grubosc(opis)
                if grubosc:
                    vol = ilosc * grubosc
                    if kategoria == 'wykopy':
                        wykopy_m3 += vol
                    elif kategoria == 'wypelnienia':
                        wypelnienia_m3 += vol
        
        if wykopy_m3 == 0 and wypelnienia_m3 == 0:
            return LogicResult(
                status=LogicStatus.OK,
                message="Brak robót ziemnych do zbilansowania",
                details={'wykopy_m3': 0, 'wypelnienia_m3': 0}
            )
        
        # Tolerancja 20% (zagęszczenie, straty, etc.)
        if wykopy_m3 > 0:
            ratio = wypelnienia_m3 / wykopy_m3
        else:
            ratio = float('inf') if wypelnienia_m3 > 0 else 1.0
        
        details = {
            'wykopy_m3': round(wykopy_m3, 2),
            'wypelnienia_m3': round(wypelnienia_m3, 2),
            'ratio': round(ratio, 2),
        }
        
        if 0.8 <= ratio <= 1.3:
            return LogicResult(
                status=LogicStatus.OK,
                message=f"Bilans mas OK (wykopy: {wykopy_m3:.1f} m³, wypełnienia: {wypelnienia_m3:.1f} m³)",
                details=details
            )
        elif 0.5 <= ratio <= 1.8:
            return LogicResult(
                status=LogicStatus.WARNING,
                message=f"Bilans mas - uwaga! Wykopy: {wykopy_m3:.1f} m³, wypełnienia: {wypelnienia_m3:.1f} m³",
                details=details
            )
        else:
            return LogicResult(
                status=LogicStatus.ERROR,
                message=f"Bilans mas NIEZGODNY! Wykopy: {wykopy_m3:.1f} m³, wypełnienia: {wypelnienia_m3:.1f} m³",
                details=details
            )
    
    def _extract_grubosc(self, opis) -> float:
        """Wyciąga grubość z opisu (w metrach)"""
        # Wzorce: "gr. 15 cm", "grubości 20cm", "o grubości 0.15m"
        patterns = [
            r'gr(?:ubości?)?\s*(\d+(?:[.,]\d+)?)\s*cm',
            r'gr(?:ubości?)?\s*(\d+(?:[.,]\d+)?)\s*m(?!m)',
            r'(\d+(?:[.,]\d+)?)\s*cm\s*gr',
            r'warstwa\s*(\d+(?:[.,]\d+)?)\s*cm',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, opis, re.IGNORECASE)
            if match:
                val = float(match.group(1).replace(',', '.'))
                if 'cm' in pattern or val > 1:  # prawdopodobnie cm
                    return val / 100
                return val
        
        return 0
    
    def validate_kolejnosc_robot(self, pozycje) -> LogicResult:
        """
        Sprawdza logiczną kolejność robót
        np. rozbiórki przed montażem, wykopy przed podbudową
        """
        categories = [self.categorize_pozycja(p) for p in pozycje]
        
        errors = []
        
        # Rozbiórki powinny być przed montażem
        last_rozbiorka = -1
        first_montaz = len(categories)
        
        for i, cat in enumerate(categories):
            if cat == 'rozbiorki':
                last_rozbiorka = i
            elif cat == 'montaz' and first_montaz == len(categories):
                first_montaz = i
        
        if last_rozbiorka > first_montaz:
            errors.append("Rozbiórki po montażu - sprawdź kolejność")
        
        # Wykopy przed wypełnieniami
        last_wykop = -1
        first_wypelnienie = len(categories)
        
        for i, cat in enumerate(categories):
            if cat == 'wykopy':
                last_wykop = i
            elif cat == 'wypelnienia' and first_wypelnienie == len(categories):
                first_wypelnienie = i
        
        if last_wykop > first_wypelnienie:
            errors.append("Wykopy po wypełnieniach - sprawdź kolejność")
        
        if errors:
            return LogicResult(
                status=LogicStatus.WARNING,
                message="; ".join(errors),
                details={'categories': categories}
            )
        
        return LogicResult(
            status=LogicStatus.OK,
            message="Kolejność robót poprawna"
        )
    
    def validate_jednostki(self, pozycje) -> LogicResult:
        """
        Sprawdza spójność jednostek
        """
        warnings = []
        
        for i, poz in enumerate(pozycje):
            opis = poz.get('opis', '').lower()
            jm = poz.get('jm', '').lower()
            
            # Beton powinien być w m3
            if 'beton' in opis and jm not in ['m3', 'm³']:
                if 'm2' in jm or 'm²' in jm:
                    # OK jeśli jest grubość
                    if not self._extract_grubosc(opis):
                        warnings.append(f"Poz {i+1}: beton w m2 bez grubości")
            
            # Obrzeża/krawężniki w m (metrach bieżących)
            if any(x in opis for x in ['obrzeż', 'krawężnik', 'opornik']):
                if jm not in ['m', 'mb', 'm.b.']:
                    warnings.append(f"Poz {i+1}: obrzeża powinny być w m.b.")
        
        if warnings:
            return LogicResult(
                status=LogicStatus.WARNING,
                message="; ".join(warnings[:5])  # max 5 ostrzeżeń
            )
        
        return LogicResult(
            status=LogicStatus.OK,
            message="Jednostki spójne"
        )
    
    def validate_all(self, pozycje) -> List[LogicResult]:
        """Uruchamia wszystkie walidacje"""
        return [
            self.validate_bilans_mas(pozycje),
            self.validate_kolejnosc_robot(pozycje),
            self.validate_jednostki(pozycje),
        ]
    
    def get_summary(self, pozycje) -> Dict:
        """
        Generuje podsumowanie statystyk kosztorysu
        """
        categories = {}
        total_r, total_m, total_s = 0, 0, 0
        
        for poz in pozycje:
            cat = self.categorize_pozycja(poz)
            if cat not in categories:
                categories[cat] = {'count': 0, 'value': 0}
            categories[cat]['count'] += 1
            categories[cat]['value'] += poz.get('wartosc', 0)
            
            total_r += poz.get('R', 0)
            total_m += poz.get('M', 0)
            total_s += poz.get('S', 0)
        
        total = total_r + total_m + total_s
        
        return {
            'pozycje_count': len(pozycje),
            'categories': categories,
            'structure': {
                'R': round(total_r, 2),
                'M': round(total_m, 2),
                'S': round(total_s, 2),
                'R_pct': round(total_r / total * 100, 1) if total else 0,
                'M_pct': round(total_m / total * 100, 1) if total else 0,
                'S_pct': round(total_s / total * 100, 1) if total else 0,
            }
        }


# ============ TEST ============
if __name__ == "__main__":
    validator = LogicValidator()
    
    # Przykładowe pozycje
    pozycje = [
        {'opis': 'Rozbiórka nawierzchni asfaltowej', 'jm': 'm2', 'ilosc': 144.44, 'R': 100, 'M': 0, 'S': 50},
        {'opis': 'Wykopy mechaniczne głębokości 20 cm', 'jm': 'm3', 'ilosc': 28.89, 'R': 200, 'M': 0, 'S': 150},
        {'opis': 'Podbudowa z kruszywa gr. 10 cm', 'jm': 'm2', 'ilosc': 144.44, 'R': 300, 'M': 800, 'S': 100},
        {'opis': 'Nawierzchnia betonowa C25/30 gr. 20 cm', 'jm': 'm3', 'ilosc': 28.89, 'R': 500, 'M': 2000, 'S': 200},
    ]
    
    print("=== Test bilansu mas ===")
    result = validator.validate_bilans_mas(pozycje)
    print(f"Status: {result.status.value}")
    print(f"Komunikat: {result.message}")
    print(f"Szczegóły: {result.details}")
    
    print("\n=== Test kolejności ===")
    result = validator.validate_kolejnosc_robot(pozycje)
    print(f"Status: {result.status.value}")
    print(f"Komunikat: {result.message}")
    
    print("\n=== Podsumowanie ===")
    summary = validator.get_summary(pozycje)
    print(f"Pozycji: {summary['pozycje_count']}")
    print(f"Struktura: R={summary['structure']['R_pct']}%, M={summary['structure']['M_pct']}%, S={summary['structure']['S_pct']}%")
    
    print("\n✓ LogicValidator OK")
