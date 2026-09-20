import React from 'react'
import { Moon, Sun } from 'lucide-react'

function App() {
  const [darkMode, setDarkMode] = React.useState(false)

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    if (!darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <header className="flex justify-between items-center mb-12">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Procura Enterprise
          </h1>
          <button 
            onClick={toggleDarkMode}
            className="p-2 rounded-full glass hover:bg-white/90 dark:hover:bg-gray-800/90 transition-colors"
          >
            {darkMode ? <Sun className="w-5 h-5 text-yellow-500" /> : <Moon className="w-5 h-5 text-slate-700" />}
          </button>
        </header>

        <main>
          <div className="glass-card p-8 text-center space-y-4">
            <h2 className="text-2xl font-semibold">Frontend Foundation Ready</h2>
            <p className="text-gray-600 dark:text-gray-400">
              React, Vite, and Tailwind CSS with glassmorphism have been successfully configured.
            </p>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
