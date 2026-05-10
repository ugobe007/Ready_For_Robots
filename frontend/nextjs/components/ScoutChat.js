import { useEffect, useMemo, useState } from 'react';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

function fingerprint() {
  if (typeof window === 'undefined') return 'server-scout';
  const key = 'rfr_scout_fingerprint';
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const next = `scout_${Math.random().toString(36).slice(2)}_${Date.now().toString(36)}`;
  window.localStorage.setItem(key, next);
  return next;
}

export default function ScoutChat() {
  const API = useMemo(() => getApiBase(), []);
  const [open, setOpen] = useState(false);
  const [fp, setFp] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'I’m SCOUT. Send me a company URL, target vertical, or territory and I’ll help identify robot-ready opportunities.',
    },
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const id = fingerprint();
    setFp(id);
    fetch(`${API}/api/scout/session`, liveFetchInit({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fingerprint: id }),
    }))
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (Array.isArray(data?.history) && data.history.length) {
          setMessages(data.history.map((m) => ({ role: m.role === 'scout' ? 'assistant' : m.role, content: m.content })));
        }
      })
      .catch(() => {});
  }, [API]);

  async function sendMessage(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy || !fp) return;
    const nextMessages = [...messages, { role: 'user', content: text }];
    setMessages(nextMessages);
    setInput('');
    setBusy(true);
    try {
      const response = await fetch(`${API}/api/scout/chat`, liveFetchInit({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fingerprint: fp, messages: nextMessages.slice(-12) }),
      }));
      const data = await response.json();
      setMessages((current) => [...current, { role: 'assistant', content: data.reply || 'SCOUT could not generate a response right now.' }]);
    } catch {
      setMessages((current) => [...current, { role: 'assistant', content: 'SCOUT is offline for a moment. Try again after the API is reachable.' }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className="scout-chat-launch" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span>SCOUT</span>
        <strong>Ask</strong>
      </button>
      {open && (
        <div className="scout-chat-panel" role="dialog" aria-label="SCOUT assistant">
          <div className="scout-chat-header">
            <div>
              <p className="scout-kicker">Autonomous GTM agent</p>
              <h2>SCOUT</h2>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close SCOUT chat">×</button>
          </div>
          <div className="scout-chat-messages">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`scout-chat-message scout-chat-message-${message.role}`}>
                {message.content}
              </div>
            ))}
            {busy && <div className="scout-chat-message scout-chat-message-assistant">Thinking…</div>}
          </div>
          <form onSubmit={sendMessage} className="scout-chat-form">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask SCOUT to scan a company or find prospects…"
            />
            <button type="submit" disabled={busy || !input.trim()}>Send</button>
          </form>
        </div>
      )}
    </>
  );
}
