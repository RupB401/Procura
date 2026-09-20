import React from 'react'
import { ArrowRight, ShieldCheck, Globe, Zap } from 'lucide-react'

interface Props {
  onLoginClick: () => void
}

export function LandingPage({ onLoginClick }: Props) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-500/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-indigo-500/20 rounded-full blur-[120px] pointer-events-none" />

      {/* Navbar */}
      <header className="px-6 py-4 flex items-center justify-between z-10">
        <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
          Procura
        </div>
        <button
          onClick={onLoginClick}
          className="px-6 py-2 rounded-full font-medium transition-all duration-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
        >
          Sign In
        </button>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 text-center z-10 pt-16 pb-24">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100/50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium mb-8 border border-blue-200 dark:border-blue-800 backdrop-blur-md">
          <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
          The future of B2B Procurement
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl mb-6">
          Enterprise RFQs, <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
            Simplified.
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mb-10 leading-relaxed">
          Connect buyers and vendors seamlessly. Create requests, gather quotes, ask questions, and award contracts in a secure, real-time platform designed for modern enterprises.
        </p>

        <button
          onClick={onLoginClick}
          className="group px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-lg shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 transition-all duration-300 flex items-center gap-2 transform hover:-translate-y-1"
        >
          Get Started Now
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </button>
      </main>

      {/* Features Section */}
      <section className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl border-t border-gray-200/50 dark:border-gray-700/50 py-20 px-6 z-10">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard 
            icon={<Zap className="w-8 h-8 text-amber-500" />}
            title="Lightning Fast"
            desc="Built on a modern React & FastAPI stack, ensuring sub-second response times for all procurement operations."
          />
          <FeatureCard 
            icon={<ShieldCheck className="w-8 h-8 text-emerald-500" />}
            title="Secure & Compliant"
            desc="Role-based access control and strict data isolation ensures your quotes and RFQs remain completely confidential."
          />
          <FeatureCard 
            icon={<Globe className="w-8 h-8 text-blue-500" />}
            title="Global Reach"
            desc="Vendors can bid globally in multiple currencies. Connect with the best suppliers regardless of borders."
          />
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="p-8 rounded-2xl bg-white/70 dark:bg-gray-800/70 border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-md shadow-sm hover:shadow-md transition-shadow">
      <div className="w-14 h-14 rounded-xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center mb-6 shadow-inner border border-gray-100 dark:border-gray-800">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
        {desc}
      </p>
    </div>
  )
}
