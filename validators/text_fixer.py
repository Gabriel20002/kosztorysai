# -*- coding: utf-8 -*-
"""
TextFixer - naprawa błędów OCR i kodowania cp1250

Wzorce OCR są ładowane z config/ocr_patterns.json (jeśli istnieje).
"""

import re
import json
import os
from pathlib import Path
from difflib import SequenceMatcher


def _load_ocr_config():
    """Ładuje konfigurację OCR z pliku JSON lub zwraca domyślne"""
    config_path = Path(__file__).parent.parent / "config" / "ocr_patterns.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Blad ladowania ocr_patterns.json: {e}, uzywam domyslnych")
    
    # Domyślne wartości (fallback)
    return {
        "ocr_patterns": {
            r'otiße?\d+': 'odległość do {} km',
            r'odleg[łl]o[śs][ćc]\s*\d+': 'odległość do {} km',
            r'przem\d+': 'przemysłowa',
            r'cermentow': 'cementow',
        },
        "rms_separators": [
            r'--\s*R\s*--', r'-+\s*R\s*-*',
            r'--\s*M\s*--', r'-+\s*M\s*-*',
            r'--\s*S\s*--', r'-+\s*S\s*-*',
        ],
        "cp1250_fix": {
            'ą': 'ą', 'ć': 'ć', 'ę': 'ę', 'ł': 'ł', 'ń': 'ń',
            'ó': 'ó', 'ś': 'ś', 'ź': 'ź', 'ż': 'ż',
            '¹': 'ą', '³': 'ł', '¿': 'ż', '£': 'Ł',
            'ďż˝': '', '�': '',
        },
        "unit_mapping": {
            'm2': 'm2', 'm²': 'm2', 'm3': 'm3', 'm³': 'm3',
            'm': 'm', 'mb': 'm', 'szt': 'szt.', 'szt.': 'szt.',
            'kpl': 'kpl.', 'kpl.': 'kpl.', 'kg': 'kg', 't': 't',
            'r-g': 'r-g', 'rg': 'r-g', 'm-g': 'm-g',
        }
    }


# Załaduj konfigurację raz przy imporcie modułu
_CONFIG = _load_ocr_config()


class TextFixer:
    """Naprawia błędy OCR i kodowania w tekstach kosztorysowych"""
    
    # Wzorce ładowane z konfiguracji
    OCR_PATTERNS = _CONFIG.get("ocr_patterns", {})
    RMS_SEPARATORS = _CONFIG.get("rms_separators", [])
    CP1250_FIX = _CONFIG.get("cp1250_fix", {})
    UNIT_MAPPING = _CONFIG.get("unit_mapping", {})
    
    def __init__(self, baza_wzorcow_path=None):
        """
        Args:
            baza_wzorcow_path: ścieżka do pozycje_wzorcowe.json
        """
        self.wzorce = []
        if baza_wzorcow_path and os.path.exists(baza_wzorcow_path):
            with open(baza_wzorcow_path, 'r', encoding='utf-8') as f:
                self.wzorce = json.load(f)
    
    def fix_encoding(self, text):
        """Naprawia błędy kodowania cp1250"""
        if not text:
            return text
        
        for bad, good in self.CP1250_FIX.items():
            text = text.replace(bad, good)
        
        # Usuń niewidoczne znaki
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        
        return text
    
    def fix_number(self, text):
        """
        Naprawia błędne liczby typu "0.428.89" → "28.89"
        """
        if not text:
            return text
        
        text = str(text)
        
        # Wzorzec: liczba z podwójną kropką
        # "0.428.89" → prawdopodobnie "28.89"
        pattern = r'(\d+)\.(\d+)\.(\d+)'
        
        def fix_match(m):
            p1, p2, p3 = m.groups()
            # Heurystyka: "0.4" na początku to prawdopodobnie śmieć OCR
            # "0.428.89" → chcemy "28.89"
            if p1 == '0':
                # Sprawdź czy p2 ma sens jako całość
                if len(p2) > 2:  # np "428" - prawdopodobnie "28" z prefiksem
                    return f"{p2[-2:]}.{p3}"  # weź ostatnie 2 cyfry
                return f"{p2}.{p3}"
            # Może to format tysiąca: "1.234.56" → "1234.56"
            return f"{p1}{p2}.{p3}"
        
        return re.sub(pattern, fix_match, text)
    
    def extract_number(self, text):
        """Wyciąga liczbę z tekstu, naprawiając błędy"""
        if isinstance(text, (int, float)):
            return float(text)
        
        text = self.fix_number(str(text))
        
        # Znajdź pierwszą sensowną liczbę
        # Obsłuż format polski (przecinek) i angielski (kropka)
        text = text.replace(',', '.')
        text = text.replace(' ', '')
        
        match = re.search(r'-?\d+\.?\d*', text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return 0.0
    
    def fix_opis(self, text):
        """Naprawia opis pozycji używając wzorców OCR i bazy"""
        if not text:
            return text
        
        text = self.fix_encoding(text)
        
        # Zastosuj wzorce OCR
        for pattern, replacement in self.OCR_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Wyciągnij liczbę z dopasowania
                num_match = re.search(r'\d+', match.group())
                if num_match and '{}' in replacement:
                    text = re.sub(pattern, replacement.format(num_match.group()), text, flags=re.IGNORECASE)
                else:
                    text = re.sub(pattern, replacement.replace('{}', ''), text, flags=re.IGNORECASE)
        
        # Spróbuj dopasować do wzorca z bazy (jeśli tekst jest bardzo uszkodzony)
        if self._is_corrupted(text) and self.wzorce:
            best_match = self._find_best_match(text)
            if best_match:
                return best_match
        
        return text.strip()
    
    def _is_corrupted(self, text):
        """Sprawdza czy tekst wygląda na uszkodzony"""
        if not text:
            return True
        
        # Dużo znaków specjalnych
        special_ratio = len(re.findall(r'[^\w\s\.,\-()łąęśżźćńóŁĄĘŚŻŹĆŃÓ]', text)) / max(len(text), 1)
        if special_ratio > 0.15:
            return True
        
        # Bardzo krótki
        if len(text) < 10:
            return True
        
        # Brak samogłosek (prawdopodobnie śmieci)
        if not re.search(r'[aeiouyąęó]', text, re.IGNORECASE):
            return True
        
        return False
    
    def _find_best_match(self, text, threshold=0.5):
        """Znajduje najlepsze dopasowanie w bazie wzorców"""
        if not self.wzorce:
            return None
        
        best_score = 0
        best_match = None
        
        # Normalizuj tekst do porównania
        text_norm = self._normalize_for_compare(text)
        
        for wzor in self.wzorce:
            if isinstance(wzor, dict):
                wzor_text = wzor.get('opis', '')
            else:
                wzor_text = str(wzor)
            
            wzor_norm = self._normalize_for_compare(wzor_text)
            
            # Similarity score
            score = SequenceMatcher(None, text_norm, wzor_norm).ratio()
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = wzor_text
        
        return best_match
    
    def _normalize_for_compare(self, text):
        """Normalizuje tekst do porównania (lowercase, bez liczb, bez znaków spec.)"""
        text = text.lower()
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = ' '.join(text.split())
        return text
    
    def fix_jednostka(self, jm):
        """Naprawia jednostkę miary, w tym hybrydowe błędy OCR"""
        if not jm:
            return 'm2'
        
        # Najpierw zamień superscript PRZED fix_encoding (bo ³ -> ł w cp1250)
        jm = jm.replace('\u00b2', '2').replace('\u00b3', '3')  # ² -> 2, ³ -> 3
        jm = self.fix_encoding(jm).strip().lower()
        
        # Napraw hybrydowe jednostki OCR
        # "r-/gm2" → "r-g/m2" (norma zużycia)
        # "r-g/m2", "r-g/m3" → to normy, wyciągnij jednostkę bazową
        hybrid_match = re.search(r'r-?/?g\s*/?\s*(m2|m3|m|szt)', jm)
        if hybrid_match:
            return hybrid_match.group(1)
        
        # "m-g/m2" podobnie
        hybrid_match2 = re.search(r'm-?g\s*/?\s*(m2|m3|m|szt)', jm)
        if hybrid_match2:
            return hybrid_match2.group(1)
        
        # Usuń śmieci wokół jednostki
        jm = re.sub(r'[^\w\d\.\-²³]', '', jm)
        
        # Mapowanie z konfiguracji (config/ocr_patterns.json)
        return self.UNIT_MAPPING.get(jm, jm)
    
    def normalize_rms_separator(self, text):
        """
        Normalizuje różne formaty separatorów R/M/S
        "--R-", "- R --", "--R--" → "-- R --"
        """
        if not text:
            return text
        
        # Normalizuj separatory R
        text = re.sub(r'-+\s*R\s*-*', '-- R --', text)
        # Normalizuj separatory M
        text = re.sub(r'-+\s*M\s*-*', '-- M --', text)
        # Normalizuj separatory S
        text = re.sub(r'-+\s*S\s*-*', '-- S --', text)
        
        return text
    
    def extract_rms_section(self, text):
        """
        Wyciąga sekcje R/M/S z tekstu, obsługując różne formaty
        Zwraca dict {'R': [...], 'M': [...], 'S': [...]}
        """
        result = {'R': [], 'M': [], 'S': []}
        
        # Normalizuj separatory
        text = self.normalize_rms_separator(text)
        
        # Podziel na sekcje
        current_section = None
        lines = text.split('\n')
        
        for line in lines:
            # Sprawdź czy to nagłówek sekcji
            if '-- R --' in line:
                current_section = 'R'
                # Usuń nagłówek z linii i sprawdź czy jest treść
                line = line.replace('-- R --', '').strip()
                if not line:
                    continue
            elif '-- M --' in line:
                current_section = 'M'
                line = line.replace('-- M --', '').strip()
                if not line:
                    continue
            elif '-- S --' in line:
                current_section = 'S'
                line = line.replace('-- S --', '').strip()
                if not line:
                    continue
            elif 'Razem' in line or 'RAZEM' in line:
                current_section = None
                continue
            
            if current_section and line.strip():
                result[current_section].append(line.strip())
        
        return result
    
    def fix_podstawa(self, podstawa):
        """Naprawia numer podstawy KNR"""
        if not podstawa:
            return ''

        podstawa = self.fix_encoding(podstawa).upper().strip()

        # Format Zuzia ze ukośnikami (KNR N/M/K) — zachowaj bez normalizacji
        if '/' in podstawa:
            return podstawa

        # Format standardowy z myślnikami: "KNR 2-31 0703-03"
        match = re.search(r'(KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\s*(\d+)-(\d+)\s*(\d{4})-(\d+)', podstawa, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}-{match.group(3)} {match.group(4)}-{match.group(5)[:2]}"

        # Format z myślnikiem w katalogu, bez w czynności: "KNR 2-31 070303"
        match = re.search(r'(KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\s*(\d+)-(\d+)\s*(\d{6,8})', podstawa, re.IGNORECASE)
        if match:
            num = match.group(4)[:6]
            return f"{match.group(1)} {match.group(2)}-{match.group(3)} {num[:4]}-{num[4:6]}"

        # Format Norma STD: "KNR 201 012502" → "KNR 2-01 0125-02"
        # Katalog 3-4 cyfry bez myślnika + czynność 6-8 cyfr
        match = re.search(r'(KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\s*(\d{2,4})\s+(\d{6,8})', podstawa, re.IGNORECASE)
        if match:
            cat = match.group(2)
            cat_norm = f"{cat[:-2]}-{cat[-2:]}"  # "201" → "2-01", "0202" → "02-02"
            act = match.group(3)[:6]
            act_norm = f"{act[:4]}-{act[4:6]}"   # "012502" → "0125-02"
            return f"{match.group(1)} {cat_norm} {act_norm}"

        # Format Norma STD tylko katalog: "KNR 201" → "KNR 2-01"
        match = re.search(r'(KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\s*(\d{3,4})\b', podstawa, re.IGNORECASE)
        if match:
            cat = match.group(2)
            cat_norm = f"{cat[:-2]}-{cat[-2:]}"
            return f"{match.group(1)} {cat_norm}"

        # KNNR, KNP z myślnikami
        match = re.search(r'(KN[NRP]R?)\s*(\d+)[- ](\d+)\s*(\d{4})[- ]?(\d+)', podstawa, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}-{match.group(3)} {match.group(4)}-{match.group(5)}"

        return podstawa
    
    def fix_pozycja(self, pozycja):
        """Naprawia całą pozycję kosztorysową"""
        return {
            'podstawa': self.fix_podstawa(pozycja.get('podstawa', '')),
            'opis': self.fix_opis(pozycja.get('opis', '')),
            'jm': self.fix_jednostka(pozycja.get('jm', '')),
            'ilosc': self.extract_number(pozycja.get('ilosc', 0)),
            'R': self.extract_number(pozycja.get('R', 0)),
            'M': self.extract_number(pozycja.get('M', 0)),
            'S': self.extract_number(pozycja.get('S', 0)),
            'cena_jednostkowa': self.extract_number(pozycja.get('cena_jednostkowa', 0)),
            'wartosc': self.extract_number(pozycja.get('wartosc', 0)),
        }


# ============ TEST ============
if __name__ == "__main__":
    fixer = TextFixer()
    
    # Test liczb
    print("=== Test liczb ===")
    print(f"'0.428.89' → {fixer.fix_number('0.428.89')}")
    print(f"'1.234.56' → {fixer.fix_number('1.234.56')}")
    print(f"'28,89 m2' → {fixer.extract_number('28,89 m2')}")
    
    # Test opisów
    print("\n=== Test opisów ===")
    print(f"'otiße78' → {fixer.fix_opis('otiße78')}")
    print(f"'woda przem27' → {fixer.fix_opis('woda przem27')}")
    print(f"'gr. 15 cm' → {fixer.fix_opis('gr. 15 cm')}")
    
    # Test jednostek
    print("\n=== Test jednostek ===")
    print(f"'m²' → {fixer.fix_jednostka('m²')}")
    print(f"'mb.' → {fixer.fix_jednostka('mb.')}")
    
    # Test podstawy
    print("\n=== Test podstawy ===")
    print(f"'KNR 2-31 0703-03' → {fixer.fix_podstawa('KNR 2-31 0703-03')}")
    print(f"'knr2 31 070303' → {fixer.fix_podstawa('knr2 31 070303')}")
    
    print("\n✓ TextFixer OK")
