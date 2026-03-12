import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
    const { login } = useAuth()
    const navigate = useNavigate()
    const [form, setForm] = useState({ email: '', password: '', remember: false })
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        setError(null)
        try {
            await login(form.email, form.password)
            navigate('/dashboard')
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="w-full max-w-md mx-auto my-16 md:my-24 px-4 md:px-6 relative z-10">
            <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-800/50 shadow-2xl relative mt-10 md:mt-0">
                <div className="absolute top-[-50px] left-1/2 -translate-x-1/2 size-20 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center shadow-lg shadow-black/50">
                    <span className="material-symbols-outlined text-primary text-4xl">architecture</span>
                </div>

                <div className="text-center mt-12 mb-8">
                    <h2 className="text-2xl font-black text-white tracking-tight">Witaj Ponownie</h2>
                    <p className="text-slate-400 text-sm mt-2">Zaloguj się do Kosztorysy AI, aby kontynuować kosztorysowanie</p>
                </div>

                <form className="space-y-4" onSubmit={handleSubmit}>
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Adres Email</label>
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
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Hasło</label>
                        <input
                            type="password"
                            required
                            value={form.password}
                            onChange={e => set('password', e.target.value)}
                            className="w-full h-12 px-4 rounded-lg bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            placeholder="••••••••"
                        />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={form.remember}
                                onChange={e => set('remember', e.target.checked)}
                                className="rounded bg-slate-900 border-slate-700 text-primary w-4 h-4"
                            />
                            <span className="text-slate-400">Zapamiętaj mnie</span>
                        </label>
                        <a href="#" className="text-primary hover:text-sky-400 font-medium transition-colors">Zapomniałeś hasła?</a>
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
                        className="w-full h-12 mt-2 rounded-lg bg-primary text-white font-bold hover:bg-sky-400 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>Logowanie...</>
                        ) : 'Zaloguj się'}
                    </button>
                </form>

                <div className="mt-8 text-center text-sm text-slate-400">
                    Nie masz konta?{' '}
                    <Link to="/register" className="text-white hover:text-primary font-bold transition-colors">Utwórz konto za darmo</Link>
                </div>
            </div>
        </div>
    )
}
