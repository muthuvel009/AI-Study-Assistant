import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => api.getToken());
  const [loading, setLoading] = useState(true);

  // Initialize auth state on application mount / reload
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = api.getToken();
      if (!storedToken) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        // Validate token against real backend /api/auth/me
        const userData = await authService.getMe();
        setUser(userData);
        localStorage.setItem('ai_study_user', JSON.stringify(userData));
      } catch (err) {
        // Token is invalid, expired, or backend rejected
        console.warn('Session restoration failed:', err.message);
        api.setToken(null);
        setToken(null);
        setUser(null);
        localStorage.removeItem('ai_study_user');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    // Listen for global 401 unauthorized events
    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (email, password) => {
    // 1. Call FastAPI /api/auth/login
    const data = await authService.login({ email, password });
    
    // 2. Receive and store JWT
    setToken(data.access_token);
    api.setToken(data.access_token);

    // 3. Set current authenticated user
    const student = data.user;
    setUser(student);
    localStorage.setItem('ai_study_user', JSON.stringify(student));

    return { success: true, user: student };
  };

  const register = async (userData) => {
    // 1. Call FastAPI /api/auth/register
    const data = await authService.register(userData);

    // 2. Receive and store JWT
    setToken(data.access_token);
    api.setToken(data.access_token);

    // 3. Set current authenticated user
    const student = data.user;
    setUser(student);
    localStorage.setItem('ai_study_user', JSON.stringify(student));

    return { success: true, user: student };
  };

  const updateUserProfile = (updatedFields) => {
    setUser((prev) => {
      const updated = { ...prev, ...updatedFields };
      localStorage.setItem('ai_study_user', JSON.stringify(updated));
      return updated;
    });
  };

  const logout = () => {
    authService.logout();
    setToken(null);
    setUser(null);
    localStorage.removeItem('ai_study_user');
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    loading,
    login,
    register,
    logout,
    updateUserProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
