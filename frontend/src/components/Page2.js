import { useState, useEffect } from 'react';
import ThemeToggle from './ThemeToggle';
import ChatWindow from './ChatWindow';
import SecurityPanel from './SecurityPanel';
import { submitQuery } from '../data/chatEngine';

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function Page2({ onBack, onToggleTheme, stats }) {
  const [mode, setMode]         = useState('baseline');
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const isAegis = mode === 'aegis';

  // Sync mode class to body for CSS selector targeting
  useEffect(() => {
    document.body.classList.remove('mode-baseline', 'mode-aegis');
    document.body.classList.add(`mode-${mode}`);
    return () => document.body.classList.remove('mode-baseline', 'mode-aegis');
  }, [mode]);

  function handleSend(text) {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { role: 'user', text, time: now() }]);
    stats.incrementQuery();
    setIsTyping(true);

    (async () => {
      try {
        const response = await submitQuery(text, mode);
        const responseType = response.verdict === 'blocked' ? 'blocked' : 'normal';
        if (responseType === 'blocked' && mode === 'aegis') stats.incrementBlocked();
        setMessages(prev => [...prev, { role: 'bot', text: response.answer, type: responseType, time: now() }]);
      } catch (error) {
        const errorMsg = `⚠️ Backend error: ${error.message || 'Unable to process request. Please ensure the backend API is running.'}`;
        setMessages(prev => [...prev, { role: 'bot', text: errorMsg, type: 'error', time: now() }]);
        console.error('[Aegis] API Error:', error);
      } finally {
        setIsTyping(false);
      }
    })();
  }

  function handleClear() { setMessages([]); }

  return (
    <div className="page" id="page2">
      <div className="page2-bg" aria-hidden="true"></div>

      <nav className="navbar" style={{ position: 'sticky', top: 0 }}>
        <div className="navbar__inner">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <button className="back-btn" onClick={onBack} aria-label="Back">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12 19 5 12 12 5"/>
              </svg>
              Back
            </button>
            <div className="navbar__logo">
              <span className="navbar__logo-icon" aria-hidden="true">
                <div className="logo-placeholder">A</div>
              </span>
              <span className="navbar__logo-text">AEGIS</span>
            </div>
          </div>
          <div className="navbar__controls">
            <div className="status-pill" aria-live="polite">
              <span className="status-dot"></span>
              <span>{isAegis ? 'AEGIS Active' : 'Baseline Active'}</span>
            </div>
            <ThemeToggle onToggle={onToggleTheme} />
          </div>
        </div>
      </nav>

      <main className="main" style={{ position: 'relative', zIndex: 1 }}>
        <div className="glow-divider"></div>

        {/* Model selector */}
        <section className="selector-section">
          <div className="container">
            <p className="selector-section__label">Select RAG mode</p>
            <div className="model-selector" role="radiogroup">
              <button
                className={`model-btn model-btn--baseline${mode === 'baseline' ? ' active' : ''}`}
                role="radio" aria-checked={mode === 'baseline'}
                onClick={() => setMode('baseline')}
              >
                <span className="model-btn__icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                </span>
                <span className="model-btn__name">Baseline RAG</span>
                <span className="model-btn__tag">Vulnerable</span>
              </button>

              <button
                className={`model-btn model-btn--aegis${mode === 'aegis' ? ' active' : ''}`}
                role="radio" aria-checked={mode === 'aegis'}
                onClick={() => setMode('aegis')}
              >
                <span className="model-btn__icon">
                  <svg width="16" height="16" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M11 1L2 5.5V11C2 15.97 5.93 20.6 11 22C16.07 20.6 20 15.97 20 11V5.5L11 1Z"/>
                    <path d="M7.5 11L10 13.5L14.5 9" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
                <span className="model-btn__name">AEGIS RAG</span>
                <span className="model-btn__tag">Protected</span>
              </button>
            </div>
          </div>
        </section>

        {/* Chat section */}
        <section className="chat-section">
          <div className="container container--chat">
            <ChatWindow
              messages={messages}
              isTyping={isTyping}
              mode={mode}
              onSend={handleSend}
              onClear={handleClear}
            />
          </div>
        </section>

        {/* Security panel */}
        <SecurityPanel
          mode={mode}
          blockedCount={stats.blockedCount}
          queryCount={stats.queryCount}
          riskLevel={stats.riskLevel}
        />
      </main>

      <footer className="footer">
        <div className="container">
          <p className="footer__text">
            <span className="footer__aegis">AEGIS</span> — Detection &amp; Mitigation of Prompt Injection in RAG Systems
            <span className="footer__sep">·</span>
            <span className="footer__mono">Research Prototype</span>
          </p>
        </div>
      </footer>
    </div>
  );
}
