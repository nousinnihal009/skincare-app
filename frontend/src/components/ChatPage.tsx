import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../api';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const QUICK_QUESTIONS = [
  "Is melanoma dangerous?",
  "What treatments exist for eczema?",
  "Should I see a doctor?",
  "How should I use retinol?",
  "Tell me about sunscreen",
  "What causes acne?",
  "How to care for dry skin?",
];

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0, sender: 'bot', timestamp: new Date(),
      text: "Hello! 👋 I'm your AI Dermatology Assistant. I can help you with:\n\n🔬 Skin conditions — acne, eczema, melanoma, psoriasis, and more\n💊 Treatments — treatment options for various conditions\n🧴 Skincare routines — personalized guidance\n🧪 Ingredient safety — check if ingredients are safe\n👨‍⚕️ When to see a doctor\n\nAsk me anything about skin health!"
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    const userMsg: Message = { id: Date.now(), text: msg, sender: 'user', timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await sendChatMessage(msg);
      const botMsg: Message = { id: Date.now() + 1, text: res.response, sender: 'bot', timestamp: new Date() };
      setMessages(prev => [...prev, botMsg]);
    } catch {
      const errMsg: Message = { id: Date.now() + 1, text: "Sorry, I couldn't process that request. Please try again.", sender: 'bot', timestamp: new Date() };
      setMessages(prev => [...prev, errMsg]);
    }
    setLoading(false);
  };

  // Simple markdown-like rendering
  const renderText = (text: string) => {
    return text.split('\n').map((line, i) => {
      if (!line.trim()) return <br key={i} />;
      let processed = line
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/^- (.*)$/, '• $1')
        .replace(/^(\d+)\. (.*)$/, '$1. $2');
      return <div key={i} dangerouslySetInnerHTML={{ __html: processed }} />;
    });
  };

  return (
    <div className="page-container" style={{ paddingBottom: '0' }}>
      <div className="chat-container">
        {/* Header */}
        <div style={{ textAlign: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--dark-600)' }}>
          <h1 style={{ color: 'white', fontWeight: 800, fontSize: '1.5rem', marginBottom: '4px' }}>
            🤖 AI Dermatologist
          </h1>
          <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem' }}>
            Ask questions about skin conditions, treatments, and skincare
          </p>
        </div>

        {/* Quick Questions */}
        <div style={{ padding: '12px 0', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {QUICK_QUESTIONS.map((q, i) => (
            <button
              key={i}
              onClick={() => handleSend(q)}
              disabled={loading}
              style={{
                padding: '6px 14px', borderRadius: '20px', fontSize: '0.8rem',
                background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
                color: 'var(--primary-300)', cursor: 'pointer', transition: 'all 0.2s',
                fontWeight: 500,
              }}
              onMouseOver={(e) => (e.currentTarget.style.background = 'rgba(99,102,241,0.2)')}
              onMouseOut={(e) => (e.currentTarget.style.background = 'rgba(99,102,241,0.1)')}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.map(msg => (
            <div key={msg.id} className={`chat-bubble ${msg.sender}`}>
              {msg.sender === 'bot' ? renderText(msg.text) : msg.text}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble bot" style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary-400)', animation: 'pulse-glow 1s infinite' }} />
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary-400)', animation: 'pulse-glow 1s infinite 0.2s' }} />
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary-400)', animation: 'pulse-glow 1s infinite 0.4s' }} />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <input
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about any skin condition..."
            disabled={loading}
            id="chat-input"
          />
          <button
            className="btn-primary"
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            style={{ padding: '12px 20px', flexShrink: 0 }}
            id="chat-send"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
