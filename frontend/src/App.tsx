import { useState } from 'react'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { Navbar } from './components/layout/Navbar'
import { Sidebar } from './components/layout/Sidebar'
import { LoginPage } from './pages/LoginPage'
import { RFQListPage } from './pages/RFQListPage'
import { CreateRFQPage } from './pages/CreateRFQPage'
import { RFQDetailPage } from './pages/RFQDetailPage'
import { LandingPage } from './pages/LandingPage'
import { ProfilePage } from './pages/ProfilePage'
import { Loader2 } from 'lucide-react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams, useLocation } from 'react-router-dom'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    )
  }
  
  if (user) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const [darkMode, setDarkMode] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()

  const toggleDarkMode = () => {
    setDarkMode((prev) => {
      const next = !prev
      document.documentElement.classList.toggle('dark', next)
      return next
    })
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen((prev) => !prev)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        userRole={user!.role}
        onLogout={logout}
        onMenuClick={toggleMobileMenu}
      />
      <Sidebar 
        userRole={user!.role} 
        activePath={location.pathname} 
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />
      <main className="lg:pl-64 pt-16">
        {children}
      </main>
      
      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </div>
  )
}

function RFQDetailWrapper() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  if (!id) return null
  return <RFQDetailPage rfqId={id} onBack={() => navigate('/dashboard')} />
}

function AppRoutes() {
  const navigate = useNavigate()

  return (
    <Routes>
      <Route path="/" element={<PublicRoute><LandingPage onLoginClick={() => navigate('/login')} /></PublicRoute>} />
      <Route path="/login" element={<PublicRoute><LoginPage onLogin={() => navigate('/dashboard')} /></PublicRoute>} />
      
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <DashboardLayout>
            <RFQListPage 
              onSelectRFQ={(id) => navigate(`/dashboard/rfq/${id}`)} 
              onCreateRFQ={() => navigate('/dashboard/rfq/create')} 
            />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/dashboard/rfq/create" element={
        <ProtectedRoute>
          <DashboardLayout>
            <CreateRFQPage 
              onBack={() => navigate('/dashboard')} 
              onCreated={(rfq) => navigate(`/dashboard/rfq/${rfq.id}`)} 
            />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/dashboard/rfq/:id" element={
        <ProtectedRoute>
          <DashboardLayout>
            <RFQDetailWrapper />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/dashboard/profile" element={
        <ProtectedRoute>
          <DashboardLayout>
            <ProfilePage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || 'dummy-client-id-for-showcase'
  console.log("Using Google Client ID:", googleClientId);
  
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  )
}
