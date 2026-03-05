import { useState, useRef } from 'react'

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

export default function AddProgram() {
    const [file, setFile] = useState(null)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [dragging, setDragging] = useState(false)
    const inputRef = useRef(null)

    const [params, setParams] = useState({
        nazwa: '',
        inwestor: '',
        wykonawca: '',
        format: 'both',
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
            const res = await fetch(`${API}/api/generate`, { method: 'POST', body: form })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || 'Błąd serwera')
            setResult(data)
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    const setParam = (k, v) => setParams(p => ({ ...p, [k]: v }))

    return (
        <div className="flex-1 w-full max-w-[1440px] mx-auto px-4 sm:px-8 py-6 sm:py-12 relative z-10 font-sans">
            {/* Nagłówek */}
            <div className="mb-8 sm:mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-3">
                    <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white">Generator Kosztorysu</h1>
                    <p className="text-slate-400 max-w-2xl text-lg leading-relaxed">Wgraj przedmiar PDF i wygeneruj kosztorys ATH (Norma PRO) oraz PDF.</p>
                </div>
                <button
                    onClick={() => { setFile(null); setResult(null); setError(null) }}
                    className="h-11 px-5 glass-panel text-slate-300 hover:text-white hover:bg-white/10 font-semibold text-sm rounded-xl transition-all flex items-center justify-center border border-slate-700 w-full sm:w-auto"
                >
                    <span className="material-symbols-outlined mr-2 text-xl text-slate-500">refresh</span>
                    Resetuj
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
                {/* Lewa kolumna — upload */}
                <div className="lg:col-span-8 flex flex-col gap-8">
                    <div className="flex-1 glass-panel rounded-2xl p-8 flex flex-col relative overflow-hidden group border border-slate-700">
                        <div className="absolute top-0 left-0 w-24 h-24 border-t-2 border-l-2 border-primary/20 rounded-tl-2xl"></div>
                        <div className="absolute bottom-0 right-0 w-24 h-24 border-b-2 border-r-2 border-primary/20 rounded-br-2xl"></div>

                        <div
                            className={`w-full flex-1 flex flex-col items-center justify-center border-2 border-dashed rounded-2xl bg-white/[0.02] p-12 transition-all cursor-pointer relative
                                ${dragging ? 'border-primary/70 bg-primary/5' : file ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-white/5 hover:border-primary/50 group-hover:bg-white/[0.04]'}`}
                            onDragOver={e => { e.preventDefault(); setDragging(true) }}
                            onDragLeave={() => setDragging(false)}
                            onDrop={handleDrop}
                            onClick={() => inputRef.current?.click()}
                        >
                            <input ref={inputRef} className="hidden" type="file" accept=".pdf" onChange={e => handleFileChange(e.target.files?.[0])} />

                            {file ? (
                                <>
                                    <div className="size-28 rounded-full bg-emerald-500/10 flex items-center justify-center mb-8 border border-emerald-500/20">
                                        <span className="material-symbols-outlined text-emerald-400 text-6xl">task</span>
                                    </div>
                                    <h3 className="text-2xl font-bold text-white mb-2 text-center">{file.name}</h3>
                                    <p className="text-slate-400 text-center mb-6">{(file.size / 1024 / 1024).toFixed(1)} MB • Gotowy do generowania</p>
                                    <button className="text-sm text-slate-500 hover:text-slate-300 transition-colors" onClick={e => { e.stopPropagation(); setFile(null); setResult(null) }}>
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
                                        <span className="flex items-center"><span className="material-symbols-outlined text-sm mr-2 text-primary">check_circle</span>Format Norma PRO</span>
                                    </div>
                                </>
                            )}
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
                                    <button onClick={() => downloadB64(result.files.ath.filename, result.files.ath.content)}
                                        className="h-12 px-8 bg-primary hover:bg-sky-400 text-white font-bold rounded-xl flex items-center gap-3 transition-all shadow-lg shadow-primary/20">
                                        <span className="material-symbols-outlined">download</span>
                                        Pobierz ATH <span className="text-xs opacity-70">(Norma PRO)</span>
                                    </button>
                                )}
                                {result.files?.pdf && (
                                    <button onClick={() => downloadB64(result.files.pdf.filename, result.files.pdf.content)}
                                        className="h-12 px-8 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-xl flex items-center gap-3 transition-all border border-slate-600">
                                        <span className="material-symbols-outlined">picture_as_pdf</span>
                                        Pobierz PDF
                                    </button>
                                )}
                            </div>
                        </div>
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
                            {[
                                { key: 'nazwa', label: 'Nazwa inwestycji', placeholder: '(z nazwy pliku)', type: 'text' },
                                { key: 'inwestor', label: 'Inwestor', placeholder: 'Nazwa inwestora', type: 'text' },
                                { key: 'wykonawca', label: 'Wykonawca', placeholder: 'Nazwa firmy', type: 'text' },
                            ].map(({ key, label, placeholder, type }) => (
                                <div key={key}>
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">{label}</label>
                                    <input type={type} value={params[key]} onChange={e => setParam(key, e.target.value)} placeholder={placeholder}
                                        className="w-full bg-slate-800/80 border border-slate-700 text-white text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-primary/60 placeholder:text-slate-600" />
                                </div>
                            ))}

                            <div>
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">Format wyjścia</label>
                                <div className="flex gap-2">
                                    {['both', 'ath', 'pdf'].map(f => (
                                        <button key={f} onClick={() => setParam('format', f)}
                                            className={`flex-1 py-2 rounded-xl text-xs font-bold uppercase tracking-wider border transition-all
                                                ${params.format === f ? 'bg-primary/20 border-primary/50 text-primary' : 'border-slate-700 text-slate-500 hover:text-slate-300'}`}>
                                            {f === 'both' ? 'ATH+PDF' : f.toUpperCase()}
                                        </button>
                                    ))}
                                </div>
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
                                        <input type="number" min={min} max={max} value={params[key]}
                                            onChange={e => setParam(key, parseFloat(e.target.value) || 0)}
                                            className="w-full bg-slate-800/80 border border-slate-700 text-white text-sm rounded-xl px-3 py-2 focus:outline-none focus:border-primary/60" />
                                    </div>
                                ))}
                            </div>

                            <div className="bg-slate-900/80 rounded-xl p-4 font-mono text-[11px] leading-relaxed text-slate-400 border border-slate-700/50 min-h-[80px]">
                                {loading ? (
                                    <p className="animate-pulse text-primary">&gt; Przetwarzanie PDF... dopasowywanie nakładów KNR...</p>
                                ) : result ? (
                                    <><p className="text-emerald-500">&gt; Generowanie zakończone</p><p>&gt; Pliki gotowe do pobrania</p></>
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
                            <button onClick={handleGenerate} disabled={loading || !file}
                                className={`w-full h-14 font-extrabold rounded-xl shadow-xl flex items-center justify-center gap-3 group transition-all transform
                                    ${loading || !file ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-primary hover:bg-sky-400 text-white shadow-primary/20 hover:-translate-y-0.5'}`}>
                                {loading ? (
                                    <><svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>Generowanie...</>
                                ) : (
                                    <><span className="text-base">Generuj Kosztorys</span><span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span></>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
