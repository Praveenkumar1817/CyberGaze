/**
 * PanicButton.jsx — Emergency Incident Response Trigger
 * Connects to Python Core Commander POST /api/commander/trigger-response
 */
import React, { useState } from 'react';
import axios from 'axios';
import { AlertOctagon, Shield, CheckCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react';

const CORE_URL = 'http://localhost:8080';

const SEV = {
    LOW: { color: '#4ade80', bg: 'rgba(74,222,128,0.1)', border: 'rgba(74,222,128,0.25)' },
    MEDIUM: { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)', border: 'rgba(251,191,36,0.25)' },
    HIGH: { color: '#f87171', bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.25)' },
    CRITICAL: { color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', border: 'rgba(167,139,250,0.25)' },
};

function getSeverity(level) {
    if (level >= 10) return 'CRITICAL';
    if (level >= 7) return 'HIGH';
    if (level >= 4) return 'MEDIUM';
    return 'LOW';
}

const LABELS = [
    { min: 1, max: 3, label: 'LOW', desc: 'Recon / Anomaly' },
    { min: 4, max: 6, label: 'MEDIUM', desc: 'Credential Attack' },
    { min: 7, max: 9, label: 'HIGH', desc: 'Active Intrusion' },
    { min: 10, max: 10, label: 'CRITICAL', desc: 'Full Breach' },
];
function getLabel(lvl) { return LABELS.find(l => lvl >= l.min && lvl <= l.max) || LABELS[0]; }

export default function PanicButton() {
    const [level, setLevel] = useState(7);
    const [desc, setDesc] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [stepsOpen, setStepsOpen] = useState(true);

    const sev = getSeverity(level);
    const info = getLabel(level);
    const s = SEV[sev];

    const trigger = async () => {
        setLoading(true); setError(null); setResult(null);
        try {
            const { data } = await axios.post(`${CORE_URL}/api/commander/trigger-response`, {
                threatLevel: level,
                description: desc || `Manual trigger — Level ${level} / ${sev}`,
            }, { timeout: 10000 });
            setResult(data);
            setStepsOpen(true);
        } catch (e) {
            setError(
                e.response?.data?.detail ||
                `Cannot reach Core Commander at port 8080.\nRun: cd core-system && python core_service.py`
            );
        } finally { setLoading(false); }
    };

    return (
        <div className="card flex flex-col" style={{ height: 560 }}>
            {/* Header */}
            <div className="card-header">
                <AlertOctagon size={15} className="text-red" />
                <span className="card-title">Incident Response</span>
                <span className="badge badge-red ml-auto">NIST SP 800-61</span>
            </div>

            <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
                <div className="card-body space-y-5">

                    {/* Threat level */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold uppercase tracking-widest text-secondary">Threat Level</span>
                            <div className="flex items-center gap-2">
                                <span className="mono font-black text-3xl" style={{ color: s.color, lineHeight: 1 }}>{level}</span>
                                <div className="text-right">
                                    <p className="text-xs font-bold" style={{ color: s.color }}>{sev}</p>
                                    <p className="text-xs text-muted">{info.desc}</p>
                                </div>
                            </div>
                        </div>

                        <input
                            type="range" min={1} max={10} value={level}
                            onChange={e => setLevel(Number(e.target.value))}
                            className="range-input w-full"
                            style={{
                                background: `linear-gradient(to right, ${s.color} ${(level - 1) / 9 * 100}%, var(--border) ${(level - 1) / 9 * 100}%)`
                            }}
                        />

                        {/* Scale labels */}
                        <div className="flex justify-between mono text-xs">
                            <span style={{ color: '#4ade80' }}>LOW</span>
                            <span style={{ color: '#fbbf24' }}>MED</span>
                            <span style={{ color: '#f87171' }}>HIGH</span>
                            <span style={{ color: '#a78bfa' }}>CRIT</span>
                        </div>

                        {/* Severity pill */}
                        <div className="rounded-md px-3 py-2 mono text-xs font-semibold"
                            style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.color }}>
                            ⚡ {info.desc} — Level {level}/10
                        </div>
                    </div>

                    {/* Optional description */}
                    <div>
                        <label className="text-xs font-semibold uppercase tracking-widest text-secondary block mb-1.5">
                            Incident Note (optional)
                        </label>
                        <input
                            className="input"
                            placeholder="e.g. Ransomware on FINANCE-PC-001"
                            value={desc}
                            onChange={e => setDesc(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && trigger()}
                        />
                    </div>

                    {/* PANIC BUTTON */}
                    <button
                        className={`btn btn-danger w-full ${loading ? 'pulsing' : ''}`}
                        onClick={trigger}
                        disabled={loading}
                    >
                        <AlertOctagon size={18} />
                        {loading ? 'Triggering Response…' : '⚠ TRIGGER INCIDENT RESPONSE'}
                    </button>

                    {/* Error */}
                    {error && (
                        <div className="rounded-md p-3 mono text-xs whitespace-pre-wrap text-red"
                            style={{ background: 'var(--red-dim)', border: '1px solid rgba(248,113,113,0.25)' }}>
                            {error}
                        </div>
                    )}

                    {/* Result */}
                    {result && (
                        <div className="space-y-3">
                            {/* Incident summary */}
                            <div className="rounded-md p-3 space-y-2"
                                style={{ background: SEV[result.severity]?.bg, border: `1px solid ${SEV[result.severity]?.border}` }}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Shield size={14} style={{ color: SEV[result.severity]?.color }} />
                                        <span className="font-bold mono text-sm" style={{ color: SEV[result.severity]?.color }}>
                                            {result.severity} INCIDENT
                                        </span>
                                    </div>
                                    <span className="badge" style={{
                                        color: SEV[result.severity]?.color,
                                        background: SEV[result.severity]?.bg,
                                        border: `1px solid ${SEV[result.severity]?.border}`,
                                    }}>
                                        Level {result.threatLevel}
                                    </span>
                                </div>
                                <p className="mono text-xs text-muted">{result.incidentId}</p>
                                <p className="text-xs" style={{ color: 'var(--text-primary)' }}>{result.message}</p>
                            </div>

                            {/* Threat context */}
                            {result.threatContext && (
                                <div className="grid grid-cols-2 gap-2">
                                    {Object.entries(result.threatContext).map(([k, v]) => (
                                        <div key={k} className="rounded-md px-3 py-2"
                                            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                                            <p className="text-muted mono" style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                                                {k.replace(/_/g, ' ')}
                                            </p>
                                            <p className="mono text-xs mt-0.5" style={{ color: 'var(--text-primary)' }}>{v}</p>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Playbook steps */}
                            <div>
                                <button
                                    className="flex items-center gap-2 w-full text-left mb-2"
                                    onClick={() => setStepsOpen(o => !o)}
                                >
                                    <Clock size={13} className="text-cyan" />
                                    <span className="text-xs font-bold uppercase tracking-widest text-cyan">
                                        Response Playbook ({result.playbookStepCount} steps)
                                    </span>
                                    {stepsOpen ? <ChevronUp size={13} className="ml-auto text-muted" /> : <ChevronDown size={13} className="ml-auto text-muted" />}
                                </button>

                                {stepsOpen && (
                                    <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
                                        {result.playbookSteps?.map((step, i) => (
                                            <div
                                                key={i}
                                                className="fade-slide flex items-start gap-2 rounded-md px-3 py-2 mono text-xs"
                                                style={{
                                                    background: 'var(--surface)',
                                                    border: '1px solid var(--border)',
                                                    color: 'var(--text-primary)',
                                                    animationDelay: `${i * 40}ms`,
                                                }}
                                            >
                                                <CheckCircle size={11} className="flex-shrink-0 mt-0.5 text-green" />
                                                <span style={{ lineHeight: 1.55 }}>{step}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
