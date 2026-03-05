# -*- coding: utf-8 -*-
"""
Generator kosztorysu ATH: Remont wezlow sanitarnych budynek nr 33
Format zgodny z Norma PRO - sprawdzony wzorzec
"""

from datetime import datetime

# Dane naglowkowe
NAZWA_INWESTYCJI = "Remont wezlow sanitarnych w budynku nr 33"
ADRES_INWESTYCJI = "ul. Sikorskiego 6, 49-300 Brzeg"
NAZWA_INWESTORA = "2 Wojskowy Oddzial Gospodarczy"
ADRES_INWESTORA = "ul. Obornicka 100-102, 50-984 Wroclaw"
WYKONAWCA = "AI Kosztorysant"
DATA = datetime.now().strftime("%d.%m.%Y")

# Kody jednostek miar
UNIT_CODES = {
    'm': '010', 'mb': '010',
    'm2': '050',
    'm3': '060',
    'kg': '033',
    't': '063',
    'szt': '020', 'szt.': '020',
    'kpl': '090', 'kpl.': '090',
    'r-g': '149',
    'wyp.': '020', 'wyp': '020',
    'podej.': '020', 'podej': '020',
    'pom.': '020', 'pom': '020',
    'pion': '020',
    'odc.200m': '020',
    'gniazd.': '020',
    'cm': '010',
}

def get_unit_code(unit):
    return UNIT_CODES.get(unit.lower().strip().rstrip('.'), '020')

# Nazwy katalogow
CATALOG_NAMES = {
    'KNR': 'WACETOB wyd.I 1997',
    'KNR-W': 'WACETOB wyd.I 1997',
    'KNNR': 'Kancelaria Prezesa Rady Ministrow 2001',
    'KSNR': 'KSNR',
    'NNRNKB': 'NNRNKB',
    'KNR AT': 'ATHENASOFT',
    'kalk.': 'Kalkulacja wlasna',
    'analiza': 'Analiza indywidualna',
    'S': 'Specyfikacja',
    'TZKNBK': 'TZKNBK',
}

def get_catalog_name(basis):
    for prefix, name in CATALOG_NAMES.items():
        if basis.lower().startswith(prefix.lower()):
            return name
    return 'WACETOB wyd.I 1997'

def parse_basis(basis):
    parts = basis.split()
    if len(parts) >= 3:
        prefix = parts[0]
        if len(parts) > 3 and parts[1] in ['AT', 'K', 'AL']:
            prefix = parts[0] + ' ' + parts[1]
            cat_num = parts[2]
            pos_num = parts[3] if len(parts) > 3 else ''
        else:
            cat_num = parts[1]
            pos_num = parts[2] if len(parts) > 2 else ''
        return prefix, cat_num, pos_num
    elif len(parts) == 2:
        return parts[0], parts[1], ''
    return basis, '', ''

# Struktura dzialow i pozycji
DZIALY = [
    # ============ PARTER ============
    {
        'numer': 1,
        'nazwa': 'PARTER - Roboty rozbiórkowe',
        'pozycje': [
            ('KNR 4-01 0354-09', 'Wykucie z muru oscieznic stalowych lub krat drzwiowych o powierzchni do 2 m2', 'szt.', '29'),
            ('KNR 4-01 0354-12', 'Wykucie z muru podokiennikow betonowych', 'm', '4,5'),
            ('KNR 9-29 0103-01', 'Rozbiorka scianek dzialowych z plyt gipsowo-kartonowych na szkielecie pojedynczym', 'm2', '10,416'),
            ('KNR 9-29 0105-02', 'Rozbiorka obudow pionow instalacyjnych z plyt gipsowo-kartonowych', 'm2', '10,405'),
            ('KNR 9-29 0101-01', 'Rozbiorka okladzin scian z plyt gipsowo-kartonowych', 'm2', '18,348'),
            ('KNR 4-01 0427-05', 'Rozebranie scianek dzialowych sanitarnych', 'm2', '7,04'),
            ('KNR 4-01 0819-15', 'Rozebranie wykladziny sciennej z plytek', 'm2', '123,181'),
            ('KNR 4-01 0701-05', 'Odbicie tynkow wewnetrznych z zaprawy cementowo-wapiennej na scianach', 'm2', '123,181'),
            ('KNR 4-01 1202-08', 'Zeskrobanie i zmycie starej farby w pomieszczeniach', 'm2', '107,25'),
            ('KNR 4-01 0811-07', 'Rozebranie posadzki z plytek na zaprawie cementowej', 'm2', '41,15'),
            ('KNR 4-01 0347-09', 'Skucie nierownosci 4 cm na scianach z cegiel - poszerzenie otworu', 'm2', '7,38'),
            ('KNR 4-01 0354-13', 'Wykucie z muru kratek wentylacyjnych, drzwiczek, wentylatorow', 'szt.', '7'),
            ('KNR 4-01 0211-03', 'Skucie nierownosci betonu przy glebokosci skucia do 5 cm na podlogach', 'm2', '41,15'),
            ('KNR 4-01 0339-01', 'Wykucie bruzd pionowych 1/4x1/2 ceg. w scianach z cegiel', 'm', '15'),
            ('KNR 4-01 0336-01', 'Wykucie bruzd poziomych 1/4x1/2 ceg. w scianach z cegiel', 'm', '15'),
            ('KNR 4-01 0210-02', 'Wykucie bruzd o przekroju do 0.040 m2 w elementach z betonu zwirowego', 'm', '10'),
            ('KNR 4-01 0106-04', 'Usuniecie z parteru budynku gruzu i ziemi', 'm3', '18,285'),
        ]
    },
    {
        'numer': 2,
        'nazwa': 'PARTER - Nadproze nad otworami',
        'pozycje': [
            ('KNR 4-01 0346-05', 'Wykucie gniazd o glebokosci 1 ceg. w scianach dla belek stalowych', 'szt.', '3'),
            ('KNR 4-01 0206-03', 'Podlewka, poduszka betonowa gr. 10 cm pod belki nadprozowe', 'szt.', '3'),
            ('KNR 4-01 0313-02', 'Wykonanie przesklepien otworow w scianach z cegiel z wykuciem bruzd dla belek', 'm3', '0,081'),
            ('KNR 4-01 0313-04', 'Wykonanie przesklepien otworow - dostarczenie i obsadzenie belek stalowych', 'm', '5,4'),
            ('KNR 7-12 0101-01', 'Czyszczenie i odtluszczanie belek stalowych i malowanie farbami miniowymi', 'm2', '3,024'),
            ('KNR AT-17 0103-01', 'Wiercenie otworow o glebokosci do 40 cm sr. 40 mm technika diamentowa', 'cm', '8'),
            ('KNR 4-06 0112-01', 'Skrecanie polaczen srubami M12 kl. 5,8', 'szt.', '8'),
            ('KNR 0-40 0110-01', 'Uszczelnienie i wypelnienie szczelin miedzy wykutym otworem i ksztaltownikiem', 'm', '5,4'),
            ('KNR 4-01 0703-03', 'Umocowanie siatki Rabitza na stopkach i sciankach belek', 'm', '5,4'),
            ('KNR 4-01 0704-03', 'Wypelnienie oczek siatki cieto-ciagnionej zaprawa cementowa', 'm2', '2,43'),
            ('KNR-W 2-02 0129-05', 'Okladanie (szpaldowanie) belek stalowych', 'm2', '0,81'),
        ]
    },
    {
        'numer': 3,
        'nazwa': 'PARTER - Roboty murowe i zabudowy GK',
        'pozycje': [
            ('KNR-W 4-01 0327-02', 'Zamurowanie bruzd pionowych o przekroju 1/4 x 1/2 ceg. w scianach z cegiel', 'm', '15'),
            ('KNR-W 4-01 0326-02', 'Zamurowanie bruzd poziomych o przekroju 1/4 x 1/2 ceg. w scianach z cegiel', 'm', '15'),
            ('KNR 9-29 0306-01', 'Uzupelnienie okladzin z plyt gipsowo-kartonowych scianek dzialowych', 'm2', '18,348'),
            ('KNR-W 2-02 2003-05', 'Scianki dzialowe GR z plyt gipsowo-kartonowych gkbi na rusztach metalowych', 'm2', '22,755'),
            ('KNR AT-43 0119-02', 'Przygotowanie otworow w sciankach dzialowych z profili UA 75', 'szt.', '7'),
            ('KNR 2-02 2004-01', 'Zabudowy instalacyjne plytami gipsowo-kartonowymi gkbi na rusztach metalowych', 'm2', '30'),
        ]
    },
    {
        'numer': 4,
        'nazwa': 'PARTER - Roboty tynkowe i okladziny',
        'pozycje': [
            ('KNR 4-01 0705-04', 'Wykonanie pasow tynku zwyklego kat. III o szerokosci do 15 cm pokrywajacego bruzdy', 'm', '30'),
            ('KNR 4-01 0716-02', 'Tynki wewnetrzne zwykle kat. III wykonywane recznie na podlozu z cegly', 'm2', '123,181'),
            ('KNR 4-01 0711-14', 'Uzupelnienie tynkow zwyklych wewnetrznych kat. III na stropach', 'm2', '48,564'),
            ('KNR 4-01 0708-03', 'Wykonanie tynkow zwyklych wewnetrznych kat. III na osciezach', 'm', '15,3'),
            ('KNR 4-01 0713-01', 'Przecieranie istniejacych tynkow wewnetrznych z zeskrobaniem farby', 'm2', '16,895'),
            ('KNR 2-02 0812-01', 'Tynki wewnetrzne pocienione kat. III na scianach powyzej plytek', 'm2', '69,115'),
            ('KNR 2-02 2006-07', 'Okladziny z plyt gipsowo-kartonowych - dodatek za druga warstwe', 'm2', '14,51'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni pod gladzie', 'm2', '109,585'),
            ('KNR 2-02 2009-04', 'Tynki (gladzie) jednowarstwowe wewnetrzne gr. 3 mm na stropach', 'm2', '40,47'),
            ('KNR 2-02 2009-02', 'Tynki (gladzie) jednowarstwowe wewnetrzne gr. 3 mm na scianach', 'm2', '69,115'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni pod izolacje', 'm2', '126,355'),
            ('KNR AT-27 0401-01', 'Pionowa izolacja podplytkowa przeciwwilgociowa gr. 1 mm z folii w plynie', 'm2', '126,355'),
            ('KNR AT-27 0401-04', 'Pionowa izolacja podplytkowa z folii w plynie - dodatek za kolejna warstwe', 'm2', '126,355'),
            ('KNR AT-27 0401-05', 'Izolacja podplytkowa folii w plynie - wklejenie tasmy uszczelniajcej', 'm', '98,4'),
            ('KNR 2-02 0829-11', 'Licowanie scian plytkami o wymiarach 30x60 cm na klej metoda kombinowana', 'm2', '126,355'),
            ('KNR-W 2-02 0840-08', 'Licowanie scian plytkami - listwy naroznikowe aluminiowe', 'm', '111,75'),
            ('KNR 2-02 1505-03', 'Dwukrotne malowanie farbami emulsyjnymi powierzchni wewnetrznych', 'm2', '140,99'),
            ('KNR 2-02 1505-06', 'Malowanie farbami emulsyjnymi - dodatek za kazde dalsze malowanie', 'm2', '140,99'),
            ('KNR 4-01 1206-05', 'Dwukrotne malowanie farbami olejnymi starych tynkow wewnetrznych', 'm2', '5,7'),
        ]
    },
    {
        'numer': 5,
        'nazwa': 'PARTER - Roboty posadzkowe',
        'pozycje': [
            ('KNR 4-01 0207-03', 'Zabetonowanie zwirobetonem bruzd o przekroju do 0.045 m2 w podlozach', 'm', '12'),
            ('KNR 2-02 1102-02', 'Warstwy wyrownawcze pod posadzki z zaprawy cementowej grubo 50 mm', 'm2', '40,47'),
            ('KNR 2-02 1106-07', 'Posadzki cementowe - doplata za zbrojenie siatka stalowa', 'm2', '40,47'),
            ('KNR-W 2-02 1105-01', 'Warstwy niwelujaco-wyrownawcze cementowe grubo 2 mm', 'm2', '40,47'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni', 'm2', '40,47'),
            ('KNR AT-27 0401-03', 'Pozioma izolacja podplytkowa przeciwwilgociowa gr. 1 mm z folii w plynie', 'm2', '40,47'),
            ('KNR AT-27 0401-04', 'Pozioma izolacja podplytkowa z folii w plynie - dodatek za kolejna warstwe', 'm2', '40,47'),
            ('KNR AT-27 0401-05', 'Izolacja podplytkowa folii w plynie - wklejenie tasmy uszczelniajcej', 'm', '55,3'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni', 'm2', '40,47'),
            ('KNR 2-02 1118-11', 'Posadzki plytkowe z kamieni sztucznych; plytki 60x60 cm na klej', 'm2', '40,47'),
            ('KNR 4-01 0411-08', 'Systemowe aluminiowe listwy progowe na polaczeniu z korytarzem', 'szt.', '5'),
        ]
    },
    {
        'numer': 6,
        'nazwa': 'PARTER - Stolarka',
        'pozycje': [
            ('KNR 4-01 0320-03', 'Obsadzenie oscieznic stalowych stalych', 'm2', '6,15'),
            ('KNR 4-01 0320-03', 'Obsadzenie oscieznic stalowych regulowanych (opaskowych)', 'm2', '11,07'),
            ('KNR 2-02 1017-02', 'Skrzydla drzwiowe plytowe wewnetrzne jednodzielne pelne o powierzchni ponad 1.6 m2', 'm2', '17,22'),
            ('KNR-W 2-02 1029-05', 'Systemowe scianki sanitarne z drzwiami', 'm2', '12,04'),
            ('KNR 2-02 1009-06', 'Naswietla PCV', 'm2', '3,36'),
            ('KNR 2-02 1215-02', 'Drzwiczki rewizyjne osadzone w scianach GK o powierzchni do 0.2 m2', 'szt.', '7'),
            ('KNR 2-17 0156-01', 'Nawietrzaki okienne z frezowaniem otworow', 'szt.', '3'),
            ('KNR 4-01 0919-20', 'Wymiana klamek okiennych z regulacja skrzydel okiennych', 'szt.', '12'),
        ]
    },
    {
        'numer': 7,
        'nazwa': 'PARTER - Instalacja kanalizacji sanitarnej',
        'pozycje': [
            ('KNR 4-02 0235-06', 'Demontaz umywalki', 'kpl.', '5'),
            ('KNR 4-02 0235-08', 'Demontaz ustepu z miska fajansowa', 'kpl.', '5'),
            ('KNR 4-02 0235-07', 'Demontaz brodzika', 'kpl.', '2'),
            ('KNR 4-02 0235-01', 'Demontaz pisuaru', 'kpl.', '2'),
            ('KNR 4-02 0230-04', 'Demontaz rurociagu zeliwnego/PCV kanalizacyjnego o sr. 50-100 mm', 'm', '30'),
            ('KNR 4-02 0230-05', 'Demontaz rurociagu zeliwnego/PCV kanalizacyjnego o sr. 150 mm', 'm', '20'),
            ('KNR 4-02 0234-02', 'Demontaz elementow uzbrojenia rurociagu - wpust zeliwny podlogowy', 'szt.', '3'),
            ('KNR 4-02 0202-09', 'Polaczenie nowo budowanej kanalizacji sanitarnej z istniejaca wewnetrzna instalacja', 'kpl', '4'),
            ('KNR AT-17 0104-04', 'Ciecie pila diamentowa betonu zbrojonego o grub. powyzej 15 do 40 cm', 'm2', '2'),
            ('KNR-W 4-01 0212-02', 'Mechaniczna rozbiorka elementow konstrukcji betonowych niezbrojonych', 'm3', '0,5'),
            ('KNR 2-15 0205-04', 'Montaz rurociagow z PCW o sr. 160 mm na scianach z laczeniem metoda wciskowa', 'm', '9'),
            ('KNR 2-15 0205-04', 'Montaz rurociagow z PCW o sr. 110 mm na scianach z laczeniem metoda wciskowa', 'm', '15'),
            ('KNR 2-15 0205-03', 'Montaz rurociagow z PCW o sr. 75 mm na scianach z laczeniem metoda wciskowa', 'm', '10'),
            ('KNR 2-15 0205-02', 'Montaz rurociagow z PCW o sr. 50 mm na scianach z laczeniem metoda wciskowa', 'm', '20'),
            ('S 215 0200-01', 'Zawory napowietrzajace plywakowe o sr.nom. 50 mm', 'szt.', '1'),
            ('KNR-W 2-15 0211-03', 'Dodatki za wykonanie podejsc odplywowych z PVC o sr. 110 mm', 'szt.', '5'),
            ('KNR-W 2-15 0234-02', 'Pisuary pojedyncze wyposazione w zawory splukujace', 'kpl.', '3'),
            ('KNR-W 2-15 0230-02', 'Umywalki pojedyncze porcelanowe (komplet z syfonem i zawiesiami)', 'kpl.', '5'),
            ('KNR-W 2-15 0230-05', 'Polpostument porcelanowy do umywalek', 'kpl.', '5'),
            ('KNR-W 2-15 0232-02', 'Brodziki natryskowe na podstawie styropianowej z obudowa 90x100 cm', 'kpl.', '2'),
            ('KNR 0-35 0123-01', 'Kabiny natryskowe do kapieli z szybami ze szkla hartowanego', 'kpl.', '2'),
            ('KNR-W 2-15 0218-01', 'Wpusty sciekowe ze stali nierdzewnej o sr. 50 mm', 'szt.', '4'),
            ('KNR-W 2-15 0127-02', 'Proba szczelnosci instalacji kanalizacyjnej z rur PVC', 'm', '54'),
            ('KNR 4-03 1015-04', 'Przykrecanie drobnych elementow na scianie - uchwyty, dozowniki, lustra', 'szt.', '20'),
        ]
    },
    {
        'numer': 8,
        'nazwa': 'PARTER - Instalacja wody zimnej i cwu',
        'pozycje': [
            ('KNR 4-02 0111-03', 'Polaczenie instalacji c.w.u. z istniejaca wewnetrzna instalacja wodociagowa', 'szt.', '1'),
            ('KNR 4-02 0111-03', 'Polaczenie instalacji w.z. z istniejaca wewnetrzna instalacja wodociagowa', 'szt.', '1'),
            ('KNR 4-01 0208-04', 'Przebicie otworow w elementach z betonu zwirowego o grub. do 40 cm', 'szt.', '4'),
            ('KNR-W 2-15 0111-01', 'Rurociagi z tworzyw sztucznych PP-R o sr. 16 mm', 'm', '35'),
            ('KNR-W 2-15 0111-01', 'Rurociagi z tworzyw sztucznych PP-R o sr. 20 mm', 'm', '30'),
            ('KNR-W 2-15 0111-02', 'Rurociagi z tworzyw sztucznych PP-R o sr. 25 mm', 'm', '30'),
            ('KNR-W 2-15 0111-03', 'Rurociagi z tworzyw sztucznych PP-R o sr. 32 mm', 'm', '15'),
            ('KNR-W 2-15 0132-03', 'Zawory kulowe instalacji wodociagowych z rur z tworzyw sztucznych', 'szt.', '6'),
            ('KNR-W 2-15 0116-08', 'Dodatki za podejscia doplywowe w rurocagach z tworzyw sztucznych', 'szt.', '19'),
            ('KNR-W 2-15 0135-01', 'Zawory czerpalne ze zlaczka o sr. nominalnej 15 mm', 'szt.', '22'),
            ('KNR-W 2-15 0137-02', 'Baterie umywalkowe stojace o sr. nominalnej 15 mm', 'szt.', '5'),
            ('KNR-W 2-15 0137-09', 'Baterie natryskowe z natryskiem przesuwnym o sr. nominalnej 15 mm', 'szt.', '2'),
            ('KNR 0-31 0116-01', 'Proba szczelnosci instalacji wody zimnej i cieplej - plukanie', 'kpl.', '1'),
            ('KNR 0-31 0116-02', 'Proba szczelnosci instalacji wody - proba wodna cisnieniowa', 'm', '110'),
            ('KNR-W 2-18 0707-01', 'Dezynfekcja rurociagow sieci wodociagowych', 'm', '1'),
            ('KNR 0-34 0101-06', 'Izolacja rurociagow sr.20 mm otulinami Thermaflex FRZ gr.13 mm', 'm', '39'),
            ('KNR 0-34 0101-10', 'Izolacja rurociagow sr. 12-22 mm otulinami Thermaflex FRZ gr. 20 mm', 'm', '26'),
            ('KNR 0-34 0101-11', 'Izolacja rurociagow sr. 28-48 mm otulinami Thermaflex FRZ gr. 20 mm', 'm', '22,5'),
            ('KNR 0-34 0101-07', 'Izolacja rurociagow sr. 28-48 mm otulinami Thermaflex FRZ gr. 13 mm', 'm', '22,5'),
            ('KNR 0-34 0110-14', 'Izolacja dwuwarstwowa rurociagow sr. 28-48 mm otulinami gr. 40 mm', 'm', '10'),
        ]
    },
    {
        'numer': 9,
        'nazwa': 'PARTER - Instalacja c.o.',
        'pozycje': [
            ('KNR-W 4-02 0515-06', 'Wymiana grzejnika zeliwnego czlonowego na stalowy grzejnik panelowy', 'kpl.', '5'),
            ('KNR-W 4-02 0517-05', 'Wymiana rur przylacznych do grzejnika z rur stalowych ze stali nierdzewnej', 'kpl.', '10'),
            ('KNR 2-15 0404-02', 'Proby cisnieniowe szczelnosci instalacji wewnetrznej c.o.', 'm', '40'),
        ]
    },
    {
        'numer': 10,
        'nazwa': 'PARTER - Wentylacja mechaniczna',
        'pozycje': [
            ('KNR-W 2-17 0206-01', 'Wentylator lazienkowy z timerem regulowanym, czujnikiem ruchu', 'szt.', '2'),
        ]
    },
    {
        'numer': 11,
        'nazwa': 'PARTER - Instalacja elektryczna',
        'pozycje': [
            ('KSNR 5 0406-05', 'Wypust oswietleniowy podtynkowy z wykonaniem i zaprawieniem bruzd', 'szt.', '19'),
            ('KSNR 5 0406-05', 'Wypust oswietleniowy ewakuacyjny podtynkowy', 'szt.', '4'),
            ('KSNR 5 0502-02', 'Montaz opraw oswietleniowych LED przykrecanych z modulem ewakuacyjnym', 'kpl.', '14'),
            ('KSNR 5 0502-02', 'Montaz opraw oswietleniowych LED przykrecanych nad umywalkami', 'kpl.', '5'),
            ('KSNR 5 0502-01', 'Montaz opraw oswietleniowych przykrecanych ewakuacyjnych', 'kpl.', '4'),
            ('KNR AL-01 0201-01', 'Montaz czujki ruchu - pasywna podczerwieni', 'szt.', '8'),
            ('KSNR 5 0405-01', 'Wypusty wykonywane przewodami wtynkowymi na wylacznik', 'szt.', '5'),
            ('KSNR 5 0406-07', 'Wypusty dla gniazd 230V podtynkowo - gniazdo pojedyncze', 'szt.', '5'),
            ('KSNR 5 0406-07', 'Wypusty dla gniazd 230V podtynkowo - zasilanie suszarek', 'szt.', '5'),
            ('KNR 5-08 0309-03', 'Montaz do gotowego podloza gniazd wtyczkowych podtynkowych', 'szt.', '5'),
            ('KNR 5-08 0402-01', 'Mocowanie na gotowym podlozu aparatow - suszarka do rak', 'szt.', '5'),
            ('KNR 4-03 1205-05', 'Pomiar skutecznosci zerowania', 'kpl.', '1'),
            ('KNR 4-03 1202-01', 'Sprawdzenie i pomiar kompletnego 1-fazowego obwodu elektrycznego', 'kpl.', '1'),
            ('KNR-W 4-03 1208-01', 'Pierwszy pomiar rezystancji izolacji instalacji elektrycznych', 'kpl.', '1'),
            ('KNR 13-21 0301-03', 'Pomiary natezenia oswietlenia', 'kpl.', '5'),
        ]
    },
    # ============ I PIETRO ============
    {
        'numer': 12,
        'nazwa': 'I PIETRO - Roboty rozbiórkowe',
        'pozycje': [
            ('KNR 4-01 0354-09', 'Wykucie z muru oscieznic stalowych lub krat drzwiowych o powierzchni do 2 m2', 'szt.', '7'),
            ('KNR 4-01 0354-12', 'Wykucie z muru podokiennikow betonowych z lastryko', 'm', '4,35'),
            ('KNR 9-29 0105-02', 'Rozbiorka obudow pionow instalacyjnych z plyt gipsowo-kartonowych', 'm2', '21,87'),
            ('KNR 4-01 0427-05', 'Rozebranie scianek dzialowych sanitarnych', 'm2', '10,458'),
            ('KNR 4-01 0348-03', 'Rozebranie scianki z cegiel o grub. 1/2 ceg.', 'm2', '28,85'),
            ('KNR 4-01 0819-15', 'Rozebranie wykladziny sciennej z plytek', 'm2', '100,831'),
            ('KNR 4-01 0701-05', 'Odbicie tynkow wewnetrznych z zaprawy cementowo-wapiennej na scianach', 'm2', '100,831'),
            ('KNR 4-01 0702-06', 'Odbicie tynkow wewnetrznych pasami o szerokosci do 30 cm', 'm', '8,2'),
            ('KNR 4-01 1202-08', 'Zeskrobanie i zmycie starej farby w pomieszczeniach', 'm2', '97,166'),
            ('KNR 4-01 0811-07', 'Rozebranie posadzki z plytek na zaprawie cementowej', 'm2', '47,566'),
            ('KNR 4-01 0354-13', 'Wykucie z muru kratek wentylacyjnych, wentylatorow, drzwiczek', 'szt.', '8'),
            ('KNR 4-01 0804-07', 'Zerwanie posadzki cementowej/lastykowej - wyrownanie podloza', 'm2', '47,566'),
            ('KNR 4-01 0339-01', 'Wykucie bruzd pionowych 1/4x1/2 ceg. w scianach z cegiel', 'm', '30'),
            ('KNR 4-01 0336-01', 'Wykucie bruzd poziomych 1/4x1/2 ceg. w scianach z cegiel', 'm', '30'),
            ('KNR 4-01 0210-02', 'Wykucie bruzd o przekroju do 0.040 m2 w elementach z betonu zwirowego', 'm', '12'),
            ('KNR 4-01 0106-04', 'Usuniecie z budynku gruzu i ziemi', 'm3', '18,727'),
        ]
    },
    {
        'numer': 13,
        'nazwa': 'I PIETRO - Roboty murowe i zabudowy GK',
        'pozycje': [
            ('KNR-W 4-01 0327-02', 'Zamurowanie bruzd pionowych o przekroju 1/4 x 1/2 ceg. w scianach z cegiel', 'm', '30'),
            ('KNR-W 4-01 0326-02', 'Zamurowanie bruzd poziomych o przekroju 1/4 x 1/2 ceg. w scianach z cegiel', 'm', '30'),
            ('KNR-W 2-02 2003-05', 'Scianki dzialowe GR z plyt gipsowo-kartonowych gkbi na rusztach metalowych', 'm2', '33,825'),
            ('KNR AT-43 0119-02', 'Przygotowanie otworow w sciankach dzialowych z profili UA 75', 'szt.', '8'),
            ('KNR 2-02 2004-01', 'Zabudowy instalacyjne plytami gipsowo-kartonowymi gkbi na rusztach metalowych', 'm2', '50'),
        ]
    },
    {
        'numer': 14,
        'nazwa': 'I PIETRO - Roboty tynkowe i okladziny',
        'pozycje': [
            ('KNR 4-01 0705-04', 'Wykonanie pasow tynku zwyklego kat. III o szerokosci do 15 cm', 'm', '60'),
            ('KNR 4-01 0716-02', 'Tynki wewnetrzne zwykle kat. III wykonywane recznie na podlozu z cegly', 'm2', '100,831'),
            ('KNR 4-01 0711-14', 'Uzupelnienie tynkow zwyklych wewnetrznych kat. III na stropach', 'm2', '56,119'),
            ('KNR 4-01 0708-03', 'Wykonanie tynkow zwyklych wewnetrznych kat. III na osciezach', 'm', '26,6'),
            ('KNR 4-01 0713-01', 'Przecieranie istniejacych tynkow wewnetrznych z zeskrobaniem farby', 'm2', '11,34'),
            ('KNR 2-02 2006-07', 'Okladziny z plyt gipsowo-kartonowych - dodatek za druga warstwe', 'm2', '21,856'),
            ('KNR 2-02 0812-01', 'Tynki wewnetrzne pocienione kat. III na scianach powyzej plytek', 'm2', '52,92'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni pod gladzie', 'm2', '99,686'),
            ('KNR 2-02 2009-04', 'Tynki (gladzie) jednowarstwowe wewnetrzne gr. 3 mm na stropach', 'm2', '46,766'),
            ('KNR 2-02 2009-02', 'Tynki (gladzie) jednowarstwowe wewnetrzne gr. 3 mm na scianach', 'm2', '52,92'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni pod izolacje', 'm2', '154,049'),
            ('KNR AT-27 0401-01', 'Pionowa izolacja podplytkowa przeciwwilgociowa gr. 1 mm z folii w plynie', 'm2', '154,049'),
            ('KNR AT-27 0401-04', 'Pionowa izolacja podplytkowa z folii w plynie - dodatek za kolejna warstwe', 'm2', '154,049'),
            ('KNR AT-27 0401-05', 'Izolacja podplytkowa folii w plynie - wklejenie tasmy uszczelniajcej', 'm', '69,4'),
            ('KNR 2-02 0829-11', 'Licowanie scian plytkami o wymiarach 30x60 cm na klej', 'm2', '158,584'),
            ('KNR-W 2-02 0840-08', 'Licowanie scian plytkami - listwy naroznikowe aluminiowe', 'm', '90,95'),
            ('KNR 2-02 1505-03', 'Dwukrotne malowanie farbami emulsyjnymi powierzchni wewnetrznych', 'm2', '132,882'),
            ('KNR 2-02 1505-06', 'Malowanie farbami emulsyjnymi - dodatek za kazde dalsze malowanie', 'm2', '132,882'),
            ('KNR 4-01 1206-05', 'Dwukrotne malowanie farbami olejnymi starych tynkow wewnetrznych', 'm2', '4,05'),
        ]
    },
    {
        'numer': 15,
        'nazwa': 'I PIETRO - Roboty posadzkowe',
        'pozycje': [
            ('KNR 4-01 0207-03', 'Zabetonowanie zwirobetonem bruzd o przekroju do 0.045 m2 w podlozach', 'm', '12'),
            ('KNR 2-02 1102-02', 'Warstwy wyrownawcze pod posadzki z zaprawy cementowej grubo 50 mm', 'm2', '47,566'),
            ('KNR 2-02 1106-07', 'Posadzki cementowe - doplata za zbrojenie siatka stalowa', 'm2', '47,566'),
            ('KNR-W 2-02 1105-01', 'Warstwy niwelujaco-wyrownawcze cementowe grubo 2 mm', 'm2', '47,566'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni', 'm2', '47,566'),
            ('KNR AT-27 0401-03', 'Pozioma izolacja podplytkowa przeciwwilgociowa gr. 1 mm z folii w plynie', 'm2', '47,566'),
            ('KNR AT-27 0401-04', 'Pozioma izolacja podplytkowa z folii w plynie - dodatek za kolejna warstwe', 'm2', '47,566'),
            ('KNR AT-27 0401-05', 'Izolacja podplytkowa folii w plynie - wklejenie tasmy uszczelniajcej', 'm', '68,18'),
            ('NNRNKB 202 1134-02', 'Gruntowanie podlozy preparatami powierzchni', 'm2', '47,566'),
            ('KNR 2-02 1118-11', 'Posadzki plytkowe z kamieni sztucznych; plytki 60x60 cm na klej', 'm2', '47,566'),
            ('KNR 4-01 0411-08', 'Systemowe aluminiowe listwy progowe na polaczeniu z korytarzem', 'szt.', '3'),
        ]
    },
    {
        'numer': 16,
        'nazwa': 'I PIETRO - Stolarka',
        'pozycje': [
            ('KNR 4-01 0320-03', 'Obsadzenie oscieznic stalowych stalych', 'm2', '6,15'),
            ('KNR 4-01 0320-03', 'Obsadzenie oscieznic stalowych regulowanych (opaskowych)', 'm2', '9,635'),
            ('KNR 2-02 1017-02', 'Skrzydla drzwiowe plytowe wewnetrzne jednodzielne pelne', 'm2', '14,145'),
            ('KNR-W 2-02 1029-05', 'Systemowe scianki sanitarne z drzwiami', 'm2', '16,82'),
            ('KNR 2-02 1009-06', 'Naswietla PCV', 'm2', '3,6'),
            ('KNR 2-02 1215-02', 'Drzwiczki rewizyjne osadzone w scianach GK', 'szt.', '6'),
            ('KNR 2-17 0156-01', 'Nawietrzaki okienne z frezowaniem otworow', 'szt.', '5'),
            ('KNR 4-01 0919-20', 'Wymiana klamek okiennych z regulacja skrzydel okiennych', 'szt.', '14'),
        ]
    },
    {
        'numer': 17,
        'nazwa': 'I PIETRO - Instalacja kanalizacji sanitarnej',
        'pozycje': [
            ('KNR 4-02 0235-03', 'Demontaz zlewu', 'kpl.', '1'),
            ('KNR 4-02 0235-06', 'Demontaz umywalki', 'kpl.', '5'),
            ('KNR 4-02 0235-08', 'Demontaz ustepu z miska fajansowa', 'kpl.', '5'),
            ('KNR 4-02 0235-01', 'Demontaz pisuaru', 'kpl.', '2'),
            ('KNR 4-02 0235-07', 'Demontaz brodzika', 'kpl.', '2'),
            ('KNR 4-02 0230-04', 'Demontaz rurociagu kanalizacyjnego o sr. 50-100 mm', 'm', '15'),
            ('KNR 4-02 0230-05', 'Demontaz rurociagu kanalizacyjnego o sr. 150 mm', 'm', '20'),
            ('KNR 4-02 0234-02', 'Demontaz elementow uzbrojenia rurociagu - wpust zeliwny podlogowy', 'szt.', '2'),
            ('KNR 4-02 0202-09', 'Polaczenie nowo budowanej kanalizacji sanitarnej z istniejaca instalacja', 'kpl', '5'),
            ('KNR AT-17 0104-04', 'Ciecie pila diamentowa betonu zbrojonego', 'm2', '2'),
            ('KNR-W 4-01 0212-02', 'Mechaniczna rozbiorka elementow konstrukcji betonowych niezbrojonych', 'm3', '0,5'),
            ('KNR 2-15 0205-04', 'Montaz rurociagow z PCW o sr. 160 mm', 'm', '9'),
            ('KNR 2-15 0205-04', 'Montaz rurociagow z PCW o sr. 110 mm', 'm', '15'),
            ('KNR 2-15 0205-03', 'Montaz rurociagow z PCW o sr. 75 mm', 'm', '12'),
            ('KNR 2-15 0205-02', 'Montaz rurociagow z PCW o sr. 50 mm', 'm', '25'),
            ('S 215 0200-01', 'Zawory napowietrzajace plywakowe o sr.nom. 50 mm', 'szt.', '3'),
            ('KNR-W 2-15 0211-03', 'Dodatki za wykonanie podejsc odplywowych z PVC o sr. 110 mm', 'szt.', '4'),
            ('KNR-W 2-15 0218-01', 'Wpusty sciekowe ze stali nierdzewnej o sr. 50 mm', 'szt.', '3'),
            ('KNR-W 2-15 0230-02', 'Umywalki pojedyncze porcelanowe', 'kpl.', '5'),
            ('KNR-W 2-15 0230-05', 'Polpostument porcelanowy do umywalek', 'kpl.', '5'),
            ('KNR-W 2-15 0234-02', 'Pisuary pojedyncze wyposazione w zawory splukujace', 'kpl.', '3'),
            ('KNR-W 2-15 0232-02', 'Brodziki natryskowe na podstawie styropianowej', 'kpl.', '2'),
            ('KNR 0-35 0123-01', 'Kabiny natryskowe do kapieli z szybami ze szkla hartowanego', 'kpl.', '2'),
            ('KNR-W 2-15 0127-02', 'Proba szczelnosci instalacji kanalizacyjnej z rur PVC', 'm', '61'),
            ('KNR 4-03 1015-04', 'Przykrecanie drobnych elementow na scianie - uchwyty, dozowniki, lustra', 'szt.', '18'),
        ]
    },
    {
        'numer': 18,
        'nazwa': 'I PIETRO - Instalacja wody zimnej i cwu',
        'pozycje': [
            ('KNR 4-02 0111-03', 'Polaczenie instalacji c.w.u. z istniejaca wewnetrzna instalacja wodociagowa', 'szt.', '1'),
            ('KNR 4-02 0111-03', 'Polaczenie instalacji w.z. z istniejaca wewnetrzna instalacja wodociagowa', 'szt.', '1'),
            ('KNR 4-01 0208-04', 'Przebicie otworow w elementach z betonu zwirowego o grub. do 40 cm', 'szt.', '9'),
            ('KNR-W 2-15 0111-01', 'Rurociagi z tworzyw sztucznych PP-R o sr. 16 mm', 'm', '40'),
            ('KNR-W 2-15 0111-01', 'Rurociagi z tworzyw sztucznych PP-R o sr. 20 mm', 'm', '40'),
            ('KNR-W 2-15 0111-02', 'Rurociagi z tworzyw sztucznych PP-R o sr. 25 mm', 'm', '30'),
            ('KNR-W 2-15 0111-03', 'Rurociagi z tworzyw sztucznych PP-R o sr. 32 mm', 'm', '10'),
            ('KNR-W 2-15 0132-03', 'Zawory kulowe instalacji wodociagowych z rur z tworzyw sztucznych', 'szt.', '6'),
            ('KNR-W 2-15 0116-08', 'Dodatki za podejscia doplywowe w rurocagach z tworzyw sztucznych', 'szt.', '17'),
            ('KNR-W 2-15 0135-01', 'Zawory czerpalne ze zlaczka o sr. nominalnej 15 mm', 'szt.', '20'),
            ('KNR-W 2-15 0137-02', 'Baterie umywalkowe stojace o sr. nominalnej 15 mm', 'szt.', '5'),
            ('KNR-W 2-15 0137-09', 'Baterie natryskowe z natryskiem przesuwnym', 'szt.', '2'),
            ('KNR 0-31 0116-01', 'Proba szczelnosci instalacji wody - plukanie', 'kpl.', '1'),
            ('KNR 0-31 0116-02', 'Proba szczelnosci instalacji wody - proba wodna cisnieniowa', 'm', '120'),
            ('KNR 0-34 0101-06', 'Izolacja rurociagow sr.20 mm otulinami Thermaflex FRZ gr.13 mm', 'm', '48'),
            ('KNR 0-34 0101-10', 'Izolacja rurociagow sr. 12-22 mm otulinami Thermaflex FRZ gr. 20 mm', 'm', '32'),
            ('KNR 0-34 0101-11', 'Izolacja rurociagow sr. 28-48 mm otulinami Thermaflex FRZ gr. 20 mm', 'm', '20'),
            ('KNR 0-34 0101-07', 'Izolacja rurociagow sr. 28-48 mm otulinami Thermaflex FRZ gr. 13 mm', 'm', '20'),
            ('KNR 0-34 0110-14', 'Izolacja dwuwarstwowa rurociagow sr. 28-48 mm otulinami gr. 40 mm', 'm', '10'),
        ]
    },
    {
        'numer': 19,
        'nazwa': 'I PIETRO - Instalacja c.o.',
        'pozycje': [
            ('KNR-W 4-02 0515-06', 'Wymiana grzejnika zeliwnego czlonowego na stalowy grzejnik panelowy', 'kpl.', '3'),
            ('KNR-W 4-02 0517-05', 'Wymiana rur przylacznych do grzejnika z rur stalowych ze stali nierdzewnej', 'kpl.', '6'),
            ('KNR 2-15 0404-02', 'Proby cisnieniowe szczelnosci instalacji wewnetrznej c.o.', 'm', '40'),
        ]
    },
    {
        'numer': 20,
        'nazwa': 'I PIETRO - Wentylacja mechaniczna',
        'pozycje': [
            ('KNR-W 2-17 0206-01', 'Wentylator lazienkowy z timerem regulowanym, czujnikiem ruchu', 'szt.', '3'),
        ]
    },
    {
        'numer': 21,
        'nazwa': 'I PIETRO - Instalacja elektryczna',
        'pozycje': [
            ('KSNR 5 0406-05', 'Wypust oswietleniowy podtynkowy z wykonaniem i zaprawieniem bruzd', 'szt.', '23'),
            ('KSNR 5 0406-05', 'Wypust oswietleniowy ewakuacyjny podtynkowy', 'szt.', '3'),
            ('KSNR 5 0502-02', 'Montaz opraw oswietleniowych LED przykrecanych - natrysk z modulem ewakuacyjnym', 'kpl.', '4'),
            ('KSNR 5 0502-02', 'Montaz opraw oswietleniowych LED przykrecanych z modulem ewakuacyjnym', 'kpl.', '14'),
            ('KSNR 5 0502-02', 'Montaz opraw oswietleniowych LED przykrecanych nad umywalkami', 'kpl.', '5'),
            ('KSNR 5 0502-01', 'Montaz opraw oswietleniowych przykrecanych ewakuacyjnych', 'kpl.', '3'),
            ('KNR AL-01 0201-01', 'Montaz czujki ruchu - pasywna podczerwieni', 'szt.', '8'),
            ('KSNR 5 0405-01', 'Wypusty wykonywane przewodami wtynkowymi na wylacznik', 'szt.', '5'),
            ('KSNR 5 0406-07', 'Wypusty dla gniazd 230V podtynkowo - gniazdo pojedyncze', 'szt.', '5'),
            ('KSNR 5 0406-07', 'Wypusty dla gniazd 230V podtynkowo - zasilanie suszarek', 'szt.', '3'),
            ('KNR 5-08 0309-03', 'Montaz do gotowego podloza gniazd wtyczkowych podtynkowych', 'szt.', '5'),
            ('KNR 5-08 0402-01', 'Mocowanie na gotowym podlozu aparatow - suszarka do rak', 'szt.', '3'),
            ('KNR 4-03 1205-05', 'Pomiar skutecznosci zerowania', 'kpl.', '1'),
            ('KNR 4-03 1202-01', 'Sprawdzenie i pomiar kompletnego 1-fazowego obwodu elektrycznego', 'kpl.', '1'),
            ('KNR-W 4-03 1208-01', 'Pierwszy pomiar rezystancji izolacji instalacji elektrycznych', 'kpl.', '1'),
            ('KNR 13-21 0301-03', 'Pomiary natezenia oswietlenia', 'kpl.', '3'),
        ]
    },
]

def generate_ath():
    """Generuje plik ATH"""
    lines = []
    
    # Zlicz wszystkie pozycje
    total_positions = sum(len(d['pozycje']) for d in DZIALY)
    
    # === NAGLOWEK ===
    lines.append("[KOSZTORYS ATHENASOFT]")
    lines.append("co=Copyright Athenasoft Sp. z o.o.")
    lines.append("wf=5")
    lines.append("pr=NORMA\t5.16.400.14")
    lines.append("nan=BUDOWLANA ")
    lines.append("op=1")
    lines.append("opn=0\t0\t2\t1\t1\t0\t19\t8\t0\t7\t0\t0\t0\t0\t1.\t1\t1\t0\t0\t1\t1\t2\t0\t0\t0")
    lines.append("prn=2\t2\t3\t3\t4\t1\t6\t0\t1\t0")
    lines.append("own=3\t1\t1\t0\t1\t0\t0\t1\t1\t1\t0\t0\t1\t1\t1\t0\tpoz.\t{\t}\t1\t0\t0\t0\t0\t0\t0\t1\t0\t2\t0\t0\t1\t1\t0\t0\t0\t0\t0\t0\t0")
    lines.append("pm=dzial\tdzial")
    lines.append("pd=dzialu\tdzialu")
    lines.append("mm=dzialy\tdzialy")
    lines.append("md=dzialow\tdzialow")
    lines.append("wan=PLN")
    lines.append("wbn=PLN\tzl")
    lines.append("wk=0")
    lines.append("na=Koszty posrednie\tZysk\tVAT")
    lines.append("wn=0\t0\t0")
    lines.append(f"ir={total_positions}")
    
    # === PODSUMOWANIE ===
    lines.append("")
    lines.append("[PODSUMOWANIE]")
    lines.append("wa=")
    lines.append("kb=0\t0\t0\t0\t0\t0\t0\t")
    lines.append("na=0\t0\t0\t0\t0\t0\t0\t0\tKp\tKoszty posrednie\t65% (R+S)")
    lines.append("na=0\t0\t0\t0\t0\t0\t0\t0\tZ\tZysk\t12% (R+S+Kp(R+S))")
    lines.append("va=0\t23%\t0\tR+M+S+Kp(R+S)+Z(R+S)")
    lines.append("wc=0\t0\t0\t0\t0\t0\t0\t")
    
    # === STRONA TYTULOWA ===
    lines.append("")
    lines.append("[STRONA TYT]")
    lines.append("na=KOSZTORYS\tPRZEDMIAR")
    lines.append(f"nfn={WYKONAWCA} ")
    lines.append("afn= ")
    lines.append(f"nb={NAZWA_INWESTYCJI}")
    lines.append(f"ab={ADRES_INWESTYCJI}")
    lines.append(f"ni={NAZWA_INWESTORA} ")
    lines.append(f"ai={ADRES_INWESTORA} ")
    lines.append(f"nw={WYKONAWCA} ")
    lines.append("aw= ")
    lines.append(f"dt={DATA}\t0\t0")
    
    # === NARZUTY ===
    lines.append("")
    lines.append("[NARZUTY NORMA 2]")
    lines.append("na=Koszty posrednie\tKp")
    lines.append("wa=65\t1\t0\t")
    lines.append("op=1\t0")
    lines.append("nr=1")
    lines.append("ns=1")
    
    lines.append("")
    lines.append("[NARZUTY NORMA 2]")
    lines.append("na=Zysk\tZ")
    lines.append("wa=12\t1\t0\t")
    lines.append("op=1\t0")
    lines.append("nr=1")
    lines.append("ns=1")
    
    lines.append("")
    lines.append("[NARZUTY NORMA 1]")
    lines.append("na=VAT\tV")
    lines.append("wa=23\t1\t0\t")
    lines.append("op=0\t0")
    lines.append("nc=1")
    
    lines.append("")
    lines.append("[NARZUTY NEX 1]")
    lines.append("na=Koszt zakupu\tKz")
    lines.append("kz=7\t\t1")
    
    lines.append("")
    lines.append("[NARZUTY NEX 2]")
    lines.append("na=Koszty posrednie\tKp")
    lines.append("wa=65\t1\t1\t0")
    lines.append("nr=1\tR\t1\t65\t0")
    lines.append("ns=1\tS\t1\t65\t0")
    
    lines.append("")
    lines.append("[NARZUTY NEX 2]")
    lines.append("na=Zysk\tZ")
    lines.append("wa=12\t1\t1\t0")
    lines.append("nr=1\tR+Kp\t1\t12\t0")
    lines.append("ns=1\tS+Kp\t1\t12\t0")
    
    lines.append("")
    lines.append("[NARZUTY NEX 4]")
    lines.append("na=VAT\tV")
    lines.append("vat=23%\t23\t\t1")
    
    # === RMS ZEST ===
    lines.append("")
    lines.append("[RMS ZEST 1]")
    lines.append("ty=R\t0")
    lines.append("na=robocizna\t0\t")
    lines.append("id=999\t1\t")
    lines.append("jm=r-g\t149")
    lines.append("ce=0\t\t\t\t\t0\t\t")
    lines.append("cw=0\tPLN\t0")
    lines.append("wa=0")
    lines.append("il=0")
    
    # === DZIALY I POZYCJE ===
    pos_id = 1
    pos_num = 0
    
    for dzial in DZIALY:
        # Element (dzial)
        lines.append("")
        lines.append("[ELEMENT 1]")
        lines.append(f"na={dzial['nazwa']} ")
        lines.append("wa=0")
        lines.append("kn=0\t0\t0")
        lines.append("wn=0\t0\t0")
        lines.append(f"id={pos_id}")
        lines.append(f"nu={dzial['numer']}")
        
        lines.append("")
        lines.append("[PODSUMOWANIE]")
        lines.append("wa=")
        lines.append("kb=0\t0\t0\t0\t0\t0\t0\t")
        lines.append("na=0\t0\t0\t0\t0\t0\t0\t0\tKp\tKoszty posrednie\t65% (R+S)")
        lines.append("na=0\t0\t0\t0\t0\t0\t0\t0\tZ\tZysk\t12% (R+S+Kp(R+S))")
        lines.append("wc=0\t0\t0\t0\t0\t0\t0\t")
        
        pos_id += 1
        
        # Pozycje
        for basis, desc, unit, qty in dzial['pozycje']:
            pos_num += 1
            prefix, cat_num, pos_num_str = parse_basis(basis)
            catalog = get_catalog_name(basis)
            unit_code = get_unit_code(unit)
            
            lines.append("")
            lines.append("[POZYCJA]")
            lines.append(f"id={pos_id}")
            
            if cat_num and pos_num_str:
                lines.append(f"pd={catalog}\t{prefix}\t{cat_num} {pos_num_str}\t{cat_num}\t{pos_num_str}\t\t1")
                lines.append(f"pd5={catalog}\tKATSRC_KATAL\t{prefix} {cat_num} {pos_num_str}\t")
            else:
                lines.append(f"pd={catalog}\t{prefix}\t{basis}\t\t\t\t1")
                lines.append(f"pd5={catalog}\tKATSRC_KATAL\t{basis}\t")
            
            lines.append("mpn=1211\t<DaneKNR><Nie_wybrano_modyfikacji /></DaneKNR>")
            lines.append(f"na={desc}")
            lines.append("op=0\t1\t0\t0\t0\t0\t0\t0\t0")
            lines.append(f"nu={pos_num}")
            lines.append(f"ob={qty}\t{qty}\t\t1")
            lines.append(f"jm={unit}\t{unit_code}")
            lines.append("kj=0\t0\t0")
            lines.append("cj=0\t\t0\t0\t0")
            lines.append("cjw=\t\t0\t")
            lines.append("kjw=\t\t\t0\t0\t0")
            lines.append("wn=0\t0\t0")
            lines.append("wcn=1\t1\t1\t1\t1\t1\t1\t1")
            
            # Podsumowanie pozycji
            lines.append("")
            lines.append("[PODSUMOWANIE]")
            lines.append("wa=")
            lines.append("kb=0\t0\t0\t0\t0\t0\t0\t")
            lines.append("na=0\t0\t0\t0\t0\t0\t0\t0\tKp\tKoszty posrednie\t65% (R+S)")
            lines.append("na=0\t0\t0\t0\t0\t0\t0\t0\tZ\tZysk\t12% (R+S+Kp(R+S))")
            lines.append("wc=0\t0\t0\t0\t0\t0\t0\t")
            lines.append("pr=2")
            lines.append("kbj=0\t0\t0\t0\t0\t0\t0\t")
            lines.append("naj=0\t0\t0\t0\t0\t0\t0\t0\tKp\tKoszty posrednie\t65% (R+S)")
            lines.append("naj=0\t0\t0\t0\t0\t0\t0\t0\tZ\tZysk\t12% (R+S+Kp(R+S))")
            lines.append("wcj=0\t0\t0\t0\t0\t0\t0\t")
            
            # Obmiar
            lines.append("")
            lines.append("[OBMIAR NEX]")
            lines.append("id=0")
            lines.append(f"ob={qty}")
            lines.append(f"jm={unit}\t{unit_code}")
            lines.append("pm=-1")
            lines.append(f"wo=0\t{qty}\t{qty}\t\t\t\t0")
            
            # Przedmiar
            lines.append("")
            lines.append("[PRZEDMIAR]")
            lines.append(f"wo={qty}\t1\t{qty}\t\t\t\t\t\t\t")
            
            # RMS
            lines.append("")
            lines.append("[RMS 1]")
            lines.append(f"id={pos_id + 1}")
            lines.append("nz=0\t0\t0\t")
            lines.append("np=0\t0\t0")
            lines.append("wa=0")
            lines.append("wb=0")
            lines.append("il=0")
            lines.append("uw=")
            lines.append("kj=0")
            lines.append("ij=0\t0")
            
            pos_id += 2
    
    return '\n'.join(lines)


if __name__ == "__main__":
    content = generate_ath()
    
    output_path = r"C:\Users\Gabriel\Downloads\kosztorys_brzeg_sanitariaty.ath"
    with open(output_path, 'w', encoding='cp1250', errors='replace') as f:
        f.write(content)
    
    total = sum(len(d['pozycje']) for d in DZIALY)
    print(f"Zapisano: {output_path}")
    print(f"Dzialow: {len(DZIALY)}")
    print(f"Pozycji: {total}")
    print(f"Rozmiar: {len(content)} znakow")
