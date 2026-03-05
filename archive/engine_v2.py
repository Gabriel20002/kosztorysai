# -*- coding: utf-8 -*-
"""
kosztorysAI - Silnik v2.0
Integracja z bazą 688 pozycji KNR + generator ATH
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from difflib import SequenceMatcher

# Ścieżki
BASE_DIR = Path(__file__).parent
KOSZTORYS_DIR = BASE_DIR.parent / "kosztorys"
KNR_DIR = KOSZTORYS_DIR / "knowledge" / "knr"


class BazaKNR:
    """Zaawansowana baza wiedzy KNR z 688+ pozycjami"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._by_description: List[Tuple[str, Dict]] = []
        self._loaded = False
        
    def _load(self):
        """Wczytaj wszystkie pliki KNR"""
        if self._loaded:
            return
            
        if not KNR_DIR.exists():
            print(f"[WARN] Katalog KNR nie istnieje: {KNR_DIR}")
            self._loaded = True
            return
        
        for file in KNR_DIR.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pozycja in data.get('pozycje', []):
                        key = pozycja.get('podstawa', '').strip()
                        if key:
                            self._cache[key] = pozycja
                            # Indeks po opisie dla fuzzy search
                            opis = pozycja.get('opis', '').lower()
                            self._by_description.append((opis, pozycja))
            except Exception as e:
                print(f"[WARN] Błąd wczytywania {file}: {e}")
        
        self._loaded = True
        print(f"[BazaKNR] Wczytano {len(self._cache)} pozycji")
    
    def znajdz_dokladnie(self, knr: str) -> Optional[Dict]:
        """Znajdź pozycję po dokładnym numerze KNR"""
        self._load()
        
        # Normalizuj numer
        knr = knr.strip().upper()
        
        # Dokładne dopasowanie
        if knr in self._cache:
            return self._cache[knr]
        
        # Dopasowanie częściowe (zawiera się)
        for key, data in self._cache.items():
            if knr in key or key in knr:
                return data
        
        return None
    
    def znajdz_podobne(self, opis: str, limit: int = 5) -> List[Dict]:
        """Znajdź pozycje podobne do opisu (fuzzy matching)"""
        self._load()
        
        opis = opis.lower()
        wyniki = []
        
        for cached_opis, pozycja in self._by_description:
            # Oblicz podobieństwo
            ratio = SequenceMatcher(None, opis, cached_opis).ratio()
            
            # Bonus za zawieranie kluczowych słów
            words = opis.split()
            word_matches = sum(1 for w in words if len(w) > 3 and w in cached_opis)
            bonus = word_matches * 0.1
            
            score = ratio + bonus
            
            if score > 0.3:  # Próg minimalny
                wyniki.append((score, pozycja))
        
        # Sortuj po score, zwróć top N
        wyniki.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in wyniki[:limit]]
    
    def szukaj(self, query: str, limit: int = 10) -> List[Dict]:
        """Szukaj po tekście (w KNR i opisie)"""
        self._load()
        
        query = query.lower()
        wyniki = []
        
        for key, pozycja in self._cache.items():
            opis = pozycja.get('opis', '').lower()
            if query in key.lower() or query in opis:
                wyniki.append(pozycja)
                if len(wyniki) >= limit:
                    break
        
        return wyniki
    
    def get_stats(self) -> Dict[str, Any]:
        """Statystyki bazy"""
        self._load()
        
        katalogi = {}
        for data in self._cache.values():
            kat = data.get('katalog', 'unknown')
            katalogi[kat] = katalogi.get(kat, 0) + 1
        
        return {
            'liczba_pozycji': len(self._cache),
            'liczba_katalogow': len(katalogi),
            'katalogi': dict(sorted(katalogi.items(), key=lambda x: -x[1])[:20])
        }


class KosztorysGeneratorV2:
    """Generator kosztorysów v2.0 z bazą 688 KNR"""
    
    def __init__(self):
        self.baza = BazaKNR()
        
        # Domyślne stawki
        self.defaults = {
            'stawka_rg': 35.0,
            'koszty_posrednie': 68.0,
            'zysk': 10.0,
            'vat': 23
        }
    
    def generate_from_przedmiar(
        self,
        przedmiar_positions: List[Dict],
        metadata: Dict = None,
        vat_rate: int = 8,
        kp_rate: float = 68.0,
        zysk_rate: float = 10.0
    ) -> Dict:
        """
        Generuje kosztorys na podstawie przedmiaru.
        Używa bazy 688 KNR do dopasowania cen.
        """
        metadata = metadata or {}
        pozycje = []
        
        for pos in przedmiar_positions:
            knr = pos.get('knr', '')
            opis = pos.get('description', '')
            quantity = float(pos.get('quantity', 1.0) or 1.0)
            unit = pos.get('unit', 'szt')
            
            # Szukaj w bazie KNR
            price_info = self._find_price(knr, opis)
            
            price_unit = price_info['cena']
            value_netto = round(quantity * price_unit, 2)
            
            pozycje.append({
                'lp': len(pozycje) + 1,
                'knr': price_info['knr'] or knr or 'KALKULACJA',
                'description': opis or price_info['opis'],
                'unit': unit,
                'quantity': round(quantity, 3),
                'price_unit': price_unit,
                'price_R': price_info.get('cena_R', 0),
                'price_M': price_info.get('cena_M', price_unit),
                'price_S': price_info.get('cena_S', 0),
                'value_netto': value_netto,
                'source': price_info['source'],
                'confidence': price_info['confidence']
            })
        
        # Obliczenia
        suma_R = sum(p['quantity'] * p['price_R'] for p in pozycje)
        suma_M = sum(p['quantity'] * p['price_M'] for p in pozycje)
        suma_S = sum(p['quantity'] * p['price_S'] for p in pozycje)
        razem_bezposrednie = suma_R + suma_M + suma_S
        
        koszty_posrednie = (suma_R + suma_S) * (kp_rate / 100)
        zysk = (suma_R + suma_S + koszty_posrednie) * (zysk_rate / 100)
        netto = razem_bezposrednie + koszty_posrednie + zysk
        vat = netto * (vat_rate / 100)
        brutto = netto + vat
        
        return {
            'meta': {
                'title': f"KOSZTORYS - {metadata.get('title', 'Przedmiar')}",
                'type': 'Kosztorys ofertowy (projekt)',
                'generated_by': 'kosztorysAI v2.0',
                'generated_at': datetime.now().isoformat(),
                'status': 'DRAFT - wymaga weryfikacji'
            },
            'investment': {
                'description': metadata.get('title', ''),
                'location': metadata.get('location', ''),
                'investor': metadata.get('investor', '')
            },
            'rates': {
                'stawka_rg': self.defaults['stawka_rg'],
                'koszty_posrednie_pct': kp_rate,
                'zysk_pct': zysk_rate,
                'vat_pct': vat_rate
            },
            'positions': pozycje,
            'summary': {
                'suma_R': round(suma_R, 2),
                'suma_M': round(suma_M, 2),
                'suma_S': round(suma_S, 2),
                'razem_bezposrednie': round(razem_bezposrednie, 2),
                'koszty_posrednie': round(koszty_posrednie, 2),
                'zysk': round(zysk, 2),
                'total_netto': round(netto, 2),
                'vat': round(vat, 2),
                'total_brutto': round(brutto, 2),
                'positions_count': len(pozycje),
                'positions_matched': sum(1 for p in pozycje if p['source'] == 'baza_knr'),
                'match_rate': round(sum(1 for p in pozycje if p['source'] == 'baza_knr') / len(pozycje) * 100 if pozycje else 0, 1)
            }
        }
    
    def _find_price(self, knr: str, opis: str) -> Dict:
        """Znajdź cenę dla pozycji"""
        
        # 1. Próbuj dokładne dopasowanie KNR
        if knr:
            found = self.baza.znajdz_dokladnie(knr)
            if found:
                return {
                    'knr': found.get('podstawa', knr),
                    'opis': found.get('opis', opis),
                    'cena': found.get('cena_jednostkowa', 50.0),
                    'cena_R': found.get('cena_R', 0),
                    'cena_M': found.get('cena_M', found.get('cena_jednostkowa', 50.0)),
                    'cena_S': found.get('cena_S', 0),
                    'source': 'baza_knr',
                    'confidence': 0.95
                }
        
        # 2. Fuzzy matching po opisie
        if opis:
            podobne = self.baza.znajdz_podobne(opis, limit=1)
            if podobne:
                found = podobne[0]
                return {
                    'knr': found.get('podstawa', ''),
                    'opis': found.get('opis', opis),
                    'cena': found.get('cena_jednostkowa', 50.0),
                    'cena_R': found.get('cena_R', 0),
                    'cena_M': found.get('cena_M', found.get('cena_jednostkowa', 50.0)),
                    'cena_S': found.get('cena_S', 0),
                    'source': 'fuzzy_match',
                    'confidence': 0.7
                }
        
        # 3. Szacunek na podstawie słów kluczowych
        cena = self._estimate_price(opis)
        return {
            'knr': '',
            'opis': opis,
            'cena': cena,
            'cena_R': cena * 0.3,
            'cena_M': cena * 0.6,
            'cena_S': cena * 0.1,
            'source': 'szacunek',
            'confidence': 0.3
        }
    
    def _estimate_price(self, opis: str) -> float:
        """Szacuj cenę na podstawie słów kluczowych"""
        opis = opis.lower()
        
        # Słowa kluczowe → przedziały cenowe
        keywords = {
            'beton': (200, 600),
            'zbrojenie': (3000, 6000),  # za tonę
            'izolacja': (30, 150),
            'tynk': (25, 80),
            'malowanie': (15, 50),
            'wykopy': (20, 80),
            'fundamenty': (150, 500),
            'dach': (100, 400),
            'okna': (300, 1500),
            'drzwi': (200, 2000),
            'instalacja': (50, 200),
            'elektryka': (40, 150),
        }
        
        for word, (min_p, max_p) in keywords.items():
            if word in opis:
                return (min_p + max_p) / 2
        
        return 50.0  # Domyślna cena


def generate_ath(kosztorys: Dict, filepath: str) -> str:
    """
    Generuje plik ATH z kosztorysu.
    Używa generatora z kosztorys/output/ath_generator.py
    """
    import sys
    sys.path.insert(0, str(KOSZTORYS_DIR))
    
    from output.ath_generator import ATH_Kosztorys, ATH_Element, ATH_Pozycja, ATHGenerator
    
    # Konwertuj do struktur ATH
    k = ATH_Kosztorys(
        nazwa=kosztorys['meta']['title'],
        inwestor=kosztorys['investment'].get('investor', ''),
        adres=kosztorys['investment'].get('location', ''),
        stawka_robocizny=kosztorys['rates'].get('stawka_rg', 35.0),
        koszty_posrednie=kosztorys['rates'].get('koszty_posrednie_pct', 68.0),
        zysk=kosztorys['rates'].get('zysk_pct', 10.0),
        vat=kosztorys['rates'].get('vat_pct', 23),
    )
    
    # Grupuj pozycje w elementy (działy)
    # Na razie jeden dział
    elem = ATH_Element(id=1, numer="1", nazwa="Roboty budowlane")
    
    for i, pos in enumerate(kosztorys['positions'], 1):
        # Parsuj KNR
        knr_parts = pos['knr'].split()
        katalog = ' '.join(knr_parts[:2]) if len(knr_parts) >= 2 else pos['knr']
        numer = knr_parts[2] if len(knr_parts) >= 3 else ''
        
        poz = ATH_Pozycja(
            id=i,
            katalog=katalog,
            numer=numer,
            opis=pos['description'],
            jednostka=pos['unit'],
            ilosc=pos['quantity'],
            cena_R=pos.get('price_R', 0),
            cena_M=pos.get('price_M', pos['price_unit']),
            cena_S=pos.get('price_S', 0),
        )
        elem.pozycje.append(poz)
    
    k.elementy.append(elem)
    
    # Generuj i zapisz
    gen = ATHGenerator(k)
    gen.save(filepath)
    
    return filepath


# Test
if __name__ == '__main__':
    gen = KosztorysGeneratorV2()
    
    print("=== Statystyki bazy KNR ===")
    stats = gen.baza.get_stats()
    print(f"Pozycji: {stats['liczba_pozycji']}")
    print(f"Katalogów: {stats['liczba_katalogow']}")
    print("\nTop katalogi:")
    for kat, count in list(stats['katalogi'].items())[:10]:
        print(f"  {kat}: {count}")
    
    print("\n=== Test wyszukiwania ===")
    wyniki = gen.baza.szukaj("fundament", limit=5)
    for w in wyniki:
        print(f"  {w.get('podstawa')}: {w.get('opis', '')[:50]}... | {w.get('cena_jednostkowa', 0):.2f} zł")
