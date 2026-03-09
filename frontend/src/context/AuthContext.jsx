import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const API = import.meta.env.VITE_API_URL ?? ''

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)         // { id, email, name, plan }
    const [loading, setLoading] = useState(true)   // sprawdzanie sesji przy starcie

    // Przy starcie: odczytaj token z localStorage i zweryfikuj
    useEffect(() => {
        const token = localStorage.getItem('auth_token')
        if (!token) { setLoading(false); return }
        fetch(`${API}/api/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(r => r.ok ? r.json() : null)
            .then(data => { if (data) setUser(data) })
            .catch(() => {})
            .finally(() => setLoading(false))
    }, [])

    async function _post(url, body, fallbackMsg) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        })
        let data
        try { data = await res.json() } catch { throw new Error(fallbackMsg) }
        if (!res.ok) throw new Error(data.detail || fallbackMsg)
        return data
    }

    async function login(email, password) {
        const data = await _post(`${API}/api/auth/login`, { email, password }, 'Błąd logowania')
        localStorage.setItem('auth_token', data.token)
        setUser(data.user)
        return data.user
    }

    async function register(email, password, name) {
        const data = await _post(`${API}/api/auth/register`, { email, password, name }, 'Błąd rejestracji')
        localStorage.setItem('auth_token', data.token)
        setUser(data.user)
        return data.user
    }

    function logout() {
        localStorage.removeItem('auth_token')
        setUser(null)
    }

    function getToken() {
        return localStorage.getItem('auth_token')
    }

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout, getToken }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    return useContext(AuthContext)
}
