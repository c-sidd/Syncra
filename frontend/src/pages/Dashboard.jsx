import React, { useContext, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../utils/api';
import { directUpload } from '../utils/directUpload';

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);
  const [currentFolder, setCurrentFolder] = useState(null);
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [path, setPath] = useState([]);
  const [totalStorageUsed, setTotalStorageUsed] = useState(0);
  const [pagination, setPagination] = useState({ folders_page: 1, folders_pages: 1, folders_has_next: false, files_page: 1, files_pages: 1, files_has_next: false, page_size: 50 });
  const [s3Connected, setS3Connected] = useState(false);
  const [bucketName, setBucketName] = useState('');
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const loadConnection = async () => {
    try {
      const response = await api.get('/auth/aws/');
      setS3Connected(Boolean(response.data.connected));
      setBucketName(response.data.bucket_name || '');
    } catch { setS3Connected(false); }
  };

  const loadFolderContents = async (folderId = null, folderPage = 1, filePage = 1) => {
    setLoading(true); setError('');
    try {
      const base = folderId ? `/folders/${folderId}/` : '/folders/';
      const response = await api.get(`${base}?folders_page=${folderPage}&files_page=${filePage}`);
      setFolders(response.data.subfolders || []);
      setFiles(response.data.files || []);
      setTotalStorageUsed(response.data.total_storage_used || 0);
      setPagination(response.data.pagination || pagination);
    } catch (err) { setError(err.response?.data?.detail || 'Unable to load your drive.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadConnection(); loadFolderContents(); }, []);

  const openFolder = (folder) => { setPath((p) => [...p, { id: folder.id, name: folder.name }]); setCurrentFolder(folder); loadFolderContents(folder.id); };
  const goToBreadcrumb = (folder, index = -1) => { if (!folder) { setPath([]); setCurrentFolder(null); loadFolderContents(); } else { setPath((p) => p.slice(0, index + 1)); setCurrentFolder(folder); loadFolderContents(folder.id); } };
  const getReadableError = (err, fallback) => { const data = err.response?.data; if (!data) return fallback; if (typeof data.detail === 'string') return data.detail; const key = Object.keys(data)[0]; if (key && Array.isArray(data[key])) return `${key}: ${data[key][0]}`; return fallback; };

  const handleCreateFolder = async (event) => {
    event.preventDefault(); const name = newFolderName.trim(); if (!name) return;
    setActionLoading(true); setError('');
    try { const response = await api.post('/folders/', { name, parent: currentFolder?.id || null }); setFolders((p) => [...p, response.data]); setNewFolderName(''); setIsCreatingFolder(false); setMessage(`Folder "${name}" created.`); }
    catch (err) { setError(getReadableError(err, 'Could not create the folder.')); }
    finally { setActionLoading(false); }
  };

  const handleFileUpload = async (selectedFiles) => {
    if (!selectedFiles?.length) return;
    if (!s3Connected) { setError('Connect your AWS S3 bucket in Account before uploading files.'); return; }
    setIsUploading(true); setUploadProgress(0); setError(''); setMessage('');
    try {
      for (const file of Array.from(selectedFiles)) {
        const response = await directUpload(file, currentFolder?.id || null, setUploadProgress);
        setFiles((p) => [...p, response]);
        setTotalStorageUsed((p) => p + (response.size || 0));
      }
      setMessage(`${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} uploaded directly to S3.`);
      setUploadProgress(100);
    } catch (err) { setError(getReadableError(err, err.message || 'Upload failed. Check your S3 connection.')); }
    finally { setIsUploading(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const downloadFile = async (file) => { setError(''); try { const response = await api.get(`/files/${file.id}/download/`); window.open(response.data.url, '_blank', 'noopener,noreferrer'); } catch (err) { setError(getReadableError(err, 'Could not create a secure download link.')); } };
  const deleteFile = async (file) => { if (!window.confirm(`Delete "${file.name}" permanently?`)) return; setActionLoading(true); setError(''); try { await api.delete(`/files/${file.id}/`); setFiles((p) => p.filter((i) => i.id !== file.id)); setTotalStorageUsed((p) => Math.max(0, p - (file.size || 0))); setMessage(`"${file.name}" deleted.`); } catch (err) { setError(getReadableError(err, 'Could not delete the file.')); } finally { setActionLoading(false); } };
  const deleteFolder = async (folder) => { if (!window.confirm(`Delete "${folder.name}" and everything inside it?`)) return; setActionLoading(true); setError(''); try { await api.delete(`/folders/${folder.id}/`); await loadFolderContents(currentFolder?.id || null); setMessage(`"${folder.name}" deleted.`); } catch (err) { setError(getReadableError(err, 'Could not delete the folder.')); } finally { setActionLoading(false); } };
  const formatBytes = (bytes) => { if (!bytes) return '0 B'; const units = ['B', 'KB', 'MB', 'GB', 'TB']; const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1); return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`; };
  const formatDate = (date) => date ? new Date(date).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
  const getFileIcon = (name) => { const extension = name.split('.').pop()?.toLowerCase(); const icon = ['jpg','jpeg','png','gif','webp','svg'].includes(extension) ? '▧' : extension === 'pdf' ? 'PDF' : ['mp4','mkv','mov','avi','webm'].includes(extension) ? '▶' : ['mp3','wav','ogg','flac'].includes(extension) ? '♫' : ['zip','rar','7z','tar','gz'].includes(extension) ? 'ZIP' : 'DOC'; return <span className="text-[10px] font-black tracking-tight">{icon}</span>; };
  const handleDragEnter = (event) => { event.preventDefault(); dragCounter.current += 1; if (event.dataTransfer.items?.length) setIsDragging(true); };
  const handleDragLeave = (event) => { event.preventDefault(); dragCounter.current -= 1; if (dragCounter.current <= 0) { dragCounter.current = 0; setIsDragging(false); } };
  const handleDrop = (event) => { event.preventDefault(); dragCounter.current = 0; setIsDragging(false); if (event.dataTransfer.files?.length) handleFileUpload(event.dataTransfer.files); };

  return (
    <div className="relative flex-1 min-h-full bg-gray-950 text-white font-sans overflow-hidden" onDragEnter={handleDragEnter} onDragOver={(e) => e.preventDefault()} onDragLeave={handleDragLeave} onDrop={handleDrop}>
      <input ref={fileInputRef} type="file" multiple className="hidden" onChange={(e) => handleFileUpload(e.target.files)} />
      <main className="h-full overflow-y-auto p-5 md:p-8 lg:p-10 pb-28"><div className="max-w-7xl mx-auto">
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-5 border-b border-gray-900 pb-6"><div><div className="flex items-center gap-3 mb-2"><h1 className="text-3xl md:text-4xl font-black tracking-tight">{currentFolder?.name || 'My Drive'}</h1><span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${s3Connected ? 'text-emerald-300 border-emerald-500/20 bg-emerald-500/10' : 'text-amber-300 border-amber-500/20 bg-amber-500/10'}`}>{s3Connected ? 'S3 connected' : 'S3 not connected'}</span></div><div className="flex items-center gap-1.5 text-xs text-gray-500 overflow-x-auto whitespace-nowrap"><button onClick={() => goToBreadcrumb(null)} className="hover:text-white transition">Root</button>{path.map((item,index)=><React.Fragment key={item.id}><span className="text-gray-700">/</span><button onClick={() => goToBreadcrumb(item,index)} className="hover:text-white transition max-w-36 truncate">{item.name}</button></React.Fragment>)}</div></div><div className="flex flex-wrap gap-2"><button onClick={() => setIsCreatingFolder(true)} className="px-4 py-2.5 rounded-xl border border-gray-800 bg-gray-900/60 hover:bg-gray-800 text-sm font-semibold transition">+ New Folder</button><button onClick={() => fileInputRef.current?.click()} disabled={!s3Connected || isUploading} className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-lavender via-pink to-blue-brand text-gray-950 text-sm font-extrabold transition hover:brightness-110 disabled:opacity-40">↑ Upload File</button></div></header>
        {!s3Connected && <div className="mt-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"><div><p className="font-bold text-amber-200">Connect your own S3 storage to upload files</p><p className="text-sm text-gray-400 mt-1">Syncra stores your files in your AWS bucket.</p></div><button onClick={() => navigate('/account')} className="px-4 py-2 rounded-xl bg-amber-400 text-gray-950 font-bold text-sm">Connect S3</button></div>}
        {error && <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 text-red-300 px-4 py-3 text-sm">{error}</div>}{message && <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 px-4 py-3 text-sm">{message}</div>}
        {isUploading && <div className="mt-5 rounded-xl border border-gray-800 bg-gray-900/60 p-4"><div className="flex justify-between text-xs text-gray-400 mb-2"><span>Uploading directly to S3…</span><span>{Math.round(uploadProgress)}%</span></div><div className="h-2 rounded-full bg-gray-800 overflow-hidden"><div className="h-full bg-lavender transition-all" style={{ width: `${uploadProgress}%` }} /></div></div>}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6"><div className="rounded-2xl border border-gray-900 bg-gray-900/30 p-5"><p className="text-xs text-gray-500 uppercase tracking-wider font-bold">Storage used</p><p className="text-2xl font-black mt-2">{formatBytes(totalStorageUsed)}</p></div><div className="rounded-2xl border border-gray-900 bg-gray-900/30 p-5"><p className="text-xs text-gray-500 uppercase tracking-wider font-bold">Items here</p><p className="text-2xl font-black mt-2">{folders.length + files.length}</p><p className="text-xs text-gray-600 mt-1">Page {pagination.folders_page}/{pagination.folders_pages} folders · {pagination.files_page}/{pagination.files_pages} files</p></div><div className="rounded-2xl border border-gray-900 bg-gray-900/30 p-5"><p className="text-xs text-gray-500 uppercase tracking-wider font-bold">Storage provider</p><p className="text-2xl font-black mt-2 truncate">{s3Connected ? 'Amazon S3' : 'Not connected'}</p><p className="text-xs text-gray-600 mt-1 truncate">{bucketName || 'Connect a bucket in Account'}</p></div></section>
        {loading ? <div className="min-h-80 flex items-center justify-center"><div className="w-9 h-9 rounded-full border-2 border-gray-800 border-t-lavender animate-spin" /></div> : <div className="mt-8 space-y-8"><section><div className="flex items-center justify-between mb-3"><h2 className="text-xs font-bold uppercase tracking-widest text-gray-500">Folders</h2><span className="text-xs text-gray-600">{folders.length}</span></div><div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">{folders.map((folder)=><div key={folder.id} className="rounded-2xl border border-gray-900 bg-gray-900/30 p-4 flex items-center justify-between"><button onClick={()=>openFolder(folder)} className="min-w-0 text-left"><div className="font-bold truncate">📁 {folder.name}</div></button><button onClick={()=>deleteFolder(folder)} disabled={actionLoading} className="text-gray-500 hover:text-red-300">⋯</button></div>)}</div></section><section><div className="flex items-center justify-between mb-3"><h2 className="text-xs font-bold uppercase tracking-widest text-gray-500">Files</h2><span className="text-xs text-gray-600">{files.length}</span></div><div className="rounded-2xl border border-gray-900 overflow-hidden"><div className="divide-y divide-gray-900">{files.map((file)=><div key={file.id} className="flex items-center justify-between gap-4 p-4 bg-gray-900/20"><div className="min-w-0 flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-gray-900 flex items-center justify-center">{getFileIcon(file.name)}</div><div className="min-w-0"><p className="font-semibold truncate">{file.name}</p><p className="text-xs text-gray-600">{formatBytes(file.size)} · {formatDate(file.uploaded_at)}</p></div></div><div className="flex gap-2 shrink-0"><button onClick={()=>downloadFile(file)} className="px-3 py-2 rounded-lg border border-gray-800 text-xs">Download</button><button onClick={()=>deleteFile(file)} disabled={actionLoading} className="px-3 py-2 rounded-lg border border-gray-800 text-xs hover:text-red-300">Delete</button></div></div>)}</div></div></section></div>}
        {(pagination.folders_has_next || pagination.files_has_next || pagination.folders_page > 1 || pagination.files_page > 1) && <div className="mt-6 flex flex-wrap gap-2 justify-center"><button disabled={pagination.folders_page<=1} onClick={()=>loadFolderContents(currentFolder?.id||null, Math.max(1,pagination.folders_page-1), pagination.files_page)} className="px-3 py-2 rounded-lg border border-gray-800 disabled:opacity-30">← Folders</button><span className="px-3 py-2 text-xs text-gray-500">Folders {pagination.folders_page}/{pagination.folders_pages} · Files {pagination.files_page}/{pagination.files_pages}</span><button disabled={!pagination.folders_has_next} onClick={()=>loadFolderContents(currentFolder?.id||null, pagination.folders_page+1, pagination.files_page)} className="px-3 py-2 rounded-lg border border-gray-800 disabled:opacity-30">Folders →</button><button disabled={!pagination.files_has_next} onClick={()=>loadFolderContents(currentFolder?.id||null, pagination.folders_page, pagination.files_page+1)} className="px-3 py-2 rounded-lg border border-gray-800 disabled:opacity-30">Files →</button></div>}
      </div></main>
    </div>
  );
};
export default Dashboard;
