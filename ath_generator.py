# -*- coding: utf-8 -*-
"""
ATH Generator v6.0
Generator plików ATH (format Norma PRO / Athenasoft)

Format wzorowany na prawdziwych plikach ATH z Normy PRO:
- pd= z referencją KNR, kj=0, cj=0, wn= puste
- [RMS ZEST N] = definicje zasobów z cenami
  ZEST 1 = R (robocizna, stawka_rg)
  ZEST 2 = M zbiorcze (fallback ce=1 dla pozycji bez danych materiałowych)
  ZEST 3 = S (sprzęt, stawka_sprzetu)
  ZEST 4..N = indywidualne materiały z realnymi cenami
- [RMS N] per pozycja: N = numer ZEST
  Norma PRO sama oblicza kj/wn z RMS
"""

import hashlib
import json
import logging
import math
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from formatters import fmt_ath as fmt


log = logging.getLogger(__name__)


# ── Formattery ────────────────────────────────────────────────────────────────

def _dot(val: float, decimals: int = 4) -> str:
    """Liczba z PRZECINKIEM — dla pól nz=, il=, ob= w ATH (format Norma PRO)."""
    if not math.isfinite(val):
        return "0"
    return f"{val:.{decimals}f}".replace(".", ",").rstrip("0").rstrip(",") or "0"


# ── Korekty jednostek miary materiałów ───────────────────────────────────────
# Aplikowane do WSZYSTKICH materiałów (DB + AI cache + fallback)

_JM_CORRECTIONS_ATH = {
    # Przewody i kable → m
    'kabel': 'm', 'przewód': 'm', 'przewod': 'm', 'linka': 'm',
    'kable solar': 'm', 'kable solarne': 'm',
    # Rury i kanały → m
    'rura': 'm', 'rurka': 'm', 'rury': 'm', 'rurociąg': 'm', 'rurociag': 'm',
    'rury winidur': 'm', 'winidur': 'm',
    # Taśmy, bednarka, drut → m
    'bednarka': 'm', 'taśma': 'm', 'tasma': 'm', 'drut': 'm',
    # Profile, kątowniki → m
    'listwa': 'm', 'profil': 'm', 'kątownik': 'm', 'katownik': 'm',
    # Elementy szt
    'wspornik': 'szt', 'uchwyt': 'szt', 'obejma': 'szt',
    'śruba': 'szt', 'sruba': 'szt', 'wkręt': 'szt', 'wkret': 'szt',
    'nakrętka': 'szt', 'nakretka': 'szt', 'podkładka': 'szt', 'podkladka': 'szt',
    'puszka': 'szt', 'skrzynka': 'szt', 'rozdzielnica': 'szt',
    'wyłącznik': 'szt', 'wylacznik': 'szt', 'łącznik': 'szt', 'lacznik': 'szt',
    'gniazdo': 'szt', 'wtyk': 'szt', 'wtyczka': 'szt',
    'bezpiecznik': 'szt', 'wkładka': 'szt',
    'lampa': 'szt', 'oprawa': 'szt', 'świetlówka': 'szt', 'swietlowka': 'szt',
    'żarówka': 'szt', 'zarowka': 'szt',
    'zawór': 'szt', 'zawor': 'szt', 'kurek': 'szt',
    'klips': 'szt', 'końcówka': 'szt', 'koncowka': 'szt', 'tulejka': 'szt',
    'złączka': 'szt', 'zlaczka': 'szt', 'kołek': 'szt', 'kolek': 'szt',
    'panel fotowoltaic': 'szt', 'panel pv': 'szt', 'moduł': 'szt', 'modул': 'szt',
    'falownik': 'szt', 'inwerter': 'szt', 'sterownik': 'szt',
    'konstrukcja wsporcza': 'szt', 'konstrukcje wsporcze': 'szt',
    'dzwonek': 'szt', 'sygnalizator': 'szt', 'czujnik': 'szt', 'detektor': 'szt',
    # Blachy, płyty metalowe → kg (PRZED 'lakier' — blacha lakierowana nie może dostać jm='l')
    'blacha': 'kg',
    # Masy i farby → kg/l
    'klej': 'kg', 'cement': 'kg', 'zaprawa': 'kg',
    'farba': 'l', 'lakier': 'l',
    # Ciecze instalacyjne → l
    'preparat': 'l', 'primer': 'l', 'żywica': 'l', 'zywica': 'l',
    'plastyfikator': 'l', 'emulsja': 'l',
    # Elementy betonowe prefabrykowane → szt
    'krąg': 'szt', 'krag': 'szt', 'pokrywa': 'szt',
    'właz': 'szt', 'wlaz': 'szt',
}

# Normalizacja niestandardowych JM → format ATH (lowercase, bez kropki)
_GARBLED_JM = {
    'dm?': 'dm3', 'mm?': 'mm2', 'cm?': 'cm2', 'm?': 'm2',  # garbled superscripts
    'dm³': 'dm3', 'dm²': 'dm2', 'mm²': 'mm2', 'm²': 'm2', 'm³': 'm3',  # unicode superscripts
    'l': 'l', 'L': 'l',        # litr wielką literą
    'szt.': 'szt', 'kpl.': 'kpl', 'mb.': 'mb', 'm.b.': 'mb',  # kropki
    'opak': 'kpl', 'rolka': 'szt', 'rol': 'szt', 'par': 'szt', 'para': 'szt',
    'szp': 'szt', 'butelka': 'szt',
}


def _fix_superscripts(text: str) -> str:
    """Naprawia garbled superscripts w tekście materiału: mm? → mm², dm? → dm³.
    Znak '?' pojawia się gdy PDF parser nie zdekodował ²/³ przed wywołaniem AI."""
    if not text or '?' not in text:
        return text
    text = re.sub(r'\bdm\?', 'dm\u00b3', text)   # dm? → dm³
    text = re.sub(r'\bmm\?', 'mm\u00b2', text)   # mm? → mm²
    text = re.sub(r'\bcm\?', 'cm\u00b2', text)   # cm? → cm²
    text = re.sub(r'(?<![md]m)\bm\?', 'm\u00b2', text)  # m? → m² (nie mm?, dm?)
    return text


def _apply_jm_corrections(mats: list) -> list:
    """Koryguje jm materiałów na podstawie słownika — stosowane do wszystkich źródeł.
    Przy okazji czyści garbled superscripts (dm?→dm³, mm?→mm²) w nazwach i jm."""
    result = []
    for mat in mats:
        # Napraw garbled chars w nazwie (AI reprodukuje je z garbled PDF input)
        name = _fix_superscripts(mat.get('name') or '')
        name_l = name.lower()
        # Normalizuj jm: garbled chars, unicode superscripts, kropki, niestandardowe nazwy
        raw_jm = (mat.get('jm') or 'szt').strip()
        corrected_jm = _GARBLED_JM.get(raw_jm, _GARBLED_JM.get(raw_jm.lower(), raw_jm))
        for fragment, correct_jm in _JM_CORRECTIONS_ATH.items():
            if fragment in name_l:
                corrected_jm = correct_jm
                break
        result.append({**mat, 'name': name, 'jm': corrected_jm})
    return result


# ── Jednostki ─────────────────────────────────────────────────────────────────

JEDNOSTKI_KODY = {
    "szt.": "020", "szt": "020",
    "m": "010", "mb": "010", "m.b.": "010",
    "m2": "050", "m²": "050", "mkw": "050",
    "m3": "060", "m³": "060",
    "dm3": "060", "dm³": "060", "l": "060",   # litr / dm³ → kod objętości
    "kg": "033",
    "t": "063",
    "kpl": "090", "kpl.": "090",
    "r-g": "149",
    "m-g": "150",
}


def get_jm_code(jm: str) -> str:
    if not jm:
        return "020"
    jm_clean = jm.lower().strip().replace(" ", "").replace(".", "")
    for key, code in JEDNOSTKI_KODY.items():
        if key.replace(".", "") == jm_clean:
            return code
    return "020"


# ── Parser podstawy ───────────────────────────────────────────────────────────

def _parse_podstawa(podstawa: str) -> Tuple[str, str, str]:
    """Rozkłada podstawę KNR na (typ, short, num).

    "KNR 4-01 0354-09"   → ('KNR', '4-01', '0354-09')
    "KNR-W 2-18 0434-02" → ('KNR-W', '2-18', '0434-02')
    "KNNR 1 0111-01"     → ('KNNR', '1', '0111-01')
    "KNR 45/1/2"         → ('KNR', '45/1/2', '')   # format Zuzia
    "KNR 401/350/1"      → ('KNR', '401/350/1', '') # format Zuzia
    """
    if not podstawa:
        return '', '', ''
    s = podstawa.strip()

    # Format Zuzia: "KNR N/M/K" — ukośniki zamiast spacji
    if '/' in s:
        mz = re.match(
            r'^(KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)\s+([\d/]+(?:\s*\(\d+\))?)',
            s, re.IGNORECASE,
        )
        if mz:
            code = mz.group(2).strip()
            if '/' in code:
                short, num = code.rsplit('/', 1)
            else:
                short, num = code, ''
            return mz.group(1).upper(), short, num

    m = re.match(
        r'^(KN+R(?:-[A-Z]+)?|KSNR|KNK|AT|AL)'
        r'\s+'
        r'([A-Za-z]*-?[\d]+-?[\d]*)'
        r'(?:\s+(\d{4}-\d{2}))?',
        s, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper(), m.group(2), (m.group(3) or '')
    return '', '', ''


def _podstawa_to_norm(podstawa: str) -> str:
    """Normalizuje podstawę KNR do klucza DB (identycznie jak extract_materialy)."""
    typ, short, num = _parse_podstawa(podstawa)
    if not typ:
        return ''
    return re.sub(r'\s+', '', f"{typ}{short}{num}".upper())


# ── Pomocnicze ────────────────────────────────────────────────────────────────

# Czasowniki oznaczające czynności — nie powinny być nazwami materiałów
_ACTION_VERBS = {
    'demontaż', 'montaż', 'rozebranie', 'rozbiórka', 'wykonanie', 'układanie',
    'roboty', 'prace', 'instalacja', 'wymiana', 'naprawa', 'czyszczenie',
    'malowanie', 'oczyszczenie', 'załadunek', 'transport', 'wywóz', 'usunięcie',
    'odtłuszczenie', 'obróbka', 'wykucie', 'zamurowanie', 'tynkowanie',
    'betonowanie', 'zbrojenie', 'szpachlowanie', 'gruntowanie', 'izolacja',
    'zeskrobanie', 'skucie', 'odbicie', 'kucie', 'ługowanie', 'przecieranie',
    'zasypanie', 'zagęszczenie', 'uzupełnienie', 'nawiercenie', 'przebicie',
    'likwidacja', 'likwidacja', 'demontowanie', 'rozbieranie', 'skuwanie',
}


def _is_action_name(name: str) -> bool:
    """Zwraca True jeśli nazwa wygląda jak czynność, nie materiał.
    Ignoruje prefiksy w nawiasach, np. '(z.VII) Gruntowanie...'"""
    if not name:
        return False
    # Usuń wiodące fragmenty w nawiasach: "(z.VII)", "(pkt.3)" itp.
    s = re.sub(r'^\s*\([^)]+\)\s*', '', name).strip()
    if not s:
        return False
    first_word = s.split()[0].lower().rstrip(',.')
    return first_word in _ACTION_VERBS


def _fallback_mat_name(opis: str) -> str:
    """Tworzy nazwę fallback-materiału z opisu pozycji.
    Jeśli opis zaczyna się czynnością — zwraca ogólną nazwę zamiast kopiować."""
    if not opis or _is_action_name(opis):
        return "Materiały budowlane"
    return f"Materiały: {opis}"


# ── Generator ─────────────────────────────────────────────────────────────────

class ATHGenerator:
    """Generator plików ATH (format Norma PRO v6)."""

    DEFAULT_PARAMS = {
        'stawka_rg': 35.00,
        'stawka_sprzetu': 100.00,
        'kp_procent': 70.0,
        'z_procent': 12.0,
        'vat_procent': 23.0,
    }

    def __init__(self, params: Dict = None):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self._mat_db = self._load_json_db("knr_materialy.json")
        self._spr_db = self._load_json_db("knr_sprzet.json")

    def _load_json_db(self, filename: str) -> dict:
        db_path = Path(__file__).parent / "learned_kosztorysy" / filename
        if db_path.exists():
            try:
                return json.loads(db_path.read_text(encoding='utf-8'))
            except Exception:
                pass
        return {}

    def generate(
        self,
        pozycje: List[Dict],
        podsumowanie: Dict,
        dane_tytulowe: Dict,
        output_path: str,
    ) -> str:
        """Generuje plik ATH zgodny z formatem Norma PRO."""

        ts = int(time.time())
        data = datetime.now().strftime("%d.%m.%Y")
        lines = []

        kp = self.params['kp_procent']
        z  = self.params['z_procent']
        sr = self.params['stawka_rg']
        ss = self.params['stawka_sprzetu']

        suma_R = podsumowanie.get('suma_R', 0.0)
        suma_M = podsumowanie.get('suma_M', 0.0)
        suma_S = podsumowanie.get('suma_S', 0.0)

        total_rg = suma_R / sr if sr else 0.0

        # ── Pre-pass: przypisz indywidualne materiały i sprzęt do pozycji ────
        # ZEST 1=R, 4..=materiały, potem sprzęt indywidualny lub fallback
        next_zest = 4
        # Klucz unikatowości materiału: (name, jm, ce_rounded)
        unique_mats: Dict[tuple, int] = {}   # key -> zest_num
        pos_mats: List = []                   # per pozycja: list[dict] lub None

        # Słowa kluczowe w opisie sugerujące materiały (używane gdy M=0 w DB)
        _MAT_KEYWORDS = {
            'blacha', 'blach', 'rura', 'rury', 'rurka', 'ruroci',
            'izolacj', 'uszczelni', 'bitum', 'membrana', 'papa', 'folia',
            'beton', 'posadzka', 'tynk', 'zaprawa', 'klej', 'farba', 'grunt',
            'styropian', 'wełna', 'welna', 'ocieplen',
            'kostka', 'płyta', 'plyta', 'płytka', 'plytka', 'panel',
            'ściek', 'sciek', 'wyrzutni', 'obudow',
            'kabel', 'przewód', 'przewod', 'korytko', 'rurka elektro',
            'brama', 'drzwi', 'okno', 'krata', 'siatka', 'geotkanin',
            'cokół', 'cokol', 'obróbki blacharskie', 'obrobki blacharskie',
            # Murowanie i ceramika
            'murowan', 'cegł', 'cegla', 'pustak', 'bloczek', 'bloczk',
            'glazur', 'ceramik', 'terakot', 'gres', 'okładzin', 'okladzi',
            # Malowanie i powłoki
            'malowan', 'malowani', 'lakierowan', 'szpachlow', 'gruntowa',
            # Instalacje
            'rynna', 'rynny', 'obróbk', 'obrobk', 'parapet', 'podokiennik',
            'grzejnik', 'zawór', 'zawor', 'armatur',
        }

        # Krok 1: DB lookup — zbierz brakujące do AI
        _hashlib = hashlib
        ai_needed = []  # [{knr_norm, knr, opis, jm, m_per_jm, poz_idx}]
        for idx, poz in enumerate(pozycje):
            knr_norm = _podstawa_to_norm(poz.get('podstawa', ''))
            db_mats = self._mat_db.get(knr_norm, []) if knr_norm else []
            if db_mats:
                pos_mats.append(db_mats)
            else:
                pos_mats.append(None)   # placeholder — może zastąpiony przez AI
                M = poz.get('M', 0.0) or 0.0
                ilosc = poz.get('ilosc', 1) or 1
                opis = poz.get('opis', '') or ''
                opis_l = opis.lower()
                m_per_jm = M / ilosc if ilosc else 0.0
                # Wywołaj AI gdy: M>0 LUB (M=0 ale opis sugeruje materiały)
                needs_ai = (M > 0) or any(kw in opis_l for kw in _MAT_KEYWORDS)
                if needs_ai:
                    # Gdy brak KNR: użyj hash opisu jako klucza cache
                    ai_key = knr_norm or ('OPIS:' + _hashlib.md5(opis.encode('utf-8', errors='replace')).hexdigest()[:12])
                    ai_needed.append({
                        'knr_norm': ai_key,
                        'knr': poz.get('podstawa', '') or '(brak KNR)',
                        'opis': opis[:80],
                        'jm': poz.get('jm', ''),
                        'm_per_jm': m_per_jm,  # 0.0 gdy M=0 — AI szacuje od zera
                        'poz_idx': idx,
                    })

        # Krok 2: AI estimation dla brakujących (deduplikacja wg knr_norm)
        if ai_needed:
            try:
                from ai_materials import estimate_materials_batch
                # Deduplikuj — jeden wpis per unikalny KNR
                seen_knr: Dict[str, int] = {}  # knr_norm -> first poz_idx
                unique_ai = []
                for item in ai_needed:
                    if item['knr_norm'] not in seen_knr:
                        seen_knr[item['knr_norm']] = item['poz_idx']
                        unique_ai.append(item)
                ai_results = estimate_materials_batch(unique_ai)
                # Wypełnij pos_mats wynikami AI
                for item in ai_needed:
                    mats = ai_results.get(item['knr_norm'], [])
                    if mats:
                        pos_mats[item['poz_idx']] = mats
            except Exception as e:
                log.warning("AI materials niedostępne: %s", e)

        # Krok 3a: dla pozycji bez materiałów (fallback) — stwórz dedykowany zasób
        # ce = M_nj (cena za jednostkę roboty), nz = 1.0 — zamiast ce=1/szt
        for idx, poz in enumerate(pozycje):
            if pos_mats[idx] is not None:
                continue
            M = poz.get('M', 0.0) or 0.0
            ilosc = poz.get('ilosc', 1) or 1
            M_nj = M / ilosc if ilosc else 0.0
            if M_nj <= 0:
                continue  # brak materiałów — OK
            jm = poz.get('jm', 'szt') or 'szt'
            opis_short = (poz.get('opis', '') or '')[:40].strip()
            name = _fallback_mat_name(opis_short)
            pos_mats[idx] = [{'name': name, 'jm': jm, 'nz': 1.0, 'ce': round(M_nj, 4)}]

        # Krok 3b: przypisz numery ZEST do wszystkich materiałów
        # Najpierw aplikuj korekty JM do wszystkich materiałów (DB + AI + fallback)
        pos_mats = [_apply_jm_corrections(m) if m else m for m in pos_mats]

        # Krok 3c: walidacja i korekta cen — wykrywa przestarzałe ceny z DB
        try:
            from price_validator import validate_and_correct_prices
            pos_mats = [validate_and_correct_prices(m) if m else m for m in pos_mats]
        except Exception as e:
            log.warning("Walidacja cen niedostępna: %s", e)

        for idx, mats in enumerate(pos_mats):
            if not mats:
                continue
            assigned = []
            for mat in mats:
                key = (mat['name'], mat['jm'], round(mat['ce'], 2))
                if key not in unique_mats:
                    unique_mats[key] = next_zest
                    next_zest += 1
                assigned.append({**mat, 'zest_num': unique_mats[key]})
            pos_mats[idx] = assigned

        # ── Pre-pass sprzętu: identycznie jak materiały ───────────────────────
        pos_sprzet: List = []  # per pozycja: list[dict] lub None

        _FALLBACK_SPR_CE = 50.0  # realistyczna stawka maszyny fallback [PLN/m-g]

        # Krok 1: DB lookup sprzętu — zbierz brakujące do AI
        _hashlib = hashlib
        ai_spr_needed = []
        for idx, poz in enumerate(pozycje):
            knr_norm = _podstawa_to_norm(poz.get('podstawa', ''))
            db_spr = self._spr_db.get(knr_norm, []) if knr_norm else []
            if db_spr:
                pos_sprzet.append(db_spr)
            else:
                pos_sprzet.append(None)
                S = poz.get('S', 0.0) or 0.0
                ilosc = poz.get('ilosc', 1) or 1
                if S > 0:
                    # Gdy brak KNR: użyj hash opisu jako klucza cache
                    opis = poz.get('opis', '')
                    ai_key = knr_norm or ('OPIS:' + _hashlib.md5(opis.encode('utf-8', errors='replace')).hexdigest()[:12])
                    ai_spr_needed.append({
                        'knr_norm': ai_key,
                        'knr': poz.get('podstawa', '') or '(brak KNR)',
                        'opis': opis[:80],
                        'jm': poz.get('jm', ''),
                        's_per_jm': S / ilosc,
                        'poz_idx': idx,
                    })

        # Krok 2: AI estimation dla brakującego sprzętu
        if ai_spr_needed:
            try:
                from ai_sprzet import estimate_sprzet_batch
                seen_knr: Dict[str, int] = {}
                unique_ai_spr = []
                for item in ai_spr_needed:
                    if item['knr_norm'] not in seen_knr:
                        seen_knr[item['knr_norm']] = item['poz_idx']
                        unique_ai_spr.append(item)
                ai_spr_results = estimate_sprzet_batch(unique_ai_spr)
                for item in ai_spr_needed:
                    machines = ai_spr_results.get(item['knr_norm'], [])
                    if machines:
                        pos_sprzet[item['poz_idx']] = machines
            except Exception as e:
                log.warning("AI sprzęt niedostępny: %s", e)

        # Krok 3: fallback dla pozycji bez sprzętu w DB i AI
        for idx, poz in enumerate(pozycje):
            if pos_sprzet[idx] is not None:
                continue
            S = poz.get('S', 0.0) or 0.0
            ilosc = poz.get('ilosc', 1) or 1
            if S > 0:
                nz = (S / ilosc) / _FALLBACK_SPR_CE
                pos_sprzet[idx] = [{'name': 'sprzęt budowlany', 'jm': 'm-g', 'nz': round(nz, 6), 'ce': _FALLBACK_SPR_CE}]

        # Przypisz numery ZEST do sprzętu (po materiałach, ten sam next_zest)
        unique_spr: Dict[tuple, int] = {}
        for idx, machines in enumerate(pos_sprzet):
            if not machines:
                continue
            assigned = []
            for m in machines:
                key = (m['name'], m['jm'], round(m['ce'], 2))
                if key not in unique_spr:
                    unique_spr[key] = next_zest
                    next_zest += 1
                assigned.append({**m, 'zest_num': unique_spr[key]})
            pos_sprzet[idx] = assigned

        # Totalne il= na ZEST materiałowy (suma nz*ob po wszystkich pozycjach)
        mat_il_total: Dict[int, float] = {}
        for poz, mats in zip(pozycje, pos_mats):
            if not mats:
                continue
            ob = poz.get('ilosc', 0) or 1
            for mat in mats:
                zn = mat['zest_num']
                mat_il_total[zn] = mat_il_total.get(zn, 0.0) + mat['nz'] * ob

        # Totalne il= na ZEST sprzętowy
        spr_il_total: Dict[int, float] = {}
        for poz, machines in zip(pozycje, pos_sprzet):
            if not machines:
                continue
            ob = poz.get('ilosc', 0) or 1
            for m in machines:
                zn = m['zest_num']
                spr_il_total[zn] = spr_il_total.get(zn, 0.0) + m['nz'] * ob

        needs_m_fallback = False  # ZEST 2 już nie potrzebny

        # ──────────────────── NAGŁÓWEK ──────────────────────────────────────
        lines += [
            "[KOSZTORYS ATHENASOFT]",
            "co=Copyright Athenasoft sp. z o.o.",
            "wf=4",
            "pr=NORMA\t5.11.400.12",
            "op=1",
            "opn=0\t1\t0\t1\t1\t0\t19\t8\t0\t0\t1\t0\t0\t0\t1.\t1\t1\t0\t1\t1\t1",
            "prn=2\t2\t2\t3\t4\t1\t6\t0\t1",
            "own=3\t1\t1\t0\t1\t0\t0\t1\t1\t0\t0\t0\t1\t0\t1\t1\tpoz.\t<\t>\t1\t0\t0\t0\t0\t0\t0\t0\t0\t2\t0\t1\t1\t1\t1\t0\t0\t0",
            "pm=dzia\u0142\tdzia\u0142",
            "pd=dzia\u0142u\tdzia\u0142u",
            "mm=dzia\u0142y\tdzia\u0142y",
            "md=dzia\u0142\u00f3w\tdzia\u0142\u00f3w",
            "wan=PLN",
            "wbn=PLN\tz\u0142",
            "wk=0",
            "na=Koszty po\u015brednie\tZysk",
            "wn=\t",
            "",
        ]

        # ──────────────────── STRONA TYTUŁOWA ───────────────────────────────
        nazwa = dane_tytulowe.get('nazwa_inwestycji', 'Kosztorys')
        lines += [
            "[STRONA TYT]",
            f"na=KOSZTORYS OFERTOWY\t{nazwa}",
            f"dt={data}\t0",
            "",
        ]

        # ──────────────────── NARZUTY ────────────────────────────────────────
        lines += [
            "[NARZUTY NORMA 2]",
            "na=Koszty po\u015brednie\tKp",
            f"wa={_dot(kp, 1)}\t1\t0\tPLN",
            "op=1\t0",
            "nr=1",
            "ns=1",
            "",
            "[NARZUTY NORMA 2]",
            "na=Zysk\tZ",
            f"wa={_dot(z, 1)}\t1\t0\tPLN",
            "op=1\t0",
            "nr=1",
            "ns=1",
            "",
        ]

        # ──────────────────── RMS ZEST — zasoby globalne ─────────────────────
        def _ce_str(val: float) -> str:
            """Cena w formacie ATH: przecinek dziesiętny, 2 miejsca po przecinku."""
            return f"{val:.2f}".replace(".", ",")

        def _jm_clean_zest(jm: str) -> str:
            """Usuwa zbędne znaki z JM dla bloków ZEST (np. 'szt.' → 'szt')."""
            return jm.strip().rstrip('.')

        # ZEST 1 — Robocizna
        sr_str = _ce_str(sr)
        lines += [
            "[RMS ZEST 1]",
            "ty=R\t0",
            "na=robocizna\t0",
            "id=999\t1",
            "jm=r-g\t149",
            f"ce={sr_str}\t{ts}\t1\tSEK_RMS",
            f"cw={sr_str}\tPLN\t{sr_str}",
            f"il={_dot(total_rg)}",
            "",
        ]

        # ZEST 2 — usunięty (needs_m_fallback zawsze False)

        # ZEST 4..N — Indywidualne materiały z realnymi cenami
        for (name, jm, _ce), zest_num in sorted(unique_mats.items(), key=lambda x: x[1]):
            jm_display = _jm_clean_zest(jm)
            jm_code = get_jm_code(jm)
            il_total = mat_il_total.get(zest_num, 0.0)
            ce_str = _ce_str(_ce)
            lines += [
                f"[RMS ZEST {zest_num}]",
                "ty=M\t0",
                f"na={name}\t0",
                "id=0\t3",
                f"jm={jm_display}\t{jm_code}",
                f"ce={ce_str}\t{ts}\t1\tSEK_RMS",
                f"cw={ce_str}\tPLN\t{ce_str}",
                f"il={_dot(il_total, 4)}",
                "",
            ]

        # ZEST S — Indywidualny sprzęt z realnymi cenami (lub fallback)
        for (name, jm, _ce), zest_num in sorted(unique_spr.items(), key=lambda x: x[1]):
            jm_display = _jm_clean_zest(jm)
            jm_code = get_jm_code(jm) if jm.rstrip('.') != 'm-g' else '150'
            il_total = spr_il_total.get(zest_num, 0.0)
            ce_str = _ce_str(_ce)
            lines += [
                f"[RMS ZEST {zest_num}]",
                "ty=S\t0",
                f"na={name}\t0",
                "id=0\t1",
                f"jm={jm_display}\t{jm_code}",
                f"ce={ce_str}\t{ts}\t1\tSEK_RMS",
                f"cw={ce_str}\tPLN\t{ce_str}",
                f"il={_dot(il_total, 4)}",
                "",
            ]

        # ──────────────────── ELEMENT + POZYCJE ────────────────────────────────
        # Jeden licznik ID dla ELEMENT i POZYCJA (Norma PRO wymaga globalnej sekwencji)
        object_id = 1
        current_elem_dzial = None   # aktualnie otwarty element

        def _emit_element(dzial_name: str, elem_id: int, kp_val: float, z_val: float):
            """Emituje blok [ELEMENT 1] + [PODSUMOWANIE]."""
            return [
                "[ELEMENT 1]",
                f"na={dzial_name}",
                "wa=0",
                "kn=0\t0\t0",
                f"id={elem_id}",
                "nu=1",
                "",
                "[PODSUMOWANIE]",
                "wa=",
                "kb=0\t0\t0\t0\t0\t0\t0\t",
                f"na=0\t0\t0\t0\t0\t0\t0\t0\tKp\tKoszty po\u015brednie\t{_dot(kp_val, 1)}% (R+S)",
                f"na=0\t0\t0\t0\t0\t0\t0\t0\tZ\tZysk\t{_dot(z_val, 1)}% (R+S+Kp(R+S))",
                "wc=0\t0\t0\t0\t0\t0\t0\t",
                "",
            ]

        lp = 0
        for poz, mats, machines in zip(pozycje, pos_mats, pos_sprzet):
            lp += 1
            dzial = poz.get('dzial', 'Kosztorys')

            # Otwórz nowy ELEMENT gdy dzial się zmienia
            if dzial != current_elem_dzial:
                current_elem_dzial = dzial
                lines += _emit_element(dzial, object_id, kp, z)
                object_id += 1

            jm       = poz.get('jm', 'szt.')
            jm_clean = jm.replace('.', '')
            jm_code  = get_jm_code(jm)
            ilosc    = poz.get('ilosc', 0) or 1
            opis     = poz.get('opis', 'Pozycja').replace('[AI] ', '').replace('[WYCENA] ', '')[:200].replace('"', "'")
            podstawa = poz.get('podstawa', '')

            R = poz.get('R', 0.0)
            M = poz.get('M', 0.0)
            S = poz.get('S', 0.0)

            # Nakłady jednostkowe dla robocizny
            R_nj = R / sr / ilosc if (R > 0 and sr > 0) else 0.0
            R_il = R / sr if (R > 0 and sr) else 0.0

            # Linia pd= z referencją KNR
            knr_typ, knr_short, knr_num = _parse_podstawa(podstawa)
            if knr_typ and knr_short:
                if knr_num and '/' in knr_short:
                    knr_full = f"{knr_short}/{knr_num}"
                else:
                    knr_full = f"{knr_short} {knr_num}".strip()
                pd_line = f"pd=\t{knr_typ}\t{knr_full}\t{knr_short}\t{knr_num}\t\t1"
            else:
                pd_line = "pd=\t\t\t\t\t\t0"

            # Obmiar
            ilosc_str = _dot(ilosc, 4)
            formula   = poz.get('formula_str', '')
            wo_val    = formula if formula else ilosc_str

            lines += [
                "[POZYCJA]",
                f"id={object_id}",
                pd_line,
                "mpn=1211",
                f"na={opis}",
                "op=0\t0\t0\t0\t0\t0\t0\t0",
                f"nu={lp}",
                f"ob={ilosc_str}\t{ilosc_str}\t\t1",
                f"jm={jm_clean}\t{jm_code}",
                "kj=0\t0\t0",
                "cj=0",
                "wn=\t",
                "",
                "[PRZEDMIAR]",
                f"wo={ilosc_str}\t1\t{wo_val}\t\t\t\t\t",
                "",
            ]

            # ── RMS per pozycja ─────────────────────────────────────────────
            # ZEST 1: Robocizna
            if R > 0:
                wa_r = _ce_str(R)
                lines += [
                    "[RMS 1]",
                    f"nz={_dot(R_nj)}\t0\t{_dot(R_nj)}",
                    "np=1\t0",
                    f"wa={wa_r}",
                    "wb=0",
                    f"il={_dot(R_il)}",
                    "",
                ]

            # Materiały: indywidualne (ZEST 4+) lub zbiorcze fallback (ZEST 2)
            if mats:
                # Indywidualne materiały z realnymi cenami
                for mat in mats:
                    nz = mat['nz']
                    il = nz * ilosc
                    wa_m = _ce_str(nz * ilosc * mat['ce'])
                    lines += [
                        f"[RMS {mat['zest_num']}]",
                        f"nz={_dot(nz)}\t0\t{_dot(nz)}",
                        "np=0\t0",
                        f"wa={wa_m}",
                        "wb=0",
                        f"il={_dot(il, 4)}",
                        "",
                    ]
            # (fallback obsłużony w pre-pass jako dedykowany ZEST)

            # Sprzęt: indywidualne maszyny (ZEST N)
            if machines:
                for mach in machines:
                    nz = mach['nz']
                    il = nz * ilosc
                    wa_s = _ce_str(nz * ilosc * mach['ce'])
                    lines += [
                        f"[RMS {mach['zest_num']}]",
                        f"nz={_dot(nz)}\t0\t{_dot(nz)}",
                        "np=1\t0",
                        f"wa={wa_s}",
                        "wb=0",
                        f"il={_dot(il, 4)}",
                        "",
                    ]

            object_id += 1

        # ──────────────────── ZAPIS ──────────────────────────────────────────
        content = "\n".join(lines)

        try:
            content.encode('cp1250')
        except UnicodeEncodeError:
            bad = {c for c in content if not c.encode('cp1250', errors='ignore')}
            log.warning("Znaki poza cp1250 zastapione '?': %s", ''.join(sorted(bad)))

        with open(output_path, 'w', encoding='cp1250', errors='ignore') as f:
            f.write(content)

        # Statystyki źródeł — ile pozycji skorzystało z DB / AI / fallback
        def _is_fallback_mat(mats):
            return mats and len(mats) == 1 and (mats[0].get('name', '').startswith('Materiały:') or mats[0].get('name') == 'Materiały budowlane')

        mat_db_count       = sum(1 for idx, m in enumerate(pos_mats) if m is not None and _podstawa_to_norm(pozycje[idx].get('podstawa','')) in self._mat_db)
        mat_ai_count       = sum(1 for m in pos_mats if m is not None) - mat_db_count - sum(1 for m in pos_mats if _is_fallback_mat(m))
        mat_fallback_count = sum(1 for m in pos_mats if _is_fallback_mat(m))
        spr_fallback_count = sum(1 for m in pos_sprzet if m and m[0]['name'] == 'sprzęt budowlany')
        spr_db_count       = sum(1 for idx, m in enumerate(pos_sprzet) if m and _podstawa_to_norm(pozycje[idx].get('podstawa','')) in self._spr_db)
        spr_ai_count       = sum(1 for m in pos_sprzet if m) - spr_db_count - spr_fallback_count

        log.info(
            "ATH zapisano | %d pozycji | mat: %d DB / %d AI / %d fallback | sprzet: %d DB / %d AI / %d fallback",
            len(pozycje), mat_db_count, mat_ai_count, mat_fallback_count,
            spr_db_count, spr_ai_count, spr_fallback_count,
        )
        if spr_fallback_count:
            log.warning("UWAGA: %d pozycji nadal ma fallback 'sprzet budowlany' — sprawdz AI cache", spr_fallback_count)
        return output_path


if __name__ == "__main__":
    gen = ATHGenerator()
    test_poz = [
        {'lp': 1, 'podstawa': 'KNR 4-01 0354-09', 'opis': 'Rozbiórka elementów',
         'jm': 'szt.', 'ilosc': 10, 'R': 1000.0, 'M': 500.0, 'S': 200.0},
    ]
    test_pods = {'suma_R': 1000.0, 'suma_M': 500.0, 'suma_S': 200.0}
    test_dane = {'nazwa_inwestycji': 'Test v6'}
    print(gen.generate(test_poz, test_pods, test_dane, '/tmp/test_v6.ath'))
