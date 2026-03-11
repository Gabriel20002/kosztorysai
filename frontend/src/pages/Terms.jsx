import { Link } from 'react-router-dom'

export default function Terms() {
    return (
        <div className="w-full max-w-3xl mx-auto my-16 px-4 md:px-6 relative z-10">
            <div className="glass-card rounded-2xl p-6 md:p-10 border border-slate-800/50 shadow-2xl">

                <div className="mb-8">
                    <h1 className="text-2xl font-black text-white tracking-tight">Regulamin Programu Beta</h1>
                    <p className="text-slate-400 text-sm mt-2">Wersja 1.0 — obowiązuje od 11 marca 2026 r.</p>
                    <p className="text-slate-400 text-sm mt-1">Administrator: Gabriel Długi | kontakt: kosztorysyai@gmail.com</p>
                </div>

                <div className="space-y-8 text-slate-300 text-sm leading-relaxed">

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§1. Cel udostępnienia — wersja Beta</h2>
                        <p>
                            Serwis KosztorysAI jest udostępniany wyłącznie w celach demonstracyjnych i testowych
                            (tzw. <strong className="text-white">Proof of Concept</strong>). Udział w programie Beta
                            polega na ocenie funkcjonalności narzędzia i przekazaniu informacji zwrotnej administratorowi.
                        </p>
                        <p className="mt-2">
                            Korzystanie z serwisu w celu sporządzania <strong className="text-white">rzeczywistych kosztorysów
                            budowlanych przeznaczonych do rozliczeń z klientami lub do celów przetargowych jest
                            bezwzględnie zabronione</strong>. Serwis nie jest produktem komercyjnym gotowym do wdrożenia
                            produkcyjnego.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§2. Charakter oprogramowania — formuła „As-Is"</h2>
                        <p>
                            Oprogramowanie jest we wczesnej fazie rozwoju i dostarczane jest w stanie{' '}
                            <strong className="text-white">„takim, jakim jest"</strong> (as-is), bez jakichkolwiek
                            gwarancji poprawności działania, kompletności wyników ani ciągłości dostępu.
                        </p>
                        <p className="mt-2">
                            Administrator zastrzega prawo do <strong className="text-white">przerwy, modyfikacji lub
                            całkowitego wyłączenia serwisu w dowolnym momencie, bez uprzedniego powiadomienia</strong>.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§3. Wyłączenie odpowiedzialności</h2>
                        <p>
                            Narzędzie może generować błędne wartości liczbowe, niepoprawne stawki lub niekompletne
                            zestawienia. Administrator <strong className="text-white">nie ponosi żadnej odpowiedzialności</strong>{' '}
                            za skutki wykorzystania wyników wygenerowanych przez serwis, w szczególności za:
                        </p>
                        <ul className="list-disc list-inside mt-2 space-y-1 text-slate-400">
                            <li>błędy w obliczeniach i kosztorysach,</li>
                            <li>straty finansowe wynikające z posługiwania się wygenerowanymi dokumentami,</li>
                            <li>utracone zyski, kontrakty lub inne korzyści majątkowe,</li>
                            <li>szkody bezpośrednie i pośrednie poniesione przez użytkownika lub osoby trzecie.</li>
                        </ul>
                        <p className="mt-2">
                            Użytkownik korzysta z serwisu <strong className="text-white">wyłącznie na własne ryzyko</strong>.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§4. Polityka wprowadzania danych</h2>
                        <p>
                            Ze względu na wczesny etap rozwoju serwisu oraz w celu ochrony danych osobowych,
                            użytkownik jest zobowiązany do <strong className="text-white">używania wyłącznie fikcyjnych,
                            testowych danych</strong>.
                        </p>
                        <p className="mt-2">
                            Bezwzględnie <strong className="text-white">zabrania się</strong> wprowadzania do serwisu:
                        </p>
                        <ul className="list-disc list-inside mt-2 space-y-1 text-slate-400">
                            <li>rzeczywistych danych osobowych klientów,</li>
                            <li>adresów inwestycji powiązanych z konkretnym podmiotem,</li>
                            <li>dokumentów zawierających informacje poufne lub wrażliwe.</li>
                        </ul>
                        <p className="mt-2">
                            Odpowiedzialność za naruszenie powyższego zakazu ponosi wyłącznie użytkownik.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§5. Prawa własności intelektualnej i poufność</h2>
                        <p>
                            Wszelkie prawa do oprogramowania KosztorysAI, jego kodu źródłowego, algorytmów,
                            interfejsu graficznego oraz koncepcji biznesowej należą wyłącznie do{' '}
                            <strong className="text-white">Gabriela Długiego</strong>.
                        </p>
                        <p className="mt-2">Użytkownikowi zabrania się:</p>
                        <ul className="list-disc list-inside mt-2 space-y-1 text-slate-400">
                            <li>kopiowania, analizowania lub odtwarzania rozwiązań zastosowanych w serwisie,</li>
                            <li>udostępniania dostępu do konta osobom trzecim,</li>
                            <li>przekazywania informacji o działaniu serwisu podmiotom konkurencyjnym,</li>
                            <li>publicznego publikowania wyników testów bez zgody administratora.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§6. Uprawnienia administratora</h2>
                        <p>Administrator zastrzega sobie prawo do:</p>
                        <ul className="list-disc list-inside mt-2 space-y-1 text-slate-400">
                            <li>usunięcia wygenerowanych kosztorysów i danych testowych w dowolnym momencie,</li>
                            <li>wyczyszczenia bazy danych bez uprzedniego powiadomienia,</li>
                            <li>cofnięcia dostępu do serwisu bez podania przyczyny,</li>
                            <li>zakończenia programu Beta w dowolnym terminie.</li>
                        </ul>
                        <p className="mt-2">
                            Użytkownik nie nabywa żadnych roszczeń z tytułu utraty dostępu lub danych.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§7. Akceptacja warunków</h2>
                        <p>
                            Rejestracja konta, zalogowanie się do serwisu lub pierwsze wygenerowanie kosztorysu jest
                            równoznaczne z <strong className="text-white">pełną akceptacją niniejszego Regulaminu</strong>{' '}
                            w brzmieniu obowiązującym w chwili wykonania tej czynności.
                        </p>
                        <p className="mt-2">
                            Administrator zastrzega prawo do zmiany treści Regulaminu. Dalsze korzystanie z serwisu
                            po opublikowaniu zmian oznacza ich akceptację.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-white font-bold text-base mb-3">§8. Postanowienia końcowe</h2>
                        <p>
                            W sprawach nieuregulowanych niniejszym Regulaminem zastosowanie mają przepisy prawa
                            polskiego. Wszelkie pytania i uwagi należy kierować na adres:{' '}
                            <a href="mailto:kosztorysyai@gmail.com" className="text-primary hover:underline">
                                kosztorysyai@gmail.com
                            </a>.
                        </p>
                    </section>

                </div>

                <div className="mt-8 pt-6 border-t border-slate-800 text-center">
                    <Link
                        to="/register"
                        className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-white font-bold hover:bg-sky-400 transition-colors shadow-lg shadow-primary/20"
                    >
                        <span className="material-symbols-outlined text-base">arrow_back</span>
                        Wróć do rejestracji
                    </Link>
                </div>
            </div>
        </div>
    )
}
