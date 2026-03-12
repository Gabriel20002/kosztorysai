import { Link } from 'react-router-dom'

export default function NotFound() {
    return (
        <div className="flex-1 flex flex-col items-center justify-center py-24 px-4 text-center">
            <p className="text-8xl font-black text-primary/20 mb-4">404</p>
            <h2 className="text-3xl font-black text-white mb-3">Strona nie istnieje</h2>
            <p className="text-slate-400 mb-8">Sprawdź adres URL lub wróć do strony głównej.</p>
            <Link to="/" className="h-12 px-8 rounded-lg bg-primary hover:bg-sky-400 text-white font-bold transition-colors flex items-center gap-2">
                <span className="material-symbols-outlined">home</span>
                Strona główna
            </Link>
        </div>
    )
}
