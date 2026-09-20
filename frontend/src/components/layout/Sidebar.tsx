import React from 'react';
import { Home, FileText, Settings, LayoutDashboard } from 'lucide-react';

interface SidebarProps {
  userRole?: string;
  activePath: string;
}

export function Sidebar({ userRole, activePath }: SidebarProps) {
  const buyerLinks = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'My RFQs', path: '/rfqs', icon: FileText },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const vendorLinks = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Available RFQs', path: '/rfqs', icon: FileText },
    { name: 'My Quotes', path: '/quotes', icon: FileText },
  ];

  const links = userRole === 'BUYER' ? buyerLinks : userRole === 'VENDOR' ? vendorLinks : [];

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 glass border-r hidden lg:flex flex-col z-40">
      <div className="p-4 flex flex-col gap-2">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = activePath === link.path;
          return (
            <a
              key={link.name}
              href={link.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive 
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 font-medium' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              <Icon className="w-5 h-5" />
              {link.name}
            </a>
          );
        })}
      </div>
    </aside>
  );
}
