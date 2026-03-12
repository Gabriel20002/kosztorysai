import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Home() {
    const { user } = useAuth();
    return (
        <>
            {/* Hero Section */}
            <section className="w-full max-w-[1280px] px-4 md:px-6 py-12 md:py-24 lg:py-32 flex flex-col lg:flex-row items-center gap-8 lg:gap-20">
                {/* Hero Text */}
                <div className="flex flex-col gap-6 lg:w-1/2 text-center lg:text-left fade-in-up">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700/50 w-fit mx-auto lg:mx-0">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                        <span className="text-xs font-medium text-slate-300 uppercase tracking-wider">Wersja Beta — W Aktywnym Rozwoju</span>
                    </div>
                    <h1 className="text-4xl md:text-5xl lg:text-6xl font-black leading-tight tracking-tight text-slate-900 dark:text-white text-glow">
                        Przyszłość <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Kosztorysowania</span>
                        {' '}Nadeszła
                    </h1>
                    <p className="text-lg text-slate-600 dark:text-slate-400 max-w-[600px] mx-auto lg:mx-0 font-light">
                        Wspomagaj pracę kosztorysanta przy tworzeniu ślepych kosztorysów z przedmiaru PDF. AI dobiera nakłady KNR, materiały i sprzęt — wynik weryfikujesz przed użyciem.
                    </p>
                    <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 mt-4">
                        {user ? (
                            <Link to="/dashboard" className="flex items-center justify-center gap-2 h-12 px-8 rounded-lg bg-primary hover:bg-sky-400 text-white font-bold transition-colors shadow-lg shadow-primary/30">
                                <span className="material-symbols-outlined text-xl">rocket_launch</span>
                                Generuj Kosztorys
                            </Link>
                        ) : (
                            <Link to="/register" className="flex items-center justify-center gap-2 h-12 px-8 rounded-lg bg-white text-slate-900 font-bold hover:bg-slate-200 transition-colors">
                                <span className="material-symbols-outlined text-xl">rocket_launch</span>
                                Dołącz do Programu Beta
                            </Link>
                        )}
                        <Link to="/how-it-works" className="flex items-center justify-center h-12 px-8 rounded-lg bg-slate-800/50 border border-slate-700 hover:bg-slate-800 text-white font-bold transition-all gap-2 group">
                            <span className="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">play_circle</span>
                            Jak to działa
                        </Link>
                    </div>
                </div>

                {/* Hero Visual / 3D Card Effect */}
                <div className="lg:w-1/2 w-full relative perspective-1000 fade-in-up delay-2">
                    <div className="relative w-full aspect-[4/3] rounded-2xl glass-card p-2 transform rotate-y-[-5deg] rotate-x-[5deg] hover:rotate-0 transition-transform duration-700 ease-out shadow-2xl overflow-hidden border border-slate-700/30">
                        {/* Abstract UI mock */}
                        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 to-slate-950 opacity-90"></div>

                        {/* Top Bar Mock */}
                        <div className="relative flex items-center justify-between p-4 border-b border-slate-700/50">
                            <div className="flex gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
                                <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
                                <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
                            </div>
                            <div className="h-2 w-24 bg-slate-700 rounded-full"></div>
                        </div>

                        {/* Content Mock */}
                        <div className="relative p-6 grid grid-cols-3 gap-4">
                            {/* Sidebar */}
                            <div className="col-span-1 flex flex-col gap-3">
                                <div className="h-20 w-full bg-slate-800/50 rounded-lg animate-pulse"></div>
                                <div className="h-8 w-full bg-slate-800/30 rounded-lg"></div>
                                <div className="h-8 w-full bg-slate-800/30 rounded-lg"></div>
                                <div className="h-8 w-full bg-slate-800/30 rounded-lg"></div>
                            </div>

                            {/* Main Area */}
                            <div className="col-span-2 flex flex-col gap-4">
                                <div className="flex justify-between items-center mb-2">
                                    <div className="h-4 w-32 bg-primary/40 rounded"></div>
                                    <div className="h-8 w-24 bg-primary rounded-md flex items-center justify-center text-[10px] text-white font-bold">Wygenerowano</div>
                                </div>

                                {/* Data Rows */}
                                <div className="space-y-2">
                                    <div className="flex items-center gap-3 p-2 rounded bg-slate-800/20 border border-slate-700/30">
                                        <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
                                        <div className="h-2 w-full bg-slate-700/50 rounded"></div>
                                        <div className="h-2 w-12 bg-slate-700/50 rounded"></div>
                                    </div>
                                    <div className="flex items-center gap-3 p-2 rounded bg-slate-800/20 border border-slate-700/30">
                                        <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
                                        <div className="h-2 w-3/4 bg-slate-700/50 rounded"></div>
                                        <div className="h-2 w-12 bg-slate-700/50 rounded"></div>
                                    </div>
                                    <div className="flex items-center gap-3 p-2 rounded bg-slate-800/20 border border-slate-700/30">
                                        <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
                                        <div className="h-2 w-5/6 bg-slate-700/50 rounded"></div>
                                        <div className="h-2 w-12 bg-slate-700/50 rounded"></div>
                                    </div>
                                </div>

                                {/* Floating Scan Element */}
                                <div className="absolute top-1/2 left-10 right-10 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent shadow-[0_0_15px_rgba(19,146,236,1)] animate-[pulse_2s_ease-in-out_infinite]"></div>
                            </div>
                        </div>

                        {/* Overlay Gradient */}
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent pointer-events-none"></div>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="w-full border-y border-slate-800 bg-surface-dark/50 backdrop-blur-sm">
                <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-8 md:py-12">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="flex flex-col items-center md:items-start p-4 text-center md:text-left fade-in-up delay-1">
                            <span className="material-symbols-outlined text-primary text-3xl mb-2">upload_file</span>
                            <p className="text-base font-bold text-white mb-1">Przedmiar PDF → ATH w minuty</p>
                            <p className="text-sm text-slate-400">Wgraj plik z Normy PRO i odbierz gotowy kosztorys</p>
                        </div>
                        <div className="flex flex-col items-center md:items-start p-4 md:border-l md:border-slate-800 text-center md:text-left fade-in-up delay-2">
                            <span className="material-symbols-outlined text-secondary text-3xl mb-2">auto_awesome</span>
                            <p className="text-base font-bold text-white mb-1">Automatyczne nakłady KNR</p>
                            <p className="text-sm text-slate-400">AI dobiera robociznę, materiały i sprzęt do każdej pozycji</p>
                        </div>
                        <div className="flex flex-col items-center md:items-start p-4 md:border-l md:border-slate-800 text-center md:text-left fade-in-up delay-3">
                            <span className="material-symbols-outlined text-primary text-3xl mb-2">download</span>
                            <p className="text-base font-bold text-white mb-1">Format ATH gotowy do użycia</p>
                            <p className="text-sm text-slate-400">Wynik gotowy do otwarcia w oprogramowaniu kosztorysowym bez żadnych konwersji</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section className="w-full max-w-[1280px] px-4 md:px-6 py-16 md:py-24 flex flex-col gap-10 md:gap-16">
                <div className="flex flex-col gap-4 text-center items-center">
                    <h2 className="text-secondary font-bold text-sm tracking-widest uppercase">Przebieg Pracy</h2>
                    <h3 className="text-3xl md:text-5xl font-black text-white">Skróć Czas Przygotowania Kosztorysu</h3>
                    <p className="text-slate-400 max-w-2xl text-lg">AI odczytuje pozycje z przedmiaru PDF i dobiera nakłady KNR. Zamiast szukać każdej pozycji ręcznie, dostajesz gotowy punkt wyjścia do dalszej weryfikacji.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Feature 1 */}
                    <div className="group relative rounded-2xl bg-surface-dark border border-slate-800 p-8 hover:border-primary/50 transition-all hover:-translate-y-1 duration-300 fade-in-up delay-1">
                        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity"></div>
                        <div className="relative z-10 flex flex-col gap-6">
                            <div className="size-14 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-black/50">
                                <span className="material-symbols-outlined text-primary text-3xl">bolt</span>
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-xl font-bold text-white">Błyskawiczna Analiza</h4>
                                <p className="text-slate-400 leading-relaxed">Wgraj przedmiar w formacie PDF i w ciągu kilku minut otrzymaj plik ATH gotowy do otwarcia w Normie PRO. Bez ręcznego przepisywania pozycji.</p>
                            </div>
                        </div>
                    </div>

                    {/* Feature 2 */}
                    <div className="group relative rounded-2xl bg-surface-dark border border-slate-800 p-8 hover:border-secondary/50 transition-all hover:-translate-y-1 duration-300 fade-in-up delay-2">
                        <div className="absolute inset-0 bg-gradient-to-b from-secondary/5 to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity"></div>
                        <div className="relative z-10 flex flex-col gap-6">
                            <div className="size-14 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-black/50">
                                <span className="material-symbols-outlined text-secondary text-3xl">my_location</span>
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-xl font-bold text-white">Weryfikacja Wyników</h4>
                                <p className="text-slate-400 leading-relaxed">Wbudowany weryfikator AI sprawdza wygenerowany kosztorys pod kątem typowych błędów — zerowych materiałów, brakujących KNR i podejrzanych wartości. Ostateczna decyzja należy do kosztorysanta.</p>
                            </div>
                        </div>
                    </div>

                    {/* Feature 3 */}
                    <div className="group relative rounded-2xl bg-surface-dark border border-slate-800 p-8 hover:border-primary/50 transition-all hover:-translate-y-1 duration-300 fade-in-up delay-3">
                        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity"></div>
                        <div className="relative z-10 flex flex-col gap-6">
                            <div className="size-14 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-black/50">
                                <span className="material-symbols-outlined text-primary text-3xl">trending_up</span>
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-xl font-bold text-white">Format ATH bez Konwersji</h4>
                                <p className="text-slate-400 leading-relaxed">Wynik generowany jest bezpośrednio w formacie ATH zgodnym z Normą PRO. Nie tracisz czasu na ręczne przepisywanie ani konwersję plików.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Video/Image Showcase Section */}
            <section className="w-full max-w-[1280px] px-4 md:px-6 pb-16 md:pb-24">
                <div className="relative w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-surface-dark group">
                    <div
                        className="aspect-video w-full bg-cover bg-center opacity-80 group-hover:opacity-100 transition-opacity duration-500"
                        style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBM3zNcxhucGe8Z1jRWDiG3K7AbTudwVWRTA0v_6AsndEOrx7L0XnG-wMmDOLt4cTC_urpDpSriLTxoRRs7-5UY1TFUopA9URER697wuI1oDnWs88zLTQSgAzrjBkRIJhaPOexQAAAyW7PrIvgIYZVhNi-JVX3JBND7rtZJwgwOY9hQXmtU-1qigkrZnRq8silQKdB1M-4b3w5XxlXhmJ-YNfpehNTrBYv9EVcEY3gXmUddDbf9Ve11YyPi9Jo2umXnfuedCduq-VM")' }}
                    >
                    </div>

                    {/* Play Button Overlay */}
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[2px] group-hover:backdrop-blur-none group-hover:bg-black/20 transition-all duration-300">
                        <button className="flex items-center justify-center size-20 rounded-full bg-primary text-white shadow-[0_0_30px_rgba(19,146,236,0.5)] hover:scale-110 transition-transform duration-300">
                            <span className="material-symbols-outlined text-5xl ml-1">play_arrow</span>
                        </button>
                    </div>

                    {/* Text Overlay */}
                    <div className="absolute bottom-0 left-0 right-0 p-4 md:p-8 bg-gradient-to-t from-black via-black/80 to-transparent">
                        <div className="flex flex-col md:flex-row items-center md:items-end justify-between gap-4 text-center md:text-left">
                            <div>
                                <h3 className="text-2xl md:text-3xl font-bold text-white mb-2">Zobacz Kosztorysy AI w akcji</h3>
                                <p className="text-slate-300 text-sm md:text-base">Zobacz jak wygląda generowanie kosztorysu z przedmiaru PDF — od wgrania pliku do pobrania ATH.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </>
    );
}
