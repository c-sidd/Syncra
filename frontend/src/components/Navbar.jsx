import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  if (!user) return null;

  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 bg-gray-950/80 backdrop-blur-md border-b border-gray-800 text-white font-sans">
      <Link to="/" className="flex items-center gap-2">
        <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-lavender via-pink to-blue-brand bg-clip-text text-transparent">Syncra</span>
      </Link>
      <div className="flex items-center gap-3">
        <Link to="/account" className="px-3.5 py-2 text-sm font-semibold text-gray-300 hover:text-white bg-gray-900 border border-gray-800 hover:border-pink/40 rounded-lg transition">Account</Link>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-lavender/20 border border-lavender/50 flex items-center justify-center font-semibold text-lavender">{user.username.charAt(0).toUpperCase()}</div>
          <span className="hidden sm:inline text-sm font-medium text-gray-300">@{user.username}</span>
        </div>
        <button onClick={logout} className="px-3.5 py-2 text-xs font-semibold text-gray-300 hover:text-white bg-gray-900 border border-gray-800 rounded-lg transition">Logout</button>
      </div>
    </nav>
  );
};

export default Navbar;
