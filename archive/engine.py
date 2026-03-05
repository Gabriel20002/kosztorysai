"""
kosztorysAI - Silnik generowania projektów kosztorysów
MVP / Proof of Concept
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ładowanie bazy KNR
BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "knr_base.json", "r", encoding="utf-8") as f:
    KNR_BASE = json.load(f)

class KosztorysGenerator:
    """Generator projektów kosztorysów budowlanych"""
    
    def __init__(self):
        self.positions = {p["id"]: p for p in KNR_BASE["positions"]}
        self.knr_lookup = {p["knr"]: p for p in KNR_BASE["positions"]}
        self.categories = KNR_BASE["categories"]
        self.defaults = KNR_BASE["meta"]["default_rates"]
    
    def generate_from_przedmiar(
        self,
        przedmiar_positions: list,
        metadata: dict = None,
        vat_rate: int = 8
    ) -> dict:
        """
        Generuje kosztorys na podstawie sparsowanego przedmiaru.
        
        Args:
            przedmiar_positions: Lista pozycji z parsera PDF
            metadata: Metadane z przedmiaru
            vat_rate: Stawka VAT
        
        Returns:
            dict z kosztorysem
        """
        
        metadata = metadata or {}
        
        selected_positions = []
        
        for pos in przedmiar_positions:
            # Znajdź cenę dla KNR
            price_info = self._find_price_for_knr(pos.get('knr', ''), pos.get('description', ''))
            
            quantity = pos.get('quantity') or 1.0
            unit = pos.get('unit') or 'm2'
            price_unit = price_info.get('price', 50.0)  # Domyślna cena jeśli nie znaleziono
            
            selected_positions.append({
                "lp": len(selected_positions) + 1,
                "knr": pos.get('knr', 'ESTYM'),
                "description": pos.get('description', 'Pozycja kosztorysowa'),
                "note": price_info.get('note', ''),
                "unit": unit,
                "quantity": round(quantity, 2),
                "price_unit": price_unit,
                "value_netto": round(quantity * price_unit, 2),
                "category": price_info.get('category', 'Roboty budowlane'),
                "price_source": price_info.get('source', 'szacunek')
            })
        
        # Oblicz sumy
        total_netto = sum(p["value_netto"] for p in selected_positions)
        total_vat = total_netto * (vat_rate / 100)
        total_brutto = total_netto + total_vat
        
        return {
            "meta": {
                "title": f"KOSZTORYS - {metadata.get('title', 'Przedmiar')}",
                "type": "Kosztorys na podstawie przedmiaru (projekt do weryfikacji)",
                "generated_by": "kosztorysAI v1.0-mvp",
                "generated_at": datetime.now().isoformat(),
                "status": "DRAFT - wymaga weryfikacji kosztorysanta"
            },
            "investment": {
                "description": metadata.get('title', 'Na podstawie przedmiaru'),
                "object_type": "przedmiar",
                "area_m2": None,
                "location": metadata.get('location', 'Polska'),
                "investor": metadata.get('investor', 'Inwestor')
            },
            "rates": {
                "labor_rate": self.defaults["labor_rate"],
                "indirect_costs_pct": self.defaults["indirect_costs"],
                "profit_pct": self.defaults["profit"],
                "vat_pct": vat_rate
            },
            "positions": selected_positions,
            "summary": {
                "total_netto": round(total_netto, 2),
                "vat": round(total_vat, 2),
                "total_brutto": round(total_brutto, 2),
                "positions_count": len(selected_positions),
                "positions_with_price": sum(1 for p in selected_positions if p['price_source'] == 'baza'),
                "positions_estimated": sum(1 for p in selected_positions if p['price_source'] != 'baza')
            }
        }
    
    def _find_price_for_knr(self, knr: str, description: str) -> dict:
        """Szuka ceny dla pozycji KNR"""
        
        # Normalizuj KNR
        knr_clean = knr.upper().replace('  ', ' ').strip()
        
        # Dokładne dopasowanie
        if knr_clean in self.knr_lookup:
            pos = self.knr_lookup[knr_clean]
            return {
                'price': pos['price_unit'],
                'category': self.categories.get(pos['category'], {}).get('name', pos['category']),
                'source': 'baza',
                'note': 'Cena z bazy KNR'
            }
        
        # Częściowe dopasowanie (pierwsze cyfry KNR)
        knr_prefix = knr_clean[:10] if len(knr_clean) > 10 else knr_clean
        for base_knr, pos in self.knr_lookup.items():
            if base_knr.startswith(knr_prefix[:7]):
                return {
                    'price': pos['price_unit'],
                    'category': self.categories.get(pos['category'], {}).get('name', pos['category']),
                    'source': 'podobne',
                    'note': f'Cena podobnej pozycji ({base_knr})'
                }
        
        # Szacowanie na podstawie opisu
        desc_lower = description.lower()
        
        price_estimates = {
            'wykop': 15.0, 'ziemne': 15.0,
            'fundament': 500.0, 'ława': 500.0, 'stopa': 500.0,
            'ścian': 150.0, 'mur': 150.0, 'bloczk': 150.0,
            'strop': 200.0,
            'dach': 150.0, 'pokryc': 120.0, 'dachów': 120.0,
            'tynk': 50.0, 'gładź': 30.0,
            'malowa': 15.0, 'farb': 15.0,
            'posadzk': 100.0, 'płyt': 100.0, 'gres': 120.0,
            'okn': 600.0, 'drzwi': 500.0, 'stolark': 500.0,
            'izolac': 80.0, 'ociepl': 120.0, 'styrop': 100.0,
            'elektr': 50.0, 'przewod': 20.0, 'gniazd': 60.0,
            'wod': 50.0, 'kanal': 80.0, 'rur': 50.0,
            'grzejnik': 800.0, 'c.o.': 100.0,
        }
        
        for keyword, price in price_estimates.items():
            if keyword in desc_lower:
                return {
                    'price': price,
                    'category': 'Roboty budowlane',
                    'source': 'szacunek',
                    'note': f'Cena szacunkowa ({keyword})'
                }
        
        # Domyślna cena
        return {
            'price': 50.0,
            'category': 'Roboty budowlane',
            'source': 'domyslna',
            'note': 'Cena domyślna - wymaga weryfikacji'
        }
        
    def generate(
        self,
        description: str,
        object_type: str = "auto",
        area_m2: float = None,
        investor_name: str = "Inwestor",
        location: str = "Polska",
        vat_rate: int = 8
    ) -> dict:
        """
        Generuje projekt kosztorysu na podstawie opisu.
        
        Args:
            description: Opis inwestycji
            object_type: Typ obiektu (dom, hala, remont, etc.) lub "auto"
            area_m2: Powierzchnia w m2 (None = auto-detect)
            investor_name: Nazwa inwestora
            location: Lokalizacja
            vat_rate: Stawka VAT (8 lub 23)
        
        Returns:
            dict z projektem kosztorysu
        """
        
        # Auto-detect typu i powierzchni z opisu
        if object_type == "auto":
            object_type = self._detect_object_type(description)
        
        if area_m2 is None:
            area_m2 = self._detect_area(description, object_type)
        
        # Dobierz pozycje na podstawie typu obiektu
        selected_positions = self._select_positions(object_type, area_m2, description)
        
        # Oblicz wartości
        total_netto = sum(p["value_netto"] for p in selected_positions)
        total_vat = total_netto * (vat_rate / 100)
        total_brutto = total_netto + total_vat
        
        return {
            "meta": {
                "title": f"PROJEKT KOSZTORYSU - {description[:50]}",
                "type": "Kosztorys inwestorski (projekt do weryfikacji)",
                "generated_by": "kosztorysAI v1.0-mvp",
                "generated_at": datetime.now().isoformat(),
                "status": "DRAFT - wymaga weryfikacji kosztorysanta"
            },
            "investment": {
                "description": description,
                "object_type": object_type,
                "area_m2": area_m2,
                "location": location,
                "investor": investor_name
            },
            "rates": {
                "labor_rate": self.defaults["labor_rate"],
                "indirect_costs_pct": self.defaults["indirect_costs"],
                "profit_pct": self.defaults["profit"],
                "vat_pct": vat_rate
            },
            "positions": selected_positions,
            "summary": {
                "total_netto": round(total_netto, 2),
                "vat": round(total_vat, 2),
                "total_brutto": round(total_brutto, 2),
                "positions_count": len(selected_positions)
            }
        }
    
    def _detect_object_type(self, description: str) -> str:
        """Wykrywa typ obiektu z opisu"""
        desc = description.lower()
        
        if any(w in desc for w in ["lazienk", "łazienk", "wc", "toalet"]):
            return "lazienka"
        elif any(w in desc for w in ["kuchni", "kuchnia"]):
            return "kuchnia"
        elif any(w in desc for w in ["remont", "malowani", "odnowien"]):
            return "remont"
        elif any(w in desc for w in ["hala", "magazyn", "hal "]):
            return "hala"
        elif any(w in desc for w in ["biur", "biurow"]):
            return "biurowiec"
        elif any(w in desc for w in ["elektr", "instalacja elektr"]):
            return "instalacja_elektryczna"
        elif any(w in desc for w in ["wod-kan", "sanitar", "hydraul", "c.o.", "ogrzewan"]):
            return "instalacja_sanitarna"
        elif any(w in desc for w in ["garaz", "garaż"]):
            return "garaz"
        elif any(w in desc for w in ["mieszkan"]):
            return "remont_mieszkania"
        else:
            return "dom"
    
    def _detect_area(self, description: str, object_type: str) -> float:
        """Wykrywa powierzchnię z opisu lub zwraca domyślną"""
        import re
        
        # Szukaj wzorców typu "120m2", "120 m2", "120m²"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*m[2²]',
            r'(\d+(?:\.\d+)?)\s*mkw',
            r'(\d+(?:\.\d+)?)\s*metrow',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                return float(match.group(1))
        
        # Domyślne powierzchnie dla typów
        defaults = {
            "lazienka": 6,
            "kuchnia": 12,
            "remont": 50,
            "remont_mieszkania": 60,
            "dom": 120,
            "hala": 500,
            "magazyn": 500,
            "biurowiec": 300,
            "garaz": 25,
            "instalacja_elektryczna": 100,
            "instalacja_sanitarna": 100,
        }
        
        return defaults.get(object_type, 100)
    
    def _select_positions(self, object_type: str, area_m2: float, description: str) -> list:
        """Dobiera pozycje KNR na podstawie typu obiektu"""
        
        positions = []
        desc_lower = description.lower()
        
        # DOMY I BUDYNKI MIESZKALNE
        if object_type in ["dom", "budynek_mieszkalny"]:
            positions.extend(self._get_house_positions(area_m2, desc_lower))
        
        # HALE I MAGAZYNY
        elif object_type in ["hala", "magazyn"]:
            positions.extend(self._get_warehouse_positions(area_m2, desc_lower))
        
        # REMONTY
        elif object_type in ["remont", "remont_mieszkania"]:
            positions.extend(self._get_renovation_positions(area_m2, desc_lower))
        
        # ŁAZIENKA
        elif object_type == "lazienka":
            positions.extend(self._get_bathroom_positions(area_m2))
        
        # KUCHNIA
        elif object_type == "kuchnia":
            positions.extend(self._get_kitchen_positions(area_m2))
        
        # GARAŻ
        elif object_type == "garaz":
            positions.extend(self._get_garage_positions(area_m2))
        
        # INSTALACJE
        elif object_type in ["instalacja_elektryczna", "instalacja_sanitarna"]:
            positions.extend(self._get_installation_positions(area_m2, object_type))
        
        # DOMYŚLNIE - pełny zakres
        else:
            positions.extend(self._get_house_positions(area_m2, desc_lower))
        
        return positions
    
    def _get_house_positions(self, area_m2: float, desc: str) -> list:
        """Pozycje dla domu jednorodzinnego"""
        
        # Współczynniki szacunkowe
        foundation_m3 = area_m2 * 0.15  # ławy fundamentowe
        walls_m2 = area_m2 * 2.8  # ściany (obwód * wysokość)
        roof_m2 = area_m2 * 1.3  # dach (ze spadkami)
        
        positions = [
            # ROBOTY ZIEMNE
            self._make_position("Z001", area_m2 * 0.8, "Pomiary geodezyjne"),
            self._make_position("Z002", area_m2 * 1.1, "Zdjęcie humusu"),
            self._make_position("Z003", foundation_m3 * 3, "Wykopy mechaniczne"),
            self._make_position("Z004", foundation_m3 * 0.3, "Wykopy ręczne (doczyszczenie)"),
            
            # FUNDAMENTY
            self._make_position("F001", area_m2, "Podkład betonowy"),
            self._make_position("F002", foundation_m3, "Ławy fundamentowe"),
            self._make_position("F005", area_m2 * 0.4, "Ściany fundamentowe"),
            self._make_position("I001", area_m2, "Izolacja pozioma fundamentów"),
            self._make_position("I002", area_m2 * 0.5, "Izolacja pionowa fundamentów"),
            
            # ŚCIANY
            self._make_position("S002", walls_m2 * 0.7, "Ściany nośne zewnętrzne"),
            self._make_position("S001", walls_m2 * 0.3, "Ściany nośne wewnętrzne"),
            self._make_position("S004", area_m2 * 0.8, "Ścianki działowe"),
            self._make_position("S005", 25, "Nadproża"),
            self._make_position("S006", area_m2 * 0.08, "Wieńce"),
            
            # STROP
            self._make_position("ST002", area_m2, "Strop"),
            
            # DACH
            self._make_position("D001", roof_m2 * 0.08, "Więźba dachowa"),
            self._make_position("D005", roof_m2, "Ołacenie"),
            self._make_position("D003", roof_m2, "Pokrycie dachowe"),
            self._make_position("D004", roof_m2 * 0.15, "Obróbki blacharskie"),
            self._make_position("I004", roof_m2, "Ocieplenie poddasza"),
            
            # STOLARKA
            self._make_position("ST_O001", area_m2 * 0.15, "Okna"),
            self._make_position("ST_O002", 4, "Drzwi zewnętrzne"),
            self._make_position("ST_O003", 8, "Drzwi wewnętrzne"),
            
            # TYNKI I WYKOŃCZENIE
            self._make_position("T001", walls_m2 + area_m2, "Tynki wewnętrzne"),
            self._make_position("T003", walls_m2 + area_m2, "Gładzie"),
            self._make_position("T004", walls_m2 + area_m2, "Malowanie"),
            
            # POSADZKI
            self._make_position("P001", area_m2, "Podkład pod posadzki"),
            self._make_position("P004", area_m2, "Wylewka"),
            self._make_position("P002", area_m2 * 0.3, "Płytki (łazienki, kuchnia)"),
            
            # ELEWACJA
            self._make_position("I003", walls_m2 * 0.7, "Ocieplenie ścian"),
            self._make_position("E002", walls_m2 * 0.7, "Tynk elewacyjny"),
            
            # INSTALACJE (uproszczone)
            self._make_position("INS001", area_m2 * 0.5, "Kanalizacja wewnętrzna"),
            self._make_position("INS002", area_m2 * 0.8, "Instalacja wodna"),
            self._make_position("INS003", int(area_m2 / 15), "Grzejniki"),
            self._make_position("INE001", area_m2 * 3, "Przewody elektryczne"),
            self._make_position("INE002", int(area_m2 / 5), "Gniazda"),
            self._make_position("INE004", int(area_m2 / 8), "Oprawy oświetleniowe"),
        ]
        
        return [p for p in positions if p is not None]
    
    def _get_warehouse_positions(self, area_m2: float, desc: str) -> list:
        """Pozycje dla hali/magazynu"""
        
        positions = [
            self._make_position("Z002", area_m2 * 1.2, "Zdjęcie humusu"),
            self._make_position("Z003", area_m2 * 0.3, "Wykopy"),
            self._make_position("F001", area_m2, "Podkład betonowy"),
            self._make_position("F002", area_m2 * 0.2, "Ławy fundamentowe"),
            self._make_position("F003", area_m2 * 0.05, "Stopy fundamentowe"),
            self._make_position("P001", area_m2, "Posadzka przemysłowa"),
            self._make_position("D003", area_m2 * 1.1, "Pokrycie dachowe"),
            self._make_position("ST_O004", area_m2 * 0.02, "Bramy"),
            self._make_position("INE001", area_m2 * 1.5, "Instalacja elektryczna"),
            self._make_position("INE004", int(area_m2 / 20), "Oświetlenie"),
        ]
        
        return [p for p in positions if p is not None]
    
    def _get_renovation_positions(self, area_m2: float, desc: str) -> list:
        """Pozycje dla remontu"""
        
        walls_m2 = area_m2 * 2.5
        
        positions = [
            self._make_position("T001", walls_m2, "Tynki/naprawy tynków"),
            self._make_position("T003", walls_m2, "Gładzie"),
            self._make_position("T004", walls_m2, "Malowanie"),
            self._make_position("P004", area_m2, "Wylewka samopoziomująca"),
            self._make_position("P002", area_m2 * 0.3, "Płytki"),
        ]
        
        if "łazienk" in desc or "wc" in desc:
            positions.extend([
                self._make_position("INS004", 1, "Umywalka"),
                self._make_position("INS005", 1, "WC"),
            ])
        
        if "elektryk" in desc or "gniazdka" in desc:
            positions.extend([
                self._make_position("INE001", area_m2 * 2, "Przewody"),
                self._make_position("INE002", int(area_m2 / 4), "Gniazda"),
            ])
        
        return [p for p in positions if p is not None]
    
    def _get_bathroom_positions(self, area_m2: float) -> list:
        """Pozycje dla łazienki"""
        
        walls_m2 = area_m2 * 2.5
        
        return [
            self._make_position("T001", walls_m2, "Tynki"),
            self._make_position("P002", area_m2, "Płytki podłogowe"),
            self._make_position("P002", walls_m2, "Płytki ścienne"),
            self._make_position("P003", (area_m2 ** 0.5) * 4, "Cokolik"),
            self._make_position("INS001", 8, "Kanalizacja"),
            self._make_position("INS002", 12, "Woda"),
            self._make_position("INS004", 1, "Umywalka"),
            self._make_position("INS005", 1, "WC"),
            self._make_position("INE002", 2, "Gniazda"),
            self._make_position("INE004", 2, "Oświetlenie"),
        ]
    
    def _get_kitchen_positions(self, area_m2: float) -> list:
        """Pozycje dla remontu kuchni"""
        
        walls_m2 = area_m2 * 2.5
        
        return [
            self._make_position("T001", walls_m2 * 0.5, "Tynki/naprawy"),
            self._make_position("T003", walls_m2, "Gładzie"),
            self._make_position("T004", walls_m2 * 0.6, "Malowanie"),
            self._make_position("P002", area_m2, "Płytki podłogowe"),
            self._make_position("P002", walls_m2 * 0.4, "Płytki ścienne (fartuch)"),
            self._make_position("INS001", 6, "Kanalizacja"),
            self._make_position("INS002", 10, "Woda"),
            self._make_position("INE002", 6, "Gniazda"),
            self._make_position("INE004", 3, "Oświetlenie"),
        ]
    
    def _get_garage_positions(self, area_m2: float) -> list:
        """Pozycje dla garażu"""
        
        walls_m2 = (area_m2 ** 0.5) * 4 * 2.5  # obwód * wysokość
        
        return [
            self._make_position("Z002", area_m2 * 1.2, "Zdjęcie humusu"),
            self._make_position("Z003", area_m2 * 0.4, "Wykopy"),
            self._make_position("F001", area_m2, "Podkład betonowy"),
            self._make_position("F002", area_m2 * 0.15, "Ławy fundamentowe"),
            self._make_position("S001", walls_m2, "Ściany"),
            self._make_position("P001", area_m2, "Posadzka betonowa"),
            self._make_position("D003", area_m2 * 1.1, "Pokrycie dachowe"),
            self._make_position("ST_O004", 6, "Brama garażowa"),
            self._make_position("ST_O002", 2, "Drzwi"),
            self._make_position("T002", walls_m2, "Tynk zewnętrzny"),
            self._make_position("INE001", area_m2 * 1.5, "Instalacja elektryczna"),
            self._make_position("INE002", 4, "Gniazda"),
            self._make_position("INE004", 4, "Oświetlenie"),
        ]
    
    def _get_installation_positions(self, area_m2: float, inst_type: str) -> list:
        """Pozycje dla instalacji"""
        
        if inst_type == "instalacja_elektryczna":
            return [
                self._make_position("INE001", area_m2 * 3, "Przewody"),
                self._make_position("INE002", int(area_m2 / 4), "Gniazda"),
                self._make_position("INE003", int(area_m2 / 6), "Łączniki"),
                self._make_position("INE004", int(area_m2 / 8), "Oprawy"),
                self._make_position("INE005", 1, "Rozdzielnica"),
            ]
        else:  # sanitarna
            return [
                self._make_position("INS001", area_m2 * 0.5, "Kanalizacja"),
                self._make_position("INS002", area_m2 * 0.8, "Woda"),
                self._make_position("INS003", int(area_m2 / 15), "Grzejniki"),
                self._make_position("INS004", 2, "Umywalki"),
                self._make_position("INS005", 2, "WC"),
            ]
    
    def _make_position(self, pos_id: str, quantity: float, note: str = "") -> Optional[dict]:
        """Tworzy pozycję kosztorysową"""
        
        if pos_id not in self.positions:
            return None
        
        pos = self.positions[pos_id]
        quantity = round(quantity, 2)
        value = round(quantity * pos["price_unit"], 2)
        
        return {
            "lp": 0,  # zostanie wypełnione później
            "knr": pos["knr"],
            "description": pos["name"],
            "note": note,
            "unit": pos["unit"],
            "quantity": quantity,
            "price_unit": pos["price_unit"],
            "value_netto": value,
            "category": self.categories.get(pos["category"], {}).get("name", pos["category"])
        }


def format_kosztorys_text(kosztorys: dict) -> str:
    """Formatuje kosztorys jako tekst do wyświetlenia"""
    
    lines = []
    lines.append("=" * 80)
    lines.append(kosztorys["meta"]["title"])
    lines.append("=" * 80)
    lines.append(f"Status: {kosztorys['meta']['status']}")
    lines.append(f"Wygenerowano: {kosztorys['meta']['generated_at'][:10]}")
    lines.append("")
    
    lines.append("DANE INWESTYCJI:")
    lines.append(f"  Opis: {kosztorys['investment']['description']}")
    lines.append(f"  Powierzchnia: {kosztorys['investment']['area_m2']} m²")
    lines.append(f"  Lokalizacja: {kosztorys['investment']['location']}")
    lines.append(f"  Inwestor: {kosztorys['investment']['investor']}")
    lines.append("")
    
    lines.append("STAWKI I NARZUTY:")
    lines.append(f"  Stawka r-g: {kosztorys['rates']['labor_rate']} zł")
    lines.append(f"  Koszty pośrednie: {kosztorys['rates']['indirect_costs_pct']}%")
    lines.append(f"  Zysk: {kosztorys['rates']['profit_pct']}%")
    lines.append(f"  VAT: {kosztorys['rates']['vat_pct']}%")
    lines.append("")
    
    lines.append("-" * 80)
    lines.append("POZYCJE KOSZTORYSOWE:")
    lines.append("-" * 80)
    
    current_category = None
    lp = 0
    
    for pos in kosztorys["positions"]:
        if pos["category"] != current_category:
            current_category = pos["category"]
            lines.append(f"\n### {current_category.upper()} ###\n")
        
        lp += 1
        lines.append(f"{lp:3}. {pos['knr']}")
        lines.append(f"     {pos['description']}")
        if pos["note"]:
            lines.append(f"     ({pos['note']})")
        lines.append(f"     {pos['quantity']} {pos['unit']} × {pos['price_unit']:.2f} zł = {pos['value_netto']:.2f} zł")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("PODSUMOWANIE:")
    lines.append(f"  Liczba pozycji: {kosztorys['summary']['positions_count']}")
    lines.append(f"  Wartość netto:  {kosztorys['summary']['total_netto']:>12,.2f} zł")
    lines.append(f"  VAT {kosztorys['rates']['vat_pct']}%:        {kosztorys['summary']['vat']:>12,.2f} zł")
    lines.append(f"  RAZEM BRUTTO:   {kosztorys['summary']['total_brutto']:>12,.2f} zł")
    lines.append("=" * 80)
    lines.append("")
    lines.append("!!! UWAGA: To jest PROJEKT kosztorysu wymagajacy weryfikacji !!!")
    lines.append("    Ilosci i ceny sa szacunkowe. Nalezy sprawdzic z dokumentacja.")
    
    return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import sys
    import io
    
    # Fix Windows encoding
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n[kosztorysAI] Generator projektow kosztorysow\n")
    
    generator = KosztorysGenerator()
    
    # Przykładowe generowanie
    if len(sys.argv) > 1:
        desc = " ".join(sys.argv[1:])
    else:
        desc = "Dom jednorodzinny parterowy z poddaszem użytkowym 150m2"
    
    kosztorys = generator.generate(
        description=desc,
        object_type="auto",  # auto-detekcja typu
        area_m2=None,        # auto-detekcja powierzchni
        investor_name="Inwestor",
        location="Polska"
    )
    
    print(format_kosztorys_text(kosztorys))
