import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const API = import.meta.env.VITE_API_URL ?? ''

const CATEGORIES = [
    { value: 'opinia', label: 'Opinia o produkcie', icon: 'rate_review' },
    { value: 'zapytanie', label: 'Zapytanie / pytanie', icon: 'help' },
    { value: 'blad', label: 'Błąd / problem techniczny', icon: 'bug_report' },
    { value: 'inne', label: 'Inne', icon: 'chat' },
]

export default function Contact() {
    const { user, loading: authLoading } = useAuth()
    const [form, setForm] = useState({
        email: user?.email ?? '',
        category: 'zapytanie',
        message: '',
    })
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sent, setSent] = useState(false)

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

    async function handleSubmit(e) {
        e.preventDefault()
        if (!form.message.trim()) { setError('Wpisz treść wiadomości'); return }
        setLoading(true)
        setError(null)
        try {
            const res = await fetch(`${API}/api/contact`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || 'Błąd serwera')
            setSent(true)
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    if (authLoading) return null
    if (!user) return <Navigate to="/login" replace />

    if (sent) return (
        <div className="flex-1 flex flex-col items-center justify-center py-24 px-4 text-center">
            <div className="size-24 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-8">
                <span className="material-symbols-outlined text-5xl text-emerald-400">check_circle</span>
            </div>
            <h2 className="text-3xl font-black text-white mb-4">Wiadomość wysłana</h2>
            <p className="text-slate-400 mb-8">Dziękujemy za kontakt. Odpowiemy na podany adres e-mail.</p>
            <button
                onClick={() => { setSent(false); setForm(f => ({ ...f, message: '' })) }}
                className="h-12 px-8 rounded-lg border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white font-bold transition-colors"
            >
                Wyślij kolejną wiadomość
            </button>
        </div>
    )

    return (
        <div className="w-full max-w-xl mx-auto my-16 px-4 md:px-6 relative z-10">
            <div className="mb-8 text-center">
                <h1 className="text-3xl font-black text-white mb-2">Kontakt</h1>
                <p className="text-slate-400">Masz pytanie, problem lub opinię? Napisz do nas.</p>
            </div>

            <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-800/50 shadow-2xl">
                <form className="space-y-5" onSubmit={handleSubmit}>

                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Kategoria</label>
                        <div className="grid grid-cols-2 gap-2">
                            {CATEGORIES.map(c => (
                                <button
                                    key={c.value}
                                    type="button"
                                    onClick={() => set('category', c.value)}
                                    className={`flex items-center gap-2 p-3 rounded-xl border text-sm font-medium transition-all text-left
                                        ${form.category === c.value
                                            ? 'border-primary bg-primary/10 text-white'
                                            : 'border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white'}`}
                                >
                                    <span className={`material-symbols-outlined text-base ${form.category === c.value ? 'text-primary' : 'text-slate-500'}`}>{c.icon}</span>
                                    {c.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Twój e-mail</label>
                        <input
                            type="email"
                            required
                            value={form.email}
                            onChange={e => set('email', e.target.value)}
                            className="w-full h-12 px-4 rounded-lg bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            placeholder="jan@firma.pl"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Wiadomość</label>
                        <textarea
                            required
                            rows={5}
                            value={form.message}
                            onChange={e => set('message', e.target.value)}
                            className="w-full px-4 py-3 rounded-lg bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none"
                            placeholder="Opisz swoje pytanie, problem lub opinię..."
                        />
                        <p className="text-xs text-slate-600 mt-1 text-right">{form.message.length}/5000</p>
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                            <span className="material-symbols-outlined text-base">error</span>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full h-12 rounded-lg bg-primary hover:bg-sky-400 text-white font-bold transition-colors shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>Wysyłanie...</>
                        ) : (
                            <><span className="material-symbols-outlined text-base">send</span>Wyślij wiadomość</>
                        )}
                    </button>
                </form>
            </div>
        </div>
    )
}
