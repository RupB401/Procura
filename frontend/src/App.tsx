import React, { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { Navbar } from './components/layout/Navbar'
import { Sidebar } from './components/layout/Sidebar'
import { LoginPage } from './pages/LoginPage'
import { RFQListPage } from './pages/RFQListPage'
import { CreateRFQPage } from './pages/CreateRFQPage'
import { RFQDetailPage } from './pages/RFQDetailPage'
import { Loader2 } from 'lucide-react'
import type { RFQ } from './lib/types'

type AppPage =
  | { name: 'rfq-list' }
  | { name: 'rfq-create' }
  | { name: 'rfq-detail'; id: string }

function AppShell() {
  const { user, isLoading, logout } = useAuth()
  const [darkMode, setDarkMode] = useState(false)
  const [page, setPage] = useState<AppPage>({ name: 'rfq-list' })

  const toggleDarkMode = () => {
    setDarkMode((prev) => {
      const next = !prev
      document.documentElement.classList.toggle('dark', next)
      return next
    })
  }

  // Reset to list view on login/logout
  useEffect(() => {
    setPage({ name: 'rfq-list' })
  }, [user?.id])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    )
  }

  // Unauthenticated — show login
  if (!user) {
    return <LoginPage onLogin={() => setPage({ name: 'rfq-list' })} />
  }

  // Authenticated shell
  const renderPage = () => {
    switch (page.name) {
      case 'rfq-list':
        return (
          <RFQListPage
            onSelectRFQ={(id) => setPage({ name: 'rfq-detail', id })}
            onCreateRFQ={() => setPage({ name: 'rfq-create' })}
          />
        )
      case 'rfq-create':
        return (
          <CreateRFQPage
            onBack={() => setPage({ name: 'rfq-list' })}
            onCreated={(rfq: RFQ) => setPage({ name: 'rfq-detail', id: rfq.id })}
          />
        )
      case 'rfq-detail':
        return (
          <RFQDetailPage
            rfqId={page.id}
            onBack={() => setPage({ name: 'rfq-list' })}
          />
        )
    }
  }

  const activePath = page.name === 'rfq-list' ? '/rfqs' : '/'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        userRole={user.role}
        onLogout={logout}
      />
      <Sidebar userRole={user.role} activePath={activePath} />
      <main className="lg:pl-64 pt-16">
        {renderPage()}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}
