import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import React from 'react'

import { AuthProvider } from './context/AuthContext'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Pricing from './pages/Pricing'
import Login from './pages/Login'
import Register from './pages/Register'
import Features from './pages/Features'
import HowItWorks from './pages/HowItWorks'
import Admin from './pages/Admin'
import Terms from './pages/Terms'
import NotFound from './pages/NotFound'
import Contact from './pages/Contact'
import Apply from './pages/Apply'

function AppInner() {
  const location = useLocation()
  return (
    <div className="relative flex flex-col w-full grow min-h-screen">
      {/* Background Ambient Glow */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-5%] w-[500px] h-[500px] bg-secondary/10 rounded-full blur-[100px]"></div>
      </div>

      <Navbar />

      <main key={location.pathname} className="relative z-10 flex flex-col items-center w-full grow page-enter">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/features" element={<Features />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="/get-started" element={<Navigate to="/register" replace />} />
          <Route path="/add-program" element={<Navigate to="/" replace />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/apply" element={<Apply />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      <Footer />
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  )
}

export default App
