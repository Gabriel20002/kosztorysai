export default function Features() {
    return (
        <div className="w-full flex-1">
            {/* Hero Section */}
            <section className="w-full max-w-[1280px] px-4 md:px-6 py-12 md:py-32 mx-auto text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 w-fit mx-auto mb-6">
                    <span className="material-symbols-outlined text-primary text-sm">stars</span>
                    <span className="text-xs font-bold text-primary uppercase tracking-wider">Możliwości platformy</span>
                </div>
                <h1 className="text-3xl md:text-5xl lg:text-6xl font-black text-white mb-6 text-glow">
                    Silnik Kosztorysowy <br className="hidden sm:block" />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Nowej Generacji</span>
                </h1>
                <p className="text-slate-400 text-lg md:text-xl max-w-3xl mx-auto font-light leading-relaxed">
                    Odkryj potężne funkcje, dzięki którym Kosztorysy AI to najszybsze i najdokładniejsze oprogramowanie kosztorysowe w branży budowlanej. Zbudowane do obsługi złożonych projektów architektonicznych w kilka sekund.
                </p>
            </section>


            {/* Deep Dive Features */}
            <section className="w-full max-w-[1280px] px-4 md:px-6 py-16 md:py-24 mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-black text-white">Funkcjonalności Platformy</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Feature Block */}
                    <div className="flex flex-col sm:flex-row gap-6 p-6 rounded-2xl hover:bg-surface-dark/50 transition-colors group items-center sm:items-start text-center sm:text-left">
                        <div className="flex-shrink-0 size-16 sm:size-14 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                            <span className="material-symbols-outlined text-primary text-3xl sm:text-2xl group-hover:scale-110 transition-transform">document_scanner</span>
                        </div>
                        <div>
                            <h4 className="text-lg font-bold text-white mb-2">Zaawansowane Auto-OCR</h4>
                            <p className="text-slate-400 leading-relaxed">Wyciąga tekst i tabele z trudnych skanów i obszernych plików PDF z 99.8% dokładnością, analizując nazwy i specyfikacje materiałów.</p>
                        </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-6 p-6 rounded-2xl hover:bg-surface-dark/50 transition-colors group items-center sm:items-start text-center sm:text-left">
                        <div className="flex-shrink-0 size-16 sm:size-14 rounded-xl bg-secondary/10 border border-secondary/20 flex items-center justify-center">
                            <span className="material-symbols-outlined text-secondary text-3xl sm:text-2xl group-hover:scale-110 transition-transform">architecture</span>
                        </div>
                        <div>
                            <h4 className="text-lg font-bold text-white mb-2">Analiza Geometrii CAD</h4>
                            <p className="text-slate-400 leading-relaxed">Rozpoznaje rysunki 2D i modele, odczytując odpowiednie skale w celu natychmiastowego wyliczenia wymiarów liniowych i metrażu powierzchni.</p>
                        </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-6 p-6 rounded-2xl hover:bg-surface-dark/50 transition-colors group items-center sm:items-start text-center sm:text-left">
                        <div className="flex-shrink-0 size-16 sm:size-14 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                            <span className="material-symbols-outlined text-orange-400 text-3xl sm:text-2xl group-hover:scale-110 transition-transform">database</span>
                        </div>
                        <div>
                            <h4 className="text-lg font-bold text-white mb-2">Ceny Materiałów na Żywo</h4>
                            <p className="text-slate-400 leading-relaxed">System stale odpytuje regionalne bazy cenowe, takie jak SEKOCENBUD, aby zapewnić, że Twój kosztorys używa najbardziej aktualnych stawek hurtowych.</p>
                        </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-6 p-6 rounded-2xl hover:bg-surface-dark/50 transition-colors group items-center sm:items-start text-center sm:text-left">
                        <div className="flex-shrink-0 size-16 sm:size-14 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                            <span className="material-symbols-outlined text-emerald-400 text-3xl sm:text-2xl group-hover:scale-110 transition-transform">group</span>
                        </div>
                        <div>
                            <h4 className="text-lg font-bold text-white mb-2">Dynamiczne Modulowanie Robocizny</h4>
                            <p className="text-slate-400 leading-relaxed">Automatycznie dobiera wymagane normy roboczogodzin (R-G) opierając się na KNR, trudności zlecenia oraz lokalnych stawkach.</p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
