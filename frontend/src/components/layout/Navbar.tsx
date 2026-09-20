
import { Moon, Sun, Menu, UserCircle } from 'lucide-react';

interface NavbarProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
  userRole?: string;
  onLogout?: () => void;
  onMenuClick?: () => void;
}

export function Navbar({ darkMode, toggleDarkMode, userRole, onLogout, onMenuClick }: NavbarProps) {
  return (
    <nav className="fixed top-0 left-0 right-0 h-16 z-50 glass border-b px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button onClick={onMenuClick} className="lg:hidden p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/10">
          <Menu className="w-6 h-6 text-gray-600 dark:text-gray-300" />
        </button>
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
          Procura
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {userRole && (
          <span className="text-sm font-medium px-3 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
            {userRole}
          </span>
        )}
        
        <button 
          onClick={toggleDarkMode}
          className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          aria-label="Toggle dark mode"
        >
          {darkMode ? (
            <Sun className="w-5 h-5 text-yellow-500" />
          ) : (
            <Moon className="w-5 h-5 text-slate-700" />
          )}
        </button>

        {userRole && (
          <button 
            onClick={onLogout}
            className="flex items-center gap-2 p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          >
            <UserCircle className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            <span className="hidden sm:inline text-sm font-medium">Logout</span>
          </button>
        )}
      </div>
    </nav>
  );
}
