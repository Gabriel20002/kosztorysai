# Struktura Kosztorysu NORMA

## 1. STRONA TYTUŁOWA

```
[DANE WYKONAWCY - jeśli kosztorys ofertowy]
Firma np. KLONEX II DŁUGI GRZEGORZ ul. KASZTANOWA 10 49-318 SKARBIMIERZ-OSIEDLE

KOSZTORYS [TYP] - BRANŻA [NAZWA]
    TYP = INWESTORSKI | OFERTOWY | POWYKONAWCZY
    NAZWA = BUDOWLANA | SANITARNA | ELEKTRYCZNA

NAZWA INWESTYCJI: [pełna nazwa zadania]
ADRES INWESTYCJI: [adres + nr działek]
NAZWA INWESTORA: [nazwa inwestora]
ADRES INWESTORA: [adres inwestora]

WYKONAWCA: [nazwa wykonawcy - dla ofertowych]
ADRES WYKONAWCY: [adres wykonawcy]

BRANŻE: [branża]
SPORZĄDZIŁ KALKULACJE
[tytuł + imię nazwisko]

DATA OPRACOWANIA: [data]
Stawka roboczogodziny: [kwota] zł

WARTOŚĆ KOSZTORYSOWA ROBÓT BEZ PODATKU VAT: [netto] zł
PODATEK VAT: (23%) [vat] zł
OGÓŁEM WARTOŚĆ KOSZTORYSOWA ROBÓT: [brutto] zł
SŁOWNIE: [słownie] zł

WYKONAWCA:                    INWESTOR:
Data opracowania              Data zatwierdzenia
[data]
```

## 2. TABELA ELEMENTÓW SCALONYCH

```
| Lp | Nazwa                    | Uproszczone | Robocizna | Materiały | Sprzęt | Kp      | Z       | Razem   | Udział % |
|----|--------------------------|-------------|-----------|-----------|--------|---------|---------|---------|----------|
| 1  | ROBOTY WEWNĘTRZNE        | 0,00        | 53 868,36 | 204 267,42| 2 907,80| 34 065,72| 9 084,27| 304 193,57| 55,60% |
| 1.1| INSTALACJA KANALIZACJI   | 0,00        | 8 498,74  | 4 102,98  | 245,08 | 5 246,29| 1 399,02| 19 492,11| 3,56%  |
```

**Kolumny:**
- **Uproszczone** - koszty bez rozbicia (kalkulacja własna)
- **Robocizna (R)** - koszty robocizny
- **Materiały (M)** - koszty materiałów
- **Sprzęt (S)** - koszty sprzętu
- **Kp** - koszty pośrednie
- **Z** - zysk
- **Razem** - suma wszystkiego
- **Udział %** - procent w całym kosztorysie

## 3. SZCZEGÓŁOWY KOSZTORYS

### Format pozycji:

```
Lp | Podstawa        | Opis                           | j.m. | Cena jedn. | Koszt jedn. | Ilość | Wartość
---|-----------------|--------------------------------|------|------------|-------------|-------|--------
1  | KNR-W 2-01      | Wykopy liniowe szer. 0.8-1.5 m | m3   | 81,31      | 46,200      |42,000 | 3 415,10
   | 0310-02         | pod fundamenty, rurociągi...   |      |            |             |       |
                     |                                |      |            |             |       |
                     | --Robocizna--                  |      |            |             |       |
                     | 1* robocizna r-g 1,650000      | 28,00| 46,200     |             |       |
                     |                                |      |            |             |       |
                     | Razem koszty bezpośrednie      |      | 46,200     |             |1 940,40|
                     | Jednostkowe koszty bezpośrednie|      | 46,200     |             |       |
                     | Razem pozycja                  |81,310|            | 42,000      |3 415,10|
                     | Cena jednostkowa               |81,31 |            |             |       |
```

### Format pozycji z R+M+S:

```
Lp | Podstawa    | Opis                        | j.m.  | Nakłady | Koszt jedn. | R      | M      | S
---|-------------|-----------------------------| ------|---------|-------------|--------|--------|-------
1  | KNNR 5      | Przewody uziemiające...     | m     | 5,000   | 20,14       |        |        |
   | 0602-02     |                             |       |         |             |        |        |
   |             | obmiar = 5,000 m            |       |         |             |        |        |
   |             |                             |       |         |             |        |        |
   |             | -- R --                     |       |         |             |        |        |
   | 1*          | robocizna r-g               | 1,7200| 9,98    |             | 49,90  |        |
   |             | 0,344 r-g/m * 29,00 zł/r-g  |       |         |             |        |        |
   |             |                             |       |         |             |        |        |
   |             | -- M --                     |       |         |             |        |        |
   | 2*          | bednarka ocynkowana         | m     | 5,2000  | 4,92        |        | 24,60  |
   |             | 1,04 m/m * 4,73 zł/m        |       |         |             |        |        |
   | 3*          | wsporniki ścienne           | szt.  | 5,0500  | 4,78        |        | 23,90  |
   |             | 1,01 szt./m * 4,73 zł/szt.  |       |         |             |        |        |
   | 4*          | śruby stalowe z nakr.       | kg    | 0,0300  | 0,09        |        | 0,45   |
   |             | 0,006 kg/m * 14,18 zł/kg    |       |         |             |        |        |
   | 5*          | materiały pomocnicze(od M)  | %     |         | 0,24        |        | 1,20   |
   |             | 2,5 %                       |       |         |             |        |        |
   |             |                             |       |         |             |        |        |
   |             | -- S --                     |       |         |             |        |        |
   | 6*          | spawarka                    | m-g   | 0,1470  | 0,13        |        |        | 0,65
   |             | 0,0294 m-g/m * 4,50 zł/m-g  |       |         |             |        |        |
   |             |                             |       |         |             |        |        |
   |             | Razem koszty bezpośrednie   |       | 100,70  | 20,14       | 49,90  | 50,15  | 0,65
   |             | Jednostkowe koszty bezp.    |       |         | 20,14       | 9,98   | 10,03  | 0,13
   |             | Razem z narzutami           |       | 139,15  | 27,83       | 87,85  | 50,15  | 1,15
   |             | Cena jednostkowa            |       |         | 27,83       | 17,57  | 10,03  | 0,23
```

## 4. PODSUMOWANIA DZIAŁÓW

```
Razem dział: [Nazwa działu]
Razem koszty bezpośrednie: [suma_bezp] | [R_suma] | [M_suma] | [S_suma]
RAZEM: [suma_z_narzutami] | [R_z_narz] | [M_suma] | [S_z_narz]
```

## 5. PODSUMOWANIE KOŃCOWE

```
Kosztorys netto: [uproszcz] | [robocizna] | [materiały] | [sprzęt] | [Kp] | [Z] | [SUMA_NETTO] | 81,30%
VAT 23%:                                                                     | [VAT]        | 18,70%
Kosztorys brutto:                                                            | [BRUTTO]     | 100,00%
Słownie: [kwota słownie] zł
```

## 6. PODSTAWY WYCENY

**Katalogi nakładów:**
- **KNR** - Katalog Nakładów Rzeczowych (ogólny)
- **KNR-W** - KNR Warunki (specyficzne)
- **KNNR** - Katalog Nakładów Normatywnych Rzeczowych (nowsze)
- **KSNR** - Katalog Scalonych Nakładów Rzeczowych
- **KNBK** - Katalog Nakładów Budowli Kolejowych
- **kalk. własna** - Kalkulacja własna (bez rozbicia)

**Format podstawy:** `KNR X-XX YYYY-ZZ`
- X-XX = numer katalogu (np. 2-01, 5-08)
- YYYY-ZZ = numer tablicy i kolumny

**Przykłady:**
- `KNR 2-01 0126-01` = Roboty ziemne
- `KNR 2-02 0202-02` = Roboty betonowe
- `KNNR 5 0602-02` = Instalacje elektryczne
- `KNR 2-18 0501-01` = Kanalizacja
- `KNR-W 2-15 0211-03` = Instalacje sanitarne

## 7. NARZUTY

**Wzór obliczania ceny z narzutami:**
```
R_z_narzutami = R * (1 + Kp% + Z%)
S_z_narzutami = S * (1 + Kp% + Z%)
M = bez narzutów (materiały idą bez narzutów)

Cena_jednostkowa = R_z_narz + M + S_z_narz
```

**Typowe narzuty:**
- **Kp (koszty pośrednie):** 60-70% od R+S
- **Z (zysk):** 10-15% od R+S+Kp
- **Materiały pomocnicze:** 1,5-2,5% od M

## 8. JEDNOSTKI MIARY

| Skrót | Pełna nazwa |
|-------|-------------|
| m     | metr        |
| m2    | metr kwadratowy |
| m3    | metr sześcienny |
| szt.  | sztuka      |
| kpl.  | komplet     |
| kg    | kilogram    |
| t     | tona        |
| r-g   | roboczogodzina |
| m-g   | maszynogodzina |
| %     | procent     |
| odc.  | odcinek     |
| pomiar | pomiar     |
