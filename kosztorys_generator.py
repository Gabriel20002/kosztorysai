# -*- coding: utf-8 -*-
"""
Kosztorys Generator v3.2
Zintegrowany pipeline: przedmiar PDF → ATH + PDF

Użycie przez CLI:
    python cli.py przedmiar.pdf [--ath] [--pdf] [--nazwa "..."]
    
Użycie jako biblioteka:
    from kosztorys_generator import KosztorysGenerator
    gen = KosztorysGenerator()
    gen.generate("przedmiar.pdf", output_ath="out.ath", output_pdf="out.pdf")
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Lokalne importy
try:
    from validators import TextFixer, CalcValidator, LogicValidator
    from pdf_generator_v2 import generuj_pdf, KosztorysPDF
    from calculator_engine import CalculatorEngine
    from ath_generator import ATHGenerator
    from db_validator import validate_databases
    from logger import get_logger
    from pdf_cache import get_cache
    from exceptions import PDFParsingError, KNRMatchingError, NormaPROError
    from formatters import fmt_summary
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from validators import TextFixer, CalcValidator, LogicValidator
    from pdf_generator_v2 import generuj_pdf, KosztorysPDF
    from calculator_engine import CalculatorEngine
    from ath_generator import ATHGenerator
    from db_validator import validate_databases
    from logger import get_logger
    from pdf_cache import get_cache
    from exceptions import PDFParsingError, KNRMatchingError, NormaPROError
    from formatters import fmt_summary

# Logger dla tego modułu
log = get_logger(__name__)

# Wzorzec kodu katalogowego — obsługuje wszystkie warianty:
#   KNR, KNR-W, KNR-INS, KNR-E, KNNR, KNNR-W, KNK, KSNR, AT, AL, itp.
_KNR_CODE = r'(?:KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\s*[\d]+(?:-[\d]+)?'

# Skompilowane wzorce regex (raz przy imporcie modułu)
_KNR_PATTERN = re.compile(
    r'^(\d+)\s*(?:SST-[A-Z]-|d\.\d+\s*)?'          # Lp i opcjonalny prefiks SST/d.
    r'.*?(' + _KNR_CODE + r'(?:\s+[\d]+-[\d]+)?)\s+'  # Kod KNR z opcjonalną tablicą
    r'(.+?)\s+'                                         # Opis
    r'(m2|m3|m\b|szt\.?|kpl\.?|kg|t|mb|r-g)\s*$',     # Jednostka miary
    re.IGNORECASE
)
_KNR_SIMPLE_PATTERN = re.compile(r'(' + _KNR_CODE + r')', re.IGNORECASE)
_JM_PATTERN = re.compile(r'(m2|m3|m\b|szt\.?|kpl\.?|kg|t|mb)\s*$', re.IGNORECASE)
_CALC_LINE_PATTERN = re.compile(r'^[\d\.,\*\+\-\s]+$')
_NEXT_POS_PATTERN = re.compile(r'^\d+\s*(?:SST|d\.)')
_RAZEM_PATTERN = re.compile(r'RAZEM\s+([\d\s,\.]+)')
_WHITESPACE_PATTERN = re.compile(r'\s+')

# Wzorzec sufiksu akcji KNR na kolejnej linii:
#   "d.1/0301-03", "d.1/10301-03" (OCR artefakt), "d.1]0111-01", "d.1|0208-02",
#   "d.10313-06" (bez separatora), "d.110208-02" (brak sep. + dodatkowa cyfra),
#   "at. 105", "aj 103", "zk 105", "ES| [03"
# \d?? — NON-GREEDY: najpierw próbuje bez cyfry, by złapać pełne "0208-02" zamiast "208"
# d\.\d+(?=\d{4}-\d{2}) — obsługuje brak separatora: "d.10313-06", "d.110208-02"
_SUFFIX_PAT = re.compile(
    r'(?:d\.\d+[\./|\[\]]+|d\.\d+(?=\d{4}-\d{2})|at\.?\s*|aj\s+|zk\s+|ES\|\s*\[?|\.1\./|^\d+\.\d+[./])'
    r'\d??(\d{4}-\d{2}|\d{2,3})\b'
)

# Granice kolumn PDF dla formatu SST (Norma PRO)
_COL_KNR_XMIN  = 112
_COL_KNR_XMAX  = 166
_COL_DESC_XMAX = 430
_COL_HDR_YMAX  = 100
_COL_FTR_YMIN  = 782

# Granice kolumn PDF dla formatu kosztorysu ofertowego Norma PRO
# (kolumny: Lp | Podstawa | Opis | j.m. | Nakłady | Koszt jedn. | R | M | S)
_NK_LP_XMAX   = 50   # Lp (x0 < 50)
_NK_KNR_XMIN  = 50   # Podstawa/KNR start
_NK_KNR_XMAX  = 112  # Podstawa/KNR end
_NK_OPIS_XMAX = 350  # Opis end
_NK_JM_XMAX   = 390  # j.m. end
_NK_VAL_XMIN  = 520  # Kolumna wartości R/M/S (prawa strona)
_NK_HDR_YMIN  = 60   # Ignoruj nagłówki strony (top < 60)


def _group_words_by_row(words, y_tolerance=4):
    """Grupuje słowa pdfplumber wg współrzędnej y (ta sama wiersz = |Δy| ≤ tolerance)."""
    if not words:
        return []
    sorted_w = sorted(words, key=lambda w: w['top'])
    rows, cur, cur_y = [], [sorted_w[0]], sorted_w[0]['top']
    for w in sorted_w[1:]:
        if abs(w['top'] - cur_y) <= y_tolerance:
            cur.append(w)
        else:
            rows.append(sorted(cur, key=lambda x: x['x0']))
            cur, cur_y = [w], w['top']
    if cur:
        rows.append(sorted(cur, key=lambda x: x['x0']))
    return rows


def _reconstruct_knr_code(parts):
    """Łączy fragmenty kodu KNR, scalając tokeny po myślniku na końcu.

    Przykład: ['KNR', 'AT-', '17', '0103-', '01'] → 'KNR AT-17 0103-01'
    """
    if not parts:
        return ''
    result = parts[0]
    for p in parts[1:]:
        result = (result + p) if result.endswith('-') else (result + ' ' + p)
    return re.sub(r'\s+', ' ', result).strip()


# Wzorzec formuł nakładów z PDF Norma PRO (r-g, m-g, zł/..., analogia)
_NAKLAD_FORMULA_PAT = re.compile(
    r'\br-g\b|\bm-g\b|zł/|analogia|\bKNR\b|\bKNNR\b|kosztory|obmiar',
    re.IGNORECASE,
)


def _is_desc_continuation(text):
    """Zwraca True jeśli tekst wygląda jak kontynuacja opisu (nie obliczenie/formuła)."""
    if not text:
        return False
    # Linie zaczynające się od cyfry, nawiasu, myślnika, +, *, = to obliczenia
    if re.match(r'^[(\d\-+*=]', text):
        return False
    # Słowa kluczowe które NIE są opisem pracy
    if text.startswith(('poz.', 'Lp.', 'spec.', 'techn.', 'Norma', 'Sanitariaty')):
        return False
    # Formuły nakładów, referencje KNR, słowo analogia
    if _NAKLAD_FORMULA_PAT.search(text):
        return False
    return bool(re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', text))


# PDF parsing
try:
    import pdfplumber
except ImportError:
    log.error("Brak pdfplumber. Zainstaluj: pip install pdfplumber")
    sys.exit(1)


class KosztorysGenerator:
    """Główny generator kosztorysów ATH + PDF"""
    
    def __init__(self, baza_nakladow_path=None, baza_wzorcow_path=None):
        # Ścieżki domyślne
        base_dir = Path(__file__).parent
        
        if not baza_nakladow_path:
            # Używaj merged (1218 rekordów) jeśli istnieje, fallback na rms (689)
            merged = base_dir / "learned_kosztorysy" / "naklady_merged.json"
            baza_nakladow_path = merged if merged.exists() else base_dir / "learned_kosztorysy" / "naklady_rms.json"
        if not baza_wzorcow_path:
            baza_wzorcow_path = base_dir / "learned_kosztorysy" / "pozycje_wzorcowe.json"
        
        # Załaduj bazy
        self.naklady = {}
        self.wzorce = []
        
        if os.path.exists(baza_nakladow_path):
            with open(baza_nakladow_path, 'r', encoding='utf-8') as f:
                self.naklady = json.load(f)
            log.info("Zaladowano %d nakladow", len(self.naklady))

        # Indeks KNR → nakład dla wyszukiwania O(1)
        self._rebuild_naklady_index()
        
        if os.path.exists(baza_wzorcow_path):
            with open(baza_wzorcow_path, 'r', encoding='utf-8') as f:
                self.wzorce = json.load(f)
            log.info("Zaladowano %d wzorcow opisow", len(self.wzorce))
        
        # Walidacja baz przy starcie (silent - nie przerywa)
        db_errors = validate_databases(str(base_dir / "learned_kosztorysy"), verbose=False)
        if db_errors:
            log.warning("Ostrzezenie: %d plikow ma bledy walidacji", len(db_errors))
        
        # Walidatory
        self.text_fixer = TextFixer(str(baza_wzorcow_path))
        self.calc_validator = CalcValidator()
        self.logic_validator = LogicValidator()
        
        # KNR Matcher z AI (opcjonalny)
        self.knr_matcher = None
        try:
            from knr_matcher import KNRMatcher
            self.knr_matcher = KNRMatcher(use_ai=True, use_embeddings=True)
            log.info("KNR Matcher z AI aktywny")
        except Exception as e:
            log.warning("KNR Matcher niedostepny: %s", e)
        
        # Domyślne parametry
        self.params = {
            'stawka_rg': 35.00,       # zł/r-g (roboczogodzina)
            'stawka_sprzetu': 100.00, # zł/m-g (maszynogodzina)
            'kp_procent': 70.0,
            'z_procent': 12.0,
            'kz_procent': 8.0,
            'vat_procent': 23.0,
        }
    
    # Minimalna liczba pozycji z głównego parsera — poniżej tej wartości
    # uruchamiamy fallback parsery
    _MIN_POSITIONS = 3

    def _rebuild_naklady_index(self):
        """Przebuduj indeks KNR → nakład. Wywołaj po zmianie self.naklady."""
        naklady_list = self.naklady if isinstance(self.naklady, list) else list(self.naklady.values())
        self._naklady_index = {}
        for n in naklady_list:
            knr = n.get('knr', n.get('podstawa', ''))
            knr_norm = _WHITESPACE_PATTERN.sub('', knr.upper())
            if knr_norm:
                self._naklady_index[knr_norm] = n

    def parse_przedmiar_pdf(self, pdf_path, use_cache=True):
        """Parsuje przedmiar z PDF.

        Kaskada parserów:
          1. Główny regex (SST/d.X + KNR/KNR-W/KNNR/...)
          2. universal_parser (Format A/B/C bez tabel)
          3. table_parser (tabelaryczny format Norma PRO)

        Args:
            pdf_path: ścieżka do pliku PDF
            use_cache: czy używać cache (domyślnie True)
        """
        # Sprawdź cache
        if use_cache:
            cache = get_cache()
            cached = cache.get(pdf_path)
            if cached:
                return cached

        log.info("Parsowanie: %s", pdf_path)

        # Otwórz PDF raz i wyciągnij tekst
        try:
            pdf_ctx = pdfplumber.open(pdf_path)
        except Exception as e:
            raise PDFParsingError(f"Nie można otworzyć pliku PDF '{pdf_path}': {e}") from e

        with pdf_ctx as pdf:
            full_text = ""
            page_count = len(pdf.pages)
            image_only_pages = 0
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
                elif page.images:
                    image_only_pages += 1

        # Diagnoza pustego/skanowanego PDF
        _ocr_tmp = None
        if not full_text.strip():
            if image_only_pages > 0:
                # Próba automatycznego OCR
                ocr_result = self._try_auto_ocr(pdf_path)
                if ocr_result:
                    _ocr_tmp, pdf_path = ocr_result
                    # Ponowna ekstrakcja tekstu z OCR'd PDF
                    with pdfplumber.open(pdf_path) as pdf_ocr:
                        full_text = '\n'.join(
                            page.extract_text() or '' for page in pdf_ocr.pages
                        )
                    log.info("Auto-OCR: wyodrebniono %d znakow z %s", len(full_text), Path(pdf_path).name)
                else:
                    raise PDFParsingError(
                        f"'{Path(pdf_path).name}' to skan — PDF zawiera {image_only_pages}/{page_count} "
                        f"stron z obrazami bez tekstu. "
                        f"Przed użyciem uruchom OCR (np.: ocrmypdf -l pol --deskew wejscie.pdf wyjscie.pdf)."
                    )
            else:
                raise PDFParsingError(
                    f"'{Path(pdf_path).name}' nie zawiera żadnego tekstu "
                    f"({page_count} stron). Sprawdź czy plik nie jest uszkodzony."
                )

        if not full_text.strip():
            raise PDFParsingError(
                f"OCR nie wyodrebnił tekstu z '{Path(pdf_path).name}'. "
                f"Sprawdź czy plik jest czytelnym skanem."
            )

        lines = full_text.split('\n')

        # --- Kaskada parserów ---
        found_positions = self._parse_with_regex(lines)
        parser_used = 'regex'

        # Parser kosztorysu ofertowego (pełny KNR + R/M/S z PDF)
        norma_positions = self._parse_with_norma_kosztorys_format(pdf_path)
        norma_has_prices = any(
            p.get('_R_pdf', 0) + p.get('_M_pdf', 0) + p.get('_S_pdf', 0) > 0
            for p in norma_positions
        )
        if len(norma_positions) > len(found_positions):
            found_positions = norma_positions
            parser_used = 'norma_kosztorys'
        if norma_has_prices:
            log.info(
                "Norma kosztorys parser: %d pozycji z cenami bezposrednio z PDF — pomijam sst_coords",
                len(norma_positions),
            )

        # Parser SST — kody KNR rozbite na >1 wiersz
        # UWAGA: uruchamiamy tylko gdy norma_kosztorys NIE znalazł cen z PDF.
        # Gdy norma ma ceny, sst_coords (bez cen) tylko by je nadpisał domyslnymi.
        if not norma_has_prices:
            coord_positions = self._parse_with_sst_coords(pdf_path)
            if len(coord_positions) > len(found_positions):
                found_positions = coord_positions
                parser_used = 'coords'

        if len(found_positions) < self._MIN_POSITIONS:
            zuzia = self._parse_with_zuzia_format(pdf_path)
            if len(zuzia) > len(found_positions):
                found_positions = zuzia
                parser_used = 'zuzia'

        # Norma Standard d-parser — zawsze sprawdzany (lepsze KNR niż regex)
        norma_std = self._parse_with_norma_standard_d(pdf_path)
        if len(norma_std) > len(found_positions):
            found_positions = norma_std
            parser_used = 'norma_standard_d'

        if len(found_positions) < self._MIN_POSITIONS:
            ocr_pipe = self._parse_with_ocr_pipe_table(pdf_path)
            if len(ocr_pipe) > len(found_positions):
                found_positions = ocr_pipe
                parser_used = 'ocr_pipe_table'

        if len(found_positions) < self._MIN_POSITIONS:
            univ = self._parse_with_universal(pdf_path)
            if len(univ) > len(found_positions):
                found_positions = univ
                parser_used = 'universal'

        if len(found_positions) < self._MIN_POSITIONS:
            tbl = self._parse_with_table(pdf_path)
            if len(tbl) > len(found_positions):
                found_positions = tbl
                parser_used = 'table'

        log.info("Parser: %s → %d surowych pozycji", parser_used, len(found_positions))

        # Diagnoza gdy żaden parser nie znalazł pozycji
        if not found_positions:
            self._diagnose_empty_result(pdf_path, full_text)

        pozycje = []
        current_dzial = "Kosztorys"

        # Przetwórz znalezione pozycje
        for pos in found_positions:
            podstawa = self.text_fixer.fix_podstawa(pos['podstawa'])
            opis = self.text_fixer.fix_opis(pos['opis'])
            jm = self.text_fixer.fix_jednostka(pos['jm'])
            ilosc = pos['ilosc']

            # R/M/S bezpośrednio z PDF (parser kosztorysu) lub z bazy danych
            if '_R_pdf' in pos:
                r_total = pos['_R_pdf']
                m_total = pos['_M_pdf']
                s_total = pos['_S_pdf']
                r = r_total / ilosc if ilosc > 0 else 0.0
                m = m_total / ilosc if ilosc > 0 else 0.0
                s = s_total / ilosc if ilosc > 0 else 0.0
                confidence, knr_source = 1.0, 'pdf_direct'
            else:
                r, m, s, confidence, knr_source, matched_knr = self._find_naklady(podstawa, opis)
                # Uzupełnij niepełny KNR tylko gdy matched_knr jest bardziej szczegółowy
                # (ma numer akcji \d{4}-\d{2} gdy podstawa go nie ma)
                _has_act = re.compile(r'\d{4}-\d{2}')
                if (knr_source == 'exact' and matched_knr and matched_knr != podstawa
                        and _has_act.search(matched_knr)):
                    podstawa = matched_knr
                elif (knr_source == 'partial' and matched_knr and matched_knr != podstawa
                        and _has_act.search(matched_knr) and not _has_act.search(podstawa)):
                    podstawa = matched_knr

            # Oznacz pozycje bez wyceny — widoczne w Norma PRO
            opis_final = opis[:200]
            if knr_source == 'default':
                opis_final = '[WYCENA] ' + opis_final

            pozycje.append({
                'lp': pos['lp'],
                'podstawa': podstawa,
                'opis': opis_final,
                'jm': jm,
                'ilosc': ilosc,
                'R': r * ilosc,
                'M': m * ilosc,
                'S': s * ilosc,
                'dzial': current_dzial,
                'knr_confidence': round(confidence, 2),
                'knr_source': knr_source,
                'formula_str': pos.get('formula_str', ''),
            })
        
        defaults = sum(1 for p in pozycje if p.get('knr_source') == 'default')
        if defaults:
            log.warning("Sparsowano %d pozycji (%d bez dopasowania KNR - użyto wartości domyślnych)", len(pozycje), defaults)
        else:
            log.info("Sparsowano %d pozycji (wszystkie dopasowane)", len(pozycje))

        # AI matcher — dla pozycji bez KNR w bazie (opcjonalny, wymaga ANTHROPIC_API_KEY)
        if defaults and os.environ.get('ANTHROPIC_API_KEY'):
            pozycje = self._apply_ai_matcher(pozycje)

        # Zapisz do cache
        if use_cache and pozycje:
            cache = get_cache()
            cache.set(pdf_path, pozycje)

        # Usuń tymczasowy folder OCR
        if _ocr_tmp:
            import shutil
            shutil.rmtree(_ocr_tmp, ignore_errors=True)

        return pozycje

    def _apply_ai_matcher(self, pozycje):
        """Dopasowuje pozycje bez KNR używając Claude API (batch, 1 wywołanie).

        Faza 1: próba dopasowania kodu KNR z bazy → R/M/S z bazy nakładów
        Faza 2: dla pozycji nadal bez wyceny — bezpośrednie szacowanie R/M/S przez AI
        """
        try:
            import ai_knr_matcher
        except ImportError:
            return pozycje

        unmatched_idx = [i for i, p in enumerate(pozycje) if p.get('knr_source') == 'default']
        if not unmatched_idx:
            return pozycje

        unmatched_list = [
            {'opis': pozycje[i]['opis'].replace('[WYCENA] ', ''),
             'jm': pozycje[i]['jm'],
             'podstawa': pozycje[i]['podstawa']}
            for i in unmatched_idx
        ]

        # ── Faza 1: dopasowanie KNR z bazy ─────────────────────────────────
        log.info("AI matcher faza 1: dopasowanie KNR dla %d pozycji...", len(unmatched_idx))
        ai_matches = ai_knr_matcher.match_unmatched_positions(
            unmatched_list, self._naklady_index
        )

        still_unmatched_local = []  # lokalne indeksy (w unmatched_list) wciąż bez wyceny
        fixed_f1 = 0
        for local_i, global_i in enumerate(unmatched_idx):
            knr = ai_matches.get(str(local_i))
            if not knr:
                still_unmatched_local.append(local_i)
                continue
            r, m, s = self._get_naklady_for_knr(knr)
            if r > 0 or m > 0 or s > 0:
                ilosc = pozycje[global_i]['ilosc']
                pozycje[global_i]['R'] = r * ilosc
                pozycje[global_i]['M'] = m * ilosc
                pozycje[global_i]['S'] = s * ilosc
                pozycje[global_i]['podstawa'] = knr
                pozycje[global_i]['knr_source'] = 'ai'
                pozycje[global_i]['opis'] = pozycje[global_i]['opis'].replace('[WYCENA] ', '')
                fixed_f1 += 1
                log.info("AI faza1 dopasowało: '%s' → %s", pozycje[global_i]['opis'][:40], knr)
            else:
                still_unmatched_local.append(local_i)

        if fixed_f1:
            log.info("AI faza 1: naprawiono %d pozycji", fixed_f1)

        # ── Faza 2: bezpośrednie szacowanie R/M/S ───────────────────────────
        if not still_unmatched_local:
            return pozycje

        still_list = [unmatched_list[i] for i in still_unmatched_local]
        stawki = {
            'rg': self.params.get('stawka_rg', 35.0),
            'sprzet': self.params.get('stawka_sprzetu', 100.0),
        }

        log.info("AI matcher faza 2: bezpośrednie szacowanie R/M/S dla %d pozycji...", len(still_list))
        rms_estimates = ai_knr_matcher.estimate_rms_direct(
            still_list, self._naklady_index, stawki
        )

        fixed_f2 = 0
        for local_still_i, local_i in enumerate(still_unmatched_local):
            global_i = unmatched_idx[local_i]
            est = rms_estimates.get(str(local_still_i))
            if not est:
                continue
            ilosc = pozycje[global_i]['ilosc']
            r = est.get('R', 0.0)
            m = est.get('M', 0.0)
            s = est.get('S', 0.0)
            if r == 0 and m == 0 and s == 0:
                continue
            pozycje[global_i]['R'] = r * ilosc
            pozycje[global_i]['M'] = m * ilosc
            pozycje[global_i]['S'] = s * ilosc
            pozycje[global_i]['knr_source'] = 'ai_estimate'
            pozycje[global_i]['opis'] = '[AI] ' + pozycje[global_i]['opis'].replace('[WYCENA] ', '')
            fixed_f2 += 1
            log.info("AI faza2 oszacowało: '%s' R=%.2f M=%.2f S=%.2f /jm",
                     pozycje[global_i]['opis'][:40], r, m, s)

        if fixed_f2:
            log.info("AI faza 2: oszacowano %d/%d pozycji", fixed_f2, len(still_list))

        return pozycje

    # ------------------------------------------------------------------
    # Auto OCR
    # ------------------------------------------------------------------

    def _try_auto_ocr(self, pdf_path: str):
        """Próbuje uruchomić ocrmypdf na skanowanym PDF.
        Zwraca (tmpdir_path, ocr_pdf_path) lub None jeśli ocrmypdf niedostępny/błąd.
        Caller jest odpowiedzialny za usunięcie tmpdir_path po zakończeniu.
        """
        import shutil, subprocess, tempfile
        if not shutil.which('ocrmypdf'):
            log.warning("ocrmypdf niedostepny — nie mozna auto-OCR '%s'", pdf_path)
            return None
        tmpdir = tempfile.mkdtemp(prefix='kosztorys_ocr_')
        out_path = os.path.join(tmpdir, 'ocr_output.pdf')
        try:
            log.info("Uruchamiam auto-OCR: ocrmypdf -l pol --deskew '%s'", pdf_path)
            result = subprocess.run(
                ['ocrmypdf', '-l', 'pol', '--deskew', '--tesseract-pagesegmode', '4',
                 '--', pdf_path, out_path],
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode == 0 and os.path.exists(out_path):
                log.info("Auto-OCR zakończony sukcesem: %s", out_path)
                return tmpdir, out_path
            log.warning("ocrmypdf błąd (%d): %s", result.returncode, result.stderr[:200])
        except Exception as e:
            log.warning("Auto-OCR wyjątek: %s", e)
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    # ------------------------------------------------------------------
    # Parsery wewnętrzne
    # ------------------------------------------------------------------

    def _parse_with_regex(self, lines):
        """Parser główny — regex dla formatów SST / d.X z KNR/KNR-W/KNNR."""
        found = []
        current_pos = None

        # Wzorzec Norma STD: lp sklejone z numerem czynności
        # np. "10125-02" = lp(1)+"0125-02", "41101-0101" = lp(4)+"1101-0101"
        _STD_ACT = re.compile(r'^\d+?(\d{4}-\d{2,4})')

        def _norm_act(act):
            """Normalizuje numer czynności do formatu XXXX-XX."""
            if '-' in act:
                return act[:7]  # bierz tylko XXXX-XX, ignoruj nadmiar cyfr
            d = act[:6]
            return f"{d[:4]}-{d[4:6]}"

        for i, line in enumerate(lines):
            match = _KNR_PATTERN.match(line)
            if match:
                lp = int(match.group(1))
                podstawa = match.group(2)
                opis = match.group(3).strip()
                jm = match.group(4)

                # Dla linii pipe-table: wyciągnij pełny KNR z kolumny (między |)
                # np. "11|KNNR 1 0318| opis | m3" → kolumna KNR = "KNNR 1 0318"
                if '|' in line:
                    pipe_cols = line.split('|')
                    if len(pipe_cols) >= 3:
                        knr_col = pipe_cols[1].strip()
                        if knr_col.upper().startswith(podstawa.upper()):
                            extra = knr_col[len(podstawa):].strip()
                            if re.match(r'^\d{4}$', extra):
                                podstawa = podstawa + ' ' + extra

                # Norma STD: następna linia to "{lp}{czyn}" np. "10125-02" lub "411010101"
                # Lub Norma Expert OCR: gołe "0215-09" / "-02" / "d.1/0301-03" na kolejnej linii
                for _j in range(i + 1, min(i + 3, len(lines))):
                    nxt = lines[_j].strip()
                    act_m = _STD_ACT.match(nxt)
                    if act_m:
                        act = _norm_act(act_m.group(1))
                        if act not in podstawa:
                            podstawa = podstawa + ' ' + act
                        break
                    bare_m = re.match(r'^(\d{4}-\d{2})\b', nxt)
                    if bare_m and bare_m.group(1) not in podstawa:
                        podstawa = podstawa + ' ' + bare_m.group(1)
                        break
                    if re.match(r'^-(\d{2})\b', nxt) and podstawa[-1:].isdigit():
                        cont = re.match(r'^-(\d{2})', nxt)
                        podstawa = podstawa + '-' + cont.group(1)
                        break
                    sm = _SUFFIX_PAT.search(nxt)
                    if sm:
                        suffix = sm.group(1)
                        if len(suffix) == 3 and suffix[0] == '1':
                            suffix = suffix[1:]
                        if suffix not in podstawa:
                            podstawa = podstawa + ' ' + suffix
                        break

                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if 'RAZEM' in next_line:
                        break
                    if _CALC_LINE_PATTERN.match(next_line):
                        continue
                    if _NEXT_POS_PATTERN.match(next_line):
                        break
                    # Pomiń linie akcji/kalkulacji SST: "d.1.1. 0308-04 + 1.1 KNNR 5 ..."
                    if re.match(r'^d\.\d', next_line):
                        continue
                    # Pomiń linie kalkulacyjne zawierające KNR (np. "1.1 KNNR 5 KNNR 5 36 + 3...")
                    if _KNR_SIMPLE_PATTERN.search(next_line):
                        continue
                    if next_line and len(next_line) > 5:
                        opis += ' ' + next_line

                current_pos = {
                    'lp': lp, 'podstawa': podstawa,
                    'opis': opis[:300], 'jm': jm, 'ilosc': 0,
                }
                continue

            if current_pos is None:
                knr_simple = _KNR_SIMPLE_PATTERN.search(line)
                if knr_simple:
                    num_match = re.match(r'^(\d+)', line)
                    lp = int(num_match.group(1)) if num_match else len(found) + 1
                    after_knr = line[knr_simple.end():].strip()
                    jm_match = _JM_PATTERN.search(after_knr)
                    if jm_match:
                        opis = after_knr[:jm_match.start()].strip()
                        jm = jm_match.group(1)
                    else:
                        opis = after_knr
                        jm = 'szt.'
                    podstawa = knr_simple.group(1)
                    # Norma STD: następna linia "{lp}{czyn}"
                    # Lub Norma Expert OCR: gołe "0215-09" / "-02" / "d.1/0301-03" na kolejnej linii
                    for _j2 in range(i + 1, min(i + 3, len(lines))):
                        nxt2 = lines[_j2].strip()
                        act_m = _STD_ACT.match(nxt2)
                        if act_m:
                            act = _norm_act(act_m.group(1))
                            if act not in podstawa:
                                podstawa = podstawa + ' ' + act
                            break
                        bare_m = re.match(r'^(\d{4}-\d{2})\b', nxt2)
                        if bare_m and bare_m.group(1) not in podstawa:
                            podstawa = podstawa + ' ' + bare_m.group(1)
                            break
                        if re.match(r'^-(\d{2})\b', nxt2) and podstawa[-1:].isdigit():
                            cont = re.match(r'^-(\d{2})', nxt2)
                            podstawa = podstawa + '-' + cont.group(1)
                            break
                        sm2 = _SUFFIX_PAT.search(nxt2)
                        if sm2:
                            suffix2 = sm2.group(1)
                            if len(suffix2) == 3 and suffix2[0] == '1':
                                suffix2 = suffix2[1:]
                            if suffix2 not in podstawa:
                                podstawa = podstawa + ' ' + suffix2
                            break
                    current_pos = {
                        'lp': lp, 'podstawa': podstawa,
                        'opis': opis[:300], 'jm': jm, 'ilosc': 0,
                    }

            razem_match = _RAZEM_PATTERN.search(line)
            if razem_match and current_pos:
                try:
                    current_pos['ilosc'] = float(
                        razem_match.group(1).replace(' ', '').replace(',', '.')
                    )
                except ValueError:
                    current_pos['ilosc'] = 0
                if current_pos['ilosc'] > 0:
                    found.append(current_pos)
                current_pos = None

        return found

    def _parse_with_universal(self, pdf_path):
        """Fallback parser — universal_parser (Format A/B/C)."""
        try:
            from universal_parser import parse_przedmiar_universal
            raw = parse_przedmiar_universal(pdf_path)
            # Normalizuj: universal używa klucza 'knr', pipeline oczekuje 'podstawa'
            return [
                {
                    'lp': p.get('lp', i + 1),
                    'podstawa': p.get('knr', p.get('podstawa', '')),
                    'opis': p.get('opis', ''),
                    'jm': p.get('jm', 'szt.'),
                    'ilosc': p.get('ilosc', 0),
                }
                for i, p in enumerate(raw)
                if p.get('ilosc', 0) > 0
            ]
        except Exception as e:
            log.warning("Universal parser niedostępny: %s", e)
            return []

    def _parse_with_table(self, pdf_path):
        """Fallback parser — table_parser (tabelaryczny format Norma PRO)."""
        try:
            from table_parser import parse_przedmiar_table
            result = parse_przedmiar_table(pdf_path)
            return [
                {
                    'lp': p.get('lp', i + 1),
                    'podstawa': p.get('podstawa', ''),
                    'opis': p.get('opis', ''),
                    'jm': p.get('jm', 'szt.'),
                    'ilosc': p.get('ilosc', 0),
                }
                for i, p in enumerate(result.get('pozycje', []))
                if p.get('ilosc', 0) > 0
            ]
        except Exception as e:
            log.warning("Table parser niedostępny: %s", e)
            return []

    def _parse_with_sst_coords(self, pdf_path):
        """Parser oparty na współrzędnych — obsługuje kody KNR rozbite na wiele wierszy.

        Format Norma PRO SST:
          Wiersz 1:  NrSST-B-  | KNR AT-      | Opis robót...        | jm
          Wiersz 2:  d.1. 02   | 17 0103-     | kontynuacja opisu    |
          Wiersz 3:  (sekcja)  | 01           |                      |
          RAZEM …

        Granice kolumn (x):
          < 112      → lewa (Lp, SST, sekcja)
          112–166    → KNR/Podstawa
          166–430    → Opis
          430–468    → j.m.
          > 468      → wartości / RAZEM
        """
        positions = []
        current = None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_rows = []
                for page in pdf.pages:
                    words = page.extract_words(x_tolerance=3, y_tolerance=3)
                    content = [
                        w for w in words
                        if _COL_HDR_YMAX <= w['top'] <= _COL_FTR_YMIN
                    ]
                    all_rows.extend(_group_words_by_row(content, y_tolerance=4))

            for row in all_rows:
                left  = [w for w in row if w['x0'] < _COL_KNR_XMIN]
                knr_w = [w for w in row if _COL_KNR_XMIN <= w['x0'] < _COL_KNR_XMAX]
                desc  = [w for w in row if _COL_KNR_XMAX <= w['x0'] < _COL_DESC_XMAX]
                jm_w  = [w for w in row if _COL_DESC_XMAX <= w['x0'] < 468]

                left_text = ' '.join(w['text'] for w in left)
                sst_m = re.match(r'^(\d+)\s*SST-[A-Z]-', left_text)

                if sst_m:
                    # Zapisz poprzednią pozycję
                    if current is not None and current['_q'] > 0:
                        positions.append(self._finalise_coord_pos(current))
                    lp = int(sst_m.group(1))
                    current = {
                        'lp':   lp,
                        '_k':   [w['text'] for w in knr_w],
                        'opis': ' '.join(w['text'] for w in desc),
                        'jm':   ' '.join(w['text'] for w in jm_w).strip() or 'szt.',
                        '_q':   0.0,
                    }
                    continue

                if current is None:
                    continue

                # Sprawdź RAZEM
                razem_w = next((w for w in row if w['text'] == 'RAZEM'), None)
                if razem_w:
                    qty = [w for w in row if w['x0'] > razem_w['x0']]
                    try:
                        current['_q'] = float(''.join(w['text'] for w in qty).replace(',', '.'))
                    except ValueError:
                        pass
                    continue

                # Tokeny KNR: tylko alfanumeryczne + myślnik (bez kropek)
                for w in knr_w:
                    tok = w['text']
                    if re.match(r'^[A-Z0-9\-]+$', tok, re.IGNORECASE):
                        current['_k'].append(tok)

                # Kontynuacja opisu (filtruj obliczenia)
                desc_text = ' '.join(w['text'] for w in desc).strip()
                if _is_desc_continuation(desc_text):
                    current['opis'] += ' ' + desc_text

            # Ostatnia pozycja
            if current is not None and current['_q'] > 0:
                positions.append(self._finalise_coord_pos(current))

        except Exception as e:
            log.warning("Coord parser error: %s", e)
            return []

        log.info("Coord parser: %d pozycji", len(positions))
        return positions

    def _parse_with_norma_standard_d(self, pdf_path):
        """Parser dla formatu Norma STANDARD z liniami d.X (przedmiar, nie kosztorys).

        Format:
          Wiersz 1: {lp}  {KNR_book}   {opis...}      {jm}
          Wiersz 2: d.{N} {XXXX-XX}    {opis cd.}
          Wiersze kalk: wyrażenie        {jm}   {wartość}
          RAZEM                                 (same w kolumnie wartości)

        Kolumny x:
          < 100    → lp lub d.X
          100–162  → KNR book / activity code
          162–410  → opis
          405–445  → j.m.
          > 445    → wartości Poszcz. i RAZEM
        """
        _LP_PAT      = re.compile(r'^\d+$')
        _D_PAT       = re.compile(r'^d\.[\d.]+$', re.IGNORECASE)          # d.1 / d.1.1 / d.1.2
        _D_MERGED    = re.compile(r'^(d\.[\d.]+?)(\d{4}-\d{2,4})$', re.IGNORECASE)  # d.1.10201-01
        _ACT_PAT     = re.compile(r'^\d{4}-\d{2,4}$')
        _NUM_PAT     = re.compile(r'^-?[\d\s]+[,\.][\d]+$')

        def _parse_val(text):
            try:
                return float(text.replace(' ', '').replace(',', '.'))
            except ValueError:
                return None

        positions = []
        current = None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_rows = []
                for page in pdf.pages:
                    words = page.extract_words(x_tolerance=3, y_tolerance=3)
                    # Wykryj dolną granicę nagłówka kolumn per-strona (wiersz z "Lp.")
                    hdr_word = next((w for w in words if w['text'] == 'Lp.'), None)
                    min_y = (hdr_word['top'] + 12) if hdr_word else _COL_HDR_YMAX
                    content = [w for w in words if min_y <= w['top'] <= _COL_FTR_YMIN]
                    all_rows.extend(_group_words_by_row(content, y_tolerance=4))

            for row in all_rows:
                left  = [w for w in row if w['x0'] < 100]
                # Kolumna KNR kończy się przed x=161 — opis zaczyna się od ~161.9
                # jm zaczyna się od ~402 (szt./kpl. na x=404.9, m2 na x=405.7)
                knr_w = [w for w in row if 100 <= w['x0'] < 161]
                desc  = [w for w in row if 161 <= w['x0'] < 402]
                vals  = [w for w in row if w['x0'] > 445]
                jm_w  = [w for w in row if 402 <= w['x0'] < 445]

                left_text = ' '.join(w['text'] for w in left).strip()
                knr_text  = ' '.join(w['text'] for w in knr_w).strip()

                # Wiersz nagłówka pozycji: left = cyfra lp + KNR lub jm obecne
                # (handles: KNR-W X-XX, KNR K-04, KNR AT-16, kalk. własna)
                if _LP_PAT.match(left_text) and (_KNR_SIMPLE_PATTERN.search(knr_text) or jm_w):
                    if current is not None and current['_q'] != 0:
                        positions.append(self._finalise_coord_pos(current))
                    elif current is not None and current['_vals']:
                        # Suma zebranych wartości
                        current['_q'] = sum(current['_vals'])
                        if current['_q'] > 0:
                            positions.append(self._finalise_coord_pos(current))
                    current = {
                        'lp':    int(left_text),
                        '_k':    [w['text'] for w in knr_w],
                        'opis':  ' '.join(w['text'] for w in desc),
                        'jm':    ' '.join(w['text'] for w in jm_w).strip() or 'szt.',
                        '_q':    0.0,
                        '_vals': [],
                    }
                    continue

                if current is None:
                    continue

                # Wiersz d.X: uzupełnij kod czynności
                # Wariant 1: "d.1.1" + "0236-02" (rozdzielone)
                # Wariant 2: "d.1.10201-01"       (sklejone przez pdfplumber)
                d_merged_m = _D_MERGED.match(left_text)
                if d_merged_m:
                    current['_k'].append(d_merged_m.group(2))
                    desc_text = ' '.join(w['text'] for w in desc).strip()
                    if _is_desc_continuation(desc_text):
                        current['opis'] += ' ' + desc_text
                    continue
                if _D_PAT.match(left_text) and _ACT_PAT.match(knr_text):
                    current['_k'].append(knr_text)
                    desc_text = ' '.join(w['text'] for w in desc).strip()
                    if _is_desc_continuation(desc_text):
                        current['opis'] += ' ' + desc_text
                    continue

                # RAZEM — zapisz pozycję (suma zebranych wartości)
                if any(w['text'] == 'RAZEM' for w in vals):
                    total = sum(current['_vals'])
                    if total > 0:
                        current['_q'] = total
                        positions.append(self._finalise_coord_pos(current))
                    current = None
                    continue

                # Wiersz kalk: wartość w kolumnie vals
                for w in vals:
                    v = _parse_val(w['text'])
                    if v is not None:
                        current['_vals'].append(v)

                # Kontynuacja opisu
                desc_text = ' '.join(w['text'] for w in desc).strip()
                if _is_desc_continuation(desc_text):
                    current['opis'] += ' ' + desc_text

            # Ostatnia pozycja bez RAZEM
            if current is not None and current['_vals']:
                total = sum(current['_vals'])
                if total > 0:
                    current['_q'] = total
                    positions.append(self._finalise_coord_pos(current))

        except Exception as e:
            log.warning("Norma Standard d-parser error: %s", e)
            return []

        log.info("Norma Standard d-parser: %d pozycji", len(positions))
        return positions

    def _parse_with_zuzia_format(self, pdf_path):
        """Parser dla formatu Zuzia (Datacomp).

        Czyta bezpośrednio z PDF: KNR, ilość, nakłady r-g i m-g.
        Nakłady w PLN: R = total_rg × stawka_rg, S = total_mg × stawka_sprzetu.

        Format:
          {lp} KNR {N}/{M}/{K}  lub  {lp} Kalkulacja indywidualna
          {opis...}
          {ilosc} {jm}
          Robocizna razem r-g {norma} {total_rg}
          {material...} {jm} {norma} {total}
          {sprzet...} m-g {norma} {total_mg}
        """
        _POS_PAT   = re.compile(
            r'^(\d+)\s+(KNR\s+[\d/]+(?:\s*\(\d+\))?|Kalkulacja\s+indywidualna)',
            re.IGNORECASE
        )
        _ILOSC_PAT = re.compile(
            r'^([\d\s]+[,\.][\d]+|[\d]+)\s+(m2|m3|m\b|szt\.?|kpl\.?|kg|t|mb|tona|szt)\s*$',
            re.IGNORECASE
        )
        # Robocizna: "Robocizna razem r-g 0,28 210,00"
        _ROB_PAT = re.compile(
            r'^Robocizna\s+razem\s+r-g\s+([\d,\.]+)\s+([\d\s,\.]+)',
            re.IGNORECASE
        )
        # Sprzęt/maszyny: "Nazwa sprzetu m-g 0,5 1,00"
        _SPRZ_PAT = re.compile(
            r'\bm-g\s+([\d,\.]+)\s+([\d\s,\.]+)\s*$',
            re.IGNORECASE
        )
        _HEADER_PAT = re.compile(
            r'^(strona|Opis pozycji|podstawy|wyliczenie|krotno|'
            r'Remont dachu|Przedmiar rob)',
            re.IGNORECASE
        )

        def _parse_num(s):
            try:
                return float(s.replace(' ', '').replace(',', '.'))
            except (ValueError, AttributeError):
                return 0.0

        stawka_rg    = self.params.get('stawka_rg', 35.0)
        stawka_sprz  = self.params.get('stawka_sprzetu', 100.0)

        positions = []
        current = None
        desc_lines = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                full = ''
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        full += t + '\n'

            lines = full.split('\n')
            for line in lines:
                line = line.strip()
                if not line or _HEADER_PAT.match(line):
                    continue

                # --- Nowa pozycja ---
                pos_m = _POS_PAT.match(line)
                if pos_m:
                    if current and current['ilosc'] > 0:
                        current['opis'] = ' '.join(desc_lines)[:300]
                        positions.append(current)
                    current = {
                        'lp':      int(pos_m.group(1)),
                        'podstawa': pos_m.group(2).strip(),
                        'opis':    '',
                        'jm':      'szt.',
                        'ilosc':   0.0,
                        '_R_pdf':  0.0,
                        '_M_pdf':  0.0,
                        '_S_pdf':  0.0,
                    }
                    desc_lines = []
                    continue

                if current is None:
                    continue

                # --- Ilość i j.m. ---
                im = _ILOSC_PAT.match(line)
                if im and current['ilosc'] == 0:
                    current['ilosc'] = _parse_num(im.group(1))
                    current['jm']    = im.group(2)
                    continue

                # --- Robocizna razem r-g ---
                rob_m = _ROB_PAT.match(line)
                if rob_m:
                    total_rg = _parse_num(rob_m.group(2))
                    current['_R_pdf'] += total_rg * stawka_rg
                    continue

                # --- Sprzęt m-g ---
                sprz_m = _SPRZ_PAT.search(line)
                if sprz_m:
                    total_mg = _parse_num(sprz_m.group(2))
                    current['_S_pdf'] += total_mg * stawka_sprz
                    continue

                # --- Opis (tylko przed ilością) ---
                if current['ilosc'] == 0 and re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{3,}', line):
                    desc_lines.append(line)

            # Ostatnia pozycja
            if current and current['ilosc'] > 0:
                current['opis'] = ' '.join(desc_lines)[:300]
                positions.append(current)

        except Exception as e:
            log.warning("Zuzia parser error: %s", e)
            return []

        log.info("Zuzia parser: %d pozycji", len(positions))
        return positions

    def _parse_with_ocr_pipe_table(self, pdf_path):
        """Parser dla skanowanych tabel z separatorami '|' (po OCR).

        Format (OCR skanowanej tabeli z kolumnami):
          lp|KNR 4-03 1140-|Opis robót...|m 150,000|
          d.1.|05 kontynuacja opisu

        KNR może być niekompletny (kończy się '-'), sufiks akcji jest na
        kolejnej linii po d.X.| lub at/aj/zk (OCR artifact).
        """
        _KNR_HEAD = re.compile(
            r'^(\d+|[A-Za-z]{1,2})\s*\|\s*((?:KN+R(?:-[A-Z]+)?|KNNR|NNRNKB|ZKNR|AT|AL)\s+[^|]+?)\s*\|',
            re.IGNORECASE
        )
        _JM_ILOSC = re.compile(
            r'\b(m2|m3|mż|mz|[IJ]m[23]|m\b|szt\.?|kpl\.?|kg|t\b|mb|r-g)\.?\s*(\d[\d\s,\.]*)',
            re.IGNORECASE
        )
        # OCR artefakty jednostek miary
        _JM_OCR_FIX = {
            'mż': 'm2', 'mz': 'm2',
            'im2': 'm2', 'jm2': 'm2',
            'im3': 'm3', 'jm3': 'm3',
        }
        # _SUFFIX_PAT — zdefiniowany na poziomie modułu
        _KNR_INCOMPLETE = re.compile(r'-\s*$')
        _HAS_ACTION = re.compile(r'\d{4}-\d{2}')

        def _pnum(s):
            try:
                return float(re.sub(r'[^\d,.]', '', s).replace(',', '.'))
            except (ValueError, AttributeError):
                return 0.0

        positions = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full = '\n'.join(page.extract_text() or '' for page in pdf.pages)
            if full.count('|') < 5:
                return []
            if not re.search(r'\|(?:KN+R|KNNR|NNRNKB)', full, re.IGNORECASE):
                return []

            lines = full.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                hm = _KNR_HEAD.match(line)
                if not hm:
                    continue
                try:
                    lp = int(hm.group(1))
                except ValueError:
                    lp = len(positions) + 1
                knr_raw = hm.group(2).strip()

                # Ilość i jm — szukaj w całej linii
                rest = line[hm.end():]
                jm_m = _JM_ILOSC.search(rest)
                if not jm_m:
                    continue
                jm = jm_m.group(1).rstrip('.')
                jm = _JM_OCR_FIX.get(jm.lower(), jm)
                ilosc = _pnum(jm_m.group(2))
                if ilosc <= 0:
                    continue

                # Opis — tekst między KNR a jm
                opis_raw = rest[:jm_m.start()].strip().strip('|').strip()

                # Uzupełnij niekompletny KNR z kolejnej linii
                knr = knr_raw.rstrip('_ ')
                if _KNR_INCOMPLETE.search(knr):
                    for j in range(i + 1, min(i + 4, len(lines))):
                        nxt = lines[j].strip()
                        sm = _SUFFIX_PAT.search(nxt)
                        if sm:
                            suffix = sm.group(1)
                            # OCR "103" → sufiks "03"
                            if len(suffix) == 3 and suffix[0] == '1':
                                suffix = suffix[1:]
                            knr = knr.rstrip('- ') + '-' + suffix
                            break
                        bare = re.match(r'^[\d./]+[/.](\d{2})\s*$', nxt)
                        if bare:
                            knr = knr.rstrip('- ') + '-' + bare.group(1)
                            break
                elif ' _ ' in knr_raw or '_' in knr_raw:
                    # NNRNKB 202 _ — szukaj action na nast. linii
                    for j in range(i + 1, min(i + 4, len(lines))):
                        nxt = lines[j].strip()
                        sm = _SUFFIX_PAT.search(nxt)
                        if sm:
                            knr = knr + ' ' + sm.group(1)
                            break
                elif not _HAS_ACTION.search(knr):
                    # KNR bez numeru akcji (np. ZKNR C-2) — szukaj akcji na nast. linii
                    for j in range(i + 1, min(i + 4, len(lines))):
                        nxt = lines[j].strip()
                        sm = _SUFFIX_PAT.search(nxt)
                        if sm:
                            suffix = sm.group(1)
                            if len(suffix) == 3 and suffix[0] == '1':
                                suffix = suffix[1:]
                            knr = knr + ' ' + suffix
                            break

                # Zbierz kontynuację opisu
                opis = opis_raw
                for j in range(i + 1, min(i + 4, len(lines))):
                    nxt = lines[j].strip()
                    if not nxt or re.match(r'^\d+\|', nxt) or nxt.startswith('Razem'):
                        break
                    pipe_part = nxt.split('|')[-1].strip() if '|' in nxt else nxt
                    if pipe_part and re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{3,}', pipe_part):
                        opis += ' ' + pipe_part

                positions.append({
                    'lp':          lp,
                    'podstawa':    knr,
                    'opis':        opis.strip()[:300],
                    'jm':          jm or 'szt.',
                    'ilosc':       ilosc,
                    'formula_str': '',
                })

        except Exception as e:
            log.warning("OCR pipe-table parser error: %s", e)
            return []

        log.info("OCR pipe-table parser: %d pozycji", len(positions))
        return positions

    def _parse_with_norma_kosztorys_format(self, pdf_path):
        """Parser dla formatu kosztorysu ofertowego Norma PRO.

        Struktura kolumn (x0):
          < 50        → Lp
          50 – 112    → Podstawa (KNR katalog, np. "KNR 9-29")
          112 – 350   → Opis + numer czynności KNR na 2. wierszu
          350 – 390   → j.m.
          ≥ 520       → Wartości R/M/S (suma dla pozycji)

        Każda pozycja ma:
          wiersz 1:  lp | KNR_katalog | opis_start     | jm
          wiersz 2:       d.X. NN AAAA-BB kontynuacja_opisu
          wiersz n:       obmiar = XXX jm
          wiersz n:  * Robocizna  r-g  nakłady        | R_total
          wiersz n:  * Materiały  zł   nakłady         | M_total
          wiersz n:  * Sprzęt     m-g  nakłady         | S_total
        """
        positions = []
        current = None
        _KNR_CAT = re.compile(
            r'^(?:KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\s*[\d]', re.IGNORECASE
        )
        _ACT_PAT = re.compile(r'\b(\d{4}-\d{2})')
        _D_PREFIX = re.compile(r'^d\.\d+\.\s*\d*\s*\d{4}-\d{2}', re.IGNORECASE)

        def _float_from_words(words):
            """Łączy tokeny liczbowe i parsuje jako float (format PL: spacja=tys, ,=dz.)."""
            text = ''.join(w['text'] for w in sorted(words, key=lambda w: w['x0']))
            clean = re.sub(r'[^\d,]', '', text)
            try:
                return float(clean.replace(',', '.'))
            except ValueError:
                return 0.0

        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_rows = []
                for page in pdf.pages:
                    words = page.extract_words(x_tolerance=3, y_tolerance=3)
                    content = [w for w in words if w['top'] >= _NK_HDR_YMIN]
                    all_rows.extend(_group_words_by_row(content, y_tolerance=4))
        except Exception as e:
            log.warning("Norma kosztorys parser error: %s", e)
            return []

        for row in all_rows:
            lp_words  = [w for w in row if w['x0'] < _NK_LP_XMAX]
            knr_words = [w for w in row if _NK_KNR_XMIN <= w['x0'] < _NK_KNR_XMAX]
            opis_words = [w for w in row if _NK_KNR_XMAX <= w['x0'] < _NK_OPIS_XMAX]
            jm_words  = [w for w in row if _NK_OPIS_XMAX <= w['x0'] < _NK_JM_XMAX]
            val_words = [w for w in row if w['x0'] >= _NK_VAL_XMIN]

            lp_text  = ' '.join(w['text'] for w in lp_words).strip()
            knr_text = ' '.join(w['text'] for w in knr_words).strip()
            opis_text = ' '.join(w['text'] for w in opis_words).strip()
            jm_text  = ' '.join(w['text'] for w in jm_words).strip()

            # ── Nowa pozycja ─────────────────────────────────
            if re.match(r'^\d+$', lp_text) and _KNR_CAT.match(knr_text):
                if current is not None and current['_q'] > 0:
                    positions.append(self._finalise_norma_pos(current))
                current = {
                    'lp':      int(lp_text),
                    '_knr_cat': knr_text,
                    '_knr_act': '',
                    'opis':    opis_text,
                    'jm':      jm_text or 'szt.',
                    '_r': 0.0, '_m': 0.0, '_s': 0.0, '_q': 0.0,
                }
                continue

            if current is None:
                continue

            # ── Numer czynności KNR (2. wiersz pozycji) ──────
            if not current['_knr_act'] and opis_text:
                act_m = _ACT_PAT.search(opis_text)
                if act_m:
                    current['_knr_act'] = act_m.group(1)
                    # Bierz tekst od końca numeru czynności (pomija "d.X. NN AAAA-BB")
                    cleaned = opis_text[act_m.end():].strip()
                    # Usuń fragmenty "N analogia", KNR-referencje i inne nieopisy
                    cleaned = re.sub(r'\b\d+\s+analogia\b', '', cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r'\b\d+\s+KNR\b.*', '', cleaned, flags=re.IGNORECASE)
                    cleaned = cleaned.strip()
                    if cleaned and _is_desc_continuation(cleaned):
                        current['opis'] += ' ' + cleaned
                    # jm może być na tym samym wierszu co activity
                    if jm_text:
                        current['jm'] = jm_text
                    continue

            # ── Aktualizacja j.m. (jm jest na osobnym wierszu PDF) ──
            if jm_text and not opis_text and not knr_text and not lp_text:
                current['jm'] = jm_text
                continue

            # Tekst całego wiersza (knr+opis) — "*" i "obmiar" mogą być przy x0≈110
            row_content = (knr_text + ' ' + opis_text).strip()

            # ── Pomiń rozdzielacze i wiersze podsumowania ─────
            # "-- R --", "-- M --", "-- S --", "Razem koszty...", "Cena jednostkowa"
            if (knr_text == '--'
                    or re.match(r'^[RMS]\s*--\s*$', opis_text)
                    or re.match(r'^(Razem|Cena)\b', row_content, re.IGNORECASE)):
                continue

            # ── Obmiar (ilość) ────────────────────────────────
            if re.match(r'obmiar', row_content, re.IGNORECASE):
                all_text = ' '.join(w['text'] for w in row)
                # Wyciągnij formułę: tekst między "obmiar" a "= LICZBA"
                formula_m = re.search(
                    r'obmiar\s+(.+?)\s*=\s*[\d,\.]+', all_text, re.IGNORECASE
                )
                if formula_m:
                    raw = formula_m.group(1).strip()
                    if raw and re.search(r'[\d\+\-\*\/\(\)]', raw):
                        current['_formula'] = raw
                qty_m = re.search(r'=\s*([\d,\.]+)', all_text)
                if qty_m:
                    try:
                        current['_q'] = float(
                            qty_m.group(1).replace(' ', '').replace(',', '.')
                        )
                    except ValueError:
                        pass
                continue

            # ── Wartości R / M / S ────────────────────────────
            # "*" może być w kolumnie lp (x0<50) lub knr (x0∈[50,112))
            all_row_text = ' '.join(w['text'] for w in row)
            rms_row = (
                row_content.startswith('*')
                or any(w['text'] == '*' for w in lp_words)
                or re.match(r'^\*', knr_text)
            )
            if rms_row and val_words:
                val = _float_from_words(val_words)
                content_lower = all_row_text.lower()
                if 'robocizna' in content_lower:
                    current['_r'] = val
                elif 'materia' in content_lower:
                    current['_m'] = val
                elif 'sprz' in content_lower:
                    current['_s'] = val
                continue

            # Pomiń wiersze z formułami nakładów (np. "1,0000 r-g/szt * 35,00 zł/r-g")
            if _NAKLAD_FORMULA_PAT.search(all_row_text):
                continue

            # ── Kontynuacja opisu ─────────────────────────────
            if opis_text and _is_desc_continuation(opis_text):
                current['opis'] += ' ' + opis_text

        if current is not None and current['_q'] > 0:
            positions.append(self._finalise_norma_pos(current))

        log.info("Norma kosztorys parser: %d pozycji", len(positions))
        return positions

    def _finalise_norma_pos(self, pos):
        """Buduje słownik pozycji z wewnętrznego stanu parsera kosztorysu."""
        knr_cat = pos['_knr_cat']
        knr_act = pos['_knr_act']
        podstawa = f"{knr_cat} {knr_act}".strip() if knr_act else knr_cat
        return {
            'lp':          pos['lp'],
            'podstawa':    podstawa,
            'opis':        _WHITESPACE_PATTERN.sub(' ', pos['opis']).strip()[:300],
            'jm':          pos['jm'],
            'ilosc':       pos['_q'],
            '_R_pdf':      pos['_r'],
            '_M_pdf':      pos['_m'],
            '_S_pdf':      pos['_s'],
            'formula_str': pos.get('_formula', ''),
        }

    def _finalise_coord_pos(self, pos):
        """Przekształca wewnętrzny dict na format pipeline."""
        knr = _reconstruct_knr_code(pos.pop('_k', []))
        q   = pos.pop('_q', 0.0)
        return {
            'lp':          pos['lp'],
            'podstawa':    knr,
            'opis':        _WHITESPACE_PATTERN.sub(' ', pos['opis']).strip()[:300],
            'jm':          pos['jm'],
            'ilosc':       q,
            'formula_str': pos.pop('_formula', ''),
        }

    def _diagnose_empty_result(self, pdf_path, full_text: str):
        """Loguje pomocną diagnozę gdy żaden parser nie znalazł pozycji."""
        name = Path(pdf_path).name
        has_knr = bool(_KNR_SIMPLE_PATTERN.search(full_text))
        text_len = len(full_text.strip())

        if text_len < 100:
            log.warning(
                "Brak pozycji w '%s': PDF zawiera tylko %d znaków tekstu — "
                "może być skanem. Spróbuj OCR: ocrmypdf \"%s\" \"%s\"",
                name, text_len, pdf_path, pdf_path.replace('.pdf', '_ocr.pdf')
            )
        elif not has_knr:
            log.warning(
                "Brak pozycji w '%s': PDF ma tekst (%d znaków) ale nie zawiera "
                "żadnych kodów KNR/KNNR. Sprawdź czy to przedmiar robót budowlanych.",
                name, text_len
            )
        else:
            log.warning(
                "Brak pozycji w '%s': PDF zawiera kody KNR ale żaden parser "
                "nie rozpoznał formatu. Sprawdź czy to przedmiar Norma PRO "
                "(formaty SST, d.X lub tabelaryczny).",
                name
            )

    def _find_naklady(self, podstawa, opis):
        """Znajduje nakłady R/M/S dla pozycji.

        Returns:
            (r, m, s, confidence, source, matched_knr)
            confidence: 0.0–1.0 (pewność dopasowania)
            source: 'ai', 'exact', 'fuzzy', 'default'
            matched_knr: pełny KNR z bazy lub podstawa jeśli brak dopasowania
        """
        # Użyj KNR Matcher z AI jeśli dostępny
        if self.knr_matcher:
            try:
                result = self.knr_matcher.match(opis, podstawa)
                if result.confidence >= 0.5:
                    log.debug("KNR Match: %s (%.2f) - %s",
                              result.knr_code, result.confidence, result.source)
                    r, m, s = self._get_naklady_for_knr(result.knr_code)
                    if r > 0 or m > 0 or s > 0:
                        return r, m, s, result.confidence, result.source, result.knr_code
            except Exception as e:
                log.warning("KNR Matcher error: %s", e)

        # Fallback: szukaj po KNR używając indeksu O(1) + partial match O(N)
        podstawa_norm = _WHITESPACE_PATTERN.sub('', podstawa.upper())

        # Dokładne dopasowanie
        if podstawa_norm in self._naklady_index:
            n = self._naklady_index[podstawa_norm]
            return n.get('R', 0), n.get('M', 0), n.get('S', 0), 0.95, 'exact', n.get('knr', podstawa)

        # Częściowe dopasowanie (tylko gdy podstawa niepusta — pusta pasuje do WSZYSTKIEGO)
        if podstawa_norm:
            for knr_norm, n in self._naklady_index.items():
                if podstawa_norm in knr_norm or knr_norm in podstawa_norm:
                    return n.get('R', 0), n.get('M', 0), n.get('S', 0), 0.7, 'partial', n.get('knr', podstawa)

        # Dokładne dopasowanie po opisie (dla pozycji bez KNR wyekstrahowanych z ATH)
        opis_key_norm = _WHITESPACE_PATTERN.sub('', ('OPIS:' + opis.upper().strip()))
        if opis_key_norm in self._naklady_index:
            n = self._naklady_index[opis_key_norm]
            return n.get('R', 0), n.get('M', 0), n.get('S', 0), 0.85, 'opis_exact', n.get('knr', podstawa)

        # Szukaj po opisie (fuzzy)
        opis_lower = opis.lower()
        opis_words = set(opis_lower.split())
        best_match = None
        best_score = 0

        for n in self._naklady_index.values():
            n_opis = n.get('opis', '').lower()
            n_words = set(n_opis.split())
            common = len(opis_words & n_words)
            if common > best_score:
                best_score = common
                best_match = n

        if best_match and best_score >= 5:
            return best_match.get('R', 0), best_match.get('M', 0), best_match.get('S', 0), 0.4, 'fuzzy', best_match.get('knr', podstawa)

        # Brak dopasowania — zwróć 0 żeby nie zaśmiecać kosztorysu fałszywymi cenami
        log.warning(
            "Brak nakladow KNR dla '%s' ('%s') — pozycja bez wyceny (R=M=S=0)",
            podstawa, opis[:60],
        )
        return 0.0, 0.0, 0.0, 0.0, 'default', podstawa

    def _get_naklady_for_knr(self, knr_code):
        """Pobierz nakłady R/M/S dla konkretnego kodu KNR"""
        knr_norm = _WHITESPACE_PATTERN.sub('', knr_code.upper())

        # Dokładne dopasowanie
        if knr_norm in self._naklady_index:
            n = self._naklady_index[knr_norm]
            return n.get('R', 0), n.get('M', 0), n.get('S', 0)

        # Częściowe dopasowanie
        for k, n in self._naklady_index.items():
            if knr_norm in k or k in knr_norm:
                return n.get('R', 0), n.get('M', 0), n.get('S', 0)

        return 0, 0, 0
    
    def validate_pozycje(self, pozycje):
        """Waliduje wszystkie pozycje"""
        log.debug("Walidacja...")
        
        errors = []
        warnings = []
        
        # Walidacja każdej pozycji
        for poz in pozycje:
            result = self.calc_validator.validate_cena_jednostkowa(poz, self.params)
            if result.status.value == 'CALC_MISMATCH':
                warnings.append(f"Poz {poz['lp']}: {result.message}")
        
        # Walidacja logiki
        logic_results = self.logic_validator.validate_all(pozycje)
        for r in logic_results:
            if r.status.value == 'ERROR':
                errors.append(r.message)
            elif r.status.value == 'WARNING':
                warnings.append(r.message)
        
        if errors:
            log.warning("Bledy walidacji (%d):", len(errors))
            for e in errors[:5]:
                log.warning("  - %s", e)
        
        if warnings:
            log.warning("Ostrzezenia (%d):", len(warnings))
            for w in warnings[:5]:
                log.warning("  - %s", w)
        
        if not errors and not warnings:
            log.debug("Walidacja OK")
        
        return errors, warnings
    
    def calculate_kosztorys(self, pozycje):
        """
        Przelicza kosztorys z narzutami
        Używa Calculator Engine - ZAWSZE oblicza od zera!
        """
        # Użyj Calculator Engine (Single Source of Truth)
        engine = CalculatorEngine(self.params)
        dzialy, podsumowanie = engine.calculate(pozycje)
        
        # Konwertuj na format dla generatorów
        dane = engine.to_dict(dzialy, podsumowanie)
        
        # Wyciągnij pozycje z działów (płaska lista)
        przeliczone = []
        for dzial in dane['dzialy']:
            for poz in dzial['pozycje']:
                poz['dzial'] = dzial['nazwa']
                przeliczone.append(poz)
        
        return przeliczone, dane['podsumowanie']
    
    def generate_ath(self, pozycje, podsumowanie, dane_tytulowe, output_path):
        """Generuje plik ATH (format Norma PRO) - deleguje do ATHGenerator"""
        log.info("Generowanie ATH: %s", output_path)

        ath_gen = ATHGenerator(self.params)
        try:
            result = ath_gen.generate(pozycje, podsumowanie, dane_tytulowe, output_path)
        except Exception as e:
            raise NormaPROError(f"Błąd generowania ATH '{output_path}': {e}") from e

        log.info("Zapisano ATH: %s", output_path)
        return result
    
    def generate_pdf(self, pozycje, podsumowanie, dane_tytulowe, output_path):
        """Generuje plik PDF"""
        log.info("Generowanie PDF: %s", output_path)
        
        # Grupuj pozycje po działach
        dzialy = {}
        for poz in pozycje:
            dzial = poz.get('dzial', 'Kosztorys')
            if dzial not in dzialy:
                dzialy[dzial] = []
            dzialy[dzial].append(poz)
        
        # Przygotuj dane
        dane = {
            'tytul': {
                **dane_tytulowe,
                **self.params,
                'wartosc_netto': podsumowanie['wartosc_netto'],
            },
            'dzialy': [
                {'nazwa': nazwa, 'pozycje': poz_list}
                for nazwa, poz_list in dzialy.items()
            ],
            'podsumowanie': {
                **podsumowanie,
                **self.params,
            }
        }
        
        # Dodaj nakłady do pozycji
        for dzial in dane['dzialy']:
            for poz in dzial['pozycje']:
                poz['naklady'] = self._generate_naklady(poz)
        
        generuj_pdf(dane, output_path)
        log.info("Zapisano PDF: %s", output_path)
        return output_path
    
    def _generate_naklady(self, poz):
        """Generuje szczegółowe nakłady dla pozycji"""
        naklady = []
        ilosc = poz.get('ilosc', 1) or 1
        stawka_rg = self.params['stawka_rg'] or 35.0
        stawka_sprzetu = self.params['stawka_sprzetu'] or 100.0

        if poz.get('R', 0) > 0:
            r_g = poz['R'] / stawka_rg
            naklady.append({
                'typ': 'R',
                'nazwa': 'Robocizna',
                'jednostka': 'r-g',
                'wartosc': r_g,
                'cena': stawka_rg,
                'opis': f"{r_g/ilosc:.4f} r-g/{poz['jm']} * {stawka_rg:.2f} zł/r-g"
            })

        if poz.get('M', 0) > 0:
            naklady.append({
                'typ': 'M',
                'nazwa': 'Materiały',
                'jednostka': 'zł',
                'wartosc': 1,
                'cena': poz['M'],
                'opis': f"materiały"
            })

        if poz.get('S', 0) > 0:
            m_g = poz['S'] / stawka_sprzetu
            naklady.append({
                'typ': 'S',
                'nazwa': 'Sprzęt',
                'jednostka': 'm-g',
                'wartosc': m_g,
                'cena': stawka_sprzetu,
                'opis': f"{m_g/ilosc:.4f} m-g/{poz['jm']} * {stawka_sprzetu:.2f} zł/m-g"
            })

        return naklady
    
    def generate(self, pdf_path, dane_tytulowe=None, output_ath=None, output_pdf=None):
        """
        Główna funkcja - generuje kosztorys z przedmiaru
        
        Args:
            pdf_path: ścieżka do przedmiaru PDF
            dane_tytulowe: słownik z danymi tytułowymi
            output_ath: ścieżka do pliku ATH (opcjonalnie)
            output_pdf: ścieżka do pliku PDF (opcjonalnie)
        
        Returns:
            dict z ścieżkami wygenerowanych plików
        """
        # Domyślne dane tytułowe
        if not dane_tytulowe:
            dane_tytulowe = {
                'nazwa_inwestycji': Path(pdf_path).stem,
                'adres_inwestycji': '',
                'inwestor': '',
                'adres_inwestora': '',
                'wykonawca': '',
                'adres_wykonawcy': '',
                'branza': 'budowlana',
                'sporzadzil': '',
                'data': datetime.now().strftime('%m.%Y'),
            }
        
        # Domyślne ścieżki wyjściowe
        base_name = Path(pdf_path).stem
        if not output_ath:
            output_ath = str(Path(pdf_path).parent / f"{base_name}_kosztorys.ath")
        if not output_pdf:
            output_pdf = str(Path(pdf_path).parent / f"{base_name}_kosztorys.pdf")
        
        # 1. Parsuj przedmiar
        pozycje = self.parse_przedmiar_pdf(pdf_path)
        
        if not pozycje:
            raise PDFParsingError(
                f"Nie znaleziono pozycji przedmiarowych w '{Path(pdf_path).name}'. "
                "Sprawdź logi (--verbose) po szczegółową diagnozę."
            )
        
        # 1b. AI Matcher dla pozycji bez dopasowania (tylko gdy ANTHROPIC_API_KEY dostępny)
        if os.environ.get("ANTHROPIC_API_KEY"):
            unmatched_idx = [
                i for i, p in enumerate(pozycje)
                if p.get('knr_source') == 'default'
            ]
            if unmatched_idx:
                try:
                    import ai_knr_matcher
                    unmatched_input = [
                        {'opis': pozycje[i]['opis'], 'jm': pozycje[i]['jm'], 'podstawa': pozycje[i]['podstawa']}
                        for i in unmatched_idx
                    ]
                    ai_matches = ai_knr_matcher.match_unmatched_positions(
                        unmatched_input, self._naklady_index
                    )
                    for local_i, poz_i in enumerate(unmatched_idx):
                        knr = ai_matches.get(str(local_i))
                        if knr:
                            r, m, s = self._get_naklady_for_knr(knr)
                            if r or m or s:
                                pozycje[poz_i]['R'] = r * pozycje[poz_i]['ilosc']
                                pozycje[poz_i]['M'] = m * pozycje[poz_i]['ilosc']
                                pozycje[poz_i]['S'] = s * pozycje[poz_i]['ilosc']
                                pozycje[poz_i]['podstawa'] = knr
                                pozycje[poz_i]['knr_source'] = 'ai'
                                pozycje[poz_i]['knr_confidence'] = 0.6
                                log.info("AI dopasowało: '%s' → %s", pozycje[poz_i]['opis'][:50], knr)
                except Exception as e:
                    log.warning("AI matcher failed: %s", e)

        # 2. Waliduj
        errors, warnings = self.validate_pozycje(pozycje)
        
        # 3. Przelicz
        pozycje, podsumowanie = self.calculate_kosztorys(pozycje)
        
        # 4. Generuj
        results = {}
        
        if output_ath:
            results['ath'] = self.generate_ath(pozycje, podsumowanie, dane_tytulowe, output_ath)
        
        if output_pdf:
            results['pdf'] = self.generate_pdf(pozycje, podsumowanie, dane_tytulowe, output_pdf)
        
        # Podsumowanie
        log.info("PODSUMOWANIE: Pozycji=%d | R=%s | M=%s | S=%s | Kp=%s | Z=%s | NETTO=%s | BRUTTO=%s zl",
                 len(pozycje),
                 fmt_summary(podsumowanie['suma_R']),
                 fmt_summary(podsumowanie['suma_M']),
                 fmt_summary(podsumowanie['suma_S']),
                 fmt_summary(podsumowanie['koszty_posrednie']),
                 fmt_summary(podsumowanie['zysk']),
                 fmt_summary(podsumowanie['wartosc_netto']),
                 fmt_summary(podsumowanie['wartosc_brutto']))
        
        return results


# CLI przeniesione do cli.py
# Użyj: python cli.py przedmiar.pdf [--ath] [--pdf] [--nazwa "..."]

if __name__ == "__main__":
    print("CLI zostało przeniesione do cli.py")
    print("Użycie: python cli.py przedmiar.pdf [--ath] [--pdf] [--nazwa '...']")
    print()
    print("Jako bibliotekę użyj:")
    print("  from kosztorys_generator import KosztorysGenerator")
    print("  gen = KosztorysGenerator()")
    print("  gen.generate('przedmiar.pdf', output_ath='out.ath')")
