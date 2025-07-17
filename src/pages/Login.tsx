import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store';
import { MapPin, AlertCircle } from 'lucide-react';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { register, signIn } = useAppStore();
  const [activeTab, setActiveTab] = useState<'citizen' | 'government'>('citizen');
  const [isRegister, setIsRegister] = useState(false);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError('All fields are required');
      return;
    }

    if (isRegister) {
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      
      const success = register(email, password, activeTab === 'government');
      if (success) {
        navigate('/profile-setup');
      } else {
        setError('Email already registered');
      }
    } else {
      const success = signIn(email, password);
      if (success) {
        // Let App.tsx handle the redirect based on user role and setup status
        navigate('/login');
      } else {
        setError('Invalid email or password');
      }
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${
      activeTab === 'government' ? 'gov-gradient' : 'dark-gradient'
    }`}>
      <div className="max-w-md w-full glass rounded-lg shadow-xl overflow-hidden">
        <div className="p-6 md:p-8">
          <div className="w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-green-500/30 transition-colors">
           <MapPin className="h-8 w-8 text-yellow-400" />
          </div>
          <h1 className="text-2xl font-bold text-center mb-6 text-white">Pothole Reporter</h1>
          
          <div className="flex mb-6 bg-black/30 rounded-lg p-1">
            <button
              className={`flex-1 py-2 text-center rounded-md transition-all ${
                activeTab === 'citizen' 
                  ? 'bg-blue-500/80 text-white shadow-lg' 
                  : 'text-blue-200 hover:text-white'
              }`}
              onClick={() => setActiveTab('citizen')}
            >
              Citizen
            </button>
            <button
              className={`flex-1 py-2 text-center rounded-md transition-all ${
                activeTab === 'government' 
                  ? 'bg-red-600/80 text-white shadow-lg' 
                  : 'text-red-200 hover:text-red'
              }`}
              onClick={() => setActiveTab('government')}
            >
              Government
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {error && (
              <div className="mb-4 p-3 bg-red-500/20 rounded-md flex items-center text-red-200">
                <AlertCircle className="h-5 w-5 mr-2" />
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-white mb-1">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-2 bg-black/30 border border-white rounded-md text-white"
                  placeholder="Enter your email"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-white mb-1">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full p-2 bg-black/30 border border-white rounded-md text-white"
                  placeholder="••••••••"
                />
              </div>

              {isRegister && (
                <div>
                  <label htmlFor="confirm-password" className="block text-sm font-medium text-white mb-1">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    id="confirm-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full p-2 bg-black/30 border border-white rounded-md text-white"
                    placeholder="••••••••"
                  />
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-white text-black py-2 px-4 rounded-md hover:bg-black/50 hover:text-white "
              >
                {isRegister ? 'Register' : 'Sign In'}
              </button>

              <button
                type="button"
                onClick={() => setIsRegister(!isRegister)}
                className="w-full text-white hover:text-blue-300"
              >
                {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;