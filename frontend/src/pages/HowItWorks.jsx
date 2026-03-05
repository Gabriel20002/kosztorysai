export default function HowItWorks() {
    return (
        <div className="w-full flex-1 flex flex-col items-center justify-center py-8 md:py-12">
            {/* How it Works Timeline */}
            <section className="w-full bg-surface-dark/50 backdrop-blur-sm relative py-12 md:py-20 mt-4 md:mt-10">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[300px] bg-primary/5 rounded-full blur-[120px] pointer-events-none"></div>
                <div className="max-w-[1280px] mx-auto px-4 md:px-6 relative z-10">
                    <div className="text-center mb-16">
                        <h2 className="text-secondary font-bold text-sm tracking-widest uppercase mb-2">Proces</h2>
                        <h3 className="text-3xl md:text-5xl lg:text-6xl font-black text-white text-glow">Jak Działa BuildAI</h3>
                        <p className="text-slate-400 text-base md:text-lg lg:text-xl max-w-2xl mx-auto font-light leading-relaxed mt-4">
                            Nasz 3-etapowy proces zamienia godziny ręcznych obliczeń w zaledwie kilka sekund.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative mt-16">
                        {/* Connecting lines for desktop */}
                        <div className="hidden md:block absolute top-[100px] left-[15%] right-[15%] h-0.5 bg-gradient-to-r from-transparent via-slate-700 to-transparent"></div>

                        {/* Step 1 */}
                        <div className="glass-card rounded-2xl p-8 border border-slate-800 relative group flex flex-col items-center text-center hover:border-primary/50 transition-colors">
                            <div className="absolute -top-6 left-1/2 -translate-x-1/2 size-12 rounded-full bg-surface-dark border-4 border-background-dark text-white font-black flex items-center justify-center z-10">1</div>
                            <div className="size-20 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center shadow-lg shadow-black/50 mb-6 mt-4 group-hover:scale-110 transition-transform">
                                <span className="material-symbols-outlined text-primary text-4xl">upload_file</span>
                            </div>
                            <h4 className="text-xl font-bold text-white mb-3">Wgraj Plany</h4>
                            <p className="text-slate-400">Po prostu przeciągnij i upuść swoje pliki PDF, CAD lub zestawienia Excel na bezpieczny panel.</p>
                        </div>

                        {/* Step 2 */}
                        <div className="glass-card rounded-2xl p-8 border border-slate-800 relative group flex flex-col items-center text-center hover:border-secondary/50 transition-colors transform md:translate-y-8">
                            <div className="absolute -top-6 left-1/2 -translate-x-1/2 size-12 rounded-full bg-primary border-4 border-background-dark text-white font-black flex items-center justify-center z-10 shadow-[0_0_15px_rgba(19,146,236,0.5)]">2</div>
                            <div className="size-20 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center shadow-lg shadow-black/50 mb-6 mt-4 group-hover:scale-110 transition-transform">
                                <span className="material-symbols-outlined text-secondary text-4xl">memory</span>
                            </div>
                            <h4 className="text-xl font-bold text-white mb-3">Przetwarzanie AI</h4>
                            <p className="text-slate-400">Nasz silnik używa zlokalizowanego Auto-OCR i rozpoznawania geometrii, aby natychmiast wyodrębnić pozycje, ilości i strukturę.</p>
                        </div>

                        {/* Step 3 */}
                        <div className="glass-card rounded-2xl p-8 border border-slate-800 relative group flex flex-col items-center text-center hover:border-emerald-500/50 transition-colors">
                            <div className="absolute -top-6 left-1/2 -translate-x-1/2 size-12 rounded-full bg-surface-dark border-4 border-background-dark text-white font-black flex items-center justify-center z-10">3</div>
                            <div className="size-20 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center shadow-lg shadow-black/50 mb-6 mt-4 group-hover:scale-110 transition-transform">
                                <span className="material-symbols-outlined text-emerald-400 text-4xl">request_quote</span>
                            </div>
                            <h4 className="text-xl font-bold text-white mb-3">Weryfikacja i Eksport</h4>
                            <p className="text-slate-400">Odbierz w pełni skategoryzowany, zlokalizowany kosztorys gotowy do Twojej weryfikacji. Eksportuj do ulubionych programów dla wykonawców.</p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
