import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import FeedbackWidget from '../components/FeedbackWidget'

const API = import.meta.env.VITE_API_URL ?? ''

function downloadB64(filename, b64content) {
    const bytes = Uint8Array.from(atob(b64content), c => c.charCodeAt(0))
    const blob = new Blob([bytes], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
}

export default function Dashboard() {
    const { user, loading: authLoading, getToken } = useAuth()
    const [file, setFile] = useState(null)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [dragging, setDragging] = useState(false)
    const inputRef = useRef(null)
    const [history, setHistory] = useState([])
    const [historyLoading, setHistoryLoading] = useState(false)
    const [showFeedback, setShowFeedback] = useState(false)

    const [params, setParams] = useState({
        nazwa: '',
        inwestor: '',
        wykonawca: 'KLONEKS',
        format: 'ath',
        stawka_rg: 35,
        kp: 70,
        zysk: 12,
        vat: 23,
    })

    function handleFileChange(f) {
        if (!f) return
        if (!f.name.toLowerCase().endsWith('.pdf')) {
            setError('Dozwolone tylko pliki PDF')
            return
        }
        setFile(f)
        setResult(null)
        setError(null)
    }

    function handleDrop(e) {
        e.preventDefault()
        setDragging(false)
        handleFileChange(e.dataTransfer.files?.[0])
    }

    async function handleGenerate() {
        if (!file) { setError('Najpierw wybierz plik PDF'); return }
        setLoading(true)
        setError(null)
        setResult(null)

        const form = new FormData()
        form.append('file', file)
        Object.entries(params).forEach(([k, v]) => form.append(k, v))

        try {
            const token = getToken()
            const headers = token ? { Authorization: `Bearer ${token}` } : {}
            const res = await fetch(`${API}/api/generate`, { method: 'POST', body: form, headers })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || 'Błąd serwera')
            setResult(data)
            setShowFeedback(true)
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    function downloadFile(info) {
        downloadB64(info.filename, info.content)
    }

    const setParam = (k, v) => setParams(p => ({ ...p, [k]: v }))

    useEffect(() => {
        if (!user) return
        setHistoryLoading(true)
        const token = getToken()
        fetch(`${API}/api/history`, {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(r => r.ok ? r.json() : [])
            .then(data => setHistory(Array.isArray(data) ? data : []))
            .catch(() => {})
            .finally(() => setHistoryLoading(false))
    }, [user, result])

    if (authLoading) return null

    if (!user) return (
        <div className="flex-1 flex flex-col items-center justify-center py-24 px-4 text-center">
            <span className="material-symbols-outlined text-6xl text-primary mb-6">lock</span>
            <h2 className="text-3xl font-black text-white mb-3">Wymagane logowanie</h2>
            <p className="text-slate-400 mb-8">Aby generować kosztorysy, musisz być zalogowany.</p>
            <div className="flex gap-4">
                <Link to="/login" className="h-12 px-8 rounded-lg bg-primary hover:bg-sky-400 text-white font-bold transition-colors flex items-center">Zaloguj się</Link>
                <Link to="/get-started" className="h-12 px-8 rounded-lg border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white font-bold transition-colors flex items-center">Utwórz konto</Link>
            </div>
        </div>
    )

    return (
        <div className="flex-1 w-full max-w-[1440px] mx-auto px-4 sm:px-8 py-6 sm:py-12 relative z-10 font-sans">
            {/* Nagłówek */}
            <div className="mb-8 sm:mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-3">
                    <h1 className="text-4xl md:text-6xl font-extrabold text-silver tracking-tight text-white">Konfiguracja Kosztorysu</h1>
                    <p className="text-slate-400 max-w-2xl text-lg leading-relaxed">Wgraj przedmiar PDF i wygeneruj kosztorys ATH (Norma PRO).</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4">
                    <button
                        onClick={() => { setFile(null); setResult(null); setError(null) }}
                        className="h-11 px-5 glass-panel text-slate-300 hover:text-white hover:bg-white/10 font-semibold text-sm rounded-xl transition-all flex items-center justify-center border border-slate-700 w-full sm:w-auto"
                    >
                        <span className="material-symbols-outlined mr-2 text-xl text-slate-500">refresh</span>
                        Resetuj
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
                {/* Lewa kolumna */}
                <div className="lg:col-span-8 flex flex-col gap-8">

                    {/* Strefa uploadu */}
                    <div className="flex-1 glass-panel rounded-2xl p-8 flex flex-col relative overflow-hidden group border border-slate-700">
                        <div className="absolute top-0 left-0 w-24 h-24 border-t-2 border-l-2 border-primary/20 rounded-tl-2xl"></div>
                        <div className="absolute bottom-0 right-0 w-24 h-24 border-b-2 border-r-2 border-primary/20 rounded-br-2xl"></div>

                        <div className="flex flex-col h-full justify-center items-center">
                            <div
                                className={`w-full flex-1 flex flex-col items-center justify-center border-2 border-dashed rounded-2xl bg-white/[0.02] p-12 transition-all glow-border cursor-pointer relative
                                    ${dragging ? 'border-primary/70 bg-primary/5' : file ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-white/5 hover:border-primary/50 group-hover:bg-white/[0.04]'}`}
                                onDragOver={e => { e.preventDefault(); setDragging(true) }}
                                onDragLeave={() => setDragging(false)}
                                onDrop={handleDrop}
                                onClick={() => inputRef.current?.click()}
                            >
                                <input
                                    ref={inputRef}
                                    className="hidden"
                                    type="file"
                                    accept=".pdf"
                                    onChange={e => handleFileChange(e.target.files?.[0])}
                                />

                                {file ? (
                                    <>
                                        <div className="size-28 rounded-full bg-emerald-500/10 flex items-center justify-center mb-8 border border-emerald-500/20">
                                            <span className="material-symbols-outlined text-emerald-400 text-6xl">task</span>
                                        </div>
                                        <h3 className="text-2xl font-bold text-white mb-2 text-center">{file.name}</h3>
                                        <p className="text-slate-400 text-center mb-6">{(file.size / 1024 / 1024).toFixed(1)} MB • Gotowy do generowania</p>
                                        <button
                                            className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
                                            onClick={e => { e.stopPropagation(); setFile(null); setResult(null) }}
                                        >
                                            Zmień plik
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <div className="size-28 rounded-full bg-primary/10 flex items-center justify-center mb-8 border border-primary/20 group-hover:scale-110 transition-transform duration-500">
                                            <span className="material-symbols-outlined text-primary text-6xl">cloud_upload</span>
                                        </div>
                                        <h3 className="text-3xl font-bold text-white mb-3 text-center tracking-tight">Przeciągnij i Upuść Przedmiar PDF</h3>
                                        <p className="text-slate-400 text-center max-w-md mb-10 leading-relaxed">
                                            Wgraj przedmiar robót budowlanych w formacie Norma PRO. Program rozpozna pozycje KNR i wyliczy kosztorys.
                                        </p>
                                        <button className="h-12 px-10 bg-slate-200 text-black font-extrabold rounded-xl hover:bg-white transition-colors flex items-center shadow-2xl">
                                            Przeglądaj Pliki
                                        </button>
                                        <div className="mt-10 flex gap-6 text-[11px] text-slate-400 font-mono uppercase tracking-widest">
                                            <span className="flex items-center"><span className="material-symbols-outlined text-sm mr-2 text-primary">check_circle</span>Tylko PDF</span>
                                            <span className="flex items-center"><span className="material-symbols-outlined text-sm mr-2 text-primary">check_circle</span>Max 50MB</span>
                                            <span className="flex items-center"><span className="material-symbols-outlined text-sm mr-2 text-primary">check_circle</span>Auto-OCR</span>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Wynik */}
                    {result && (
                        <div className="glass-panel rounded-2xl p-7 border border-emerald-500/30 bg-emerald-500/5">
                            <h3 className="text-xl font-bold text-white flex items-center gap-3 mb-6">
                                <span className="material-symbols-outlined text-emerald-400">check_circle</span>
                                Kosztorys wygenerowany pomyślnie
                            </h3>
                            <div className="flex flex-wrap gap-4">
                                {result.files?.ath && (
                                    <button
                                        onClick={() => downloadFile(result.files.ath)}
                                        className="h-12 px-8 bg-primary hover:bg-sky-400 text-white font-bold rounded-xl flex items-center gap-3 transition-all shadow-lg shadow-primary/20"
                                    >
                                        <span className="material-symbols-outlined">download</span>
                                        Pobierz ATH
                                        <span className="text-xs opacity-70">(Norma PRO)</span>
                                    </button>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Feedback po generowaniu */}
                    {showFeedback && result && (
                        <FeedbackWidget
                            context="after_generate"
                            onClose={() => setShowFeedback(false)}
                        />
                    )}

                    {/* Błąd */}
                    {error && (
                        <div className="glass-panel rounded-2xl p-5 border border-red-500/30 bg-red-500/5 flex items-start gap-4">
                            <span className="material-symbols-outlined text-red-400 mt-0.5">error</span>
                            <div>
                                <p className="text-red-400 font-bold">Błąd</p>
                                <p className="text-slate-400 text-sm mt-1">{error}</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Prawa kolumna — parametry */}
                <div className="lg:col-span-4 flex flex-col h-full">
                    <div className="bg-black/40 border border-slate-700 rounded-2xl p-7 shadow-2xl relative overflow-hidden h-full flex flex-col">
                        <div className="absolute -top-32 -right-32 w-80 h-80 bg-primary/10 rounded-full blur-[120px] pointer-events-none"></div>
                        <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-secondary/10 rounded-full blur-[120px] pointer-events-none"></div>

                        <div className="relative z-10 flex items-center justify-between mb-8 border-b border-slate-700/50 pb-6">
                            <h3 className="text-xl font-bold tracking-tight flex items-center gap-3 text-white">
                                <span className="material-symbols-outlined text-primary">tune</span>
                                Parametry
                            </h3>
                            <div className="flex items-center gap-2.5 text-[10px] font-bold text-primary tracking-widest border border-primary/20 px-3 py-1.5 rounded-full bg-primary/5">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                                </span>
                                AKTYWNY
                            </div>
                        </div>

                        <div className="space-y-5 flex-1 relative z-10">
                            <div>
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">Nazwa inwestycji</label>
                                <input
                                    type="text"
                                    value={params.nazwa}
                                    onChange={e => setParam('nazwa', e.target.value)}
                                    placeholder="(z nazwy pliku)"
                                    className="w-full bg-slate-800/80 border border-slate-700 text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-primary/60 placeholder:text-slate-600"
                                />
                            </div>

                            <div>
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">Inwestor</label>
                                <input
                                    type="text"
                                    value={params.inwestor}
                                    onChange={e => setParam('inwestor', e.target.value)}
                                    placeholder="Nazwa inwestora"
                                    className="w-full bg-slate-800/80 border border-slate-700 text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-primary/60 placeholder:text-slate-600"
                                />
                            </div>


                            <div className="grid grid-cols-2 gap-3">
                                {[
                                    { key: 'stawka_rg', label: 'Stawka RG (zł)', min: 1, max: 200 },
                                    { key: 'kp', label: 'Koszty pośr. %', min: 0, max: 100 },
                                    { key: 'zysk', label: 'Zysk %', min: 0, max: 100 },
                                    { key: 'vat', label: 'VAT %', min: 0, max: 100 },
                                ].map(({ key, label, min, max }) => (
                                    <div key={key}>
                                        <label className="text-xs font-bold text-slate-400 block mb-1">{label}</label>
                                        <input
                                            type="number"
                                            min={min}
                                            max={max}
                                            value={params[key]}
                                            onChange={e => setParam(key, parseFloat(e.target.value) || 0)}
                                            className="w-full bg-slate-800/80 border border-slate-700 text-white text-sm rounded-xl px-3 py-2 focus:outline-none focus:border-primary/60"
                                        />
                                    </div>
                                ))}
                            </div>

                            {/* Terminal status */}
                            <div className="bg-slate-900/80 rounded-xl p-4 font-mono text-[11px] leading-relaxed text-slate-400 border border-slate-700/50 min-h-[80px]">
                                {loading ? (
                                    <p className="animate-pulse text-primary">&gt; Przetwarzanie PDF... dopasowywanie nakładów KNR...</p>
                                ) : result ? (
                                    <>
                                        <p className="text-emerald-500">&gt; Generowanie zakończone</p>
                                        <p>&gt; Pliki gotowe do pobrania</p>
                                    </>
                                ) : error ? (
                                    <p className="text-red-400">&gt; BŁĄD: {error.slice(0, 100)}</p>
                                ) : file ? (
                                    <p>&gt; Plik: {file.name.slice(0, 40)}</p>
                                ) : (
                                    <p className="animate-pulse">&gt; Czekam na plik PDF_</p>
                                )}
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-slate-700/50 relative z-10">
                            <button
                                onClick={handleGenerate}
                                disabled={loading || !file}
                                className={`w-full h-14 font-extrabold rounded-xl shadow-xl flex items-center justify-center gap-3 group transition-all transform
                                    ${loading || !file
                                        ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                        : 'bg-primary hover:bg-sky-400 text-white shadow-primary/20 hover:-translate-y-0.5'}`}
                            >
                                {loading ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                                        </svg>
                                        Generowanie...
                                    </>
                                ) : (
                                    <>
                                        <span className="text-base">Generuj Kosztorys</span>
                                        <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Historia kosztorysów */}
            {user && (
                <div className="mt-12">
                    <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                        <span className="material-symbols-outlined text-primary">history</span>
                        Historia Kosztorysów
                    </h2>
                    {historyLoading ? (
                        <div className="glass-panel rounded-2xl p-8 border border-slate-700 flex items-center justify-center">
                            <svg className="animate-spin h-5 w-5 text-primary mr-3" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                            </svg>
                            <span className="text-slate-400">Ładowanie historii...</span>
                        </div>
                    ) : history.length === 0 ? (
                        <div className="glass-panel rounded-2xl p-8 border border-slate-700 text-center text-slate-500">
                            Brak poprzednich kosztorysów. Wygeneruj pierwszy!
                        </div>
                    ) : (
                        <div className="glass-panel rounded-2xl border border-slate-700 overflow-hidden">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                                        <th className="text-left px-6 py-4">Nazwa</th>
                                        <th className="text-left px-6 py-4 hidden md:table-cell">Data</th>
                                        <th className="text-left px-6 py-4 hidden sm:table-cell">Pozycji</th>
                                        <th className="text-right px-6 py-4">Pobierz</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.map((item, i) => (
                                        <tr key={item.id || i} className="border-b border-slate-800 hover:bg-white/[0.02] transition-colors">
                                            <td className="px-6 py-4 text-white font-medium">{item.name || item.filename || `Kosztorys ${i + 1}`}</td>
                                            <td className="px-6 py-4 text-slate-400 hidden md:table-cell">
                                                {item.created_at ? new Date(item.created_at).toLocaleDateString('pl-PL') : '—'}
                                            </td>
                                            <td className="px-6 py-4 text-slate-400 hidden sm:table-cell">{item.positions_count ?? '—'}</td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    {item.ath_url && (
                                                        <a href={item.ath_url} className="text-xs font-bold text-primary hover:text-sky-400 transition-colors flex items-center gap-1">
                                                            <span className="material-symbols-outlined text-sm">download</span>ATH
                                                        </a>
                                                    )}
                                                    {!item.ath_url && <span className="text-slate-600 text-xs">brak pliku</span>}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
