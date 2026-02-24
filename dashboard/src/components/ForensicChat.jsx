/**
 * ForensicChat.jsx — AI Forensic Analyst Chat
 * Connects to Python AI Service POST /chat
 */
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, User, AlertTriangle, Zap } from 'lucide-react';

const AI_URL = 'http://localhost:8000';

const QUICK_QUERIES = [
    'Show failed logins',
    'Which IP did lateral movement?',
    'Data exfiltration events?',
    'Summarize the attack timeline',
    'List malware executions',
];

export default function ForensicChat() {
    const [messages, setMessages] = useState([{
        id: 0, role: 'ai',
        text: 'CyberGaze AI Analyst ready. Ask anything about the loaded forensic logs.',
        ts: now(),
    }]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

    function now() { return new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }); }

    async function send(query) {
        const q = (query || input).trim();
        if (!q) return;
        setInput('');
        setLoading(true);

        setMessages(prev => [...prev, { id: Date.now(), role: 'user', text: q, ts: now() }]);

        try {
            const { data } = await axios.post(`${AI_URL}/chat`, { query: q }, { timeout: 30000 });
            setMessages(prev => [...prev, {
                id: Date.now() + 1, role: 'ai',
                text: data.answer,
                sources: data.source_events || [],
                ts: now(),
            }]);
        } catch (err) {
            setMessages(prev => [...prev, {
                id: Date.now() + 1, role: 'error',
                text: `Could not reach AI service: ${err.response?.data?.detail || err.message}`,
                ts: now(),
            }]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="card flex flex-col h-full" style={{ height: 560 }}>
            {/* Header */}
            <div className="card-header">
                <Bot size={15} className="text-cyan" />
                <span className="card-title">AI Forensic Analyst</span>
                <span className="badge badge-cyan ml-auto">RAG · Ollama llama3</span>
            </div>

            {/* Quick queries */}
            <div className="flex flex-wrap gap-1.5 px-4 py-2.5" style={{ borderBottom: '1px solid var(--border)' }}>
                {QUICK_QUERIES.map((q, i) => (
                    <button
                        key={i}
                        onClick={() => send(q)}
                        disabled={loading}
                        className="mono text-xs px-2.5 py-1 rounded-full transition-all"
                        style={{
                            background: 'var(--surface)',
                            border: '1px solid var(--border)',
                            color: 'var(--text-secondary)',
                            cursor: loading ? 'not-allowed' : 'pointer',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--cyan)'; e.currentTarget.style.color = 'var(--cyan)'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                    >
                        {q}
                    </button>
                ))}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4" style={{ minHeight: 0 }}>
                {messages.map(msg => (
                    <div key={msg.id} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        {/* Avatar */}
                        <div
                            className="flex-shrink-0 flex items-center justify-center rounded-full"
                            style={{
                                width: 28, height: 28,
                                background: msg.role === 'user' ? 'var(--cyan-dim)' : msg.role === 'error' ? 'var(--red-dim)' : 'var(--green-dim)',
                            }}
                        >
                            {msg.role === 'user'
                                ? <User size={13} className="text-cyan" />
                                : msg.role === 'error'
                                    ? <AlertTriangle size={13} className="text-red" />
                                    : <Bot size={13} className="text-green" />}
                        </div>

                        {/* Bubble */}
                        <div
                            className={`flex flex-col gap-1.5 max-w-[82%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                        >
                            <div
                                className="mono text-xs rounded-lg px-3 py-2.5 leading-relaxed whitespace-pre-wrap"
                                style={{
                                    background: msg.role === 'user' ? 'rgba(34,211,238,0.08)'
                                        : msg.role === 'error' ? 'rgba(248,113,113,0.08)'
                                            : 'rgba(74,222,128,0.07)',
                                    border: `1px solid ${msg.role === 'user' ? 'rgba(34,211,238,0.2)'
                                        : msg.role === 'error' ? 'rgba(248,113,113,0.25)'
                                            : 'rgba(74,222,128,0.15)'}`,
                                    color: 'var(--text-primary)',
                                    wordBreak: 'break-word',
                                }}
                            >
                                {msg.text}
                            </div>

                            {/* Source excerpts */}
                            {msg.sources?.length > 0 && (
                                <div className="w-full space-y-1">
                                    <p className="text-xs text-muted pl-1">Relevant log excerpts:</p>
                                    {msg.sources.map((s, i) => (
                                        <div key={i} className="mono text-xs px-2 py-1.5 rounded"
                                            style={{ background: 'var(--surface)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                                            {s}
                                        </div>
                                    ))}
                                </div>
                            )}

                            <span className="text-xs text-muted pl-1">{msg.ts}</span>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex gap-2.5 items-center">
                        <div className="flex items-center justify-center rounded-full"
                            style={{ width: 28, height: 28, background: 'var(--green-dim)' }}>
                            <Bot size={13} className="text-green" />
                        </div>
                        <span className="mono text-xs text-green dot-loader">
                            Analyzing<span>.</span><span>.</span><span>.</span>
                        </span>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3" style={{ borderTop: '1px solid var(--border)' }}>
                <div className="flex gap-2">
                    <input
                        className="input flex-1"
                        placeholder="Ask about the forensic logs… (Enter to send)"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
                        disabled={loading}
                    />
                    <button
                        className="btn btn-cyan"
                        onClick={() => send()}
                        disabled={loading || !input.trim()}
                    >
                        <Send size={13} />
                    </button>
                </div>
            </div>
        </div>
    );
}
