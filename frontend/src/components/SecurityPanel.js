import { getSecurityCards } from '../data/chatEngine';

export default function SecurityPanel({ mode, blockedCount, queryCount, riskLevel }) {
  const cards = getSecurityCards(mode, blockedCount, queryCount, riskLevel);

  return (
    <section className="security-panel" aria-labelledby="securityTitle">
      <div className="container">
        <div className="security-panel__header">
          <h2 className="security-panel__title" id="securityTitle">Security Status</h2>
          <span className="security-panel__subtitle">
            Current mode: {mode === 'aegis' ? 'AEGIS RAG' : 'Baseline RAG'}
          </span>
        </div>
        <div className="security-cards">
          {cards.map((card, i) => (
            <div
              key={i}
              className={`sec-card${card.variant ? ' sec-card--' + card.variant : ''}`}
            >
              <div className="sec-card__icon">{card.icon}</div>
              <div className="sec-card__title">{card.title}</div>
              <div className="sec-card__value">{card.value}</div>
              <div className="sec-card__desc">{card.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
