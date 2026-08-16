import React, { useContext, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../utils/api';

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
  const [s3Connected, setS3Connected] = useState(false);
  const [bucketName, setBucketName] = useState('');
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [isHowItWorksOpen, setIsHowItWorksOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const loadConnection = async () => {
    try {
      const response = await api.get('/auth/aws/');
      setS3Connected(Boolean(response.data.connected));
      setBucketName(response.data.bucket_name || '');
    } catch (err) {
      setS3Connected(false);
    }
  };

  const loadFolderContents = async (folderId = null) => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get(folderId ? `/folders/${folderId}/` : '/folders/');
      setFolders(response.data.subfolders || []);
      setFiles(response.data.files || []);
      setTotalStorageUsed(response.data.total_storage_used || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load your drive.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConnection();
    loadFolderContents();
  }, []);

  const openFolder = (folder) => {
    setPath((previous) => [...previous, { id: folder.id, name: folder.name }]);
    setCurrentFolder(folder);
    loadFolderContents(folder.id);
  };

  const goToBreadcrumb = (folder, index = -1) => {
    if (!folder) {
      setPath([]);
      setCurrentFolder(null);
      loadFolderContents();
      return;
    }
    setPath((previous) => previous.slice(0, index + 1));
    setCurrentFolder(folder);
    loadFolderContents(folder.id);
  };

  const getReadableError = (err, fallback) => {
    const data = err.response?.data;
    if (!data) return fallback;
    if (typeof data.detail === 'string') return data.detail;
    const key = Object.keys(data)[0];
    if (key && Array.isArray(data[key])) return `${key}: ${data[key][0]}`;
    return fallback;
  };

  const handleCreateFolder = async (event) => {
    event.preventDefault();
    const name = newFolderName.trim();
    if (!name) return;

    setActionLoading(true);
    setError('');
    try {
      const response = await api.post('/folders/', {
        name,
        parent: currentFolder?.id || null,
      });
      setFolders((previous) => [...previous, response.data]);
      setNewFolderName('');
      setIsCreatingFolder(false);
      setMessage(`Folder "${name}" created.`);
    } catch (err) {
      setError(getReadableError(err, 'Could not create the folder.'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleFileUpload = async (selectedFiles) => {
    if (!selectedFiles?.length) return;
    if (!s3Connected) {
      setError('Connect your AWS S3 bucket in Account before uploading files.');
      return;
    }

    setIsUploading(true);
    setError('');
    setMessage('');
    try {
      for (const file of Array.from(selectedFiles)) {
        const formData = new FormData();
        formData.append('file', file);
        if (currentFolder) formData.append('folder', currentFolder.id);

        const response = await api.post('/files/upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        setFiles((previous) => [...previous, response.data]);
        setTotalStorageUsed((previous) => previous + (response.data.size || 0));
      }
      setMessage(`${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} uploaded to S3.`);
    } catch (err) {
      setError(getReadableError(err, 'Upload failed. Check your S3 connection.'));
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const downloadFile = async (file) => {
    setError('');
    try {
      const response = await api.get(`/files/${file.id}/download/`);
      window.open(response.data.url, '_blank', 'noopener,noreferrer');
    } catch (err) {
      setError(getReadableError(err, 'Could not create a secure download link.'));
    }
  };

  const deleteFile = async (file) => {
    if (!window.confirm(`Delete "${file.name}" permanently?`)) return;
    setActionLoading(true);
    setError('');
    try {
      await api.delete(`/files/${file.id}/`);
      setFiles((previous) => previous.filter((item) => item.id !== file.id));
      setTotalStorageUsed((previous) => Math.max(0, previous - (file.size || 0)));
      setMessage(`"${file.name}" deleted.`);
    } catch (err) {
      setError(getReadableError(err, 'Could not delete the file.'));
    } finally {
      setActionLoading(false);
    }
  };

  const deleteFolder = async (folder) => {
    if (!window.confirm(`Delete "${folder.name}" and everything inside it?`)) return;
    setActionLoading(true);
    setError('');
    try {
      await api.delete(`/folders/${folder.id}/`);
      await loadFolderContents(currentFolder?.id || null);
      setMessage(`"${folder.name}" deleted.`);
    } catch (err) {
      setError(getReadableError(err, 'Could not delete the folder.'));
    } finally {
      setActionLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
  };

  const formatDate = (date) => date
    ? new Date(date).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })
    : '—';

  const getFileIcon = (name) => {
    const extension = name.split('.').pop()?.toLowerCase();
    const icon = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(extension) ? '▧'
      : extension === 'pdf' ? 'PDF'
      : ['mp4', 'mkv', 'mov', 'avi', 'webm'].includes(extension) ? '▶'
      : ['mp3', 'wav', 'ogg', 'flac'].includes(extension) ? '♫'
      : ['zip', 'rar', '7z', 'tar', 'gz'].includes(extension) ? 'ZIP'
      : 'DOC';
    return <span className="text-[10px] font-black tracking-tight">{icon}</span>;
  };

  const handleDragEnter = (event) => {
    event.preventDefault();
    dragCounter.current += 1;
    if (event.dataTransfer.items?.length) setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      dragCounter.current = 0;
      setIsDragging(false);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    dragCounter.current = 0;
    setIsDragging(false);
    if (event.dataTransfer.files?.length) handleFileUpload(event.dataTransfer.files);
  };

  return (
    <div
      className="relative flex-1 min-h-full bg-gray-950 text-white font-sans overflow-hidden"
      onDragEnter={handleDragEnter}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input ref={fileInputRef} type="file" multiple className="hidden" onChange={(event) => handleFileUpload(event.target.files)} />

      <main className="h-full overflow-y-auto p-5 md:p-8 lg:p-10 pb-28">
        <div className="max-w-7xl mx-auto">
          <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-5 border-b border-gray-900 pb-6">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl md:text-4xl font-black tracking-tight">{currentFolder?.name || 'My Drive'}</h1>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${s3Connected ? 'text-emerald-300 border-emerald-500/20 bg-emerald-500/10' : 'text-amber-300 border-amber-500/20 bg-amber-500/10'}`}>
                  {s3Connected ? 'S3 connected' : 'S3 not connected'}
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-500 overflow-x-auto whitespace-nowrap">
                <button onClick={() => goToBreadcrumb(null)} className="hover:text-white transition">Root</button>
                {path.map((item, index) => (
                  <React.Fragment key={item.id}>
                    <span className="text-gray-700">/</span>
                    <button onClick={() => goToBreadcrumb(item, index)} className="hover:text-white transition max-w-36 truncate">{item.name}</button>
                  </React.Fragment>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button onClick={() => setIsCreatingFolder(true)} className="px-4 py-2.5 rounded-xl border border-gray-800 bg-gray-900/60 hover:bg-gray-800 text-sm font-semibold transition flex items-center gap-2">
                <span className="text-lg leading-none">+</span> New Folder
              </button>
              <button onClick={() => fileInputRef.current?.click()} disabled={!s3Connected || isUploading} className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-lavender via-pink to-blue-brand text-gray-950 text-sm font-extrabold transition hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2">
                ↑ Upload File
              </button>
            </div>
          </header>

          {!s3Connected && (
            <div className="mt-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <p className="font-bold text-amber-200">Connect your own S3 storage to upload files</p>
                <p className="text-sm text-gray-400 mt-1">Syncra stores your files in your AWS bucket. Your AWS secret key is encrypted in the database.</p>
              </div>
              <button onClick={() => navigate('/account')} className="shrink-0 px-4 py-2 rounded-xl bg-amber-400 text-gray-950 font-bold text-sm hover:brightness-110">Connect S3</button>
            </div>
          )}

          {error && <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 text-red-300 px-4 py-3 text-sm">{error}</div>}
          {message && <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 px-4 py-3 text-sm">{message}</div>}

          <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="rounded-2xl border border-gray-900 bg-gray-900/30 p-5">
              <p className="text-xs text-gray-500 uppercase tracking-wider font-bold">Storage used</p>
              <p className="text-2xl font-black mt-2">{formatBytes(totalStorageUsed)}</p>
              <p className="text-xs text-gray-600 mt-1">Calculated from your Syncra files</p>
            </div>
            <div className="rounded-2xl border border-gray-900 bg-gray-900/30 p-5">
              <p className="text-xs text-gray-500 uppercase tracking-wider font-bold">Items here</p>
              <p className="text-2xl font-black mt-2">{folders.length + files.length}</p>
              <p className="text-xs text-gray-600 mt-1">{folders.length} folders · {files.length} files</p>
            </div>
            <div className="rounded-2xl border border-gray-900 bg-gray-900/30 p-5">
              <p className="text-xs text-gray-500 uppercase tracking-wider font-bold">Storage provider</p>
              <p className="text-2xl font-black mt-2 truncate">{s3Connected ? 'Amazon S3' : 'Not connected'}</p>
              <p className="text-xs text-gray-600 mt-1 truncate">{bucketName || 'Connect a bucket in Account'}</p>
            </div>
          </section>

          {loading ? (
            <div className="min-h-80 flex items-center justify-center"><div className="w-9 h-9 rounded-full border-2 border-gray-800 border-t-lavender animate-spin" /></div>
          ) : folders.length === 0 && files.length === 0 ? (
            <div className="mt-6 min-h-96 rounded-3xl border border-dashed border-gray-800 bg-gray-900/10 flex flex-col items-center justify-center text-center px-6">
              <div className="w-16 h-16 rounded-2xl bg-lavender/10 border border-lavender/20 flex items-center justify-center text-2xl mb-5">☁</div>
              <h2 className="text-xl font-bold">Your drive is empty</h2>
              <p className="text-sm text-gray-500 max-w-md mt-2">Create a folder or upload your first file. Once S3 is connected, uploads go directly to your own AWS bucket.</p>
              <div className="flex gap-2 mt-5">
                <button onClick={() => setIsCreatingFolder(true)} className="px-4 py-2 rounded-xl border border-gray-800 bg-gray-900 font-semibold text-sm">Create folder</button>
                <button onClick={() => s3Connected ? fileInputRef.current?.click() : navigate('/account')} className="px-4 py-2 rounded-xl bg-white text-gray-950 font-bold text-sm">{s3Connected ? 'Upload a file' : 'Connect S3'}</button>
              </div>
            </div>
          ) : (
            <div className="mt-8 space-y-8">
              {folders.length > 0 && (
                <section>
                  <div className="flex items-center justify-between mb-3"><h2 className="text-xs font-bold uppercase tracking-widest text-gray-500">Folders</h2><span className="text-xs text-gray-600">{folders.length}</span></div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {folders.map((folder) => (
                      <div key={folder.id} className="group rounded-2xl border border-gray-900 bg-gray-900/25 hover:bg-gray-900/60 hover:border-gray-800 transition p-4 flex items-center gap-3">
                        <button onClick={() => openFolder(folder)} className="flex items-center gap-3 min-w-0 flex-1 text-left">
                          <span className="w-10 h-10 shrink-0 rounded-xl bg-lavender/10 border border-lavender/20 flex items-center justify-center text-lavender">▰</span>
                          <span className="truncate text-sm font-semibold text-gray-200">{folder.name}</span>
                        </button>
                        <button disabled={actionLoading} onClick={() => deleteFolder(folder)} className="opacity-0 group-hover:opacity-100 p-2 text-gray-600 hover:text-red-400 transition" title="Delete folder">×</button>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {files.length > 0 && (
                <section>
                  <div className="flex items-center justify-between mb-3"><h2 className="text-xs font-bold uppercase tracking-widest text-gray-500">Files</h2><span className="text-xs text-gray-600">{files.length}</span></div>
                  <div className="rounded-2xl border border-gray-900 overflow-hidden bg-gray-900/15">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left">
                        <thead className="bg-gray-900/50 border-b border-gray-900"><tr><th className="px-5 py-3 text-[10px] uppercase tracking-widest text-gray-600">Name</th><th className="px-5 py-3 text-[10px] uppercase tracking-widest text-gray-600 hidden sm:table-cell">Uploaded</th><th className="px-5 py-3 text-[10px] uppercase tracking-widest text-gray-600 hidden md:table-cell">Size</th><th className="px-5 py-3" /></tr></thead>
                        <tbody className="divide-y divide-gray-900">
                          {files.map((file) => (
                            <tr key={file.id} className="hover:bg-gray-900/40 transition">
                              <td className="px-5 py-4"><div className="flex items-center gap-3 min-w-0"><span className="w-9 h-9 shrink-0 rounded-lg bg-gray-900 border border-gray-800 flex items-center justify-center text-gray-400">{getFileIcon(file.name)}</span><span className="text-sm font-medium truncate max-w-[260px]" title={file.name}>{file.name}</span></div></td>
                              <td className="px-5 py-4 text-xs text-gray-500 hidden sm:table-cell">{formatDate(file.uploaded_at)}</td>
                              <td className="px-5 py-4 text-xs text-gray-500 hidden md:table-cell">{formatBytes(file.size)}</td>
                              <td className="px-5 py-4"><div className="flex justify-end gap-1"><button onClick={() => downloadFile(file)} className="px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-400 hover:text-white hover:bg-gray-800 transition">Download</button><button disabled={actionLoading} onClick={() => deleteFile(file)} className="px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-500 hover:text-red-300 hover:bg-red-500/10 transition">Delete</button></div></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </section>
              )}
            </div>
          )}
        </div>
      </main>

      <button onClick={() => setIsHowItWorksOpen(true)} className="fixed right-5 bottom-5 z-40 px-4 py-3 rounded-2xl border border-gray-700 bg-gray-900/95 backdrop-blur text-sm font-bold shadow-2xl hover:bg-gray-800 hover:border-lavender/40 transition flex items-center gap-2">
        <span className="w-6 h-6 rounded-full bg-lavender/15 text-lavender flex items-center justify-center">?</span>
        How it works
      </button>

      {isDragging && <div className="fixed inset-4 z-50 rounded-3xl border-2 border-dashed border-lavender bg-gray-950/90 backdrop-blur flex flex-col items-center justify-center pointer-events-none"><div className="text-5xl mb-4">↑</div><h2 className="text-2xl font-black">Drop files to upload</h2><p className="text-sm text-gray-500 mt-2">Files will be sent to your connected S3 bucket</p></div>}

      {isUploading && <div className="fixed inset-0 z-[60] bg-gray-950/75 backdrop-blur-sm flex items-center justify-center"><div className="rounded-2xl border border-gray-800 bg-gray-900 p-7 text-center shadow-2xl"><div className="w-10 h-10 rounded-full border-2 border-gray-700 border-t-pink animate-spin mx-auto" /><h3 className="font-bold mt-4">Uploading to S3</h3><p className="text-xs text-gray-500 mt-1">Keep this tab open until the upload finishes.</p></div></div>}

      {isCreatingFolder && <div className="fixed inset-0 z-[70] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => !actionLoading && setIsCreatingFolder(false)}><div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl" onClick={(event) => event.stopPropagation()}><h2 className="text-xl font-bold">Create folder</h2><p className="text-sm text-gray-500 mt-1">Organize your files inside My Drive.</p><form onSubmit={handleCreateFolder} className="mt-5"><input autoFocus value={newFolderName} onChange={(event) => setNewFolderName(event.target.value)} placeholder="Folder name" className="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm outline-none focus:border-lavender" /><div className="flex justify-end gap-2 mt-4"><button type="button" disabled={actionLoading} onClick={() => setIsCreatingFolder(false)} className="px-4 py-2 rounded-xl text-sm text-gray-400">Cancel</button><button disabled={actionLoading || !newFolderName.trim()} className="px-4 py-2 rounded-xl bg-gradient-to-r from-lavender to-pink text-gray-950 font-bold text-sm">{actionLoading ? 'Creating...' : 'Create'}</button></div></form></div></div>}

      {isHowItWorksOpen && <div className="fixed inset-0 z-[80] bg-black/75 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => setIsHowItWorksOpen(false)}><div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-3xl border border-gray-800 bg-gray-950 shadow-2xl" onClick={(event) => event.stopPropagation()}><div className="p-6 md:p-8 border-b border-gray-900 flex items-start justify-between gap-5"><div><p className="text-xs uppercase tracking-widest text-pink font-bold">Syncra</p><h2 className="text-2xl md:text-3xl font-black mt-1">How it works</h2><p className="text-sm text-gray-500 mt-2">Your account is the control plane. Your AWS S3 bucket is the actual storage.</p></div><button onClick={() => setIsHowItWorksOpen(false)} className="text-2xl text-gray-500 hover:text-white">×</button></div><div className="p-6 md:p-8 space-y-4"><div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5"><b>1. Create a Syncra account</b><p className="text-sm text-gray-500 mt-1">Your login is stored in PostgreSQL. Authentication uses a token so the browser can access protected API endpoints.</p></div><div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5"><b>2. Connect AWS S3 once</b><p className="text-sm text-gray-500 mt-1">In Account, enter your S3 access key, secret key, region and bucket. Syncra encrypts the secret key before storing it.</p></div><div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5"><b>3. Upload</b><p className="text-sm text-gray-500 mt-1">Syncra sends the file to your bucket under a user-specific prefix, while PostgreSQL keeps the file metadata needed to show your Drive.</p></div><div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5"><b>4. Download securely</b><p className="text-sm text-gray-500 mt-1">Syncra creates a short-lived S3 presigned URL. Your AWS secret key never goes to the browser.</p></div><div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5"><b>5. Automatic Glacier lifecycle</b><p className="text-sm text-gray-500 mt-1">From Account, you can configure an S3 lifecycle rule to transition old Syncra objects to Intelligent-Tiering, Glacier or Deep Archive.</p></div><div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-5"><b className="text-blue-200">About the storage number</b><p className="text-sm text-gray-400 mt-1">The old “0 of 15 GB” label was an arbitrary Syncra UI limit, not your AWS S3 capacity. It has been removed. Syncra now shows the storage actually represented by your files instead of pretending that AWS gives you a 15 GB quota.</p></div></div></div></div>}
    </div>
  );
};

export default Dashboard;
