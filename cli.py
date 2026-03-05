# -*- coding: utf-8 -*-
"""
Kosztorys CLI v1.0
Interfejs linii poleceń dla generatora kosztorysów

Użycie:
    python cli.py przedmiar.pdf [--ath] [--pdf] [--nazwa "..."] [--inwestor "..."]
    
Przykłady:
    python cli.py przedmiar.pdf
    python cli.py przedmiar.pdf --nazwa "Remont budynku" --inwestor "Gmina Brzeg"
    python cli.py przedmiar.pdf --ath  # tylko ATH
    python cli.py przedmiar.pdf --pdf  # tylko PDF
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Import generatora (wspiera: moduł, bezpośrednie uruchomienie, pip install)
try:
    from .kosztorys_generator import KosztorysGenerator
    from .exceptions import PDFParsingError, NormaPROError
except ImportError:
    try:
        from kosztorys_generator import KosztorysGenerator
        from exceptions import PDFParsingError, NormaPROError
    except ImportError:
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from kosztorys_generator import KosztorysGenerator
        from exceptions import PDFParsingError, NormaPROError


def main():
    """Główna funkcja CLI"""
    parser = argparse.ArgumentParser(
        description='Generator kosztorysów ATH + PDF z przedmiarów',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  %(prog)s przedmiar.pdf
  %(prog)s przedmiar.pdf --nazwa "Remont budynku" --inwestor "Gmina Brzeg"
  %(prog)s przedmiar.pdf --ath   # tylko ATH
  %(prog)s przedmiar.pdf --pdf   # tylko PDF
  %(prog)s przedmiar.pdf -o kosztorys  # custom nazwa wyjścia
        """
    )
    
    # Wymagany argument
    parser.add_argument(
        'przedmiar',
        help='Ścieżka do przedmiaru PDF'
    )
    
    # Format wyjścia
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        '--ath',
        action='store_true',
        help='Generuj tylko ATH'
    )
    format_group.add_argument(
        '--pdf',
        action='store_true',
        help='Generuj tylko PDF'
    )
    format_group.add_argument(
        '--both',
        action='store_true',
        default=True,
        help='Generuj ATH i PDF (domyślnie)'
    )
    
    # Ścieżka wyjściowa
    parser.add_argument(
        '--output', '-o',
        help='Ścieżka wyjściowa (bez rozszerzenia)'
    )
    
    # Dane tytułowe
    parser.add_argument(
        '--nazwa',
        help='Nazwa inwestycji'
    )
    parser.add_argument(
        '--adres',
        help='Adres inwestycji'
    )
    parser.add_argument(
        '--inwestor',
        help='Nazwa inwestora'
    )
    parser.add_argument(
        '--wykonawca',
        default='KLONEKS',
        help='Nazwa wykonawcy (domyślnie: KLONEKS)'
    )
    parser.add_argument(
        '--branza',
        default='budowlana',
        help='Branża (domyślnie: budowlana)'
    )
    
    # Parametry kalkulacji
    parser.add_argument(
        '--stawka-rg',
        type=float,
        default=35.00,
        help='Stawka roboczogodziny (domyślnie: 35.00 zł)'
    )
    parser.add_argument(
        '--stawka-sprzetu',
        type=float,
        default=100.00,
        help='Stawka maszynogodziny (domyślnie: 100.00 zł)'
    )
    parser.add_argument(
        '--kp',
        type=float,
        default=70.0,
        help='Koszty pośrednie %% (domyślnie: 70%%)'
    )
    parser.add_argument(
        '--zysk',
        type=float,
        default=12.0,
        help='Zysk %% (domyślnie: 12%%)'
    )
    parser.add_argument(
        '--vat',
        type=float,
        default=23.0,
        help='VAT %% (domyślnie: 23%%)'
    )
    
    # Verbose
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Pokaż szczegóły'
    )
    
    # Dry-run
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Pokaż co zostanie wygenerowane bez zapisywania plików'
    )
    
    # No-cache
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Wyłącz cache parsowania PDF'
    )
    
    args = parser.parse_args()

    # Walidacja parametrów kalkulacji
    param_errors = []
    if args.stawka_rg <= 0:
        param_errors.append(f"--stawka-rg musi być > 0 (podano: {args.stawka_rg})")
    if args.stawka_sprzetu <= 0:
        param_errors.append(f"--stawka-sprzetu musi być > 0 (podano: {args.stawka_sprzetu})")
    if not (0 <= args.kp <= 100):
        param_errors.append(f"--kp musi być w zakresie 0-100 (podano: {args.kp})")
    if not (0 <= args.zysk <= 100):
        param_errors.append(f"--zysk musi być w zakresie 0-100 (podano: {args.zysk})")
    if not (0 <= args.vat <= 100):
        param_errors.append(f"--vat musi być w zakresie 0-100 (podano: {args.vat})")
    if param_errors:
        for err in param_errors:
            print(f"BŁĄD: {err}")
        sys.exit(1)

    # Sprawdź czy plik istnieje
    if not Path(args.przedmiar).exists():
        print(f"BŁĄD: Plik nie istnieje: {args.przedmiar}")
        sys.exit(1)
    
    # Przygotuj dane tytułowe
    dane_tytulowe = {
        'nazwa_inwestycji': args.nazwa or Path(args.przedmiar).stem,
        'adres_inwestycji': args.adres or '',
        'inwestor': args.inwestor or '',
        'adres_inwestora': '',
        'wykonawca': args.wykonawca,
        'adres_wykonawcy': '49-300 Brzeg',
        'branza': args.branza,
        'sporzadzil': '',
        'data': datetime.now().strftime('%m.%Y'),
    }
    
    # Ścieżki wyjściowe
    if args.output:
        base = args.output
    else:
        base = str(Path(args.przedmiar).with_suffix(''))
    
    output_ath = None
    output_pdf = None
    
    if args.ath:
        output_ath = f"{base}_kosztorys.ath"
    elif args.pdf:
        output_pdf = f"{base}_kosztorys.pdf"
    else:  # both
        output_ath = f"{base}_kosztorys.ath"
        output_pdf = f"{base}_kosztorys.pdf"
    
    # Inicjalizuj generator z parametrami
    generator = KosztorysGenerator()
    generator.params.update({
        'stawka_rg': args.stawka_rg,
        'stawka_sprzetu': args.stawka_sprzetu,
        'kp_procent': args.kp,
        'z_procent': args.zysk,
        'vat_procent': args.vat,
    })
    
    # Dry-run mode
    if args.dry_run:
        print("\n=== DRY-RUN MODE ===")
        print(f"Przedmiar: {args.przedmiar}")
        print(f"Output ATH: {output_ath or '(brak)'}")
        print(f"Output PDF: {output_pdf or '(brak)'}")
        
        # Parsuj i oblicz (bez zapisywania)
        pozycje = generator.parse_przedmiar_pdf(args.przedmiar, use_cache=not args.no_cache)
        if not pozycje:
            print("\n[!] Nie znaleziono pozycji!")
            sys.exit(1)
        
        pozycje, podsumowanie = generator.calculate_kosztorys(pozycje)
        
        print(f"\nPozycji: {len(pozycje)}")
        print(f"NETTO: {podsumowanie['wartosc_netto']:,.2f} zl".replace(',', ' '))
        print(f"BRUTTO: {podsumowanie['wartosc_brutto']:,.2f} zl".replace(',', ' '))
        
        # Porównaj z poprzednimi plikami
        if output_ath and Path(output_ath).exists():
            print(f"\n[i] Plik ATH istnieje - zostanie nadpisany")
        if output_pdf and Path(output_pdf).exists():
            print(f"[i] Plik PDF istnieje - zostanie nadpisany")
        
        print("\n=== Uzyj bez --dry-run zeby wygenerowac ===")
        sys.exit(0)
    
    # Generuj (normalny tryb)
    try:
        results = generator.generate(
            args.przedmiar,
            dane_tytulowe=dane_tytulowe,
            output_ath=output_ath,
            output_pdf=output_pdf
        )
        
        if results:
            print("\nGotowe!")
            for fmt, path in results.items():
                print(f"  {fmt.upper()}: {path}")
        else:
            print("\n[!] Nie wygenerowano zadnych plikow")
            sys.exit(1)
            
    except PDFParsingError as e:
        print(f"\nBŁĄD PARSOWANIA PDF: {e}")
        print("\nWskazówki:")
        print("  • Sprawdź czy plik to przedmiar robót budowlanych (Norma PRO)")
        print("  • Jeśli PDF jest skanem: ocrmypdf wejscie.pdf wyjscie.pdf")
        print("  • Użyj --verbose żeby zobaczyć szczegółowe logi")
        sys.exit(1)
    except NormaPROError as e:
        print(f"\nBŁĄD GENEROWANIA ATH: {e}")
        print("  • Sprawdź czy ścieżka wyjściowa jest dostępna do zapisu")
        sys.exit(1)
    except Exception as e:
        print(f"\nBŁĄD: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
