import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';

function SmartLink({ to, children, className, onClick }) {
    const location = useLocation();
    const isCurrentPage = location.pathname === to;

    const handleClick = (e) => {
        if (isCurrentPage) {
            e.preventDefault();
            window.location.reload();
        }
        if (onClick) onClick(e);
    };

    return (
        <Link to={to} className={className} onClick={handleClick}>
            {children}
        </Link>
    );
}

export default function Navbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <header className="sticky top-0 z-50 w-full glass-card border-b border-b-slate-800/50">
            <div className="px-4 md:px-10 py-4 flex items-center justify-between max-w-[1280px] mx-auto">
                <SmartLink to="/" className="flex items-center gap-3 text-slate-900 dark:text-white group">
                    <div className="flex items-center justify-center size-8 bg-gradient-to-br from-primary to-secondary rounded-lg text-white group-hover:scale-105 transition-transform">
                        <span className="material-symbols-outlined text-[20px]">architecture</span>
                    </div>
                    <h2 className="text-xl font-bold tracking-tight">BuildAI</h2>
                </SmartLink>
                <div className="hidden lg:flex items-center gap-8">
                    <SmartLink className="text-slate-600 dark:text-slate-300 hover:text-primary transition-colors text-sm font-medium" to="/features">Możliwości</SmartLink>
                    <SmartLink className="text-slate-600 dark:text-slate-300 hover:text-primary transition-colors text-sm font-medium" to="/how-it-works">Jak to działa</SmartLink>
                    <SmartLink className="text-slate-600 dark:text-slate-300 hover:text-primary transition-colors text-sm font-medium" to="/pricing">Cennik</SmartLink>
                    <SmartLink className="text-slate-600 dark:text-slate-300 hover:text-primary transition-colors text-sm font-medium" to="/add-program">Dodaj Program</SmartLink>
                </div>
                <div className="flex items-center gap-4">
                    <SmartLink className="hidden sm:block text-slate-600 dark:text-slate-300 hover:text-white transition-colors text-sm font-medium" to="/login">Zaloguj się</SmartLink>
                    <SmartLink to="/get-started" className="hidden sm:flex items-center justify-center rounded-lg h-9 px-4 bg-primary hover:bg-primary/90 text-white text-sm font-bold transition-all shadow-[0_0_15px_rgba(19,146,236,0.4)]">
                        Zacznij Tworzyć
                    </SmartLink>

                    {/* Mobile Menu Button */}
                    <button
                        className="lg:hidden flex flex-col items-center justify-center p-2 text-slate-300 hover:text-white"
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                    >
                        <span className="material-symbols-outlined text-2xl">{isMenuOpen ? 'close' : 'menu'}</span>
                    </button>
                </div>
            </div>

            {/* Mobile Menu Overlay */}
            {isMenuOpen && (
                <div className="lg:hidden absolute top-full left-0 right-0 glass-card border-b border-t border-slate-800/50 p-4 flex flex-col gap-4 animate-in slide-in-from-top-2">
                    <SmartLink onClick={() => setIsMenuOpen(false)} className="text-slate-300 hover:text-primary py-2 font-medium" to="/features">Możliwości</SmartLink>
                    <SmartLink onClick={() => setIsMenuOpen(false)} className="text-slate-300 hover:text-primary py-2 font-medium" to="/how-it-works">Jak to działa</SmartLink>
                    <SmartLink onClick={() => setIsMenuOpen(false)} className="text-slate-300 hover:text-primary py-2 font-medium" to="/pricing">Cennik</SmartLink>
                    <SmartLink onClick={() => setIsMenuOpen(false)} className="text-slate-300 hover:text-primary py-2 font-medium" to="/add-program">Dodaj Program</SmartLink>
                    <hr className="border-slate-800" />
                    <SmartLink onClick={() => setIsMenuOpen(false)} className="text-slate-300 hover:text-white py-2 font-medium" to="/login">Zaloguj się</SmartLink>
                    <SmartLink onClick={() => setIsMenuOpen(false)} className="text-white bg-primary hover:bg-primary/90 rounded-lg p-3 text-center font-bold" to="/get-started">Zacznij Tworzyć</SmartLink>
                </div>
            )}
        </header>
    );
}
