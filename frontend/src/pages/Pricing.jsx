export default function Pricing() {
    return (
        <div className="w-full max-w-[1280px] px-4 md:px-6 py-16 md:py-24 mx-auto text-center">
            <h1 className="text-3xl md:text-5xl lg:text-6xl font-black text-white mb-6">Prosty, Przejrzysty Cennik</h1>
            <p className="text-slate-400 text-base md:text-lg max-w-2xl mx-auto mb-10 md:mb-16 px-2 md:px-0">Wybierz plan, który najlepiej pasuje do wielkości i potrzeb Twojej firmy budowlanej.</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 text-left">
                {/* Basic Plan */}
                <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-800 flex flex-col hover:border-slate-600 transition-colors">
                    <h3 className="text-xl font-bold text-white mb-2">Starter</h3>
                    <p className="text-slate-400 mb-6">Idealny dla niezależnych kosztorysantów.</p>
                    <div className="mb-8">
                        <span className="text-4xl font-black text-white">199 PLN</span>
                        <span className="text-slate-500">/msc</span>
                    </div>
                    <button className="w-full h-12 rounded-lg bg-slate-800 text-white font-bold hover:bg-slate-700 transition-colors mb-8">Zacznij Teraz</button>
                    <ul className="space-y-4 text-slate-300">
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Do 5 kosztorysów/msc</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Obsługa PDF i CAD</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Podstawowe wsparcie e-mail</li>
                    </ul>
                </div>

                {/* Pro Plan */}
                <div className="glass-card rounded-2xl p-6 md:p-8 border border-primary relative flex flex-col shadow-[0_0_30px_rgba(19,146,236,0.15)] transform md:-translate-y-4">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">Najpopularniejszy</div>
                    <h3 className="text-xl font-bold text-white mb-2">Professional</h3>
                    <p className="text-slate-400 mb-6">Dla rosnących firm wykonawczych.</p>
                    <div className="mb-8">
                        <span className="text-4xl font-black text-white">599 PLN</span>
                        <span className="text-slate-500">/msc</span>
                    </div>
                    <button className="w-full h-12 rounded-lg bg-primary text-white font-bold hover:bg-sky-400 transition-colors mb-8 shadow-lg shadow-primary/20">Zacznij 14-Dniowy Okres Próbny</button>
                    <ul className="space-y-4 text-slate-300">
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Nielimitowane kosztorysowanie</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Zaawansowane modele robocizny</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Dostęp do API</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Priorytetowe wsparcie 24/7</li>
                    </ul>
                </div>

                {/* Enterprise Plan */}
                <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-800 flex flex-col hover:border-slate-600 transition-colors mt-4 md:mt-0">
                    <h3 className="text-xl font-bold text-white mb-2">Enterprise</h3>
                    <p className="text-slate-400 mb-6">Dla największych deweloperów.</p>
                    <div className="mb-8">
                        <span className="text-4xl font-black text-white">Indywidualna</span>
                        <span className="text-slate-500"> wycena</span>
                    </div>
                    <button className="w-full h-12 rounded-lg bg-slate-800 text-white font-bold hover:bg-slate-700 transition-colors mb-8">Kontakt z Działem Sprzedaży</button>
                    <ul className="space-y-4 text-slate-300">
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Uczenie AI na własnych bazach</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Dedykowany opiekun klienta</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Wdrożenie On-premise</li>
                        <li className="flex items-center gap-3"><span className="material-symbols-outlined text-sm text-primary">check</span>Gwarancje SLA</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
