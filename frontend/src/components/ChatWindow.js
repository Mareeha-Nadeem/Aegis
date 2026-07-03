import { useEffect, useRef } from 'react';
import { QUICK_PROMPTS } from '../data/chatEngine';

export default function ChatWindow({ messages, isTyping, mode, onSend, onClear }) {
  const inputRef   = useRef(null);
  const messagesRef = useRef(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  function handleSubmit(e) {
    e.preventDefault();
    const val = inputRef.current.value.trim();
    if (!val) return;
    onSend(val);
    inputRef.current.value = '';
  }

  function handleQuickPrompt(text) {
    if (inputRef.current) inputRef.current.value = text;
    onSend(text);
  }

  const isAegis    = mode === 'aegis';
  const modelName  = isAegis ? 'AEGIS RAG' : 'Baseline RAG';
  const badgeText  = isAegis ? 'PROTECTED' : 'UNPROTECTED';

  return (
    <>
      {/* Chat header */}
      <div className="chat-header" id="chatHeader">
        <div className="chat-header__left">
          <span className="chat-header__dot"></span>
          <span className="chat-header__model">{modelName}</span>
        </div>
        <div className="chat-header__right">
          <span className="chat-header__badge">{badgeText}</span>
          <button className="clear-btn" onClick={onClear} aria-label="Clear chat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>
              <path d="M9 6V4h6v2"/>
            </svg>
            Clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages" ref={messagesRef} role="log" aria-live="polite">
        {messages.length === 0 && (
          <div className="empty-state">
            <span className="empty-state__icon">💬</span>
            <span>Send a message to begin the demo</span>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message message--${msg.role}${msg.type && msg.type !== 'normal' ? ' ' + msg.type : ''}`}
          >
            {msg.role === 'bot' && msg.type === 'threat' && (
              <span className="message__threat-badge message__threat-badge--danger">⚠ INJECTION EXECUTED</span>
            )}
            {msg.role === 'bot' && msg.type === 'blocked' && (
              <span className="message__threat-badge message__threat-badge--success">🛡 THREAT BLOCKED</span>
            )}
            <div className="message__bubble">{msg.text}</div>
            <div className="message__meta">{msg.time}</div>
          </div>
        ))}
        {isTyping && (
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        )}
      </div>

      {/* Quick prompts */}
      <div className="quick-prompts">
        <span className="quick-prompts__label">Try:</span>
        {QUICK_PROMPTS.map((qp, i) => (
          <button
            key={i}
            className="quick-prompt-btn"
            onClick={() => handleQuickPrompt(qp.text)}
          >
            {qp.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <form className="chat-input-area" onSubmit={handleSubmit}>
        <div className="chat-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            placeholder="Send a message..."
            autoComplete="off"
            maxLength={500}
          />
          <button className="send-btn" type="submit">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </form>
    </>
  );
}
