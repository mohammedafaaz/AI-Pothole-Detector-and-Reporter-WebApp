import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { Menu } from 'lucide-react';

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-gray-100 relative">
      {/* Sidebar for desktop */}
      <div className="hidden md:block w-64 flex-shrink-0">
        <Sidebar isOpen={true} onClose={() => {}} />
      </div>
      {/* Sidebar for mobile (overlay) */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 w-64 md:hidden">
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
          </div>
        </>
      )}
      <div className="flex-1 animate-fade-in min-w-0 relative">
        {/* Hamburger button for mobile, hidden when sidebar is open */}
        {!sidebarOpen && (
          <button
            className="md:hidden fixed top-4 left-4 z-50 bg-white/90 rounded-full p-2 shadow"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
            type="button"
          >
            <Menu className="h-6 w-6 text-blue-500" />
          </button>
        )}
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;