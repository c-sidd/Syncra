import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);

  // If initial local storage credentials check is running, render a loading spinner
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white font-sans">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-purple-500"></div>
      </div>
    );
  }

  // If user is not authenticated, redirect browser to the public login form
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Otherwise, allow entry and render child components
  return children;
};

export default PrivateRoute;
