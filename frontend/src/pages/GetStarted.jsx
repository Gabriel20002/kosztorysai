import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function GetStarted() {
    const { register } = useAuth();
    const navigate = useNavigate();
    const [form, setForm] = useState({ firstName: '', lastName: '', email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

    async function handleSubmit(e) {
        e.preventDefault();
        if (form.password.length < 8) { setError('Hasło musi mieć min. 8 znaków'); return; }
        setLoading(true);
        setError(null);
        try {
            await register(form.email, form.password, `${form.firstName} ${form.lastName}`.trim());
            navigate('/dashboard');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="w-full flex-1 flex flex-col items-center justify-center py-12 md:py-20 px-4 md:px-6 relative">
            {/* Background elements */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[100px] pointer-events-none"></div>

            <div className="max-w-[1000px] w-full relative z-10 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                {/* Left side: Intro & value prop */}
                <div className="text-center md:text-left">
                    <h1 className="text-3xl md:text-5xl font-black text-white mb-6">
                        Gotowy na <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">szybsze kosztorysy</span>?
                    </h1>
                    <p className="text-slate-400 text-base md:text-lg mb-8 leading-relaxed">
                        Załóż konto już dziś, aby uzyskać dostęp do najpotężniejszego silnika AI w branży. Przyspiesz swój przepływ pracy, zwiększ dokładność i wygrywaj więcej przetargów.
                    </p>

                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-white">
                            <span className="material-symbols-outlined text-emerald-400">check_circle</span>
                            <span>14-dniowy, w pełni darmowy okres próbny na wszystkie plany</span>
                        </div>
                        <div className="flex items-center gap-3 text-white">
                            <span className="material-symbols-outlined text-emerald-400">check_circle</span>
                            <span>Możliwość anulowania w dowolnym momencie, bez zbędnych pytań</span>
                        </div>
                        <div className="flex items-center gap-3 text-white">
                            <span className="material-symbols-outlined text-emerald-400">check_circle</span>
                            <span>Bezpieczeństwo i szyfrowanie danych projektowych na poziomie bankowym</span>
                        </div>
                    </div>
                </div>

                {/* Right side: Onboarding Form Card */}
                <div className="glass-card p-6 md:p-8 rounded-2xl border border-slate-700/50 shadow-2xl relative">
                    <div className="absolute -inset-[1px] rounded-2xl bg-gradient-to-br from-primary/30 to-secondary/30 z-[-1] blur-sm"></div>

                    <h2 className="text-2xl font-bold text-white mb-6 text-center">Stwórz Konto</h2>

                    <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="flex-1">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 block">Imię</label>
                                <input type="text" required value={form.firstName} onChange={e => set('firstName', e.target.value)} className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 sm:py-2 text-white focus:outline-none focus:border-primary transition-colors" placeholder="Jan" />
                            </div>
                            <div className="flex-1">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 block">Nazwisko</label>
                                <input type="text" required value={form.lastName} onChange={e => set('lastName', e.target.value)} className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 sm:py-2 text-white focus:outline-none focus:border-primary transition-colors" placeholder="Kowalski" />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 block">Firmowy Adres Email</label>
                            <input type="email" required value={form.email} onChange={e => set('email', e.target.value)} className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 sm:py-2 text-white focus:outline-none focus:border-primary transition-colors" placeholder="jan@firma.pl" />
                        </div>

                        <div>
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 block">Hasło</label>
                            <input type="password" required value={form.password} onChange={e => set('password', e.target.value)} className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-3 sm:py-2 text-white focus:outline-none focus:border-primary transition-colors" placeholder="Min. 8 znaków" />
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                                <span className="material-symbols-outlined text-base">error</span>
                                {error}
                            </div>
                        )}

                        <button type="submit" disabled={loading} className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg mt-4 transition-all shadow-[0_0_15px_rgba(19,146,236,0.3)] hover:shadow-[0_0_20px_rgba(19,146,236,0.5)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                            {loading ? (
                                <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>Tworzenie konta...</>
                            ) : 'Zarejestruj się'}
                        </button>

                        <p className="text-slate-500 text-sm md:-mt-1 md:text-center mt-2">
                            Masz już konto? <Link to="/login" className="text-primary hover:text-white transition-colors">Zaloguj się</Link>
                        </p>
                    </form>
                </div>
            </div>
        </div>
    );
}
