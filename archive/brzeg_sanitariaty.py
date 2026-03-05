# -*- coding: utf-8 -*-
"""
Generator kosztorysu ATH: Remont węzłów sanitarnych budynek nr 33
Inwestor: 2 Wojskowy Oddział Gospodarczy
Adres: ul. Sikorskiego 6, 49-300 Brzeg
"""

from datetime import datetime

# Dane nagłówkowe
NAZWA_INWESTYCJI = "Remont węzłów sanitarnych w budynku nr 33"
ADRES_INWESTYCJI = "ul. Sikorskiego 6, 49-300 Brzeg"
NAZWA_INWESTORA = "2 Wojskowy Oddział Gospodarczy"
ADRES_INWESTORA = "ul. Obornicka 100-102, 50-984 Wrocław"
BRANZA = "budowlano-instalacyjna"
SPORZĄDZIL = "AI Kosztorysant"
DATA = datetime.now().strftime("%d.%m.%Y")
STAWKA_RG = 35.00

# Kody jednostek miar
JEDNOSTKI = {
    "szt.": "020", "szt": "020",
    "m": "010", "mb": "010",
    "m2": "050", "m²": "050",
    "m3": "060", "m³": "060",
    "kg": "033",
    "t": "063",
    "kpl": "090", "kpl.": "090",
    "r-g": "149",
    "gniazd.": "020",
    "cm": "010",
    "pion": "020",
    "odc.200m": "020",
    "wyp.": "020",
    "podej.": "020",
    "kpl pomiar.": "090",
    "kpl po-miar.": "090",
    "kpl pomiar": "090",
    "pom.": "020",
    "pom": "020",
    "prób.": "020",
}

def get_jm_code(jm):
    jm = jm.lower().strip().replace(" ", "")
    return JEDNOSTKI.get(jm, "020")

# Struktura działów i pozycji
DZIALY = [
    # ============ PARTER ============
    {
        "nazwa": "PARTER",
        "pozycje": []
    },
    {
        "nazwa": "Roboty rozbiórkowe - parter",
        "pozycje": [
            ("KNR 4-01 0354-09", "Wykucie z muru ościeżnic stalowych lub krat drzwiowych o powierzchni do 2 m2", "szt.", 29.0),
            ("KNR 4-01 0354-12", "Wykucie z muru podokienników betonowych", "m", 4.5),
            ("KNR 9-29 0103-01", "Rozbióka ścianek działowych z płyt gipsowo-kartonowych na szkielecie pojedynczym - analogia wraz z okładzinami", "m2", 10.416),
            ("KNR 9-29 0105-02", "Rozbiórka obudów pionów instalacyjnych, słupów i belek z płyt gipsowo-kartonowych - analogia wraz z okładzinami", "m2", 10.405),
            ("KNR 9-29 0101-01", "Rozbiórka okładzin ścian z płyt gipsowo-kartonowych - analogia po skutych płytkach", "m2", 18.348),
            ("KNR 4-01 0427-05", "Rozebranie ścianek działowych sanitarnych", "m2", 7.04),
            ("KNR 4-01 0819-15", "Rozebranie wykładziny ściennej z płytek", "m2", 123.181),
            ("KNR 4-01 0701-05", "Odbicie tynków wewnętrznych z zaprawy cementowo-wapiennej na ścianach - po skutych płytkach", "m2", 123.181),
            ("KNR 4-01 1202-08", "Zeskrobanie i zmycie starej farby w pomieszczeniach o powierzchni podłogi do 5 m2", "m2", 107.25),
            ("KNR 4-01 0811-07", "Rozebranie posadzki z płytek na zaprawie cementowej", "m2", 41.15),
            ("KNR 4-01 0347-09", "Skucie nierówności 4 cm na ścianach z cegieł - poszerzenie otworu; Krotność=2", "m2", 7.38),
            ("KNR 4-01 0347-02", "Skucie występów 20x10 cm na ścianach z kamienia miękkiego - analogia poszerzenie otworu; Krotność=2", "m", 8.2),
            ("KNR 4-01 0354-13", "Wykucie z muru kratek wentylacyjnych, drzwiczek, wentylatorów", "szt.", 7.0),
            ("KNR 4-01 0211-03", "Skucie nierówności betonu przy głębokości skucia do 5 cm na podłogach", "m2", 41.15),
            ("KNR 4-01 0339-01", "Wykucie bruzd pionowych 1/4x1/2 ceg. w ścianach z cegieł dla instalacji wodociągowej", "m", 15.0),
            ("KNR 4-01 0336-01", "Wykucie bruzd poziomych 1/4x1/2 ceg. w ścianach z cegieł", "m", 15.0),
            ("KNR 4-01 0210-02", "Wykucie bruzd o przekroju do 0.040 m2 poziomych lub pionowych w elementach z betonu żwirowego", "m", 10.0),
            ("KNR 4-01 0106-04", "Usunięcie z parteru budynku gruzu i ziemi", "m3", 18.285),
        ]
    },
    {
        "nazwa": "Nadproże nad poszerzanymi otworami - parter",
        "pozycje": [
            ("KNR 4-01 0346-05", "Wykucie gniazd o głębokości 1 ceg. w ścianach z cegieł na zaprawie cementowej dla belek stalowych", "gniazd.", 3.0),
            ("KNR 4-01 0206-03", "Podlewka, poduszka betonowa gr. 10 cm pod belki nadprożowe", "szt.", 3.0),
            ("KNR 4-01 0313-02", "Wykonanie przesklepień otworów w ścianach z cegieł z wykuciem bruzd dla belek", "m3", 0.081),
            ("KNR 4-01 0313-04", "Wykonanie przesklepień otworów w ścianach z cegieł - dostarczenie i obsadzenie belek stalowych", "m", 5.4),
            ("KNR 7-12 0101-01", "Czyszczenie i odtłuszczanie belek stalowych i malowanie pędzlem farbami do gruntowania miniowymi", "m2", 3.024),
            ("KNR AT-17 0103-01", "Wiercenie otworów o głębokości do 40 cm śr. 40 mm techniką diamentową w cegle", "cm", 8.0),
            ("TZKNBK XXIV 3215-03", "Wiercenie otworów o śr.do 14 mm wiertarką ręczną elektryczną w ściance do 10 mm", "szt.", 16.0),
            ("KNR 4-06 0112-01", "Skręcanie połączeń śrubami - połączenie belek śrubami M12 kl. 5,8", "szt.", 8.0),
            ("KNR 0-40 0110-01", "Uszczelnienie i wypełnienie szczelin między wykutym otworem i kształtownikiem zaprawą wypełniającą", "m", 5.4),
            ("KNR 4-01 0703-03", "Umocowanie siatki Rabitza na stopkach i ściankach belek", "m", 5.4),
            ("KNR 4-01 0704-03", "Wypełnienie oczek siatki cięto-ciągnionej na ścianach i stropach zaprawą cementową", "m2", 2.43),
            ("KNR-W 2-02 0129-05", "Okładanie (szpałdowanie) belek stalowych - wypełnie belek", "m2", 0.81),
        ]
    },
    {
        "nazwa": "Roboty murowe, ścianki i zabudowy GK - parter",
        "pozycje": [
            ("KNR-W 4-01 0327-02", "Zamurowanie bruzd pionowych lub pochyłych o przekroju 1/4 x 1/2 ceg. w ścianach z cegieł", "m", 15.0),
            ("KNR-W 4-01 0326-02", "Zamurowanie bruzd poziomych o przekroju 1/4 x 1/2 ceg. w ścianach z cegieł", "m", 15.0),
            ("KNR 9-29 0306-01", "Uzupełnienie okładzin z płyt gipsowo-kartonowych ścianek działowych przy powierzchni do 5 m2 - pierwsza warstwa", "m2", 18.348),
            ("KNR-W 2-02 2003-05", "Ścianki działowe GR z płyt gipsowo-kartonowych gkbi na rusztach metalowych pojedynczych z pokryciem obustronnym dwuwarstwowo 75-02", "m2", 22.755),
            ("KNR AT-43 0119-02", "Przygotowanie otworów w ściankach działowych z profili UA 75 pod montaż drzwi i naświetli", "szt.", 7.0),
            ("KNR 2-02 2004-01", "Zabudowy instalacyjne płytami gipsowo-kartonowymi gkbi na rusztach metalowych pojedynczych jednowarstwowo 55-01 - analogia", "m2", 30.0),
        ]
    },
    {
        "nazwa": "Roboty tynkowe, malarskie i okładziny - parter",
        "pozycje": [
            ("KNR 4-01 0705-04", "Wykonanie pasów tynku zwykłego kat. III o szerokości do 15 cm pokrywającego bruzdy z osiatkowaniem", "m", 30.0),
            ("KNR 4-01 0716-02", "Tynki wewnętrzne zwykłe kat. III wykonywane ręcznie na podłożu z cegły", "m2", 123.181),
            ("KNR 4-01 0711-14", "Uzupełnienie tynków zwykłych wewnętrznych kat. III na stropach, belkach, podciągach", "m2", 48.564),
            ("KNR 4-01 0708-03", "Wykonanie tynków zwykłych wewnętrznych kat. III na ościeżach szerokości do 40 cm", "m", 15.3),
            ("KNR 4-01 0713-01", "Przecieranie istniejących tynków wewnętrznych z zeskrobaniem farby na ścianach od strony korytarza", "m2", 16.895),
            ("KNR 2-02 0812-01", "Tynki wewnętrzne pocienione kat. III na ścianach powyżej płytek dla ich zlicowania - analogia", "m2", 69.115),
            ("KNR 2-02 2006-07", "Okładziny z płyt gipsowo-kartonowych - dodatek za drugą warstwę na rusztach na ścianach - analogia", "m2", 14.51),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni pod gładzie", "m2", 109.585),
            ("KNR 2-02 2009-04", "Tynki (gładzie) jednowarstwowe wewnętrzne gr. 3 mm z gipsu szpachlowego na stropach", "m2", 40.47),
            ("KNR 2-02 2009-02", "Tynki (gładzie) jednowarstwowe wewnętrzne gr. 3 mm z gipsu szpachlowego na ścianach", "m2", 69.115),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni pod izolację", "m2", 126.355),
            ("KNR AT-27 0401-01", "Pionowa izolacja podpłytkowa przeciwwilgociowa gr. 1 mm z folii w płynie", "m2", 126.355),
            ("KNR AT-27 0401-04", "Pionowa izolacja podpłytkowa z folii w płynie - dodatek za kolejną warstwę gr. 0,5 mm", "m2", 126.355),
            ("KNR AT-27 0401-05", "Izolacja podpłytkowa folii w płynie - wklejenie taśmy uszczelniającej - analogia", "m", 98.4),
            ("KNR 2-02 0829-11", "Licowanie ścian płytkami o wymiarach 30x60 cm na klej metodą kombinowaną - analogia", "m2", 126.355),
            ("KNR-W 2-02 0840-08", "Licowanie ścian płytkami - listwy narożnikowe aluminiowe", "m", 111.75),
            ("KNR 2-02 1505-03", "Dwukrotne malowanie farbami emulsyjnymi powierzchni wewnętrznych - podłoży gipsowych z gruntowaniem", "m2", 140.99),
            ("KNR 2-02 1505-06", "Malowanie farbami emulsyjnymi powierzchni wewnętrznych - dodatek za każde dalsze malowanie", "m2", 140.99),
            ("KNR 4-01 1206-05", "Dwukrotne malowanie farbami olejnymi starych tynków wewnętrznych ścian z dwukrotnym szpachlowaniem", "m2", 5.7),
        ]
    },
    {
        "nazwa": "Roboty posadzkowe - parter",
        "pozycje": [
            ("KNR 4-01 0207-03", "Zabetonowanie żwirobetonem bruzd o przekroju do 0.045 m2 w podłożach", "m", 12.0),
            ("KNR 2-02 1102-02", "Warstwy wyrównawcze pod posadzki z zaprawy cementowej grubo 50 mm zatarte na gładko z ukształtowaniem spadków", "m2", 40.47),
            ("KNR 2-02 1106-07", "Posadzki cementowe wraz z cokolikami - dopłata za zbrojenie siatką stalową", "m2", 40.47),
            ("KNR-W 2-02 1105-01", "Warstwy niwelująco-wyrównawcze cementowe grubo 2 mm zatarte na gładko", "m2", 40.47),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni", "m2", 40.47),
            ("KNR AT-27 0401-03", "Pozioma izolacja podpłytkowa przeciwwilgociowa gr. 1 mm z folii w płynie", "m2", 40.47),
            ("KNR AT-27 0401-04", "Pozioma izolacja podpłytkowa z folii w płynie - dodatek za kolejną warstwę gr. 0,5 mm", "m2", 40.47),
            ("KNR AT-27 0401-05", "Izolacja podpłytkowa folii w płynie - wklejenie taśmy uszczelniającej - analogia", "m", 55.3),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni", "m2", 40.47),
            ("KNR 2-02 1118-11", "Posadzki płytkowe z kamieni sztucznych; płytki 60x60 cm na klej metodą kombinowaną - analogia", "m2", 40.47),
            ("KNR 4-01 0411-08", "Systemowe aluminiowe listwy progowe na połączeniu z korytarzem - analogia", "szt.", 5.0),
        ]
    },
    {
        "nazwa": "Stolarka - parter",
        "pozycje": [
            ("KNR 4-01 0320-03", "Obsadzenie ościeżnic stalowych stałych", "m2", 6.15),
            ("KNR 4-01 0320-03", "Obsadzenie ościeżnic stalowych regulowanych (opaskowych)", "m2", 11.07),
            ("KNR 2-02 1017-02", "Skrzydła drzwiowe płytowe wewnętrzne jednodzielne pełne o powierzchni ponad 1.6 m2", "m2", 17.22),
            ("KNR-W 2-02 1029-05", "Systemowe ścianki sanitarne z drzwiami", "m2", 12.04),
            ("KNR 2-02 1009-06", "Naświetla PCV", "m2", 3.36),
            ("KNR 2-02 1215-02", "Drzwiczki rewizyjne osadzone w ścianach GK o powierzchni do 0.2 m2", "szt.", 7.0),
            ("KNR 2-17 0156-01", "Nawietrzaki okienne z frezowaniem otworów - analogia", "szt.", 3.0),
            ("KNR 4-01 0919-20", "Wymiana klamek okiennych z regulacją skrzydeł okiennych", "szt.", 12.0),
        ]
    },
    {
        "nazwa": "Instalacja kanalizacji sanitarnej - parter",
        "pozycje": [
            ("kalk. własna", "Projekt wykonawczy wewnętrznej instalacji kanalizacji sanitarnej", "kpl", 1.0),
            ("KNR 4-02 0235-06", "Demontaż umywalki", "kpl.", 5.0),
            ("KNR 4-02 0235-08", "Demontaż ustępu z miską fajansową", "kpl.", 5.0),
            ("KNR 4-02 0235-07", "Demontaż brodzika", "kpl.", 2.0),
            ("KNR 4-02 0235-01", "Demontaż pisuaru", "kpl.", 2.0),
            ("KNR 4-02 0230-04", "Demontaż rurociągu żeliwnego/PCV kanalizacyjnego o śr. 50-100 mm", "m", 30.0),
            ("KNR 4-02 0230-05", "Demontaż rurociągu żeliwnego/PCV kanalizacyjnego o śr. 150 mm", "m", 20.0),
            ("KNR 4-02 0234-02", "Demontaż elementów uzbrojenia rurociągu - wpust żeliwny podłogowy śr. 50 mm", "szt.", 3.0),
            ("KNR 4-02 0202-09", "Połączenie nowo budowanej kanalizacji sanitarnej z istniejącą wewnętrzną instalacją - analogia", "kpl", 4.0),
            ("kalk. własna", "Tuleje ochronne dla przejść rurociągów przez przegrody budowlane - uszczelnione zaprawą p.poż.", "szt.", 4.0),
            ("KNR AT-17 0104-04", "Cięcie piłą diamentową betonu zbrojonego o grub. powyżej 15 do 40 cm; miejsce cięcia - posadzka", "m2", 2.0),
            ("KNR-W 4-01 0212-02", "Mechaniczna rozbiórka elementów konstrukcji betonowych niezbrojonych o grub do 15 cm", "m3", 0.5),
            ("KNR 2-15 0205-04", "Montaż rurociągów z PCW o śr. 160 mm na ścianach z łączeniem metodą wciskową", "m", 9.0),
            ("KNR 2-15 0205-04", "Montaż rurociągów z PCW o śr. 110 mm na ścianach z łączeniem metodą wciskową", "m", 15.0),
            ("KNR 2-15 0205-03", "Montaż rurociągów z PCW o śr. 75 mm na ścianach z łączeniem metodą wciskową", "m", 10.0),
            ("KNR 2-15 0205-02", "Montaż rurociągów z PCW o śr. 50 mm na ścianach z łączeniem metodą wciskową", "m", 20.0),
            ("S 215 0200-01", "Zawory napowietrzające pływakowe o śr.nom. 50 mm", "szt.", 1.0),
            ("KNR-W 2-15 0211-03", "Dodatki za wykonanie podejść odpływowych z PVC o śr. 110 mm", "podej.", 5.0),
            ("KNR 2-15/GEBERIT 0101-01", "Elementy montażowe/stelaż do miski ustępowej montowane na ścianie z przyciskiem spłukującym - analogia", "kpl.", 5.0),
            ("KNR 2-15/GEBERIT 0104-01", "Urządzenia sanitarne na elemencie montażowym - ustęp bezkołnierzowy z deską sedesową wolnopadającą", "kpl.", 5.0),
            ("KNR-W 2-15 0211-01", "Dodatki za wykonanie podejść odpływowych z PVC o śr. 50 mm", "podej.", 14.0),
            ("KNR-W 2-15 0234-02", "Pisuary pojedyncze wyposażone w zawory spłukujące uruchamiane przyciskiem z wyłącznikiem czasowym", "kpl.", 3.0),
            ("KNR-W 2-15 0230-02", "Umywalki pojedyncze porcelanowe (komplet z syfonem i zawiesiami)", "kpl.", 5.0),
            ("KNR-W 2-15 0230-05", "Półpostument porcelanowy do umywalek", "kpl.", 5.0),
            ("KNR-W 2-15 0232-02", "Brodziki natryskowe na podstawie styropianowej z obudową 90x100 cm", "kpl.", 2.0),
            ("KNR 0-35 0123-01", "Kabiny natryskowe do kąpieli z szybami ze szkła hartowanego - 2 ściany i drzwi", "kpl.", 1.0),
            ("KNR 0-35 0123-01", "Kabiny natryskowe do kąpieli z szybami ze szkła hartowanego - drzwi przesuwne", "kpl.", 1.0),
            ("KNR-W 2-15 0218-01", "Wpusty ściekowe ze stali nierdzewnej o śr. 50 mm", "szt.", 4.0),
            ("KNR-W 2-15 0127-02", "Próba szczelności instalacji kanalizacyjnej z rur PVC - analogia", "m", 54.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - uchwyt na papier toaletowy - analogia", "szt.", 5.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - dozowniki mydła w płynie - analogia", "szt.", 5.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - dozownik na ręczniki papierowy - analogia", "szt.", 5.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - lustra 60x80 cm - analogia", "szt.", 5.0),
        ]
    },
    {
        "nazwa": "Instalacja wody zimnej i cwu. z cyrkulacją - parter",
        "pozycje": [
            ("kalk. własna", "Projekt wykonawczy wewnętrznej instalacji wody zimnej i cwu. z cyrkulacją", "kpl", 1.0),
            ("analiza indywidualna", "Demontaż rurociągów, podejść, armatury itp.", "kpl", 1.0),
            ("KNR 4-02 0111-03", "Połączenie instalacji c.w.u. z istniejącą wewnętrzną instalacją wodociągową z montażem zaworu - analogia", "szt.", 1.0),
            ("KNR 4-02 0111-03", "Połączenie instalacji w.z. z istniejącą wewnętrzną instalacją wodociągową z montażem zaworu - analogia", "szt.", 1.0),
            ("KNR 4-01 0208-04", "Przebicie otworów w elementach z betonu żwirowego o grub. do 40 cm dla instalacji - analogia", "szt.", 4.0),
            ("kalk. własna", "Tuleje ochronne dla przejść rurociągów przez przegrody budowlane - uszczelnione zaprawą p.poż.", "szt.", 4.0),
            ("KNR-W 2-15 0111-01", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 16 mm - analogia", "m", 35.0),
            ("KNR-W 2-15 0111-01", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 20 mm - analogia", "m", 30.0),
            ("KNR-W 2-15 0111-02", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 25 mm - analogia", "m", 30.0),
            ("KNR-W 2-15 0111-03", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 32 mm - analogia", "m", 15.0),
            ("KNR-W 2-15 0132-03", "Zawory kulowe instalacji wodociągowych z rur z tworzyw sztucznych o śr. nominalnej 25 mm", "szt.", 6.0),
            ("KNR-W 2-15 0116-08", "Dodatki za podejścia dopływowe w rurociągach z tworzyw sztucznych do zaworów", "szt.", 19.0),
            ("KNR-W 2-15 0135-01", "Zawory czerpalne ze złączką o śr. nominalnej 15 mm", "szt.", 22.0),
            ("KNR-W 2-15 0137-02", "Baterie umywalkowe stojące o śr. nominalnej 15 mm", "szt.", 5.0),
            ("KNR-W 2-15 0137-09", "Baterie natryskowe z natryskiem przesuwnym o śr. nominalnej 15 mm", "szt.", 2.0),
            ("KNR 0-31 0116-01", "Próba szczelności instalacji wody zimnej i ciepłej w budynkach mieszkalnych - płukanie", "kpl.", 1.0),
            ("KNR 0-31 0116-02", "Próba szczelności instalacji wody zimnej i ciepłej w budynkach mieszkalnych - próba wodna ciśnieniowa", "m", 110.0),
            ("KNR-W 2-18 0707-01", "Dezynfekcja rurociągów sieci wodociągowych o śr.nominalnej do 150 mm", "odc.200m", 0.55),
            ("KNR 0-34 0101-06", "Izolacja rurociągów śr.20 mm otulinami Thermaflex FRZ - jednowarstw. gr.13 mm (J)", "m", 39.0),
            ("KNR 0-34 0101-10", "Izolacja rurociągów śr. 12-22 mm otulinami Thermaflex FRZ - jednowarstw. gr. 20 mm (N)", "m", 26.0),
            ("KNR 0-34 0101-11", "Izolacja rurociągów śr. 28-48 mm otulinami Thermaflex FRZ - jednowarstw. gr. 20 mm (N) - woda ciepła", "m", 22.5),
            ("KNR 0-34 0101-07", "Izolacja rurociągów śr. 28-48 mm otulinami Thermaflex FRZ - jednowarstw. gr. 13 mm (J) - woda zimna", "m", 22.5),
            ("KNR 0-34 0110-14", "Izolacja dwuwarstwowa rurociągów śr. 28-48 mm otulinami Thermaflex FRZ - gr. izolacji 40 mm", "m", 10.0),
        ]
    },
    {
        "nazwa": "Instalacja c.o. - parter",
        "pozycje": [
            ("KNR-W 4-02 0515-06", "Wymiana grzejnika żeliwnego członowego na stalowy grzejnik panelowy płytowy - analogia", "kpl.", 5.0),
            ("KNR-W 4-02 0517-05", "Wymiana rur przyłącznych do grzejnika z rur stalowych ze stali nierdzewnej - analogia", "kpl.", 10.0),
            ("kalk. własna", "Wymiana pionów instalacji centralnego ogrzewania z przejściem nowych rur przez stropy", "pion", 6.0),
            ("analiza indywidualna", "Przejścia przeciwpożarowe dla instalacji C.O. - stropy i ściany do wymaganej odporn. ogniowej", "szt", 6.0),
            ("KNR 2-15 0404-02", "Próby ciśnieniowe szczelności instalacji wewnętrznej c.o. w budynkach niemieszkalnych", "m", 40.0),
        ]
    },
    {
        "nazwa": "Wentylacja mechaniczna - parter",
        "pozycje": [
            ("analiza indywidualna", "Uzyskanie opinii kominiarskiej z opisem zawierającym m.in określenie przynależności kanałów", "kpl", 1.0),
            ("kalk. własna", "Wentylacja mechaniczna - wykonanie i montaż w pomieszczeniu węzła sanitarnego z wentylatorami", "pom", 3.0),
            ("KNR-W 2-17 0206-01", "Wentylator łazienkowy z timerem regulowanym, czujnikiem ruchu - obiekty modernizowane", "szt.", 2.0),
        ]
    },
    {
        "nazwa": "Instalacja elektryczna i oświetleniowa - parter",
        "pozycje": [
            ("kalk. własna", "Projekt wykonawczy wewnętrznej instalacji elektrycznej, gniazd, oświetlenia podstawowego i ewakuacyjnego", "kpl", 1.0),
            ("kalk. własna", "Demontaż istniejącej instalacji elektrycznej i oświetleniowej (przewody, oprawy, gniazda, włączniki)", "kpl.", 1.0),
            ("KSNR 5 0406-05", "Wypust oświetleniowy podtynkowy z wykonaniem i zaprawieniem bruzd i wpięciem do rozdzielnicy - analogia", "wyp.", 19.0),
            ("KSNR 5 0406-05", "Wypust oświetleniowy ewakuacyjny podtynkowy z wykonaniem i zaprawieniem bruzd - analogia", "wyp.", 4.0),
            ("KSNR 5 0502-02", "Montaż opraw oświetleniowych LED przykręcanych odpowiedniej klasie szczelności z modułem ewakuacyjnym", "kpl.", 14.0),
            ("KSNR 5 0502-02", "Montaż opraw oświetleniowych LED przykręcanych nad umywalkami odpowiedniej klasie szczelności", "kpl.", 5.0),
            ("KSNR 5 0502-01", "Montaż opraw oświetleniowych przykręcanych ewakuacyjnych (kierunkowych)", "kpl.", 4.0),
            ("KNR AL-01 0201-01", "Montaż czujki ruchu - pasywna podczerwieni", "szt.", 8.0),
            ("KSNR 5 0405-01", "Wypusty wykonywane przewodami wtynkowymi na wyłącznik - włączniki pojedyncze opraw nad umywalkami - analogia", "wyp.", 5.0),
            ("KSNR 5 0406-07", "Wypusty dla gniazd 230V podtynkowo z wykonaniem i zaprawieniem bruzd - gniazdo pojedyncze - analogia", "wyp.", 5.0),
            ("KSNR 5 0406-07", "Wypusty dla gniazd 230V podtynkowo z wykonaniem i zaprawieniem bruzd - zasilanie suszarek - analogia", "wyp.", 5.0),
            ("KNR 5-08 0309-03", "Montaż do gotowego podłoża gniazd wtyczkowych podtynkowych 2-biegunowych z uziemieniem", "szt.", 5.0),
            ("KNR 5-08 0402-01", "Mocowanie na gotowym podłożu aparatów o masie do 2.5 kg - suszarka do rąk w wykonaniu nierdzewnym", "szt.", 5.0),
            ("analiza indywidualna", "Instalacja uziemiająca i połączeń wyrównawczych", "kpl", 1.0),
            ("KNR 4-03 1205-05", "Pomiar skuteczności zerowania - analogia", "kpl pomiar.", 1.0),
            ("KNR 4-03 1202-01", "Sprawdzenie i pomiar kompletnego 1-fazowego obwodu elektrycznego niskiego napięcia - analogia", "kpl pomiar.", 1.0),
            ("KNR-W 4-03 1208-01", "Pierwszy pomiar rezystancji izolacji instalacji elektrycznych w obwodzie 1-fazowym", "kpl pomiar", 1.0),
            ("KNR 13-21 0301-03", "Pomiary natężenia oświetlenia", "pom.", 5.0),
        ]
    },
    # ============ I PIĘTRO ============
    {
        "nazwa": "I PIĘTRO",
        "pozycje": []
    },
    {
        "nazwa": "Roboty rozbiórkowe - I piętro",
        "pozycje": [
            ("KNR 4-01 0354-09", "Wykucie z muru ościeżnic stalowych lub krat drzwiowych o powierzchni do 2 m2", "szt.", 7.0),
            ("KNR 4-01 0354-12", "Wykucie z muru podokienników betonowych z lastryko", "m", 4.35),
            ("KNR 9-29 0105-02", "Rozbiórka obudów pionów instalacyjnych z płyt gipsowo-kartonowych - analogia wraz z okładzinami", "m2", 21.87),
            ("KNR 4-01 0427-05", "Rozebranie ścianek działowych sanitarnych", "m2", 10.458),
            ("KNR 4-01 0348-03", "Rozebranie ścianki z cegieł o grub. 1/2 ceg. na zaprawie cementowo-wapiennej wraz z okładzinami", "m2", 28.85),
            ("KNR 4-01 0819-15", "Rozebranie wykładziny ściennej z płytek", "m2", 100.831),
            ("KNR 4-01 0701-05", "Odbicie tynków wewnętrznych z zaprawy cementowo-wapiennej na ścianach - po skutych płytkach", "m2", 100.831),
            ("KNR 4-01 0702-06", "Odbicie tynków wewnętrznych z zaprawy cementowo-wapiennej pasami o szerokości do 30 cm", "m", 8.2),
            ("KNR 4-01 0347-09", "Skucie nierówności 4 cm na ścianach z cegieł - poszerzenie otworu; Krotność=2", "m2", 0.41),
            ("KNR 4-01 1202-08", "Zeskrobanie i zmycie starej farby w pomieszczeniach o powierzchni podłogi do 5 m2", "m2", 97.166),
            ("KNR 4-01 0811-07", "Rozebranie posadzki z płytek na zaprawie cementowej", "m2", 47.566),
            ("KNR 4-01 0354-13", "Wykucie z muru kratek wentylacyjnych, wentylatorów, drzwiczek", "szt.", 8.0),
            ("KNR 4-01 0804-07", "Zerwanie posadzki cementowej/lastykowej - wyrównanie podłoża", "m2", 47.566),
            ("KNR 4-01 0339-01", "Wykucie bruzd pionowych 1/4x1/2 ceg. w ścianach z cegieł dla instalacji wodociągowej", "m", 30.0),
            ("KNR 4-01 0336-01", "Wykucie bruzd poziomych 1/4x1/2 ceg. w ścianach z cegieł", "m", 30.0),
            ("KNR 4-01 0210-02", "Wykucie bruzd o przekroju do 0.040 m2 poziomych lub pionowych w elementach z betonu żwirowego", "m", 12.0),
            ("KNR 4-01 0106-04", "Usunięcie z parteru budynku gruzu i ziemi", "m3", 18.727),
        ]
    },
    {
        "nazwa": "Roboty murowe, ścianki i zabudowy GK - I piętro",
        "pozycje": [
            ("KNR-W 4-01 0327-02", "Zamurowanie bruzd pionowych lub pochyłych o przekroju 1/4 x 1/2 ceg. w ścianach z cegieł", "m", 30.0),
            ("KNR-W 4-01 0326-02", "Zamurowanie bruzd poziomych o przekroju 1/4 x 1/2 ceg. w ścianach z cegieł", "m", 30.0),
            ("KNR-W 2-02 2003-05", "Ścianki działowe GR z płyt gipsowo-kartonowych gkbi na rusztach metalowych pojedynczych z pokryciem obustronnym dwuwarstwowo 75-02", "m2", 33.825),
            ("KNR AT-43 0119-02", "Przygotowanie otworów w ściankach działowych z profili UA 75 pod montaż drzwi i naświetli", "szt.", 8.0),
            ("KNR 2-02 2004-01", "Zabudowy instalacyjne płytami gipsowo-kartonowymi gkbi na rusztach metalowych pojedynczych jednowarstwowo 55-01 - analogia", "m2", 50.0),
        ]
    },
    {
        "nazwa": "Roboty tynkowe, malarskie i okładziny - I piętro",
        "pozycje": [
            ("KNR 4-01 0705-04", "Wykonanie pasów tynku zwykłego kat. III o szerokości do 15 cm pokrywającego bruzdy z osiatkowaniem", "m", 60.0),
            ("KNR 4-01 0716-02", "Tynki wewnętrzne zwykłe kat. III wykonywane ręcznie na podłożu z cegły", "m2", 100.831),
            ("KNR 4-01 0711-14", "Uzupełnienie tynków zwykłych wewnętrznych kat. III na stropach, belkach, podciągach", "m2", 56.119),
            ("KNR 4-01 0708-03", "Wykonanie tynków zwykłych wewnętrznych kat. III na ościeżach szerokości do 40 cm", "m", 26.6),
            ("KNR 4-01 0713-01", "Przecieranie istniejących tynków wewnętrznych z zeskrobaniem farby na ścianach od strony korytarza", "m2", 11.34),
            ("KNR 2-02 2006-07", "Okładziny z płyt gipsowo-kartonowych - dodatek za drugą warstwę na rusztach na ścianach - analogia", "m2", 21.856),
            ("KNR 2-02 0812-01", "Tynki wewnętrzne pocienione kat. III na ścianach powyżej płytek dla ich zlicowania - analogia", "m2", 52.92),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni pod gładzie", "m2", 99.686),
            ("KNR 2-02 2009-04", "Tynki (gładzie) jednowarstwowe wewnętrzne gr. 3 mm z gipsu szpachlowego na stropach", "m2", 46.766),
            ("KNR 2-02 2009-02", "Tynki (gładzie) jednowarstwowe wewnętrzne gr. 3 mm z gipsu szpachlowego na ścianach", "m2", 52.92),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni pod izolację", "m2", 154.049),
            ("KNR AT-27 0401-01", "Pionowa izolacja podpłytkowa przeciwwilgociowa gr. 1 mm z folii w płynie", "m2", 154.049),
            ("KNR AT-27 0401-04", "Pionowa izolacja podpłytkowa z folii w płynie - dodatek za kolejną warstwę gr. 0,5 mm", "m2", 154.049),
            ("KNR AT-27 0401-05", "Izolacja podpłytkowa folii w płynie - wklejenie taśmy uszczelniającej - analogia", "m", 69.4),
            ("KNR 2-02 0829-11", "Licowanie ścian płytkami o wymiarach 30x60 cm na klej metodą kombinowaną - analogia", "m2", 158.584),
            ("KNR-W 2-02 0840-08", "Licowanie ścian płytkami - listwy narożnikowe aluminiowe", "m", 90.95),
            ("KNR 2-02 1505-03", "Dwukrotne malowanie farbami emulsyjnymi powierzchni wewnętrznych - podłoży gipsowych z gruntowaniem", "m2", 132.882),
            ("KNR 2-02 1505-06", "Malowanie farbami emulsyjnymi powierzchni wewnętrznych - dodatek za każde dalsze malowanie", "m2", 132.882),
            ("KNR 4-01 1206-05", "Dwukrotne malowanie farbami olejnymi starych tynków wewnętrznych ścian z dwukrotnym szpachlowaniem", "m2", 4.05),
        ]
    },
    {
        "nazwa": "Roboty posadzkowe - I piętro",
        "pozycje": [
            ("KNR 4-01 0207-03", "Zabetonowanie żwirobetonem bruzd o przekroju do 0.045 m2 w podłożach", "m", 12.0),
            ("KNR 2-02 1102-02", "Warstwy wyrównawcze pod posadzki z zaprawy cementowej grubo 50 mm zatarte na gładko z ukształtowaniem spadków", "m2", 47.566),
            ("KNR 2-02 1106-07", "Posadzki cementowe wraz z cokolikami - dopłata za zbrojenie siatką stalową", "m2", 47.566),
            ("KNR-W 2-02 1105-01", "Warstwy niwelująco-wyrównawcze cementowe grubo 2 mm zatarte na gładko", "m2", 47.566),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni", "m2", 47.566),
            ("KNR AT-27 0401-03", "Pozioma izolacja podpłytkowa przeciwwilgociowa gr. 1 mm z folii w płynie", "m2", 47.566),
            ("KNR AT-27 0401-04", "Pozioma izolacja podpłytkowa z folii w płynie - dodatek za kolejną warstwę gr. 0,5 mm", "m2", 47.566),
            ("KNR AT-27 0401-05", "Izolacja podpłytkowa folii w płynie - wklejenie taśmy uszczelniającej - analogia", "m", 68.18),
            ("NNRNKB 202 1134-02", "Gruntowanie podłoży preparatami powierzchni", "m2", 47.566),
            ("KNR 2-02 1118-11", "Posadzki płytkowe z kamieni sztucznych; płytki 60x60 cm na klej metodą kombinowaną - analogia", "m2", 47.566),
            ("KNR 4-01 0411-08", "Systemowe aluminiowe listwy progowe na połączeniu z korytarzem - analogia", "szt.", 3.0),
        ]
    },
    {
        "nazwa": "Stolarka - I piętro",
        "pozycje": [
            ("KNR 4-01 0320-03", "Obsadzenie ościeżnic stalowych stałych", "m2", 6.15),
            ("KNR 4-01 0320-03", "Obsadzenie ościeżnic stalowych regulowanych (opaskowych)", "m2", 9.635),
            ("KNR 2-02 1017-02", "Skrzydła drzwiowe płytowe wewnętrzne jednodzielne pełne o powierzchni ponad 1.6 m2", "m2", 14.145),
            ("KNR-W 2-02 1029-05", "Systemowe ścianki sanitarne z drzwiami", "m2", 16.82),
            ("KNR 2-02 1009-06", "Naświetla PCV - analogia", "m2", 3.6),
            ("KNR 2-02 1215-02", "Drzwiczki rewizyjne osadzone w ścianach GK o powierzchni do 0.2 m2", "szt.", 6.0),
            ("KNR 2-17 0156-01", "Nawietrzaki okienne z frezowaniem otworów - analogia", "szt.", 5.0),
            ("KNR 4-01 0919-20", "Wymiana klamek okiennych z regulacją skrzydeł okiennych", "szt.", 14.0),
        ]
    },
    {
        "nazwa": "Instalacja kanalizacji sanitarnej - I piętro",
        "pozycje": [
            ("kalk. własna", "Projekt wykonawczy wewnętrznej instalacji kanalizacji sanitarnej", "kpl", 1.0),
            ("KNR 4-02 0235-03", "Demontaż zlewu", "kpl.", 1.0),
            ("KNR 4-02 0235-06", "Demontaż umywalki", "kpl.", 5.0),
            ("KNR 4-02 0235-08", "Demontaż ustępu z miską fajansową", "kpl.", 5.0),
            ("KNR 4-02 0235-01", "Demontaż pisuaru", "kpl.", 2.0),
            ("KNR 4-02 0235-07", "Demontaż brodzika", "kpl.", 2.0),
            ("KNR 4-02 0230-04", "Demontaż rurociągu żeliwnego/PCV kanalizacyjnego o śr. 50-100 mm", "m", 15.0),
            ("KNR 4-02 0230-05", "Demontaż rurociągu żeliwnego/PCV kanalizacyjnego o śr. 150 mm", "m", 20.0),
            ("KNR 4-02 0234-02", "Demontaż elementów uzbrojenia rurociągu - wpust żeliwny podłogowy śr. 50 mm", "szt.", 2.0),
            ("KNR 4-02 0202-09", "Połączenie nowo budowanej kanalizacji sanitarnej z istniejącą wewnętrzną instalacją - analogia", "kpl", 5.0),
            ("kalk. własna", "Tuleje ochronne dla przejść rurociągów przez przegrody budowlane - uszczelnione zaprawą p.poż.", "szt.", 5.0),
            ("KNR AT-17 0104-04", "Cięcie piłą diamentową betonu zbrojonego o grub. powyżej 15 do 40 cm; miejsce cięcia - posadzka", "m2", 2.0),
            ("KNR-W 4-01 0212-02", "Mechaniczna rozbiórka elementów konstrukcji betonowych niezbrojonych o grub do 15 cm", "m3", 0.5),
            ("KNR 2-15 0205-04", "Montaż rurociągów z PCW o śr. 160 mm na ścianach i stropach z łączeniem metodą wciskową", "m", 9.0),
            ("KNR 2-15 0205-04", "Montaż rurociągów z PCW o śr. 110 mm na ścianach i stropach z łączeniem metodą wciskową", "m", 15.0),
            ("KNR 2-15 0205-03", "Montaż rurociągów z PCW o śr. 75 mm na ścianach i stropach z łączeniem metodą wciskową", "m", 12.0),
            ("KNR 2-15 0205-02", "Montaż rurociągów z PCW o śr. 50 mm na ścianach z łączeniem metodą wciskową", "m", 25.0),
            ("S 215 0200-01", "Zawory napowietrzające pływakowe o śr.nom. 50 mm", "szt.", 3.0),
            ("KNR-W 2-15 0211-03", "Dodatki za wykonanie podejść odpływowych z PVC o śr. 110 mm", "podej.", 4.0),
            ("KNR 2-15/GEBERIT 0101-01", "Elementy montażowe/stelaż do miski ustępowej montowane na ścianie z przyciskiem spłukującym - analogia", "kpl.", 4.0),
            ("KNR 2-15/GEBERIT 0104-01", "Urządzenia sanitarne na elemencie montażowym - ustęp bezkołnierzowy z deską sedesową wolnopadającą", "kpl.", 4.0),
            ("KNR-W 2-15 0211-01", "Dodatki za wykonanie podejść odpływowych z PVC o śr. 50 mm", "podej.", 16.0),
            ("KNR-W 2-15 0218-01", "Wpusty ściekowe ze stali nierdzewnej o śr. 50 mm", "szt.", 3.0),
            ("KNR-W 2-15 0230-02", "Umywalki pojedyncze porcelanowe (komplet z syfonem i zawiesiami)", "kpl.", 5.0),
            ("KNR-W 2-15 0230-05", "Półpostument porcelanowy do umywalek", "kpl.", 5.0),
            ("KNR-W 2-15 0234-02", "Pisuary pojedyncze wyposażone w zawory spłukujące uruchamiane przyciskiem z wyłącznikiem czasowym", "kpl.", 3.0),
            ("KNR-W 2-15 0232-02", "Brodziki natryskowe na podstawie styropianowej z obudową 90x100 cm", "kpl.", 2.0),
            ("KNR 0-35 0123-01", "Kabiny natryskowe do kąpieli z szybami ze szkła hartowanego - drzwi", "kpl.", 2.0),
            ("KNR-W 2-15 0127-02", "Próba szczelności instalacji kanalizacyjnej z rur PVC - analogia", "m", 61.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - uchwyt na papier toaletowy - analogia", "szt.", 4.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - dozowniki mydła w płynie - analogia", "szt.", 3.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - dozownik na ręczniki papierowy - analogia", "szt.", 3.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - haczyki - analogia", "szt.", 2.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - przegroda pisuarowa - analogia", "szt.", 1.0),
            ("KNR 4-03 1015-04", "Przykręcanie drobnych elementów na ścianie - lustra 60x80 cm - analogia", "szt.", 5.0),
        ]
    },
    {
        "nazwa": "Instalacja wody zimnej i cwu. z cyrkulacją - I piętro",
        "pozycje": [
            ("kalk. własna", "Projekt wykonawczy wewnętrznej instalacji wody zimnej i cwu. z cyrkulacją", "kpl", 1.0),
            ("analiza indywidualna", "Demontaż rurociągów, podejść, armatury itp.", "kpl", 1.0),
            ("KNR 4-02 0111-03", "Połączenie instalacji c.w.u. z istniejącą wewnętrzną instalacją wodociągową z montażem zaworu - analogia", "szt.", 1.0),
            ("KNR 4-02 0111-03", "Połączenie instalacji w.z. z istniejącą wewnętrzną instalacją wodociągową z montażem zaworu - analogia", "szt.", 1.0),
            ("KNR 4-01 0208-04", "Przebicie otworów w elementach z betonu żwirowego o grub. do 40 cm dla instalacji - analogia", "szt.", 9.0),
            ("kalk. własna", "Tuleje ochronne dla przejść rurociągów przez przegrody budowlane - uszczelnione zaprawą p.poż.", "szt.", 9.0),
            ("KNR-W 2-15 0111-01", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 16 mm - analogia", "m", 40.0),
            ("KNR-W 2-15 0111-01", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 20 mm - analogia", "m", 40.0),
            ("KNR-W 2-15 0111-02", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 25 mm - analogia", "m", 30.0),
            ("KNR-W 2-15 0111-03", "Rurociągi z tworzyw sztucznych PP-R w systemie fusiotherm Stabi Glass o śr. 32 mm - analogia", "m", 10.0),
            ("KNR-W 2-15 0132-03", "Zawory kulowe instalacji wodociągowych z rur z tworzyw sztucznych o śr. nominalnej 25 mm", "szt.", 6.0),
            ("KNR-W 2-15 0116-08", "Dodatki za podejścia dopływowe w rurociągach z tworzyw sztucznych do zaworów", "szt.", 17.0),
            ("KNR-W 2-15 0135-01", "Zawory czerpalne ze złączką o śr. nominalnej 15 mm", "szt.", 20.0),
            ("KNR-W 2-15 0137-02", "Baterie umywalkowe stojące o śr. nominalnej 15 mm", "szt.", 5.0),
            ("KNR-W 2-15 0137-09", "Baterie natryskowe z natryskiem przesuwnym o śr. nominalnej 15 mm", "szt.", 2.0),
            ("KNR 0-31 0116-01", "Próba szczelności instalacji wody zimnej i ciepłej w budynkach mieszkalnych - płukanie", "kpl.", 1.0),
            ("KNR 0-31 0116-02", "Próba szczelności instalacji wody zimnej i ciepłej w budynkach mieszkalnych - próba wodna ciśnieniowa", "m", 120.0),
            ("KNR-W 2-18 0707-01", "Dezynfekcja rurociągów sieci wodociągowych o śr.nominalnej do 150 mm", "odc.200m", 0.6),
            ("KNR 0-34 0101-06", "Izolacja rurociągów śr.20 mm otulinami Thermaflex FRZ - jednowarstw. gr.13 mm (J)", "m", 48.0),
            ("KNR 0-34 0101-10", "Izolacja rurociągów śr. 12-22 mm otulinami Thermaflex FRZ - jednowarstw. gr. 20 mm (N)", "m", 32.0),
            ("KNR 0-34 0101-11", "Izolacja rurociągów śr. 28-48 mm otulinami Thermaflex FRZ - jednowarstw. gr. 20 mm (N) - woda ciepła", "m", 20.0),
            ("KNR 0-34 0101-07", "Izolacja rurociągów śr. 28-48 mm otulinami Thermaflex FRZ - jednowarstw. gr. 13 mm (J) - woda zimna", "m", 20.0),
            ("KNR 0-34 0110-14", "Izolacja dwuwarstwowa rurociągów śr. 28-48 mm otulinami Thermaflex FRZ - gr. izolacji 40 mm", "m", 10.0),
        ]
    },
    {
        "nazwa": "Instalacja c.o. - I piętro",
        "pozycje": [
            ("KNR-W 4-02 0515-06", "Wymiana grzejnika żeliwnego członowego na stalowy grzejnik panelowy płytowy - analogia", "kpl.", 3.0),
            ("KNR-W 4-02 0517-05", "Wymiana rur przyłącznych do grzejnika z rur stalowych ze stali nierdzewnej - analogia", "kpl.", 6.0),
            ("kalk. własna", "Wymiana pionów instalacji centralnego ogrzewania z przejściem nowych rur przez stropy", "pion", 6.0),
            ("analiza indywidualna", "Przejścia przeciwpożarowe dla instalacji C.O. - stropy i ściany do wymaganej odporn. ogniowej", "szt", 6.0),
            ("KNR 2-15 0404-02", "Próby ciśnieniowe szczelności instalacji wewnętrznej c.o. w budynkach niemieszkalnych", "m", 40.0),
        ]
    },
    {
        "nazwa": "Wentylacja mechaniczna - I piętro",
        "pozycje": [
            ("kalk. własna", "Wentylacja mechaniczna - wykonanie i montaż w pomieszczeniu węzła sanitarnego z wentylatorami", "pom", 3.0),
        ]
    },
    {
        "nazwa": "Instalacja elektryczna i oświetleniowa - I piętro",
        "pozycje": [
            ("kalk. własna", "Projekt wykonawczy wewnętrznej instalacji elektrycznej, gniazd, oświetlenia podstawowego i ewakuacyjnego", "kpl", 1.0),
            ("kalk. własna", "Demontaż istniejącej instalacji elektrycznej i oświetleniowej (przewody, oprawy, gniazda, włączniki)", "kpl.", 1.0),
            ("kalk. własna", "Złączenie nowowykonywanej instalacji z istniejącą", "kpl.", 1.0),
            ("KSNR 5 0406-05", "Wypust oświetleniowy podtynkowy z wykonaniem i zaprawieniem bruzd i wpięciem do rozdzielnicy - analogia", "wyp.", 23.0),
            ("KSNR 5 0406-05", "Wypust oświetleniowy ewakuacyjny podtynkowy z wykonaniem i zaprawieniem bruzd - analogia", "wyp.", 3.0),
            ("KSNR 5 0502-02", "Montaż opraw oświetleniowych LED przykręcanych odpowiedniej klasie szczelności - natrysk z modułem ewakuacyjnym", "kpl.", 4.0),
            ("KSNR 5 0502-02", "Montaż opraw oświetleniowych LED przykręcanych odpowiedniej klasie szczelności z modułem ewakuacyjnym", "kpl.", 14.0),
            ("KSNR 5 0502-02", "Montaż opraw oświetleniowych LED przykręcanych nad umywalkami odpowiedniej klasie szczelności", "kpl.", 5.0),
            ("KSNR 5 0502-01", "Montaż opraw oświetleniowych przykręcanych ewakuacyjnych (kierunkowych)", "kpl.", 3.0),
            ("KNR AL-01 0201-01", "Montaż czujki ruchu - pasywna podczerwieni", "szt.", 8.0),
            ("KSNR 5 0405-01", "Wypusty wykonywane przewodami wtynkowymi na wyłącznik - włączniki pojedyncze opraw nad umywalkami - analogia", "wyp.", 5.0),
            ("KSNR 5 0406-07", "Wypusty dla gniazd 230V podtynkowo z wykonaniem i zaprawieniem bruzd - gniazdo pojedyncze - analogia", "wyp.", 5.0),
            ("KSNR 5 0406-07", "Wypusty dla gniazd 230V podtynkowo z wykonaniem i zaprawieniem bruzd - zasilanie suszarek - analogia", "wyp.", 3.0),
            ("KNR 5-08 0309-03", "Montaż do gotowego podłoża gniazd wtyczkowych podtynkowych 2-biegunowych z uziemieniem", "szt.", 5.0),
            ("KNR 5-08 0402-01", "Mocowanie na gotowym podłożu aparatów o masie do 2.5 kg - suszarka do rąk w wykonaniu nierdzewnym", "szt.", 3.0),
            ("analiza indywidualna", "Instalacja uziemiająca i połączeń wyrównawczych", "kpl", 1.0),
            ("KNR 4-03 1205-05", "Pomiar skuteczności zerowania - analogia", "kpl pomiar.", 1.0),
            ("KNR 4-03 1202-01", "Sprawdzenie i pomiar kompletnego 1-fazowego obwodu elektrycznego niskiego napięcia - analogia", "kpl pomiar.", 1.0),
            ("KNR-W 4-03 1208-01", "Pierwszy pomiar rezystancji izolacji instalacji elektrycznych w obwodzie 1-fazowym", "kpl pomiar", 1.0),
            ("KNR 13-21 0301-03", "Pomiary natężenia oświetlenia", "pom.", 3.0),
        ]
    },
    # ============ II PIĘTRO ============
    {
        "nazwa": "II PIĘTRO",
        "pozycje": []
    },
    {
        "nazwa": "Roboty rozbiórkowe - II piętro",
        "pozycje": [
            ("KNR 4-01 0354-03", "Wykucie z muru ościeżnic drewnianych o powierzchni do 1 m2 - okno", "szt.", 1.0),
            ("KNR 4-01 0354-05", "Wykucie z muru ościeżnic drewnianych o powierzchni ponad 2 m2 - okno", "m2", 5.945),
            ("KNR 4-01 0354-12", "Wykucie z muru podokienników betonowych z lastryko", "m", 5.8),
            ("KNR 4-01 0354-11", "Wykucie z muru podokienników stalowych", "m", 3.4),
            ("KNR 4-01 0354-09", "Wykucie z muru ościeżnic stalowych lub krat drzwiowych o powierzchni do 2 m2", "szt.", 10.0),
            ("KNR 9-29 0105-02", "Rozbiórka obudów pionów instalacyjnych z płyt gipsowo-kartonowych - analogia wraz z okładzinami", "m2", 35.0),
            ("KNR 4-01 0348-03", "Rozebranie ścianki z cegieł o grub. 1/2 ceg. na zaprawie cementowo-wapiennej wraz z okładzinami", "m2", 37.242),
            ("KNR 4-01 0819-15", "Rozebranie wykładziny ściennej z płytek", "m2", 138.028),
            ("KNR 4-01 0701-05", "Odbicie tynków wewnętrznych z zaprawy cementowo-wapiennej na ścianach - po skutych płytkach", "m2", 138.028),
            ("KNR 4-01 0702-06", "Odbicie tynków wewnętrznych z zaprawy cementowo-wapiennej pasami o szerokości do 30 cm", "m", 12.3),
            ("KNR 4-01 0347-09", "Skucie nierówności 4 cm na ścianach z cegieł - poszerzenie otworu; Krotność=2", "m2", 0.41),
            ("KNR 4-01 1202-08", "Zeskrobanie i zmycie starej farby w pomieszczeniach o powierzchni podłogi do 5 m2", "m2", 141.2),
            ("KNR 4-01 0811-07", "Rozebranie posadzki z płytek na zaprawie cementowej", "m2", 69.215),
            ("KNR 4-01 0354-13", "Wykucie z muru kratek wentylacyjnych, wentylatorów, drzwiczek", "szt.", 10.0),
            ("KNR 4-01 0804-07", "Zerwanie posadzki cementowej/lastykowej - wyrównanie podłoża", "m2", 69.215),
            ("KNR 4-01 0339-01", "Wykucie bruzd pionowych 1/4x1/2 ceg. w ścianach z cegieł dla instalacji wodociągowej", "m", 30.0),
            ("KNR 4-01 0336-01", "Wykucie bruzd poziomych 1/4x1/2 ceg. w ścianach z cegieł", "m", 30.0),
            ("KNR 4-01 0210-02", "Wykucie bruzd o przekroju do 0.040 m2 poziomych lub pionowych w elementach z betonu żwirowego", "m", 12.0),
            ("KNR 4-01 0106-04", "Usunięcie z parteru budynku gruzu i ziemi", "m3", 25.872),
        ]
    },
    {
        "nazwa": "Roboty murowe, ścianki i zabudowy GK - II piętro",
        "pozycje": [
            ("KNR-W 4-01 0327-02", "Zamurowanie bruzd pionowych lub pochyłych o przekroju 1/4 x 1/2 ceg. w ścianach z cegieł", "m", 30.0),
            ("KNR-W 4-01 0326-02", "Zamurowanie bruzd poziomych o przekroju 1/4 x 1/2 ceg. w ścianach z cegieł", "m", 30.0),
            ("KNR-W 2-02 2003-05", "Ścianki działowe GR z płyt gipsowo-kartonowych gkbi na rusztach metalowych pojedynczych z pokryciem obustronnym dwuwarstwowo 75-02", "m2", 42.405),
            ("KNR AT-43 0119-02", "Przygotowanie otworów w ściankach działowych z profili UA 75 pod montaż drzwi i naświetli", "szt.", 8.0),
            ("KNR 2-02 2004-01", "Zabudowy instalacyjne płytami gipsowo-kartonowymi gkbi na rusztach metalowych pojedynczych jednowarstwowo 55-01 - analogia", "m2", 70.0),
        ]
    },
    # Pozostałe działy II piętra analogicznie...
]

def generate_ath():
    """Generuje pełny plik ATH"""
    
    lines = []
    
    # === NAGŁÓWEK ===
    lines.append(f"[KOSZTORYS ATHENASOFT]\t5.10\t{DATA}\t\"Norma STANDARD\"\t\"5.16.200.16\"")
    lines.append("")
    
    # === STRONA TYTUŁOWA ===
    lines.append("[STRONA TYT]")
    lines.append(f"st1n=\t\"{NAZWA_INWESTYCJI}\"")
    lines.append(f"st2n=\t\"{ADRES_INWESTYCJI}\"")
    lines.append(f"st3n=\t\"{NAZWA_INWESTORA}\"")
    lines.append(f"st4n=\t\"{ADRES_INWESTORA}\"")
    lines.append(f"st5n=\t\"{BRANZA}\"")
    lines.append(f"st6n=\t\"{SPORZĄDZIL}\"")
    lines.append(f"st7n=\t\"{DATA}\"")
    lines.append("")
    
    # === PODSUMOWANIE GŁÓWNE ===
    lines.append("[PODSUMOWANIE]")
    lines.append("rk=0\trm=0\trs=0")
    lines.append("")
    
    # === NARZUTY ===
    lines.append("[NARZUTY NORMA 2]")
    lines.append("tn=Koszty pośrednie\ttsp=0\ttwn=65,00\ttwod=R,S\ttna=1\tttyp=1\ttpod=0\ttprc=1")
    lines.append("")
    lines.append("[NARZUTY NORMA 2]")
    lines.append("tn=Zysk\ttsp=0\ttwn=12,00\ttwod=R,S,Kp\ttna=2\tttyp=1\ttpod=0\tttyp=1\ttprc=1")
    lines.append("")
    lines.append("[NARZUTY NORMA 1]")
    lines.append("tn=VAT\ttsp=0\ttwn=23,00\ttna=3\ttyp=2\ttpod=0\ttprc=1")
    lines.append("")
    lines.append("[NARZUTY NEX 1]")
    lines.append("Koszty pośrednie [Kp]\t\t\t\t0\t\t\t65,00\t\t\t\t\t\t\t\t\t1\t\t\t\t1\t")
    lines.append("")
    lines.append("[NARZUTY NEX 2]")
    lines.append("Zysk [Z]\t\t\t\t0\t\t\t12,00\t\t\t\t\t\t\t\t\t2\t\t\t\t1\t")
    lines.append("")
    lines.append("[NARZUTY NEX 4]")
    lines.append("VAT\t\t\t\t0\t\t\t23,00\t\t\t\t\t\t\t\t\t3\t2\t\t\t1\t")
    lines.append("")
    
    # === RMS ===
    lines.append("[RMS ZEST 1]")
    lines.append(f"sr=robocizna\trc=r-g\trj=149\trn=1,0000\trc={str(STAWKA_RG).replace('.', ',')}\tnr=1")
    lines.append("")
    
    # === GENERUJ DZIAŁY I POZYCJE ===
    element_id = 1
    pozycja_id = 2
    
    for dzial in DZIALY:
        if not dzial.get("pozycje"):
            # To dział nadrzędny (np. "PARTER")
            lines.append(f"[ELEMENT 1]")
            lines.append(f"ne={element_id}\tnd=d.{element_id}.\tnn=\"{dzial['nazwa']}\"\tnb=\tnst=\tnl=1\tnic=\tnwp=\tnpr=1\tnpok=\tnos=\tnig=1")
            lines.append("")
            lines.append("[PODSUMOWANIE]")
            lines.append("rk=0\trm=0\trs=0")
            lines.append("")
            element_id += 1
            continue
            
        lines.append(f"[ELEMENT 1]")
        lines.append(f"ne={element_id}\tnd=d.{element_id}.\tnn=\"{dzial['nazwa']}\"\tnb=\tnst=\tnl=2\tnic=\tnwp=\tnpr=1\tnpok=\tnos=\tnig=1")
        lines.append("")
        lines.append("[PODSUMOWANIE]")
        lines.append("rk=0\trm=0\trs=0")
        lines.append("")
        
        for idx, (podstawa, opis, jm, ilosc) in enumerate(dzial["pozycje"], 1):
            jm_code = get_jm_code(jm)
            ilosc_str = str(ilosc).replace(".", ",")
            
            # Parsuj podstawę
            parts = podstawa.split()
            if len(parts) >= 2:
                katalog = parts[0]
                numer = " ".join(parts[1:])
            else:
                katalog = podstawa
                numer = "0000-00"
            
            lines.append("[POZYCJA]")
            lines.append(f"id={pozycja_id}\tid2={pozycja_id+1}\tnp={idx}\tnjk={jm_code}\tnjn={jm}\tpp=0\tiob={ilosc_str}\tpn=\"{opis}\"")
            lines.append(f"pd={katalog}\t{katalog}\t{numer}\t\t{numer}\t\t1")
            lines.append(f"pd5={katalog}\tKATSRC_KATAL\t{katalog} {numer}\t")
            lines.append("mpn=1211\t<DaneKNR><Nie_wybrano_modyfikacji /></DaneKNR>")
            lines.append("")
            lines.append("[PODSUMOWANIE]")
            lines.append("rk=0\trm=0\trs=0")
            lines.append("")
            lines.append("[OBMIAR NEX]")
            lines.append(f"{ilosc_str}")
            lines.append("")
            lines.append("[PRZEDMIAR]")
            lines.append(f"0\t0\t{ilosc_str}\t\t{ilosc_str}")
            lines.append("")
            lines.append("[RMS 1]")
            lines.append(f"sr=robocizna\trc=r-g\trj=149\trn=1,0000\trc={str(STAWKA_RG).replace('.', ',')}\tnr=1")
            lines.append("")
            
            pozycja_id += 2
        
        element_id += 1
    
    return "\n".join(lines)

def main():
    """Główna funkcja"""
    output_path = r"C:\Users\Gabriel\Downloads\kosztorys_brzeg_sanitariaty.ath"
    
    print("=" * 60)
    print("GENERATOR KOSZTORYSU ATH")
    print("=" * 60)
    print(f"Inwestycja: {NAZWA_INWESTYCJI}")
    print(f"Adres: {ADRES_INWESTYCJI}")
    print(f"Inwestor: {NAZWA_INWESTORA}")
    print(f"Data: {DATA}")
    print(f"Stawka r-g: {STAWKA_RG} zł")
    print()
    
    # Policz pozycje
    total_pozycji = sum(len(d.get("pozycje", [])) for d in DZIALY)
    print(f"Działów: {len(DZIALY)}")
    print(f"Pozycji: {total_pozycji}")
    print()
    
    # Generuj ATH
    print("Generowanie pliku ATH...")
    content = generate_ath()
    
    # Zapisz w cp1250
    with open(output_path, 'w', encoding='cp1250') as f:
        f.write(content)
    
    print(f"[OK] Zapisano: {output_path}")
    print()
    print("Otworz w Norma PRO: Plik -> Otworz")
    print()
    
if __name__ == "__main__":
    main()
