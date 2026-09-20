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
    return <Navigate to="/login" replace />
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
  const location = useLocation()

  const toggleDarkMode = () => {
    setDarkMode((prev) => {
      const next = !prev
      document.documentElement.classList.toggle('dark', next)
      return next
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        userRole={user!.role}
        onLogout={logout}
      />
      <Sidebar userRole={user!.role} activePath={location.pathname} />
      <main className="lg:pl-64 pt-16">
        {children}
      </main>
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
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || 'dummy-client-id-for-showcase'
  
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
