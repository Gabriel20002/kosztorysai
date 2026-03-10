import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const API = import.meta.env.VITE_API_URL ?? ''

export default function FeedbackWidget({ context = 'general', onClose }) {
    const { getToken } = useAuth()
    const [rating, setRating] = useState(0)
    const [hovered, setHovered] = useState(0)
    const [message, setMessage] = useState('')
    const [sent, setSent] = useState(false)
    const [sending, setSending] = useState(false)

    async function handleSubmit() {
        if (!rating) return
        setSending(true)
        try {
            const token = getToken()
            const headers = { 'Content-Type': 'application/json' }
            if (token) headers['Authorization'] = `Bearer ${token}`
            await fetch(`${API}/api/feedback`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ rating, message, context }),
            })
            setSent(true)
        } catch {
            // cicha porażka — nie blokujemy UX
        } finally {
            setSending(false)
        }
    }

    if (sent) return (
        <div className="glass-panel rounded-2xl p-6 border border-emerald-500/30 bg-emerald-500/5 flex items-center gap-4">
            <span className="material-symbols-outlined text-emerald-400 text-3xl">check_circle</span>
            <div>
                <p className="text-white font-bold">Dziękujemy za opinię!</p>
                <p className="text-slate-400 text-sm">Twoja ocena pomaga nam ulepszać narzędzie.</p>
            </div>
            {onClose && (
                <button onClick={onClose} className="ml-auto text-slate-500 hover:text-white transition-colors">
                    <span className="material-symbols-outlined">close</span>
                </button>
            )}
        </div>
    )

    const labels = ['', 'Słaba', 'Przeciętna', 'Dobra', 'Bardzo dobra', 'Doskonała']

    return (
        <div className="glass-panel rounded-2xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-bold flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">rate_review</span>
                    Jak oceniasz wynik?
                </h3>
                {onClose && (
                    <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                )}
            </div>

            {/* Gwiazdki */}
            <div className="flex items-center gap-2 mb-2">
                {[1, 2, 3, 4, 5].map(s => (
                    <button
                        key={s}
                        onMouseEnter={() => setHovered(s)}
                        onMouseLeave={() => setHovered(0)}
                        onClick={() => setRating(s)}
                        className="transition-transform hover:scale-125"
                    >
                        <span className={`material-symbols-outlined text-3xl transition-colors ${
                            s <= (hovered || rating) ? 'text-yellow-400' : 'text-slate-600'
                        }`}>star</span>
                    </button>
                ))}
                {(hovered || rating) > 0 && (
                    <span className="text-slate-400 text-sm ml-1">{labels[hovered || rating]}</span>
                )}
            </div>

            {/* Opcjonalny komentarz */}
            <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                placeholder="Opcjonalnie — co można poprawić? (dowolny komentarz)"
                rows={2}
                className="w-full mt-3 bg-slate-800/80 border border-slate-700 text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-primary/60 placeholder:text-slate-600 resize-none"
            />

            <button
                onClick={handleSubmit}
                disabled={!rating || sending}
                className={`mt-4 h-10 px-6 rounded-xl text-sm font-bold transition-all flex items-center gap-2
                    ${rating && !sending
                        ? 'bg-primary hover:bg-sky-400 text-white'
                        : 'bg-slate-700 text-slate-500 cursor-not-allowed'}`}
            >
                {sending ? (
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                ) : (
                    <span className="material-symbols-outlined text-base">send</span>
                )}
                Wyślij opinię
            </button>
        </div>
    )
}
