import React, { useEffect, useState } from 'react';
import api from '../utils/api';

const Account = () => {
  const [connection, setConnection] = useState(null);
  const [form, setForm] = useState({ name: 'My S3 Storage', access_key_id: '', secret_access_key: '', region: 'us-east-1', bucket_name: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadConnection = async () => {
    try {
      const response = await api.get('/auth/aws/');
      setConnection(response.data.connected ? response.data : null);
      if (response.data.connected) setForm(prev => ({ ...prev, ...response.data, secret_access_key: '' }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load AWS connection.');
    } finally { setLoading(false); }
  };

  useEffect(() => { loadConnection(); }, []);

  const onChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const save = async e => {
    e.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      const response = await api.post('/auth/aws/', form);
      setConnection(response.data);
      setForm(prev => ({ ...prev, secret_access_key: '' }));
      setMessage('AWS S3 connected successfully.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not connect to S3. Check your credentials, bucket and region.');
    } finally { setSaving(false); }
  };

  const disconnect = async () => {
    if (!window.confirm('Disconnect this S3 account from Syncra?')) return;
    await api.delete('/auth/aws/');
    setConnection(null);
    setMessage('S3 connection removed from Syncra.');
    setForm({ name: 'My S3 Storage', access_key_id: '', secret_access_key: '', region: 'us-east-1', bucket_name: '' });
  };

  if (loading) return <div className="flex-1 bg-gray-950 text-white p-8">Loading account...</div>;

  return (
    <main className="flex-1 bg-gray-950 text-white p-4 md:p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <p className="text-sm text-pink">Account</p>
          <h1 className="text-3xl font-bold mt-1">Cloud Storage Connection</h1>
          <p className="text-gray-400 mt-2">Connect your own AWS S3 bucket once. Syncra will use it for your uploads and downloads.</p>
        </div>

        <section className="rounded-2xl border border-gray-800 bg-gray-900/60 p-6 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div><h2 className="text-lg font-semibold">AWS S3</h2><p className="text-sm text-gray-500">Credentials are encrypted before being stored.</p></div>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${connection ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-800 text-gray-400'}`}>{connection ? 'Connected' : 'Not connected'}</span>
          </div>

          <form onSubmit={save} className="space-y-4">
            {[['name','Connection name','text'],['access_key_id','AWS Access Key ID','text'],['secret_access_key','AWS Secret Access Key','password'],['bucket_name','S3 Bucket Name','text']].map(([name,label,type]) => (
              <label key={name} className="block"><span className="block text-sm text-gray-300 mb-2">{label}</span><input name={name} type={type} value={form[name]} onChange={onChange} required={!connection || name !== 'secret_access_key'} placeholder={name === 'secret_access_key' && connection ? 'Leave blank to keep current secret' : ''} className="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 outline-none focus:border-pink text-white" /></label>
            ))}
            <label className="block"><span className="block text-sm text-gray-300 mb-2">AWS Region</span><input name="region" value={form.region} onChange={onChange} required className="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 outline-none focus:border-pink text-white" /></label>

            {error && <div className="rounded-xl border border-red-500/20 bg-red-500/10 text-red-300 p-3 text-sm">{error}</div>}
            {message && <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 p-3 text-sm">{message}</div>}

            <div className="flex gap-3 pt-2"><button disabled={saving} className="rounded-xl px-5 py-3 bg-gradient-to-r from-lavender to-pink text-gray-950 font-bold disabled:opacity-50">{saving ? 'Testing & Saving...' : connection ? 'Update Connection' : 'Connect S3'}</button>{connection && <button type="button" onClick={disconnect} className="rounded-xl px-5 py-3 border border-red-500/30 text-red-300 hover:bg-red-500/10">Disconnect</button>}</div>
          </form>
        </section>

        <section className="rounded-2xl border border-gray-800 bg-gray-900/60 p-6">
          <h2 className="font-semibold">Next-level storage controls</h2>
          <p className="text-sm text-gray-400 mt-2">Storage-class selection and S3 lifecycle rules are planned for the next Syncra storage layer. Your bucket remains under your AWS account.</p>
        </section>
      </div>
    </main>
  );
};

export default Account;
