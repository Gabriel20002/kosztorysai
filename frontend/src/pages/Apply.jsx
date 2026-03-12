import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const API = import.meta.env.VITE_API_URL ?? ''

const BENEFITS = [
    { icon: 'rocket_launch', text: 'Bezpłatny dostęp przez cały okres beta' },
    { icon: 'workspace_premium', text: 'Dostęp do pełnej wersji produktu po zakończeniu beta' },
    { icon: 'sell', text: 'Dożywotni rabat dla beta testerów — tylko dla wybranych' },
    { icon: 'rate_review', text: 'Bezpośredni wpływ na kierunek rozwoju produktu' },
    { icon: 'support_agent', text: 'Priorytetowe wsparcie techniczne' },
]

const STANOWISKA = [
    'Kosztorysant',
    'Kierownik budowy',
    'Inwestor',
    'Deweloper',
    'Projektant / Architekt',
    'Inne',
]

const DOSWIADCZENIA = [
    'Brak doświadczenia',
    'Do 1 roku',
    '1–5 lat',
    'Ponad 5 lat',
]

export default function Apply() {
    const { user, loading: authLoading, getToken } = useAuth()
    const [submitted, setSubmitted] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [form, setForm] = useState({
        firma: '',
        stanowisko: STANOWISKA[0],
        doswiadczenie: DOSWIADCZENIA[0],
        cel: '',
    })

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

    // Ostrzeżenie przy zamknięciu przeglądarki
    useEffect(() => {
        if (submitted) return
        const handler = e => { e.preventDefault(); e.returnValue = '' }
        window.addEventListener('beforeunload', handler)
        return () => window.removeEventListener('beforeunload', handler)
    }, [submitted])

    async function handleSubmit(e) {
        e.preventDefault()
        if (!form.firma.trim()) { setError('Podaj nazwę firmy / organizacji'); return }
        if (!form.cel.trim()) { setError('Opisz cel użycia'); return }
        setLoading(true)
        setError(null)
        try {
            const token = getToken()
            const res = await fetch(`${API}/api/beta/apply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                body: JSON.stringify(form),
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || 'Błąd serwera')
            setSubmitted(true)
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    if (authLoading) return null
    if (!user) return <Navigate to="/login" replace />
    if (user.can_generate) return <Navigate to="/dashboard" replace />

    // Już złożył wniosek — pokaż ekran oczekiwania
    if (user.has_applied || submitted) return (
        <div className="flex-1 flex flex-col items-center justify-center py-24 px-4 text-center max-w-lg mx-auto">
            <div className="size-24 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-8 pop-in">
                <span className="material-symbols-outlined text-5xl text-primary">hourglass_top</span>
            </div>
            <h2 className="text-3xl font-black text-white mb-4 fade-in-up">Wniosek złożony</h2>
            <p className="text-slate-400 mb-3 leading-relaxed fade-in-up delay-1">
                Twój wniosek o dostęp do bety został przyjęty. Rozpatrzymy go i aktywujemy konto — zazwyczaj w ciągu 24 godzin.
            </p>
            <p className="text-slate-500 text-sm fade-in-up delay-2">
                Otrzymasz powiadomienie e-mail gdy konto zostanie aktywowane.
            </p>
        </div>
    )

    return (
        <div className="w-full max-w-[1100px] mx-auto px-4 md:px-6 py-12 relative z-10">

<div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-start">

                {/* Lewa kolumna — korzyści */}
                <div className="fade-in-up">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 mb-6">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                        <span className="text-xs font-bold text-primary uppercase tracking-wider">Program Beta</span>
                    </div>
                    <h1 className="text-4xl font-black text-white mb-4 leading-tight">
                        Złóż wniosek<br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">o dostęp beta</span>
                    </h1>
                    <p className="text-slate-400 mb-8 leading-relaxed">
                        Kosztorysy AI jest w fazie beta i dostęp przyznajemy ręcznie. Wypełnij krótki formularz — aktywujemy Twoje konto w ciągu 24 godzin.
                    </p>

                    <div className="space-y-4">
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Co zyskujesz jako beta tester:</p>
                        {BENEFITS.map((b, i) => (
                            <div key={i} className={`flex items-center gap-4 fade-in-up delay-${i + 1}`}>
                                <div className="size-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                                    <span className="material-symbols-outlined text-primary text-base">{b.icon}</span>
                                </div>
                                <p className="text-slate-300 text-sm">{b.text}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Prawa kolumna — formularz */}
                <div className="glass-card rounded-2xl p-7 border border-slate-700 shadow-2xl fade-in-up delay-2">
                    <h2 className="text-xl font-bold text-white mb-6">Dane wniosku</h2>
                    <form className="space-y-5" onSubmit={handleSubmit}>

                        <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Firma / Organizacja</label>
                            <input
                                type="text"
                                required
                                value={form.firma}
                                onChange={e => set('firma', e.target.value)}
                                placeholder="Nazwa firmy lub organizacji"
                                className="w-full h-12 px-4 rounded-xl bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Stanowisko</label>
                            <select
                                value={form.stanowisko}
                                onChange={e => set('stanowisko', e.target.value)}
                                className="w-full h-12 px-4 rounded-xl bg-slate-900/50 border border-slate-700 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            >
                                {STANOWISKA.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Doświadczenie z kosztorysowaniem</label>
                            <select
                                value={form.doswiadczenie}
                                onChange={e => set('doswiadczenie', e.target.value)}
                                className="w-full h-12 px-4 rounded-xl bg-slate-900/50 border border-slate-700 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            >
                                {DOSWIADCZENIA.map(d => <option key={d} value={d}>{d}</option>)}
                            </select>
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Cel użycia</label>
                            <textarea
                                required
                                rows={4}
                                value={form.cel}
                                onChange={e => set('cel', e.target.value)}
                                placeholder="W jaki sposób planujesz używać Kosztorysy AI? Jakie problemy ma rozwiązać?"
                                className="w-full px-4 py-3 rounded-xl bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none"
                            />
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                                <span className="material-symbols-outlined text-base">error</span>
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full h-13 py-3.5 rounded-xl bg-primary hover:bg-sky-400 text-white font-extrabold transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 btn-press"
                        >
                            {loading ? (
                                <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>Wysyłanie...</>
                            ) : (
                                <><span className="material-symbols-outlined text-base">send</span>Złóż wniosek o dostęp</>
                            )}
                        </button>

                        <p className="text-xs text-slate-600 text-center">
                            Aktywacja zazwyczaj w ciągu 24 godzin · Powiadomienie e-mail
                        </p>
                    </form>
                </div>
            </div>
        </div>
    )
}
