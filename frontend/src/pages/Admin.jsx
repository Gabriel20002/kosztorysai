import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL ?? ''

function authHeaders(token) {
    return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
}

export default function Admin() {
    const { user, loading, getToken } = useAuth()
    const navigate = useNavigate()

    const [users, setUsers] = useState([])
    const [feedback, setFeedback] = useState([])
    const [tab, setTab] = useState('users')
    const [loadingData, setLoadingData] = useState(true)

    useEffect(() => {
        if (loading) return
        if (!user || !user.is_admin) { navigate('/'); return }
        loadAll()
    }, [user, loading])

    async function loadAll() {
        setLoadingData(true)
        const token = getToken()
        try {
            const [u, f] = await Promise.all([
                fetch(`${API}/api/admin/users`, { headers: authHeaders(token) }).then(r => r.json()),
                fetch(`${API}/api/admin/feedback`, { headers: authHeaders(token) }).then(r => r.json()),
            ])
            setUsers(Array.isArray(u) ? u : [])
            setFeedback(Array.isArray(f) ? f : [])
        } catch (e) {
            console.error(e)
        } finally {
            setLoadingData(false)
        }
    }

    async function toggleGenerate(userId, current) {
        const token = getToken()
        const res = await fetch(`${API}/api/admin/users/${userId}`, {
            method: 'PATCH',
            headers: authHeaders(token),
            body: JSON.stringify({ can_generate: !current }),
        })
        if (res.ok) {
            const updated = await res.json()
            setUsers(prev => prev.map(u => u.id === userId ? updated : u))
        }
    }

    if (loading || loadingData) return (
        <div className="flex-1 flex items-center justify-center">
            <svg className="animate-spin h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
        </div>
    )

    if (!user?.is_admin) return null

    const avgRating = feedback.length
        ? (feedback.reduce((s, f) => s + f.rating, 0) / feedback.length).toFixed(1)
        : '—'

    return (
        <div className="flex-1 w-full max-w-[1200px] mx-auto px-4 sm:px-8 py-8">
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-black text-white">Panel Administratora</h1>
                    <p className="text-slate-400 mt-1">Zarządzaj użytkownikami i przeglądaj opinie</p>
                </div>
                <button onClick={loadAll} className="h-10 px-4 rounded-xl border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 transition-all flex items-center gap-2 text-sm font-medium">
                    <span className="material-symbols-outlined text-base">refresh</span>
                    Odśwież
                </button>
            </div>

            {/* Statystyki */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                {[
                    { label: 'Użytkownicy', value: users.length, icon: 'group' },
                    { label: 'Aktywni (mogą generować)', value: users.filter(u => u.can_generate).length, icon: 'check_circle' },
                    { label: 'Opinie', value: feedback.length, icon: 'rate_review' },
                    { label: 'Śr. ocena', value: avgRating, icon: 'star' },
                ].map(s => (
                    <div key={s.label} className="glass-panel rounded-2xl p-5 border border-slate-700">
                        <span className="material-symbols-outlined text-primary text-2xl mb-2 block">{s.icon}</span>
                        <div className="text-2xl font-black text-white">{s.value}</div>
                        <div className="text-xs text-slate-400 mt-1">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Zakładki */}
            <div className="flex gap-2 mb-6">
                {[
                    { id: 'users', label: 'Użytkownicy', icon: 'group' },
                    { id: 'feedback', label: 'Opinie', icon: 'rate_review' },
                ].map(t => (
                    <button
                        key={t.id}
                        onClick={() => setTab(t.id)}
                        className={`h-10 px-5 rounded-xl text-sm font-bold transition-all flex items-center gap-2
                            ${tab === t.id ? 'bg-primary text-white' : 'border border-slate-700 text-slate-400 hover:text-white'}`}
                    >
                        <span className="material-symbols-outlined text-base">{t.icon}</span>
                        {t.label}
                    </button>
                ))}
            </div>

            {/* Tabela użytkowników */}
            {tab === 'users' && (
                <div className="glass-panel rounded-2xl border border-slate-700 overflow-hidden">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                                <th className="text-left px-6 py-4">Użytkownik</th>
                                <th className="text-left px-6 py-4 hidden md:table-cell">Email</th>
                                <th className="text-left px-6 py-4 hidden sm:table-cell">Dołączył</th>
                                <th className="text-center px-6 py-4">Może generować</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id} className="border-b border-slate-800 hover:bg-white/[0.02] transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs font-bold">
                                                {(u.name || u.email)[0].toUpperCase()}
                                            </div>
                                            <span className="text-white font-medium">{u.name}</span>
                                            {u.is_admin && (
                                                <span className="text-[10px] font-bold bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full border border-yellow-500/30">ADMIN</span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-slate-400 hidden md:table-cell">{u.email}</td>
                                    <td className="px-6 py-4 text-slate-400 hidden sm:table-cell text-xs">
                                        {u.created_at ? new Date(u.created_at).toLocaleDateString('pl-PL') : '—'}
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <button
                                            onClick={() => !u.is_admin && toggleGenerate(u.id, u.can_generate)}
                                            disabled={u.is_admin}
                                            title={u.is_admin ? 'Admin ma zawsze dostęp' : (u.can_generate ? 'Kliknij aby zablokować' : 'Kliknij aby odblokować')}
                                            className={`relative inline-flex items-center h-6 w-11 rounded-full transition-colors focus:outline-none
                                                ${u.can_generate || u.is_admin ? 'bg-primary' : 'bg-slate-700'}
                                                ${u.is_admin ? 'opacity-50 cursor-default' : 'cursor-pointer'}`}
                                        >
                                            <span className={`inline-block w-4 h-4 rounded-full bg-white shadow transform transition-transform
                                                ${u.can_generate || u.is_admin ? 'translate-x-6' : 'translate-x-1'}`}
                                            />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {users.length === 0 && (
                        <div className="p-12 text-center text-slate-500">Brak użytkowników</div>
                    )}
                </div>
            )}

            {/* Tabela opinii */}
            {tab === 'feedback' && (
                <div className="space-y-4">
                    {feedback.length === 0 && (
                        <div className="glass-panel rounded-2xl p-12 border border-slate-700 text-center text-slate-500">
                            Brak opinii
                        </div>
                    )}
                    {feedback.map(f => (
                        <div key={f.id} className="glass-panel rounded-2xl p-5 border border-slate-700">
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    {[1,2,3,4,5].map(s => (
                                        <span key={s} className={`material-symbols-outlined text-lg ${s <= f.rating ? 'text-yellow-400' : 'text-slate-700'}`}>star</span>
                                    ))}
                                    <span className="text-slate-400 text-sm font-medium">{f.rating}/5</span>
                                </div>
                                <div className="text-xs text-slate-500 shrink-0">
                                    {f.created_at ? new Date(f.created_at).toLocaleString('pl-PL') : '—'}
                                </div>
                            </div>
                            {f.message && (
                                <p className="mt-3 text-slate-300 text-sm leading-relaxed">{f.message}</p>
                            )}
                            <div className="mt-3 flex gap-4 text-xs text-slate-600">
                                <span>ID: {f.id}</span>
                                <span>User: {f.user_id ?? 'gość'}</span>
                                <span>Kontekst: {f.context}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
