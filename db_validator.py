# -*- coding: utf-8 -*-
"""
Database Validator v1.0
Walidacja baz danych nakładów przy starcie programu

Użycie:
    from db_validator import validate_databases
    
    errors = validate_databases()
    if errors:
        print("Błędy w bazach:", errors)
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class DatabaseValidator:
    """Walidator baz danych kosztorysowych"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent / "learned_kosztorysy"
        self.base_dir = Path(base_dir)
        self.schemas_dir = self.base_dir / "schemas"
    
    def validate_naklady_rms(self, data: List[Dict]) -> List[str]:
        """
        Waliduje bazę nakładów R+M+S
        
        Returns:
            Lista błędów (pusta jeśli OK)
        """
        errors = []
        
        if not isinstance(data, list):
            return ["naklady_rms: oczekiwano tablicy, otrzymano " + type(data).__name__]
        
        if len(data) == 0:
            return ["naklady_rms: baza jest pusta"]
        
        for i, item in enumerate(data):
            prefix = f"naklady_rms[{i}]"
            
            # Wymagane pola
            if not isinstance(item, dict):
                errors.append(f"{prefix}: oczekiwano obiektu")
                continue
            
            # KNR - wymagane
            knr = item.get('knr', '')
            if not knr:
                errors.append(f"{prefix}: brak pola 'knr'")
            elif not isinstance(knr, str):
                errors.append(f"{prefix}: 'knr' musi być stringiem")
            
            # jm - wymagane
            jm = item.get('jm', '')
            if not jm:
                errors.append(f"{prefix}: brak pola 'jm'")
            
            # R, M, S - muszą być liczbami >= 0
            for field in ['R', 'M', 'S']:
                val = item.get(field, 0)
                if not isinstance(val, (int, float)):
                    errors.append(f"{prefix}: '{field}' musi być liczbą")
                elif val < 0:
                    errors.append(f"{prefix}: '{field}' nie może być ujemne ({val})")
            
            # Weryfikacja sumy (jeśli podana) - tolerancja 0.02 dla floating point
            if 'suma' in item:
                expected = item.get('R', 0) + item.get('M', 0) + item.get('S', 0)
                actual = item['suma']
                if abs(expected - actual) > 0.02:
                    errors.append(f"{prefix}: suma={actual} != R+M+S={expected:.2f}")
        
        return errors
    
    def validate_pozycje_wzorcowe(self, data: List[Dict]) -> List[str]:
        """
        Waliduje bazę pozycji wzorcowych
        
        Returns:
            Lista błędów (pusta jeśli OK)
        """
        errors = []
        
        if not isinstance(data, list):
            return ["pozycje_wzorcowe: oczekiwano tablicy"]
        
        if len(data) == 0:
            return ["pozycje_wzorcowe: baza jest pusta"]
        
        for i, item in enumerate(data):
            prefix = f"pozycje_wzorcowe[{i}]"
            
            if not isinstance(item, dict):
                errors.append(f"{prefix}: oczekiwano obiektu")
                continue
            
            # opis - wymagane
            opis = item.get('opis', '')
            if not opis:
                errors.append(f"{prefix}: brak pola 'opis'")
            elif len(opis) < 5:
                errors.append(f"{prefix}: 'opis' za krótki (<5 znaków)")
            elif len(opis) > 500:
                errors.append(f"{prefix}: 'opis' za długi (>500 znaków)")
        
        return errors
    
    def load_and_validate(self, filename: str) -> Tuple[Optional[List], List[str]]:
        """
        Ładuje i waliduje plik JSON
        
        Returns:
            (data, errors) - dane i lista błędów
        """
        filepath = self.base_dir / filename
        
        if not filepath.exists():
            return None, [f"Plik nie istnieje: {filepath}"]
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return None, [f"Błąd parsowania JSON {filename}: {e}"]
        except Exception as e:
            return None, [f"Błąd odczytu {filename}: {e}"]
        
        # Waliduj w zależności od typu
        if 'naklady' in filename.lower():
            errors = self.validate_naklady_rms(data)
        elif 'wzorcow' in filename.lower():
            errors = self.validate_pozycje_wzorcowe(data)
        else:
            errors = []  # Nieznany typ - brak walidacji
        
        return data, errors
    
    def validate_all(self) -> Dict[str, List[str]]:
        """
        Waliduje wszystkie bazy danych
        
        Returns:
            Słownik {nazwa_pliku: [błędy]}
        """
        results = {}
        
        # Lista plików do walidacji
        files = [
            'naklady_rms.json',
            'pozycje_wzorcowe.json',
        ]
        
        for filename in files:
            data, errors = self.load_and_validate(filename)
            if errors:
                results[filename] = errors
            else:
                # Podsumowanie sukcesu
                count = len(data) if data else 0
                print(f"OK: {filename} ({count} rekordów)")
        
        return results


def validate_databases(base_dir: str = None, verbose: bool = True) -> Dict[str, List[str]]:
    """
    Funkcja pomocnicza do walidacji baz
    
    Args:
        base_dir: ścieżka do katalogu learned_kosztorysy
        verbose: czy wypisywać podsumowanie
        
    Returns:
        Słownik z błędami (pusty = wszystko OK)
    """
    validator = DatabaseValidator(base_dir)
    errors = validator.validate_all()
    
    if verbose:
        if errors:
            print(f"\n[!] Znaleziono bledy w {len(errors)} plikach:")
            for filename, file_errors in errors.items():
                print(f"\n{filename}:")
                for err in file_errors[:10]:  # Max 10 bledow na plik
                    print(f"  - {err}")
                if len(file_errors) > 10:
                    print(f"  ... i {len(file_errors) - 10} wiecej")
        else:
            print("\n[OK] Wszystkie bazy OK")
    
    return errors


# ============ TEST ============
if __name__ == "__main__":
    print("Walidacja baz danych kosztorysowych")
    print("=" * 40)
    
    errors = validate_databases()
    
    if errors:
        print(f"\nZnaleziono problemy!")
        exit(1)
    else:
        print("\nBrak błędów")
        exit(0)
