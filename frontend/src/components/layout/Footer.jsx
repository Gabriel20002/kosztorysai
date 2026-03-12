import { Link } from 'react-router-dom'

export default function Footer() {
    return (
        <footer className="w-full border-t border-slate-800 bg-surface-dark py-12 relative z-10 mt-auto">
            <div className="max-w-[1280px] mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex items-center gap-2 text-slate-400">
                    <span className="material-symbols-outlined text-[20px]">architecture</span>
                    <span className="font-bold">Kosztorysy AI</span>
                    <span className="text-xs ml-2">© 2026 Inc.</span>
                </div>
                <div className="flex items-center gap-6">
                    <Link to="/terms" className="text-slate-500 hover:text-white text-xs transition-colors">
                        Regulamin Beta
                    </Link>
                    <a href="mailto:kosztorysyai@gmail.com" className="text-slate-500 hover:text-white transition-colors flex items-center gap-1 text-xs">
                        <span className="material-symbols-outlined text-base">mail</span>
                        kosztorysyai@gmail.com
                    </a>
                </div>
            </div>
        </footer>
    );
}
