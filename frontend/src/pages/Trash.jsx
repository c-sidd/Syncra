import React, { useEffect, useState } from 'react';
import api from '../utils/api';

const Trash = () => {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try { setFiles((await api.get('/files/trash/')).data); }
    catch { setError('Unable to load Trash.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const restore = async (file) => { try { await api.post(`/files/${file.id}/restore/`); setFiles((items) => items.filter((item) => item.id !== file.id)); } catch { setError('Unable to restore this file.'); } };
  const remove = async (file) => { if (!window.confirm(`Permanently delete "${file.name}"? This cannot be undone.`)) return; try { await api.delete(`/files/${file.id}/permanent/`); setFiles((items) => items.filter((item) => item.id !== file.id)); } catch { setError('Unable to permanently delete this file.'); } };
  return <main className="flex-1 bg-gray-950 text-white p-5 md:p-8"><div className="max-w-5xl mx-auto"><h1 className="text-3xl font-black">Trash</h1><p className="mt-2 text-gray-400">Restore files or permanently remove them from your S3 bucket.</p>{error && <p className="mt-4 rounded-lg bg-red-500/10 p-3 text-red-300">{error}</p>}{loading ? <p className="mt-8 text-gray-400">Loading…</p> : files.length === 0 ? <p className="mt-8 text-gray-500">Trash is empty.</p> : <div className="mt-6 divide-y divide-gray-800 rounded-xl border border-gray-800">{files.map((file) => <div key={file.id} className="flex items-center justify-between gap-3 p-4"><div className="min-w-0"><p className="truncate font-semibold">{file.name}</p><p className="text-xs text-gray-500">Deleted {new Date(file.deleted_at).toLocaleDateString()}</p></div><div className="flex gap-2"><button onClick={() => restore(file)} className="rounded-lg border border-gray-700 px-3 py-2 text-sm">Restore</button><button onClick={() => remove(file)} className="rounded-lg border border-red-500/30 px-3 py-2 text-sm text-red-300">Delete forever</button></div></div>)}</div>}</div></main>;
};
export default Trash;
