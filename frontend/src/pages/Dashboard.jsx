import React, { useState, useEffect, useContext, useRef } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../utils/api';

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  
  // Drive content states
  const [currentFolder, setCurrentFolder] = useState(null);
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [path, setPath] = useState([]); // List of { id, name } representing sequential path
  const [totalStorageUsed, setTotalStorageUsed] = useState(0);
  
  // UX / UI states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  
  // Drag and drop visual state
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);
  
  // File input ref
  const fileInputRef = useRef(null);

  // Load folder contents from API
  const loadFolderContents = async (folderId) => {
    setLoading(true);
    setError(null);
    try {
      const url = folderId ? `/folders/${folderId}/` : '/folders/';
      const response = await api.get(url);
      setFolders(response.data.subfolders || []);
      setFiles(response.data.files || []);
      setTotalStorageUsed(response.data.total_storage_used || 0);
    } catch (err) {
      console.error('Failed to load drive contents:', err);
      setError(err.response?.data?.detail || 'Failed to load drive contents. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch data reactively when currentFolder changes
  useEffect(() => {
    loadFolderContents(currentFolder ? currentFolder.id : null);
  }, [currentFolder]);

  // Navigate to a child folder
  const handleFolderClick = (folder) => {
    setPath(prev => [...prev, { id: folder.id, name: folder.name }]);
    setCurrentFolder(folder);
  };

  // Navigate using breadcrumbs
  const handleBreadcrumbClick = (folder, index) => {
    if (folder === null) {
      // Home / Root
      setPath([]);
      setCurrentFolder(null);
    } else {
      // Ancestor folder
      setPath(prev => prev.slice(0, index + 1));
      setCurrentFolder(folder);
    }
  };

  // Handle folder creation
  const handleCreateFolder = async (e) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    
    setActionLoading(true);
    setError(null);
    try {
      const payload = {
        name: newFolderName.trim(),
        parent: currentFolder ? currentFolder.id : null
      };
      const response = await api.post('/folders/', payload);
      // Append to local folder list and close modal
      setFolders(prev => [...prev, response.data]);
      setIsCreatingFolder(false);
      setNewFolderName('');
    } catch (err) {
      console.error('Folder creation failed:', err);
      if (err.response?.data) {
        const errorData = err.response.data;
        if (typeof errorData === 'object') {
          const firstKey = Object.keys(errorData)[0];
          setError(`${firstKey}: ${errorData[firstKey][0]}`);
        } else {
          setError('Failed to create folder.');
        }
      } else {
        setError('Connection failed. Django backend might be offline.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Handle file uploads
  const handleFileUpload = async (selectedFiles) => {
    if (!selectedFiles || selectedFiles.length === 0) return;
    
    setIsUploading(true);
    setError(null);
    
    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        formData.append('file', file);
        if (currentFolder) {
          formData.append('folder', currentFolder.id);
        }
        
        const response = await api.post('/files/upload/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        // Append newly uploaded file info
        setFiles(prev => [...prev, response.data]);
        setTotalStorageUsed(prev => prev + (response.data.size || 0));
      }
    } catch (err) {
      console.error('File upload failed:', err);
      if (err.response?.data) {
        const errorData = err.response.data;
        if (typeof errorData === 'object') {
          const firstKey = Object.keys(errorData)[0];
          setError(`${firstKey}: ${errorData[firstKey][0]}`);
        } else {
          setError('Failed to upload file.');
        }
      } else {
        setError('Connection failed. Max file size exceeded or backend is offline.');
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const onFileSelectChange = (e) => {
    handleFileUpload(e.target.files);
  };

  // Handle file deletions
  const handleDeleteFile = async (fileId) => {
    if (!window.confirm('Are you sure you want to delete this file permanently?')) return;
    
    setActionLoading(true);
    setError(null);
    try {
      const deletedFile = files.find(f => f.id === fileId);
      await api.delete(`/files/${fileId}/`);
      if (deletedFile) {
        setTotalStorageUsed(prev => Math.max(0, prev - (deletedFile.size || 0)));
      }
      // Remove deleted file from state list
      setFiles(prev => prev.filter(f => f.id !== fileId));
    } catch (err) {
      console.error('File deletion failed:', err);
      setError(err.response?.data?.detail || 'Failed to delete file. Please check your permissions.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle folder deletions
  const handleDeleteFolder = async (folderId) => {
    if (!window.confirm('Are you sure you want to delete this folder and all its contents permanently?')) return;
    
    setActionLoading(true);
    setError(null);
    try {
      await api.delete(`/folders/${folderId}/`);
      // Remove deleted folder from state list
      setFolders(prev => prev.filter(f => f.id !== folderId));
      // Re-fetch directory structure and storage stats
      loadFolderContents(currentFolder ? currentFolder.id : null);
    } catch (err) {
      console.error('Folder deletion failed:', err);
      setError(err.response?.data?.detail || 'Failed to delete folder. Please check your permissions.');
    } finally {
      setActionLoading(false);
    }
  };

  // Drag and drop event handlers
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current += 1;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
      e.dataTransfer.clearData();
    }
  };

  // Utility to format sizes
  const formatBytes = (bytes) => {
    if (bytes === 0 || bytes === null || bytes === undefined) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  // Utility to format timestamps
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  };

  // Utility to select icons based on file name extension
  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(ext)) {
      return (
        <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
          </svg>
        </div>
      );
    }
    if (['pdf'].includes(ext)) {
      return (
        <div className="w-9 h-9 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2zM7 9h10m-10 4h10m-10 4h6"></path>
          </svg>
        </div>
      );
    }
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
      return (
        <div className="w-9 h-9 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center text-yellow-400">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path>
          </svg>
        </div>
      );
    }
    if (['mp4', 'mkv', 'avi', 'mov', 'webm'].includes(ext)) {
      return (
        <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
          </svg>
        </div>
      );
    }
    if (['mp3', 'wav', 'ogg', 'aac', 'flac'].includes(ext)) {
      return (
        <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path>
          </svg>
        </div>
      );
    }
    // Default document/file icon
    return (
      <div className="w-9 h-9 rounded-lg bg-lavender/10 border border-lavender/20 flex items-center justify-center text-lavender">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
      </div>
    );
  };

  // Calculate dynamic storage usage with 15GB cap
  const totalUsedBytes = totalStorageUsed;
  const usagePercentage = Math.min((totalUsedBytes / (1024 * 1024 * 1024 * 15)) * 100, 100);

  return (
    <div 
      className="flex-1 bg-gray-950 text-white font-sans flex relative overflow-hidden"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Hidden File Input */}
      <input 
        type="file" 
        multiple
        ref={fileInputRef} 
        onChange={onFileSelectChange} 
        className="hidden" 
      />

      {/* Sidebar Layout */}
      <aside className="w-64 border-r border-gray-900 bg-gray-950/50 p-6 flex flex-col justify-between hidden md:flex shrink-0">
        <div className="flex flex-col gap-6">
          {/* Dashboard Shortcuts list */}
          <div className="flex flex-col gap-1">
            <button 
              onClick={() => handleBreadcrumbClick(null)} 
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer ${currentFolder === null ? 'bg-gradient-to-r from-lavender via-pink to-blue-brand text-gray-950 shadow-lg shadow-pink-500/10 font-bold' : 'text-gray-400 hover:text-white hover:bg-gray-900/50'}`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path>
              </svg>
              My Drive
            </button>
          </div>
        </div>

        {/* Storage Bar Indicator */}
        <div className="p-4 bg-gray-900/40 border border-gray-800 rounded-2xl flex flex-col gap-3">
          <div className="flex justify-between items-center text-xs">
            <span className="font-semibold text-gray-400">Storage</span>
            <span className="font-bold text-gray-200">{formatBytes(totalUsedBytes)} of 15 GB</span>
          </div>
          <div className="w-full bg-gray-950 h-2 rounded-full overflow-hidden border border-gray-800">
            <div 
              className="bg-gradient-to-r from-rose via-pink to-blue-light h-full rounded-full transition-all duration-500" 
              style={{ width: `${usagePercentage}%` }}
            ></div>
          </div>
        </div>
      </aside>

      {/* Main Filesystem Area */}
      <main className="flex-1 flex flex-col overflow-y-auto min-w-0 p-6 md:p-8">
        
        {/* Header toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-900 pb-5 mb-6">
          <div className="flex flex-col gap-1.5 min-w-0">
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              {currentFolder ? currentFolder.name : 'My Drive'}
            </h1>
            
            {/* Breadcrumbs Navigation */}
            <div className="flex items-center gap-1.5 text-xs text-gray-400 font-medium overflow-x-auto whitespace-nowrap scrollbar-none py-0.5">
              <button 
                onClick={() => handleBreadcrumbClick(null)}
                className="hover:text-lavender transition-colors duration-150 cursor-pointer"
              >
                Root
              </button>
              {path.map((item, idx) => (
                <React.Fragment key={item.id}>
                  <svg className="w-3 h-3 text-gray-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7"></path>
                  </svg>
                  <button 
                    onClick={() => handleBreadcrumbClick(item, idx)}
                    className="hover:text-lavender transition-colors duration-150 cursor-pointer max-w-[120px] truncate"
                  >
                    {item.name}
                  </button>
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Actions toolbar */}
          <div className="flex items-center gap-3 shrink-0">
            <button 
              onClick={() => setIsCreatingFolder(true)}
              className="px-4 py-2.5 text-sm font-semibold text-gray-300 hover:text-white bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 rounded-xl transition-all duration-200 cursor-pointer flex items-center gap-2"
            >
              <svg className="w-4 h-4 text-lavender" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"></path>
              </svg>
              New Folder
            </button>
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2.5 text-sm font-semibold bg-gradient-to-r from-lavender via-pink to-blue-brand text-gray-950 font-bold hover:brightness-110 rounded-xl transition-all duration-200 cursor-pointer flex items-center gap-2 shadow-lg shadow-pink-500/10 active:scale-98"
            >
              <svg className="w-4 h-4 text-gray-950" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
              </svg>
              Upload File
            </button>
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="px-4 py-3 mb-6 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-gray-400 hover:text-white cursor-pointer">&times;</button>
          </div>
        )}

        {/* Loading Spinner */}
        {loading ? (
          <div className="flex-1 flex items-center justify-center py-24">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-lavender"></div>
          </div>
        ) : (
          <div className="flex flex-col gap-8 min-h-[300px]">

            {/* Folders Section */}
            {folders.length > 0 && (
              <div className="flex flex-col gap-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500">Folders</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {folders.map(folder => (
                    <div 
                      key={folder.id}
                      onClick={() => handleFolderClick(folder)}
                      className="p-4 bg-gray-900/30 hover:bg-gray-900/70 border border-gray-900 hover:border-gray-800 rounded-2xl flex items-center justify-between transition-all duration-200 cursor-pointer group"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-xl bg-lavender/10 border border-lavender/20 flex items-center justify-center text-lavender group-hover:scale-105 transition-transform duration-200">
                          <svg className="w-5.5 h-5.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"></path>
                          </svg>
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="text-sm font-semibold text-gray-200 group-hover:text-white truncate">{folder.name}</span>
                          <span className="text-[10px] text-gray-500 font-medium">{formatDate(folder.created_at)}</span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteFolder(folder.id);
                        }}
                        className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-gray-900/50 transition-all duration-150 cursor-pointer opacity-0 group-hover:opacity-100 focus:opacity-100"
                        title="Delete folder"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Files Section */}
            {files.length > 0 ? (
              <div className="flex flex-col gap-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500">Files</h3>
                <div className="overflow-hidden border border-gray-900 rounded-2xl bg-gray-950/20 backdrop-blur-sm">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-gray-900 text-xs font-bold uppercase tracking-wider text-gray-500">
                          <th className="px-6 py-4">Name</th>
                          <th className="px-6 py-4 hidden sm:table-cell">Upload Date</th>
                          <th className="px-6 py-4 hidden md:table-cell">Size</th>
                          <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {files.map(file => (
                          <tr key={file.id} className="border-b border-gray-900/50 hover:bg-gray-900/20 last:border-b-0 transition-colors duration-150">
                            {/* File name & Icon */}
                            <td className="px-6 py-3.5">
                              <div className="flex items-center gap-3 min-w-0">
                                {getFileIcon(file.name)}
                                <span className="text-sm font-medium text-gray-200 truncate max-w-[200px] sm:max-w-xs" title={file.name}>
                                  {file.name}
                                </span>
                              </div>
                            </td>
                            {/* Date */}
                            <td className="px-6 py-3.5 text-sm text-gray-400 hidden sm:table-cell">
                              {formatDate(file.uploaded_at)}
                            </td>
                            {/* Size */}
                            <td className="px-6 py-3.5 text-sm text-gray-400 hidden md:table-cell">
                              {formatBytes(file.size)}
                            </td>
                            {/* Action Buttons */}
                            <td className="px-6 py-3.5 text-right">
                              <div className="flex items-center justify-end gap-2.5">
                                <a 
                                  href={file.file} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="p-1.5 rounded-lg text-gray-400 hover:text-lavender hover:bg-gray-900/50 transition-all duration-150 cursor-pointer"
                                  title="Download file"
                                >
                                  <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                                  </svg>
                                </a>
                                <button 
                                  onClick={() => handleDeleteFile(file.id)}
                                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-gray-900/50 transition-all duration-150 cursor-pointer"
                                  title="Delete file"
                                >
                                  <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                  </svg>
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Fallback Empty State */}
            {folders.length === 0 && files.length === 0 && (
              <div className="py-24 flex flex-col items-center justify-center border border-dashed border-gray-900 rounded-3xl bg-gray-900/5 backdrop-blur-sm">
                <div className="w-14 h-14 rounded-full bg-lavender/5 border border-lavender/10 flex items-center justify-center text-lavender/80 mb-4 animate-pulse">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"></path>
                  </svg>
                </div>
                <p className="text-sm font-bold tracking-wide text-gray-300">
                  This folder is empty
                </p>
                <p className="text-xs text-gray-500 mt-1 max-w-[280px] text-center">
                  Drag and drop files here, or use the action buttons to create folders and upload files.
                </p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Uploading Overlay Indicator */}
      {isUploading && (
        <div className="absolute inset-0 bg-gray-950/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-4">
          <div className="relative w-20 h-20">
            <div className="absolute inset-0 rounded-full border-4 border-lavender/20"></div>
            <div className="absolute inset-0 rounded-full border-4 border-t-lavender animate-spin"></div>
          </div>
          <div className="flex flex-col items-center gap-1">
            <h3 className="text-lg font-bold tracking-tight text-white">Uploading to S3 Bucket...</h3>
            <p className="text-xs text-lavender animate-pulse font-medium">Please do not close this window</p>
          </div>
        </div>
      )}

      {/* Drag & Drop Visual Target Overlay */}
      {isDragging && (
        <div className="absolute inset-0 bg-gray-950/90 backdrop-blur-md z-50 border-4 border-dashed border-lavender m-4 rounded-3xl flex flex-col items-center justify-center gap-4 pointer-events-none transition-all duration-300">
          <div className="w-16 h-16 rounded-full bg-lavender/10 border border-lavender/20 flex items-center justify-center text-lavender">
            <svg className="w-8 h-8 animate-bounce text-lavender" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
            </svg>
          </div>
          <div className="flex flex-col items-center gap-1">
            <h3 className="text-xl font-extrabold tracking-tight text-white">Drop files to upload</h3>
            <p className="text-xs text-lavender font-semibold uppercase tracking-wider">Uploading directly into {currentFolder ? `"${currentFolder.name}"` : 'My Drive'}</p>
          </div>
        </div>
      )}

      {/* Create Folder Modal Dialog */}
      {isCreatingFolder && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div 
            className="w-full max-w-sm p-6 bg-gray-900/90 border border-gray-800 rounded-2xl shadow-2xl flex flex-col gap-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex flex-col gap-1.5">
              <h3 className="text-lg font-bold tracking-tight text-white">New Folder</h3>
              <p className="text-xs text-gray-400">Create a subfolder to organize your assets.</p>
            </div>
            
            <form onSubmit={handleCreateFolder} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <input 
                  type="text" 
                  autoFocus
                  required
                  placeholder="Enter folder name"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  className="px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl focus:outline-none focus:border-lavender text-sm transition-all duration-200 text-white focus:ring-1 focus:ring-lavender/30"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => {
                    setIsCreatingFolder(false);
                    setNewFolderName('');
                  }}
                  className="px-4 py-2.5 text-xs font-semibold text-gray-400 hover:text-white transition-colors duration-200 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4.5 py-2.5 bg-gradient-to-r from-lavender to-blue-brand hover:brightness-110 disabled:from-gray-800 disabled:to-gray-900 disabled:text-gray-500 text-xs font-semibold tracking-wide rounded-xl transition-all duration-200 cursor-pointer shadow-lg shadow-pink-500/10 text-gray-950 font-bold"
                >
                  {actionLoading ? 'Creating...' : 'Create Folder'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
