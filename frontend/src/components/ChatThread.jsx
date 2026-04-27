import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, X, MessageSquare } from 'lucide-react';

const ChatThread = ({ analysisResult, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const query = input.trim();
    setInput('');
    setLoading(true);

    const newMessages = [...messages, { role: "user", text: query }];
    setMessages(newMessages);

    try {
      const response = await fetch('http://localhost:8000/drilldown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query, 
          history: messages, 
          context: analysisResult 
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let assistantText = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim();
            if (!raw || raw === '') continue;
            try {
              const data = JSON.parse(raw);
              if (data.done) continue;
              
              if (data.text) {
                assistantText += data.text;
              }
            } catch (e) {
              // skip ping lines and non-json
            }
          }
        }
      }

      if (assistantText) {
        setMessages(prev => [...prev, { role: "assistant", text: assistantText }]);
      }
    } catch (err) {
      console.error("Drilldown failed", err);
      setMessages(prev => [...prev, { role: "assistant", text: "Sorry, I encountered an error answering your question." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 w-full bg-surface-2 border-t border-border z-50 flex flex-col shadow-[0_-4px_20px_rgba(0,0,0,0.1)] h-96 max-h-screen">
      <div className="flex items-center justify-between p-3 border-b border-border bg-surface">
        <div className="flex items-center text-text-primary font-medium">
          <MessageSquare className="w-4 h-4 mr-2 text-accent" />
          Follow-up Questions
        </div>
        <button 
          onClick={onClose}
          className="text-text-muted hover:text-text-primary p-1 rounded-md transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-text-muted text-sm mt-4">
            Ask follow-up questions about the synthesis report.
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div 
            key={idx} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[80%] rounded-lg p-3 text-sm whitespace-pre-wrap ${
                msg.role === 'user' 
                  ? 'bg-surface text-text-primary' 
                  : 'bg-bg text-text-primary border-l-4 border-blue-500'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg p-3 bg-bg border-l-4 border-blue-500 flex items-center text-text-muted text-sm">
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 bg-surface border-t border-border">
        <div className="relative max-w-4xl mx-auto flex items-center">
          <input
            type="text"
            className="w-full bg-bg border border-border rounded-lg py-2 pl-4 pr-12 focus:outline-none focus:border-accent transition-colors text-text-primary text-sm"
            placeholder="Ask a question about this analysis..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSend();
            }}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="absolute right-2 p-1.5 text-text-muted hover:text-accent disabled:opacity-50 disabled:hover:text-text-muted transition-colors rounded-md"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatThread;