/**
 * App.jsx — CyberGaze Dashboard Shell
 * Three-panel DFIR command center
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Cpu, Wifi, WifiOff, Terminal, RefreshCw, Eye } from 'lucide-react';
import ForensicChat from './components/ForensicChat';
import IncidentTimeline from './components/IncidentTimeline';
import PanicButton from './components/PanicButton';

const AI_URL = 'http://localhost:8000';
const CORE_URL = 'http://localhost:8080';

function useServiceStatus(url, key) {
    const [status, setStatus] = useState('checking');
    const check = async () => {
        setStatus('checking');
        try {
            await axios.get(`${url}${key}`, { timeout: 4000 });
            setStatus('online');
        } catch {
            setStatus('offline');
        }
    };
    useEffect(() => { check(); const t = setInterval(check, 20000); return () => clearInterval(t); }, []);
    return [status, check];
}

function ServicePill({ name, status, onRefresh }) {
    return (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className={`status-dot ${status}`} />
            <span className="mono text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>{name}</span>
            <button onClick={onRefresh} className="hover:text-cyan transition-colors" style={{ color: 'var(--text-muted)', lineHeight: 1 }}>
                <RefreshCw size={10} />
            </button>
        </div>
    );
}

function Clock() {
    const [t, setT] = useState(new Date());
    useEffect(() => { const i = setInterval(() => setT(new Date()), 1000); return () => clearInterval(i); }, []);
    return (
        <div className="text-right">
            <div className="mono font-bold text-cyan" style={{ fontSize: 15 }}>{t.toLocaleTimeString('en-GB')}</div>
            <div className="mono text-xs text-muted">{t.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</div>
        </div>
    );
}

export default function App() {
    const [aiStatus, checkAI] = useServiceStatus(AI_URL, '/health');
    const [coreStatus, checkCore] = useServiceStatus(CORE_URL, '/api/commander/health');
    const [ingesting, setIngesting] = useState(false);
    const [ingestMsg, setIngestMsg] = useState(null);

    const ingest = async () => {
        setIngesting(true); setIngestMsg(null);
        try {
            const { data } = await axios.post(`${AI_URL}/ingest`, {}, { timeout: 15000 });
            setIngestMsg({ ok: true, text: `✓ Ingested ${data.message}` });
        } catch (e) {
            setIngestMsg({ ok: false, text: e.response?.data?.detail || 'Ingest failed — is AI service running?' });
        } finally { setIngesting(false); }
    };

    /* auto-ingest once AI service appears online */
    useEffect(() => {
        if (aiStatus === 'online') ingest();
    }, [aiStatus]);

    const allOnline = aiStatus === 'online' && coreStatus === 'online';

    return (
        <div style={{ background: 'var(--bg)', minHeight: '100vh', fontFamily: 'var(--font-sans)' }}>
            {/* ── Top Navigation Bar ─────────────────────── */}
            <header style={{ background: 'var(--surface)', borderBottom: '1px solid var(--border)' }}>
                <div style={{ maxWidth: 1600, margin: '0 auto', padding: '0 24px' }}>
                    <div className="flex items-center justify-between" style={{ height: 56 }}>

                        {/* Logo */}
                        <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center rounded-lg"
                                style={{ width: 36, height: 36, background: 'var(--cyan-dim)', border: '1px solid rgba(34,211,238,0.3)' }}>
                                <Eye size={18} className="text-cyan" />
                            </div>
                            <div>
                                <div className="font-black mono text-base tracking-widest text-cyan">CYBER<span style={{ color: 'var(--text-secondary)' }}>GAZE</span></div>
                                <div className="mono text-xs text-muted" style={{ lineHeight: 1 }}>DFIR Command Center · v1.0</div>
                            </div>
                        </div>

                        {/* Service status pills */}
                        <div className="flex items-center gap-2">
                            <ServicePill name="AI Engine :8000" status={aiStatus} onRefresh={checkAI} />
                            <ServicePill name="Commander :8080" status={coreStatus} onRefresh={checkCore} />
                        </div>

                        {/* Right: ingest + clock */}
                        <div className="flex items-center gap-4">
                            <button className="btn btn-cyan" onClick={ingest} disabled={ingesting || aiStatus !== 'online'}>
                                {ingesting
                                    ? <><RefreshCw size={12} className="animate-spin" /> Ingesting…</>
                                    : <><Terminal size={12} /> Re-Ingest Logs</>
                                }
                            </button>
                            <Clock />
                        </div>
                    </div>
                </div>
            </header>

            {/* ── Ingest status banner ────────────────────── */}
            {ingestMsg && (
                <div className="text-center py-1.5 mono text-xs"
                    style={{
                        background: ingestMsg.ok ? 'var(--green-dim)' : 'var(--red-dim)',
                        color: ingestMsg.ok ? 'var(--green)' : 'var(--red)',
                        borderBottom: `1px solid ${ingestMsg.ok ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)'}`,
                    }}>
                    {ingestMsg.text}
                </div>
            )}

            {/* ── All-offline warning ─────────────────────── */}
            {aiStatus === 'offline' && coreStatus === 'offline' && (
                <div className="flex items-center justify-center gap-2 py-2 mono text-xs"
                    style={{ background: 'rgba(251,191,36,0.08)', borderBottom: '1px solid rgba(251,191,36,0.2)', color: 'var(--amber)' }}>
                    <WifiOff size={12} />
                    All services offline — see README.md for startup instructions
                </div>
            )}

            {/* ── Main 3-column grid ──────────────────────── */}
            <main style={{ maxWidth: 1600, margin: '0 auto', padding: '24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20, alignItems: 'start' }}>
                    {/* Col 1 — Incident Timeline */}
                    <div>
                        <IncidentTimeline />
                    </div>

                    {/* Col 2 — AI Chat */}
                    <div>
                        <ForensicChat />
                    </div>

                    {/* Col 3 — Panic Button */}
                    <div>
                        <PanicButton />
                    </div>
                </div>

                {/* ── Footer ──────────────────────────────────── */}
                <footer className="mono text-center text-xs text-muted" style={{ marginTop: 24, paddingBottom: 16 }}>
                    CyberGaze DFIR · AI Service (Python/FastAPI) · Core Commander (Python/FastAPI) · Dashboard (React/Vite)
                </footer>
            </main>
        </div>
    );
}
