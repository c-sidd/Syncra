import React, { useState, useContext } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const Login = () => {
  const { user, login, register } = useContext(AuthContext);
  const navigate = useNavigate();

  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Redirect users to dashboard if they are already logged in
  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        await register(username, email, password);
      } else {
        await login(username, password);
      }
      // Redirect successfully authenticated users to dashboard root
      navigate('/', { replace: true });
    } catch (err) {
      if (err.response && err.response.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setError(data.non_field_errors[0]);
        } else {
          // Format field validation error lists
          const firstKey = Object.keys(data)[0];
          setError(`${firstKey}: ${data[firstKey][0]}`);
        }
      } else {
        setError('Connection failed. Please check if the Django server is online.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4 font-sans text-white">
      {/* Sleek Dark Mode Glassmorphic Card Container */}
      <div className="w-full max-w-md p-8 bg-gray-900/40 backdrop-blur-md border border-gray-800 rounded-2xl shadow-xl flex flex-col gap-6">
        <div className="flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"></path>
            </svg>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">
            {isRegister ? 'Create an Account' : 'Welcome Back'}
          </h2>
          <p className="text-sm text-gray-400 text-center">
            {isRegister ? 'Sign up to start managing cloud files' : 'Enter credentials to access your drive'}
          </p>
        </div>

        {/* Display Validation or Network Errors */}
        {error && (
          <div className="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">Username</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-lg focus:outline-none focus:border-purple-500 text-sm transition-all duration-200"
              placeholder="Enter username"
            />
          </div>

          {isRegister && (
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-lg focus:outline-none focus:border-purple-500 text-sm transition-all duration-200"
                placeholder="Enter email address"
              />
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-lg focus:outline-none focus:border-purple-500 text-sm transition-all duration-200"
              placeholder="Enter password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-800 text-sm font-semibold tracking-wide rounded-lg transition-all duration-200 cursor-pointer shadow-lg shadow-purple-500/10"
          >
            {loading ? 'Processing...' : isRegister ? 'Sign Up' : 'Log In'}
          </button>
        </form>

        {/* Toggle between login and registration layouts */}
        <div className="border-t border-gray-800 pt-4 text-center">
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            className="text-xs font-medium text-purple-400 hover:text-purple-300 transition-colors duration-200 cursor-pointer"
          >
            {isRegister ? 'Already have an account? Log in' : "Don't have an account? Sign up"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
