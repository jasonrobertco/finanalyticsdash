'use client';

import { useEffect, useState } from 'react';

export default function Home() {
  const [status, setStatus] = useState('checking...');

  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status === 'ok' ? 'connected' : 'unhealthy'))
      .catch(() => setStatus('not connected'));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">Finance Analytics Dashboard</h1>
      <p className="text-xl text-gray-600">Backend status: {status}</p>
    </main>
  );
}