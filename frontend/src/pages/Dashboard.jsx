import React from 'react';

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans p-8">
      {/* Maximum boundary container */}
      <div className="max-w-6xl mx-auto flex flex-col gap-8">
        {/* Title and breadcrumbs header */}
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            My Drive
          </h1>
          <div className="text-sm text-gray-400 font-medium">
            Authenticated shell active
          </div>
        </div>

        {/* Dashboard Filemanager Explorer layout placeholder */}
        <div className="py-20 flex flex-col items-center justify-center border-2 border-dashed border-gray-800 rounded-2xl bg-gray-900/10">
          <div className="w-12 h-12 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4 animate-pulse">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
          </div>
          <p className="text-sm font-semibold tracking-wide text-gray-300">
            Welcome to your Cloud Drive Clone!
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Dashboard loaded. Folder and file API integrations are up next.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
