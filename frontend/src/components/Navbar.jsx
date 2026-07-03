import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);

  // Do not render the navbar on public authentication pages
  if (!user) return null;

  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 bg-gray-950/80 backdrop-blur-md border-b border-gray-800 text-white font-sans">
      {/* Brand Logo Container */}
      <div className="flex items-center gap-2">
        <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"></path>
        </svg>
        <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
          DriveClone
        </span>
      </div>

      {/* User Dashboard Profile Controls */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          {/* Circular avatar displaying user's first letter */}
          <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-500/50 flex items-center justify-center font-semibold text-purple-300">
            {user.username.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm font-medium text-gray-300">@{user.username}</span>
        </div>
        <button
          onClick={logout}
          className="px-3.5 py-1.5 text-xs font-semibold tracking-wide text-gray-300 hover:text-white bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 rounded-lg transition-all duration-200 cursor-pointer"
        >
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
