import { Link } from 'react-router-dom'

export default function Pricing() {
    return (
        <div className="w-full max-w-[1280px] px-4 md:px-6 py-16 md:py-24 mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700/50 mb-6">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <span className="text-xs font-medium text-slate-300 uppercase tracking-wider">Program Beta — Dostęp Bezpłatny</span>
            </div>

            <h1 className="text-3xl md:text-5xl lg:text-6xl font-black text-white mb-6">Dołącz do Programu Beta</h1>
            <p className="text-slate-400 text-base md:text-lg max-w-2xl mx-auto mb-10 md:mb-16 px-2 md:px-0">
                KosztorysAI jest teraz dostępny bezpłatnie w fazie testów beta. Pomóż nam kształtować produkt — Twoja opinia ma realny wpływ na rozwój narzędzia.
            </p>

            <div className="max-w-md mx-auto">
                <div className="glass-card rounded-2xl p-8 md:p-10 border border-primary shadow-[0_0_40px_rgba(19,146,236,0.15)] flex flex-col items-center text-left">
                    <div className="w-full flex items-center justify-between mb-6">
                        <h3 className="text-2xl font-bold text-white">Dostęp Beta</h3>
                        <span className="text-xs font-bold bg-primary/20 text-primary border border-primary/30 px-3 py-1 rounded-full uppercase tracking-wider">Bezpłatny</span>
                    </div>

                    <div className="mb-8 w-full">
                        <span className="text-5xl font-black text-white">0 PLN</span>
                        <span className="text-slate-500"> / do odwołania</span>
                    </div>

                    <Link
                        to="/register"
                        className="w-full h-12 rounded-lg bg-primary text-white font-bold hover:bg-sky-400 transition-colors mb-8 shadow-lg shadow-primary/20 flex items-center justify-center"
                    >
                        Dołącz do Programu Beta
                    </Link>

                    <ul className="space-y-4 text-slate-300 w-full">
                        <li className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-sm text-primary">check</span>
                            Generowanie kosztorysów ATH (Norma PRO)
                        </li>
                        <li className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-sm text-primary">check</span>
                            Automatyczne dopasowanie nakładów KNR
                        </li>
                        <li className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-sm text-primary">check</span>
                            Historia wygenerowanych kosztorysów
                        </li>
                        <li className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-sm text-primary">check</span>
                            Bezpośredni kontakt z twórcą
                        </li>
                    </ul>

                    <div className="mt-8 pt-6 border-t border-slate-800 w-full text-center">
                        <p className="text-slate-500 text-xs leading-relaxed">
                            Dostęp przyznawany ręcznie po rejestracji. Korzystanie z serwisu podlega{' '}
                            <Link to="/terms" className="text-primary hover:underline">Regulaminowi Programu Beta</Link>.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
