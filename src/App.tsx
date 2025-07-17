import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import ProfileSetup from './pages/ProfileSetup';
import Home from './pages/Home';
import GovDashboard from './pages/GovDashboard';
import Profile from './pages/Profile';
import NewReport from './pages/NewReport';
import Notifications from './pages/Notifications';
import { useAppStore } from './store';
import { loadModel } from './utils/detection';
import Layout from './components/Layout';

const App: React.FC = () => {
  const { isLoggedIn, isGovUser, hasCompletedSetup, initAuth } = useAppStore();

  useEffect(() => {
    loadModel().catch(console.error);
    initAuth();
  }, [initAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={
          isLoggedIn ? (
            <Navigate to={
              !hasCompletedSetup ? '/profile-setup' :
              isGovUser ? '/gov-dashboard' : '/home'
            } />
          ) : (
            <Navigate to="/login" />
          )
        } />
        <Route path="/login" element={
          isLoggedIn ? (
            <Navigate to={
              !hasCompletedSetup ? '/profile-setup' :
              isGovUser ? '/gov-dashboard' : '/home'
            } />
          ) : (
            <Login />
          )
        } />

        <Route element={isLoggedIn ? <Layout /> : <Navigate to="/login" />}>
          <Route path="/profile-setup" element={
            !hasCompletedSetup ? <ProfileSetup /> : 
            <Navigate to={isGovUser ? "/gov-dashboard" : "/home"} />
          } />
          
          {/* Protected Routes */}
          <Route path="/home" element={
            !isGovUser && hasCompletedSetup ? <Home /> : 
            <Navigate to={isGovUser ? "/gov-dashboard" : "/login"} />
          } />
          <Route path="/gov-dashboard" element={
            isGovUser && hasCompletedSetup ? <GovDashboard /> : 
            <Navigate to={isGovUser ? "/login" : "/home"} />
          } />
          <Route path="/profile" element={
            hasCompletedSetup ? <Profile /> : <Navigate to="/profile-setup" />
          } />
          <Route path="/new-report" element={
            !isGovUser && hasCompletedSetup ? <NewReport /> : 
            <Navigate to="/login" />
          } />
          <Route path="/notifications" element={<Notifications />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;