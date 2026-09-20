import React from 'react';

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Subtle background gradients for premium feel */}
        <div className="absolute -top-[40%] -left-[20%] w-[70%] h-[70%] rounded-full bg-blue-400/20 dark:bg-blue-600/10 blur-[120px]" />
        <div className="absolute -bottom-[40%] -right-[20%] w-[70%] h-[70%] rounded-full bg-indigo-400/20 dark:bg-indigo-600/10 blur-[120px]" />
      </div>
      
      <div className="w-full max-w-md z-10">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Procura
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Enterprise RFQ Management Platform
          </p>
        </div>
        
        <div className="glass-card p-8 shadow-xl">
          {children}
        </div>
      </div>
    </div>
  );
}
