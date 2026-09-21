import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Props {
  onLoginClick: () => void
}

export function LandingPage({ onLoginClick }: Props) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col relative overflow-hidden">
      {/* Background decoration with darker, richer colors */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-700/40 rounded-full blur-[120px] pointer-events-none animate-pulse" style={{ animationDuration: '4s' }} />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-fuchsia-700/30 rounded-full blur-[120px] pointer-events-none animate-pulse" style={{ animationDuration: '7s' }} />
      <div className="absolute top-[20%] right-[-10%] w-[40%] h-[40%] bg-indigo-700/30 rounded-full blur-[100px] pointer-events-none animate-pulse" style={{ animationDuration: '5s' }} />

      {/* Navbar */}
      <header className="px-6 py-4 flex items-center justify-between z-10">
        <Link to="/" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 hover:opacity-80 transition-opacity">
          Procura
        </Link>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 text-center z-10 pt-16 pb-24">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl mb-6">
          <span className="inline-block opacity-0 animate-fade-in-up">Enterprise RFQs,</span>
          <br />
          <span className="inline-block opacity-0 animate-fade-in-down bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400" style={{ animationDelay: '0.1s' }}>
            Simplified.
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mb-10 leading-relaxed opacity-0 animate-blur-fade-in" style={{ animationDelay: '0.3s' }}>
          Connect buyers and vendors seamlessly. Create requests, gather quotes, ask questions, and award contracts in a secure, real-time platform designed for modern enterprises.
        </p>

        {/* Wrapper handles fade-in, inner handles bounce, button handles hover scale */}
        <div className="opacity-0 animate-fade-in" style={{ animationDelay: '0.5s' }}>
          <div className="animate-bounce hover:animate-none">
            <button
              onClick={onLoginClick}
              className="group px-8 py-4 rounded-xl bg-blue-600 hover:bg-indigo-600 hover:scale-110 text-white font-semibold text-lg shadow-lg shadow-blue-500/30 hover:shadow-indigo-500/50 transition-all duration-300 flex items-center gap-2"
            >
              Get Started Now
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="z-10 py-8 text-center text-sm text-gray-500 dark:text-gray-400 border-t border-gray-200/50 dark:border-gray-700/50 bg-transparent">
        <p>© {new Date().getFullYear()} Procura Enterprise. All rights reserved.</p>
        <p className="mt-2">Connecting global buyers and suppliers with efficiency and security.</p>
      </footer>
    </div>
  )
}
