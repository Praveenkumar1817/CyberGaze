/**
 * IncidentTimeline.jsx — Log Timeline + FP-Growth Mining Results
 * Connects to Python AI Service GET /logs and POST /mine
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Activity, Search, RefreshCw, ChevronDown, ChevronRight, AlertTriangle } from 'lucide-react';

const AI_URL = 'http://localhost:8000';

const EVENT_COLOR = {
    'Login': '#22d3ee',
    'Failed Login': '#f87171',
    'File Access': '#fbbf24',
    'Port Scan': '#fb923c',
    'Privilege Escalation': '#a78bfa',
    'Lateral Movement': '#f97316',
    'Data Exfiltration': '#ef4444',
    'Malware Execution': '#dc2626',
    'Brute Force': '#ff1a4a',
    'USB Insertion': '#818cf8',
};

function ChartTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 6, padding: '6px 12px' }}>
            <p className="mono text-xs text-cyan">{label}</p>
            <p className="mono text-xs" style={{ color: 'var(--text-primary)' }}>Count: {payload[0].value}</p>
        </div>
    );
}

export default function IncidentTimeline() {
    const [logs, setLogs] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [patterns, setPatterns] = useState(null);
    const [expandedIdx, setExpandedIdx] = useState(null);
    const [filter, setFilter] = useState('');
    const [loadingLogs, setLoadingLogs] = useState(false);
    const [loadingMine, setLoadingMine] = useState(false);
    const [error, setError] = useState(null);

    const fetchLogs = async () => {
        setLoadingLogs(true); setError(null);
        try {
            const { data } = await axios.get(`${AI_URL}/logs`);
            setLogs(data.logs);
            const counts = {};
            data.logs.forEach(l => { counts[l.event_type] = (counts[l.event_type] || 0) + 1; });
            setChartData(Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([name, count]) => ({ name, count })));
        } catch (e) {
            setError(e.response?.data?.detail || 'Cannot reach AI service — is it running?');
        } finally { setLoadingLogs(false); }
    };

    const runMining = async () => {
        setLoadingMine(true); setError(null);
        try {
            const { data } = await axios.post(`${AI_URL}/mine`, { min_support: 0.1, min_confidence: 0.3 });
            setPatterns(data);
        } catch (e) {
            setError(e.response?.data?.detail || 'Mining failed.');
        } finally { setLoadingMine(false); }
    };

    useEffect(() => { fetchLogs(); }, []);

    const filtered = logs.filter(l =>
        !filter || [l.event_type, l.source_ip, l.status].some(v => v.toLowerCase().includes(filter.toLowerCase()))
    );

    return (
        <div className="card flex flex-col" style={{ height: 560 }}>
            {/* Header */}
            <div className="card-header">
                <Activity size={15} className="text-cyan" />
                <span className="card-title">Incident Timeline</span>
                {logs.length > 0 && <span className="badge badge-cyan">{logs.length} events</span>}
                <div className="flex gap-2 ml-auto">
                    <button className="btn btn-ghost" onClick={runMining} disabled={loadingMine || !logs.length}>
                        <Search size={12} />{loadingMine ? 'Mining…' : 'FP-Growth'}
                    </button>
                    <button className="btn btn-ghost" onClick={fetchLogs} disabled={loadingLogs}>
                        <RefreshCw size={12} className={loadingLogs ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Scrollable body */}
            <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
                {/* Error */}
                {error && (
                    <div className="mx-4 mt-3 flex gap-2 items-start p-3 rounded-md text-xs mono text-red"
                        style={{ background: 'var(--red-dim)', border: '1px solid rgba(248,113,113,0.25)' }}>
                        <AlertTriangle size={13} className="flex-shrink-0 mt-0.5" />{error}
                    </div>
                )}

                {/* Bar chart */}
                {chartData.length > 0 && (
                    <div className="px-4 pt-3 pb-1">
                        <p className="text-xs text-muted mono uppercase tracking-widest mb-2">Event Distribution</p>
                        <ResponsiveContainer width="100%" height={120}>
                            <BarChart data={chartData} margin={{ top: 0, right: 0, left: -28, bottom: 0 }}>
                                <XAxis dataKey="name" tick={{ fontSize: 8, fill: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}
                                    angle={-20} textAnchor="end" height={42} />
                                <YAxis tick={{ fontSize: 8, fill: 'var(--text-muted)' }} />
                                <Tooltip content={<ChartTooltip />} />
                                <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                                    {chartData.map((e, i) => <Cell key={i} fill={EVENT_COLOR[e.name] || '#22d3ee'} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* FP-Growth patterns */}
                {patterns && (
                    <div className="px-4 py-3 space-y-2">
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-bold uppercase tracking-widest text-purple">
                                🔬 Patterns ({patterns.association_rules?.length ?? 0} rules)
                            </p>
                            <button className="text-xs text-muted hover:text-red" onClick={() => setPatterns(null)}>✕</button>
                        </div>
                        {patterns.association_rules?.length === 0 && (
                            <p className="text-xs text-muted">No patterns found. Try lowering min_support.</p>
                        )}
                        {patterns.association_rules?.slice(0, 5).map((r, i) => (
                            <div key={i} className="rounded-md px-3 py-2 space-y-1"
                                style={{ background: 'var(--purple-dim)', border: '1px solid rgba(167,139,250,0.2)' }}>
                                <p className="mono text-xs" style={{ color: 'var(--text-primary)' }}>{r.rule}</p>
                                <div className="flex gap-3">
                                    <span className="mono text-xs text-purple">Conf {(r.confidence * 100).toFixed(0)}%</span>
                                    <span className="mono text-xs text-cyan">Lift {r.lift}×</span>
                                    <span className="mono text-xs text-amber">{r.threat_label?.split(' – ')[0]}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Filter */}
                {logs.length > 0 && (
                    <div className="px-4 pb-2">
                        <input className="input" placeholder="Filter by IP, event type, or status…"
                            value={filter} onChange={e => setFilter(e.target.value)} />
                    </div>
                )}

                {/* Timeline list */}
                <div className="px-4 pb-4 space-y-0">
                    {loadingLogs && (
                        <div className="py-10 text-center mono text-xs text-muted dot-loader">
                            Loading<span>.</span><span>.</span><span>.</span>
                        </div>
                    )}
                    {!loadingLogs && filtered.length === 0 && !error && (
                        <p className="py-10 text-center text-xs text-muted">
                            {logs.length === 0 ? 'No logs loaded — call POST /ingest first.' : 'No matching events.'}
                        </p>
                    )}

                    {filtered.map((log, i) => {
                        const open = expandedIdx === i;
                        const color = EVENT_COLOR[log.event_type] || '#64748b';
                        const isSuccess = log.status === 'Success';

                        return (
                            <div key={i} className="flex gap-3 group">
                                {/* Spine */}
                                <div className="flex flex-col items-center" style={{ width: 14, flexShrink: 0 }}>
                                    <div className="rounded-full mt-3.5 flex-shrink-0"
                                        style={{
                                            width: 8, height: 8,
                                            background: open ? color : 'transparent',
                                            border: `2px solid ${color}`,
                                            boxShadow: open ? `0 0 6px ${color}` : 'none',
                                            transition: 'all 0.2s',
                                        }}
                                    />
                                    {i < filtered.length - 1 && <div className="timeline-line" />}
                                </div>

                                {/* Row */}
                                <div className="flex-1 py-2 cursor-pointer select-none"
                                    onClick={() => setExpandedIdx(open ? null : i)}>
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="mono text-xs font-semibold" style={{ color }}>{log.event_type}</span>
                                        <span className={`badge ${isSuccess ? 'badge-green' : 'badge-red'}`}>{log.status}</span>
                                        <span className="mono text-xs text-cyan">{log.source_ip}</span>
                                        <span className="mono text-xs text-muted ml-auto">{log.timestamp?.split(' ')[1]}</span>
                                        {open
                                            ? <ChevronDown size={12} className="text-muted" />
                                            : <ChevronRight size={12} className="text-muted" />}
                                    </div>

                                    {open && (
                                        <div className="mt-2 rounded-md px-3 py-2 mono text-xs space-y-0.5"
                                            style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                                            <p><span className="text-cyan">timestamp   </span>{log.timestamp}</p>
                                            <p><span className="text-cyan">source_ip   </span>{log.source_ip}</p>
                                            <p><span className="text-cyan">description </span>{log.description}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
