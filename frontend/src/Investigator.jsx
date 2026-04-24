import React, { useState } from 'react';
import { Search, Send, Activity, Loader2 } from 'lucide-react';
import SignalCard from './components/SignalCard';
import ChartPanel from './components/ChartPanel';
import SummaryBubble from './components/SummaryBubble';

const Investigator = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [signals, setSignals] = useState({
    spend_agent: { text: '', loading: false },
    creative_agent: { text: '', loading: false },
    seasonal_agent: { text: '', loading: false },
    competitor_agent: { text: '', loading: false },
    tech_agent: { text: '', loading: false },
    synthesis_agent: { text: '', loading: false }
  });

  const runAnalysis = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setSignals({
      spend_agent: { text: '', loading: true },
      creative_agent: { text: '', loading: true },
      seasonal_agent: { text: '', loading: true },
      competitor_agent: { text: '', loading: true },
      tech_agent: { text: '', loading: true },
      synthesis_agent: { text: '', loading: true }
    });

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })  // fixed: was json.stringify
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

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
              const { agent, text } = data;
              if (agent && agent in signals) {
                setSignals(prev => ({
                  ...prev,
                  [agent]: { text, loading: false }
                }));
              }
            } catch (e) {
              // skip ping lines and non-json
            }
          }
        }
      }
    } catch (err) {
      console.error("Analysis failed", err);
    } finally {
      setLoading(false);
      // mark any still-loading agents as done
      setSignals(prev => {
        const updated = { ...prev };
        for (const key in updated) {
          if (updated[key].loading) {
            updated[key] = { text: 'No data returned.', loading: false };
          }
        }
        return updated;
      });
    }
  };

  const agentConfig = [
    { id: 'spend_agent', label: 'Spend Analysis' },
    { id: 'creative_agent', label: 'Creative Analysis' },
    { id: 'seasonal_agent', label: 'Seasonal Analysis' },
    { id: 'competitor_agent', label: 'Competitor Analysis' },
    { id: 'tech_agent', label: 'Tech & Tracking' }
  ];

  return (
    <div className="min-h-screen bg-bg text-text-primary p-6 md:p-12">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2 flex items-center">
              <Activity className="text-accent mr-3" />
              Anomaly Investigator
            </h1>
            <p className="text-text-muted">Root cause analysis for marketing performance</p>
          </div>
        </header>

        <main>
          <div className="relative mb-12">
            <input
              type="text"
              className="w-full bg-surface border border-border rounded-xl py-4 pl-12 pr-16 focus:outline-none focus:border-accent transition-colors text-lg"
              placeholder="Why did Google CPA increase on 2024-01-11?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runAnalysis()}
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
            <button
              onClick={runAnalysis}
              disabled={loading}
              className="absolute right-3 top-1/2 -translate-y-1/2 bg-accent hover:bg-accent/80 disabled:bg-surface-2 p-2 rounded-lg transition-colors"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
            </button>
          </div>

          <div className="space-y-8">
            <ChartPanel />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agentConfig.map((config) => (
                <div key={config.id} className="relative">
                  {signals[config.id].loading && (
                    <div className="absolute inset-0 bg-bg/50 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-lg border border-border/50">
                      <div className="flex flex-col items-center">
                        <Loader2 className="animate-spin text-accent mb-2" />
                        <span className="text-xs text-text-muted">Analyzing {config.label}...</span>
                      </div>
                    </div>
                  )}
                  <SignalCard
                    agent={config.label}
                    text={signals[config.id].text || (signals[config.id].loading ? '' : 'No data yet.')}
                  />
                </div>
              ))}
            </div>

            {signals.synthesis_agent.loading ? (
              <div className="bg-surface-2 border border-border border-dashed rounded-xl p-8 flex flex-col items-center justify-center">
                <Loader2 className="animate-spin text-accent mb-3" size={32} />
                <p className="text-text-muted">Synthesizing final report...</p>
              </div>
            ) : signals.synthesis_agent.text ? (
              <SummaryBubble text={signals.synthesis_agent.text} />
            ) : null}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Investigator;