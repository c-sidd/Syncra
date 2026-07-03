import React, { createContext, useState, useEffect } from 'react';
import api from '../utils/api';

// Instantiate the Authentication Context object reference
export const AuthContext = createContext();

// Provide Auth state fields to all nested children modules
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Hydrate states: Check if credentials already exist in local storage on page refresh
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    // Finished reading local storage; disable initial loading state
    setLoading(false);
  }, []);

  // Triggers user logins and saves credentials to local storage
  const login = async (username, password) => {
    const response = await api.post('/auth/login/', { username, password });
    const { token: tokenKey, user: userData } = response.data;

    // Save credentials in browser cache
    localStorage.setItem('token', tokenKey);
    localStorage.setItem('user', JSON.stringify(userData));

    // Update React virtual states
    setToken(tokenKey);
    setUser(userData);
    
    return userData;
  };

  // Triggers user registration and saves credentials to local storage
  const register = async (username, email, password) => {
    const response = await api.post('/auth/register/', { username, email, password });
    const { token: tokenKey, user: userData } = response.data;

    // Save credentials in browser cache
    localStorage.setItem('token', tokenKey);
    localStorage.setItem('user', JSON.stringify(userData));

    // Update React virtual states
    setToken(tokenKey);
    setUser(userData);
    
    return userData;
  };

  // Logs the user out and clears states and cache
  const logout = () => {
    // Clear storage cache
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Clear React states
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
