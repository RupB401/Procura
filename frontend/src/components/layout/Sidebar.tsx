import { FileText, LayoutDashboard } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Link } from 'react-router-dom';

interface SidebarProps {
  userRole?: string;
  activePath: string;
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ userRole, activePath, isOpen, onClose }: SidebarProps) {
  const { deleteAccount } = useAuth();
  
  const buyerLinks = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  ];

  const vendorLinks = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  ];

  const links = userRole === 'BUYER' ? buyerLinks : userRole === 'VENDOR' ? vendorLinks : [];

  return (
    <aside className={`fixed left-0 top-16 bottom-0 w-64 glass border-r flex flex-col z-40 transition-transform duration-300 ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
      <div className="p-4 flex flex-col gap-2 flex-grow">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = activePath === link.path || (activePath.startsWith('/dashboard') && link.path === '/dashboard');
          return (
            <Link
              key={link.name}
              to={link.path}
              onClick={onClose}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive 
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 font-medium' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              <Icon className="w-5 h-5" />
              {link.name}
            </Link>
          );
        })}
      </div>
      
      <div className="p-4 border-t border-gray-200/50 dark:border-gray-700/50">
        <button
          onClick={() => {
            if (window.confirm("Are you sure you want to completely delete your account? This will cascade and delete all your RFQs and quotes, and cannot be undone.")) {
              deleteAccount();
            }
          }}
          className="flex items-center justify-center w-full gap-2 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors font-medium text-sm"
        >
          Delete Account
        </button>
      </div>
    </aside>
  );
}
