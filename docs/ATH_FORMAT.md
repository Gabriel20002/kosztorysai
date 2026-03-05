# Format ATH (Norma PRO / Athenasoft)

**Data:** 2025-07-15  
**Status:** Zweryfikowany, działa w Norma PRO

---

## Struktura pliku ATH

### 1. Nagłówek
```
[KOSZTORYS ATHENASOFT]
co=Copyright Athenasoft Sp. z o.o.
wf=4
pr=NORMA	5.11.400.12
...
```

### 2. Strona tytułowa
```
[STRONA TYT]
na=KOSZTORYS	Nazwa inwestycji
dt=15.07.2025	0
```

### 3. Narzuty
```
[NARZUTY NORMA 2]
na=Koszty posrednie	Kp
wa=70	1	0	
op=1	0
nr=1
ns=1
```

### 4. RMS ZESTAWIENIE (GLOBALNE) ⚠️ KRYTYCZNE

**Musi być PRZED pozycjami!**

```
[RMS ZEST 1]
ty=R	0           ← typ: R=robocizna
na=robocizna	0
id=999	1
jm=r-g	149
ce=35,00	1772121487	1	SEK_RMS
cw=35,00	PLN	35,00
il=0

[RMS ZEST 2]
ty=M	0           ← typ: M=materiały
na=Materiały	0
id=998	1
jm=szt	020
ce=1,00	1772121487	1	SEK_RMS
cw=1,00	PLN	1,00
il=0

[RMS ZEST 3]
ty=S	0           ← typ: S=sprzęt
na=Sprzęt	0
id=997	1
jm=m-g	150
ce=100,00	1772121487	1	SEK_RMS
cw=100,00	PLN	100,00
il=0
```

### 5. Element główny
```
[ELEMENT 1]
na=KOSZTORYS
wa=0
kn=0	0	0
wn=0	0	0
id=1
nu=1
```

### 6. Pozycje
```
[POZYCJA]
id=2
pd=Katalog	KNR	4-01 0354-09	4-01	0354-09		1
mpn=1211
na=Opis pozycji
op=0	1	0	0	1	0	0	0
nu=1
ob=29	29		1
jm=szt	020
kj=35,00	0	1,0
cj=35,00		25,00	8,00	2,00
cjw=		0
kjw=			0	0	0
wn=1015,00	725,00	232,00	58,00
wcn=1	1	1	1	1	1	1	1

[PRZEDMIAR]
wo=29	1	29	

[RMS 1]
nz=1	0	1       ← referencja do RMS ZEST 1 (robocizna)
np=0	0
wa=725,00
wb=1290,50
il=20,71

[RMS 2]
nz=2	0	1       ← referencja do RMS ZEST 2 (materiały)
np=0	0
wa=232,00
wb=232,00
il=232

[RMS 3]
nz=3	0	1       ← referencja do RMS ZEST 3 (sprzęt)
np=0	0
wa=58,00
wb=103,24
il=0,58
```

---

## Kluczowe zasady

### RMS ZEST (globalne zestawienie)
| ID | Typ | Nazwa | Jednostka | Kod jm |
|----|-----|-------|-----------|--------|
| 1 | R | robocizna | r-g | 149 |
| 2 | M | Materiały | szt | 020 |
| 3 | S | Sprzęt | m-g | 150 |

### RMS w pozycjach (referencje)
- `nz=1` → referencja do RMS ZEST 1 (robocizna)
- `nz=2` → referencja do RMS ZEST 2 (materiały)
- `nz=3` → referencja do RMS ZEST 3 (sprzęt)

### Pola RMS w pozycji
- `wa` = wartość (cena × ilość)
- `wb` = wartość z narzutami
- `il` = ilość jednostek

### Obliczenia ilości
- **Robocizna:** `il = wartość_R / stawka_rg` (r-g)
- **Materiały:** `il = wartość_M` (przy cenie 1 zł/szt)
- **Sprzęt:** `il = wartość_S / stawka_sprzetu` (m-g)

---

## Kodowanie
- **Plik:** CP1250 (Windows-1250)
- **Separator dziesiętny:** przecinek (`,`)
- **Separator pól:** tabulator (`\t`)

---

## Wzorcowe pliki ATH
```
C:\Users\Gabriel\Downloads\kosztorysy\
├── ZOL- kosztorys budowany poprawiony...ath  ← pełne RMS (R+M+S)
├── Remiza-PRD-E (1).ath                      ← pełne RMS
└── 06. Zał. nr 2 do SWZ - Przedmiar robót (1).ath  ← tylko R
```

---

## Historia zmian
- **2025-07-15:** Naprawiono brak M i S — dodano RMS ZEST 2 i 3, referencje w pozycjach
