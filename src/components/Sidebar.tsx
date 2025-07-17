import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAppStore } from '../store';
import { MapPin, User, LogOut, Settings, BarChart3, Shield, X } from 'lucide-react';
import NotificationBell from './NotificationBell';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { 
    currentUser, 
    govUser, 
    isGovUser, 
    logout, 
    getBadge 
  } = useAppStore();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
    onClose();
  };
  
  const userPoints = currentUser?.points || 0;
  const badge = getBadge(userPoints);

  // Sidebar classes for mobile overlay and desktop fixed
  const sidebarClasses =
    "h-full flex flex-col dark-gradient animate-slide-in-left w-64 " +
    "md:relative md:translate-x-0 md:shadow-none " +
    (isOpen ? "fixed z-50 left-0 top-0 shadow-2xl" : "hidden");

  return (
    <aside className={sidebarClasses}>
      {/* Close button for mobile */}
      <div className="flex md:hidden justify-end pr-4 pt-4">
        <button onClick={onClose} aria-label="Close sidebar" type="button">
          <X className="h-7 w-7 text-white" />
        </button>
      </div>
      {/* NotificationBell for desktop */}
      <div className="hidden md:flex justify-end pr-6 pt-4">
        <NotificationBell />
      </div>
      <div className="p-6">
        <div className="flex items-center justify-center mb-8 animate-bounce-in">
          <MapPin className="h-8 w-8 text-yellow-500" />
          <h1 className="text-white font-bold ml-4">Pothole Reporter</h1>
        </div>
        
        <div className="mb-6">
          <div className="flex items-center mb-4">
            <div className="w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center animate-pop-in">
              <User className="h-6 w-6 text-black-500" />
            </div>
            <div className="ml-3">
              <p className="font-medium text-white">
                {isGovUser ? govUser?.name : currentUser?.name}
              </p>
              <p className="text-sm text-white font-bold">
                {isGovUser ? 'Government Official' : 'Citizen Reporter'}
              </p>
            </div>
          </div>
          
          {!isGovUser && (
            <div className="bg-white-100 p-3 rounded-lg mb-4 animate-fade-in">
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-white">Points: {userPoints}</span>
                <span className="text-sm font-medium capitalize text-white">{badge} Badge</span>
              </div>
              <div className="w-full bg-yellow-100 rounded-full h-2.5 overflow-hidden">
                <div 
                  className="bg-blue-500 h-2.5 rounded-full transition-all duration-700"
                  style={{ 
                    width: `${Math.min(100, (userPoints % 50) * 2)}%`,
                  }}
                ></div>
              </div>
            </div>
          )}
        </div>
        
        <nav>
          <ul className="space-y-2">
            <li>
              <Link
                to="/home"
                className="flex items-center p-3 text-white rounded hover:bg-black-50"
                onClick={onClose}
              >
                <MapPin className="h-5 w-5 mr-3" />
                <span>Map View</span>
              </Link>
            </li>
            
            {isGovUser ? (
              <>
                <li>
                  <Link
                    to="/gov-dashboard"
                    className="flex items-center p-3 text-white rounded hover:bg-black-50"
                    onClick={onClose}
                  >
                    <BarChart3 className="h-5 w-5 mr-3" />
                    <span>Dashboard</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/profile"
                    className="flex items-center p-3 text-white rounded hover:bg-black-50"
                    onClick={onClose}
                  >
                    <Shield className="h-5 w-5 mr-3" />
                    <span>Profile</span>
                  </Link>
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link
                    to="/new-report"
                    className="flex items-center p-3 text-white rounded hover:bg-black-50"
                    onClick={onClose}
                  >
                    <MapPin className="h-5 w-5 mr-3" />
                    <span>Report Pothole</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/profile"
                    className="flex items-center p-3 text-white rounded hover:bg-black-50"
                    onClick={onClose}
                  >
                    <Settings className="h-5 w-5 mr-3" />
                    <span>Profile Settings</span>
                  </Link>
                </li>
              </>
            )}
            
            <li>
              <button
                onClick={handleLogout}
                className="flex items-center w-full p-3 text-white rounded hover:bg-black-50"
              >
                <LogOut className="h-5 w-5 mr-3" />
                <span>Logout</span>
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;