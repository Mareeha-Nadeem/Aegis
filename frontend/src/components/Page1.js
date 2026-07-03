import { useEffect, useRef } from 'react';
import ThemeToggle from './ThemeToggle';
import HeroShield from './HeroShield';

export default function Page1({ onLaunch, onToggleTheme, stats }) {
  const particlesRef = useRef(null);

  useEffect(() => {
    const wrap = particlesRef.current;
    if (!wrap) return;
    wrap.innerHTML = '';
    for (let i = 0; i < 18; i++) {
      const dot = document.createElement('div');
      dot.className = 'particle';
      dot.style.left             = `${5 + Math.random() * 90}%`;
      dot.style.bottom           = `${Math.random() * 30}%`;
      dot.style.animationDuration = `${4 + Math.random() * 8}s`;
      dot.style.animationDelay   = `${Math.random() * 8}s`;
      const sz = `${1 + Math.random() * 2}px`;
      dot.style.width  = sz;
      dot.style.height = sz;
      dot.style.opacity = '0';
      wrap.appendChild(dot);
    }
  }, []);

  return (
    <div className="page" id="page1">
      <nav className="navbar" aria-label="Main navigation">
        <div className="navbar__inner">
          <div className="navbar__logo">
            <span className="navbar__logo-icon" aria-hidden="true">
              <div className="logo-placeholder">A</div>
            </span>
            <span className="navbar__logo-text">AEGIS</span>
          </div>
          <div className="navbar__controls">
            <ThemeToggle onToggle={onToggleTheme} />
          </div>
        </div>
      </nav>

      <main className="main">
        <section className="hero" id="hero" aria-labelledby="heroTitle">
          <div className="hero__grid" aria-hidden="true"></div>
          <div className="hero__noise" aria-hidden="true"></div>
          <div className="hero__orb hero__orb--1" aria-hidden="true"></div>
          <div className="hero__orb hero__orb--2" aria-hidden="true"></div>
          <div className="particles-wrap" ref={particlesRef} aria-hidden="true"></div>

          <HeroShield />

          {/* Corner brackets */}
          <div className="corner-bracket corner-bracket--tl"></div>
          <div className="corner-bracket corner-bracket--tr"></div>
          <div className="corner-bracket corner-bracket--bl"></div>
          <div className="corner-bracket corner-bracket--br"></div>

          {/* Data points */}
          <span className="data-point">SYS.READY</span>
          <span className="data-point">RAG.v2</span>
          <span className="data-point">0x4A2F</span>
          <span className="data-point">SECURE</span>
          <span className="data-point">TLS.ON</span>
          <span className="data-point">AI.DEF</span>

          <div className="hero__content">
            <div className="hero__eyebrow">
              <span className="hero__badge">RAG Security Research</span>
            </div>
            <h1 className="hero__title" id="heroTitle">AEGIS</h1>
            <p className="hero__subtitle">
              Secure Retrieval-Augmented Generation<br/>
              Against Prompt Injection
            </p>
            <p className="hero__desc">
              Real-time defense against prompt injection attacks in retrieval-augmented systems.
            </p>

            <div className="hero__stats" aria-label="System statistics">
              <div className="stat-chip">
                <span className="stat-chip__label">Injections blocked</span>
                <span className="stat-chip__value">{stats.blockedCount}</span>
              </div>
              <div className="stat-chip stat-chip--dim">
                <span className="stat-chip__label">Queries processed</span>
                <span className="stat-chip__value">{stats.queryCount}</span>
              </div>
              <div className="stat-chip stat-chip--dim">
                <span className="stat-chip__label">Risk level</span>
                <span className="stat-chip__value">{stats.riskLevel}</span>
              </div>
            </div>

            <button className="launch-btn" onClick={onLaunch} aria-label="Launch AEGIS demo">
              Launch Demo
              <span className="launch-btn__arrow" aria-hidden="true">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                  <polyline points="12 5 19 12 12 19"/>
                </svg>
              </span>
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
