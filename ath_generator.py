# -*- coding: utf-8 -*-
"""
ATH Generator v5.0
Generator plików ATH (format Norma PRO / Athenasoft)

Format wzorowany na prawdziwych plikach ATH z Normy PRO:
- pd= z referencją KNR, kj=0, cj=0, wn= puste
- [RMS ZEST N] = definicje zasobów z cenami
- [RMS N] per pozycja: N = numer ZEST, nz = nakład jednostkowy (kropka), il = nz×ob
- Norma PRO sama oblicza kj/wn z RMS
"""

import logging
import math
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple

from formatters import fmt_ath as fmt


log = logging.getLogger(__name__)


# ── Formattery ────────────────────────────────────────────────────────────────

def _dot(val: float, decimals: int = 4) -> str:
    """Liczba z KROPKĄ — używane w nz= i il= (format Norma PRO)."""
    if not math.isfinite(val):
        return "0"
    return f"{val:.{decimals}f}".rstrip("0").rstrip(".") or "0"


# ── Jednostki ─────────────────────────────────────────────────────────────────

JEDNOSTKI_KODY = {
    "szt.": "020", "szt": "020",
    "m": "010", "mb": "010", "m.b.": "010",
    "m2": "050", "m²": "050", "mkw": "050",
    "m3": "060", "m³": "060",
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
        r'([A-Za-z]*[\d]+-?[\d]*)'
        r'(?:\s+(\d{4}-\d{2}))?',
        s, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper(), m.group(2), (m.group(3) or '')
    return '', '', ''


# ── Generator ─────────────────────────────────────────────────────────────────

class ATHGenerator:
    """Generator plików ATH (format Norma PRO v5)."""

    DEFAULT_PARAMS = {
        'stawka_rg': 35.00,
        'stawka_sprzetu': 100.00,
        'kp_procent': 70.0,
        'z_procent': 12.0,
        'vat_procent': 23.0,
    }

    def __init__(self, params: Dict = None):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}

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

        kp  = self.params['kp_procent']
        z   = self.params['z_procent']
        sr  = self.params['stawka_rg']
        ss  = self.params['stawka_sprzetu']

        suma_R = podsumowanie.get('suma_R', 0.0)
        suma_M = podsumowanie.get('suma_M', 0.0)
        suma_S = podsumowanie.get('suma_S', 0.0)

        total_rg = suma_R / sr if sr else 0.0
        total_mg = suma_S / ss if ss else 0.0

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

        # ──────────────────── RMS ZEST (zasoby globalne z cenami) ────────────
        # ZEST 1 — Robocizna
        lines += [
            "[RMS ZEST 1]",
            "ty=R",
            "na=robocizna\t0",
            "id=999\t1",
            "jm=r-g\t149",
            f"ce={_dot(sr, 2)}\t{ts}",
            f"cw={_dot(sr, 2)}\tPLN",
            f"il={_dot(total_rg)}",
            "",
        ]

        # ZEST 2 — Materiały (ce=1 PLN/szt — il = wartość PLN)
        lines += [
            "[RMS ZEST 2]",
            "ty=M",
            "na=materia\u0142y\t0",
            "id=998\t1",
            "jm=szt\t020",
            f"ce=1\t{ts}",
            "cw=1\tPLN",
            f"il={_dot(suma_M, 2)}",
            "",
        ]

        # ZEST 3 — Sprzęt
        lines += [
            "[RMS ZEST 3]",
            "ty=S",
            "na=sprz\u0119t\t0",
            "id=997\t1",
            "jm=m-g\t150",
            f"ce={_dot(ss, 2)}\t{ts}",
            f"cw={_dot(ss, 2)}\tPLN",
            f"il={_dot(total_mg)}",
            "",
        ]

        # ──────────────────── ELEMENT ────────────────────────────────────────
        lines += [
            "[ELEMENT 1]",
            "na=KOSZTORYS",
            "wa=0",
            "kn=0\t0\t0",
            "id=1",
            "nu=1",
            "",
        ]

        # ──────────────────── POZYCJE ────────────────────────────────────────
        pos_id = 2

        for lp, poz in enumerate(pozycje, 1):
            jm       = poz.get('jm', 'szt.')
            jm_clean = jm.replace('.', '')
            jm_code  = get_jm_code(jm)
            ilosc    = poz.get('ilosc', 0) or 1
            opis     = poz.get('opis', 'Pozycja')[:200].replace('"', "'")
            podstawa = poz.get('podstawa', '')

            R = poz.get('R', 0.0)
            M = poz.get('M', 0.0)
            S = poz.get('S', 0.0)

            # Nakłady jednostkowe
            R_nj = R / sr / ilosc if (R > 0 and sr > 0) else 0.0  # r-g / jm
            M_nj = M / ilosc      if M > 0               else 0.0  # PLN / jm
            S_nj = S / ss / ilosc if (S > 0 and ss > 0) else 0.0  # m-g / jm

            # Sumaryczne ilości zasobu
            R_il = R / sr if (R > 0 and sr) else 0.0   # total r-g
            M_il = M      if M > 0          else 0.0   # total PLN
            S_il = S / ss if (S > 0 and ss) else 0.0   # total m-g

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

            # Obmiar (liczba lub formuła)
            ilosc_str = _dot(ilosc, 4)
            formula   = poz.get('formula_str', '')
            wo_val    = formula if formula else ilosc_str

            lines += [
                "[POZYCJA]",
                f"id={pos_id}",
                pd_line,
                "mpn=1211",
                f"na={opis}",
                "op=0\t0\t0\t0\t0\t0\t0\t0",
                f"nu={lp}",
                f"ob={ilosc_str}",
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
            # N = numer ZEST (1=R, 2=M, 3=S)
            if R > 0:
                lines += [
                    "[RMS 1]",
                    f"nz={_dot(R_nj)}\t0\t{_dot(R_nj)}",
                    "np=1",
                    "wa=0",
                    "wb=0",
                    f"il={_dot(R_il)}",
                    "",
                ]

            if M > 0:
                lines += [
                    "[RMS 2]",
                    f"nz={_dot(M_nj)}\t0\t{_dot(M_nj)}",
                    "np=1",
                    "wa=0",
                    "wb=0",
                    f"il={_dot(M_il, 2)}",
                    "",
                ]

            if S > 0:
                lines += [
                    "[RMS 3]",
                    f"nz={_dot(S_nj)}\t0\t{_dot(S_nj)}",
                    "np=1",
                    "wa=0",
                    "wb=0",
                    f"il={_dot(S_il)}",
                    "",
                ]

            pos_id += 1

        # ──────────────────── ZAPIS ──────────────────────────────────────────
        content = "\n".join(lines)

        try:
            content.encode('cp1250')
        except UnicodeEncodeError:
            bad = {c for c in content if not c.encode('cp1250', errors='ignore')}
            log.warning("Znaki poza cp1250 zastapione '?': %s", ''.join(sorted(bad)))

        with open(output_path, 'w', encoding='cp1250', errors='replace') as f:
            f.write(content)

        log.info("Zapisano ATH (%d pozycji): %s", len(pozycje), output_path)
        return output_path


if __name__ == "__main__":
    gen = ATHGenerator()
    test_poz = [
        {'lp': 1, 'podstawa': 'KNR 4-01 0354-09', 'opis': 'Rozbiórka elementów',
         'jm': 'szt.', 'ilosc': 10, 'R': 1000.0, 'M': 500.0, 'S': 200.0},
    ]
    test_pods = {'suma_R': 1000.0, 'suma_M': 500.0, 'suma_S': 200.0}
    test_dane = {'nazwa_inwestycji': 'Test v5'}
    print(gen.generate(test_poz, test_pods, test_dane, '/tmp/test_v5.ath'))
