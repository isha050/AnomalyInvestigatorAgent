import React, { useState, useEffect, useRef } from 'react';
import { Search, Send, Activity, Loader2, Crosshair, TrendingUp, Settings, HelpCircle, Clock, X, Copy, Download, ExternalLink, Calendar as CalendarIcon } from 'lucide-react';
import SignalCard from './components/SignalCard';
import ChartPanel from './components/ChartPanel';
import SummaryBubble from './components/SummaryBubble';
import AutoDetector from './components/AutoDetector';
import ChatThread from './components/ChatThread';
import ScenarioSimulator from './components/ScenarioSimulator';
import CausalDAGSettings from './components/CausalDAGSettings';
import KPIBanner from './components/KPIBanner';
import AgentStatus from './components/AgentStatus';
import TimelineVisual from './components/TimelineVisual';
import MMMStatus from './components/MMMStatus';

const Investigator = () => {
  const [activeTab, setActiveTab] = useState('manual');
  const [showChat, setShowChat] = useState(false);
  const [analysisResult, setAnalysisResult] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState(null);
  const [anomalyDate, setAnomalyDate] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionIndex, setSuggestionIndex] = useState(-1);
  const suggestionRef = useRef(null);

  const [signals, setSignals] = useState({
    spend_agent: { text: '', loading: false },
    creative_agent: { text: '', loading: false },
    seasonal_agent: { text: '', loading: false },
    competitor_agent: { text: '', loading: false },
    tech_agent: { text: '', loading: false },
    synthesis_agent: { text: '', loading: false }
  });

  const starterQueries = [
    "Why did Google CPA spike on 2024-01-06?",
    "What caused CTR to drop on 2024-01-15?",
    "Investigate Meta performance on 2024-01-20"
  ];

  useEffect(() => {
    fetch('http://localhost:8000/chart-data')
      .then(res => res.json())
      .then(data => setChartData(data))
      .catch(err => console.error("Failed to fetch chart data", err));
  }, []);

  const runAnalysis = async (customQuery = null) => {
    const activeQuery = customQuery || query;
    if (!activeQuery.trim()) return;

    // Extract date if present (YYYY-MM-DD)
    const dateMatch = activeQuery.match(/\d{4}-\d{2}-\d{2}/);
    if (dateMatch) {
      setAnomalyDate(dateMatch[0]);
    }

    setLoading(true);
    setShowSuggestions(false);
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
        body: JSON.stringify({ query: activeQuery })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let anomalyCount = 0;

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
                if (text?.toLowerCase().includes('anomaly') || text?.toLowerCase().includes('critical')) {
                  anomalyCount++;
                }
                setSignals(prev => ({
                  ...prev,
                  [agent]: { text, loading: false }
                }));
                if (agent === 'synthesis_agent') {
                  setAnalysisResult(text);
                }
              }
            } catch (e) {}
          }
        }
      }

      // Add to history
      setHistory(prev => [
        { 
          query: activeQuery, 
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          anomalies: anomalyCount 
        },
        ...prev.slice(0, 9)
      ]);

    } catch (err) {
      console.error("Analysis failed", err);
    } finally {
      setLoading(false);
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

  const handleQueryChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    
    // Autocomplete logic
    if (val.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const lastWord = val.split(' ').pop();
    let newSuggestions = [];

    // Date suggestions
    if (/\d{4}-\d{2}-/.test(lastWord)) {
      const dates = Array.from(new Set([
        ...(chartData?.spend?.map(d => d.date) || []),
        ...(chartData?.cvr ? Object.keys(chartData.cvr) : [])
      ]));
      newSuggestions = dates.filter(d => d.startsWith(lastWord)).slice(0, 5).map(d => ({ type: 'date', value: d }));
    } 
    // Channel suggestions
    else if (/^(g|m|t)/i.test(lastWord)) {
      const channels = ['Google', 'Meta', 'TikTok'];
      newSuggestions = channels
        .filter(c => c.toLowerCase().startsWith(lastWord.toLowerCase()))
        .map(c => ({ type: 'channel', value: c }));
    }

    setSuggestions(newSuggestions);
    setShowSuggestions(newSuggestions.length > 0);
    setSuggestionIndex(-1);
  };

  const applySuggestion = (suggestion) => {
    const words = query.split(' ');
    words.pop();
    setQuery([...words, suggestion.value].join(' ') + ' ');
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const copyToClipboard = () => {
    const markdown = `# Analysis Summary\n\n**Query:** ${query}\n\n${analysisResult}`;
    navigator.clipboard.writeText(markdown);
    alert('Summary copied as Markdown!');
  };

  const exportReport = () => {
    const content = `
      <html>
        <head>
          <title>Investigation Report</title>
          <style>
            body { font-family: sans-serif; padding: 40px; line-height: 1.6; color: #333; }
            h1 { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
            h2 { color: #1e40af; margin-top: 30px; }
            .metric-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            .metric-table th, .metric-table td { border: 1px solid #e5e7eb; padding: 12px; text-align: left; }
            .metric-table th { background: #f9fafb; }
            .signal-card { border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; margin-bottom: 15px; }
            .verdict { font-weight: bold; font-size: 1.1em; color: #111; }
          </style>
        </head>
        <body>
          <h1>Investigation Report</h1>
          <p><strong>Query:</strong> ${query}</p>
          <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
          
          <h2>Executive Summary</h2>
          <div style="background: #f0f7ff; padding: 20px; border-left: 4px solid #2563eb; border-radius: 4px;">
            ${analysisResult.replace(/\n/g, '<br>')}
          </div>

          <h2>Domain Signals</h2>
          ${Object.entries(signals).filter(([k]) => k !== 'synthesis_agent').map(([k, v]) => `
            <div class="signal-card">
              <div class="verdict">${v.text.split('\n')[0]}</div>
              <div style="font-size: 0.9em; color: #666; margin-top: 5px;">${v.text.split('\n').slice(1).join('<br>')}</div>
            </div>
          `).join('')}
        </body>
      </html>
    `;
    const win = window.open('', '_blank');
    win.document.write(content);
    win.document.close();
    win.print();
  };

  const agentConfig = [
    { id: 'spend_agent', label: 'Spend Analysis' },
    { id: 'creative_agent', label: 'Creative Analysis' },
    { id: 'seasonal_agent', label: 'Seasonal Analysis' },
    { id: 'competitor_agent', label: 'Competitor Analysis' },
    { id: 'tech_agent', label: 'Tech & Tracking' }
  ];

  const navItems = [
    { id: 'manual', label: 'Manual Query', icon: Search },
    { id: 'auto', label: 'Auto Detector', icon: Crosshair },
    { id: 'simulator', label: 'Scenario Simulator', icon: TrendingUp },
    { id: 'settings', label: 'DAG Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-bg text-text-primary flex flex-col md:flex-row">
      {/* Sidebar (Desktop) */}
      <aside className="hidden md:flex fixed left-0 top-0 h-screen w-64 bg-surface border-r border-border flex-col p-6 z-30">
        <div className="flex items-center space-x-3 mb-10 px-2">
          <Activity className="text-accent" size={24} />
          <span className="text-lg font-black tracking-tighter uppercase">Investigator</span>
        </div>

        <nav className="flex-1 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all relative group ${
                  isActive 
                    ? 'bg-accent/10 text-accent' 
                    : 'text-text-muted hover:text-text-primary hover:bg-surface-2'
                }`}
              >
                {isActive && <div className="absolute left-0 w-1 h-6 bg-accent rounded-r-full" />}
                <Icon size={20} className={isActive ? 'text-accent' : 'text-text-muted group-hover:text-text-primary'} />
                <span className="font-bold text-sm">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <a 
          href="#" 
          className="flex items-center space-x-3 px-4 py-3 text-text-muted hover:text-text-primary transition-colors border-t border-border mt-auto pt-6"
        >
          <HelpCircle size={20} />
          <span className="font-bold text-sm">Help & Support</span>
        </a>
      </aside>

      {/* Bottom Nav (Mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-16 bg-surface border-t border-border flex justify-around items-center z-40 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center justify-center space-y-1 p-2 transition-all ${
                isActive ? 'text-accent' : 'text-text-muted'
              }`}
            >
              <Icon size={20} />
              <span className="text-[10px] font-black uppercase tracking-tighter">{item.label.split(' ')[0]}</span>
            </button>
          );
        })}
      </nav>

      {/* Main Content Area */}
      <div className="flex-1 md:ml-64 p-6 md:p-12 pb-24 md:pb-12 min-h-screen">
        <div className="max-w-4xl mx-auto">
          <header className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2 flex items-center md:hidden">
                <Activity className="text-accent mr-3" />
                Anomaly Investigator
              </h1>
              <h2 className="text-2xl font-bold text-text-primary hidden md:block">
                {navItems.find(i => i.id === activeTab)?.label}
              </h2>
              <p className="text-text-muted text-sm">Root cause analysis for marketing performance</p>
              <MMMStatus />
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setShowHistory(true)}
                className="p-2 text-text-muted hover:text-accent transition-colors"
                title="Investigation History"
              >
                <Clock size={20} />
              </button>
              <AgentStatus agentConfig={agentConfig} signals={signals} />
            </div>
          </header>

          {/* History Slide-over */}
          <div className={`fixed inset-y-0 right-0 w-80 bg-surface border-l border-border z-50 transform transition-transform duration-300 shadow-2xl ${showHistory ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="p-6 h-full flex flex-col">
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-lg font-bold flex items-center space-x-2">
                  <Clock size={18} className="text-accent" />
                  <span>History</span>
                </h3>
                <button onClick={() => setShowHistory(false)} className="p-1 hover:bg-surface-2 rounded-lg transition-colors">
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3">
                {history.length === 0 ? (
                  <div className="text-center py-12 text-text-muted italic text-sm">No investigations run yet.</div>
                ) : (
                  history.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setQuery(item.query);
                        runAnalysis(item.query);
                        setShowHistory(false);
                      }}
                      className="w-full text-left bg-surface-2 border border-border p-3 rounded-xl hover:border-accent transition-all group"
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-[10px] text-text-muted font-bold">{item.timestamp}</span>
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase ${item.anomalies > 0 ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                          {item.anomalies} anomalies
                        </span>
                      </div>
                      <p className="text-xs text-text-primary line-clamp-2 font-medium">{item.query}</p>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          <KPIBanner />

          <main>
            {activeTab === 'manual' && (
              <>
                <div className="relative mb-8">
                  <div className="relative">
                    <input
                      type="text"
                      className="w-full bg-surface border border-border rounded-xl py-4 pl-12 pr-16 focus:outline-none focus:border-accent transition-colors text-lg"
                      placeholder="Why did Google CPA increase on 2024-01-11?"
                      value={query}
                      onChange={handleQueryChange}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          if (suggestionIndex >= 0 && suggestions[suggestionIndex]) {
                            applySuggestion(suggestions[suggestionIndex]);
                          } else {
                            runAnalysis();
                          }
                        } else if (e.key === 'ArrowDown') {
                          setSuggestionIndex(prev => Math.min(prev + 1, suggestions.length - 1));
                        } else if (e.key === 'ArrowUp') {
                          setSuggestionIndex(prev => Math.max(prev - 1, 0));
                        }
                      }}
                    />
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
                    <button
                      onClick={() => runAnalysis()}
                      disabled={loading}
                      className="absolute right-3 top-1/2 -translate-y-1/2 bg-accent hover:bg-accent/80 disabled:bg-surface-2 p-2 rounded-lg transition-colors"
                    >
                      {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                    </button>

                    {/* Autocomplete Dropdown */}
                    {showSuggestions && (
                      <div ref={suggestionRef} className="absolute left-0 right-0 top-full mt-2 bg-surface border border-border rounded-xl shadow-2xl z-20 overflow-hidden">
                        {suggestions.map((s, idx) => (
                          <button
                            key={idx}
                            onClick={() => applySuggestion(s)}
                            className={`w-full text-left px-4 py-3 text-sm flex items-center space-x-3 transition-colors ${idx === suggestionIndex ? 'bg-accent/10 text-accent' : 'hover:bg-surface-2'}`}
                          >
                            {s.type === 'date' ? <CalendarIcon size={14} /> : <Activity size={14} />}
                            <span>{s.value}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Starter Chips */}
                  {!query && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {starterQueries.map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => { setQuery(q); runAnalysis(q); }}
                          className="text-[10px] font-bold bg-surface-2 border border-border px-3 py-1.5 rounded-full text-text-muted hover:text-accent hover:border-accent transition-all uppercase tracking-wider"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="space-y-8" id="signals-section">
                  <ChartPanel anomalyDate={anomalyDate} />

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* ... signals cards rendering ... */}
                    {agentConfig.map((config) => (
                      <div key={config.id} id={`card-${config.id}`} className="relative scroll-mt-24">
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
                          severity={(() => {
                            const text = signals[config.id].text?.toLowerCase() || '';
                            if (text.includes('critical') || text.includes('anomaly') || text.includes('significant')) return 'critical';
                            if (text.includes('possible') || text.includes('warning') || text.includes('minor')) return 'warning';
                            if (text && text !== 'no data yet.' && text !== 'no data returned.') return 'success';
                            return 'info';
                          })()}
                          weight={{
                            spend_agent: 35,
                            creative_agent: 25,
                            seasonal_agent: 15,
                            competitor_agent: 15,
                            tech_agent: 10
                          }[config.id]}
                          chartData={(() => {
                            if (!chartData) return [];
                            const mapper = {
                              spend_agent: chartData.spend,
                              creative_agent: chartData.ctr,
                              seasonal_agent: chartData.cvr, // Seasonal impacts conversion
                              competitor_agent: chartData.competitor,
                              tech_agent: chartData.cvr // Tech affects tracking/cvr
                            };
                            return (mapper[config.id] || []).map(d => d.value).slice(-30);
                          })()}
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
                    <>
                      <SummaryBubble text={signals.synthesis_agent.text} signals={signals} />
                      <TimelineVisual anomalyDate={anomalyDate} />
                      
                      {/* Analysis Actions */}
                      <div className="flex flex-wrap items-center justify-center gap-4 mt-8 pt-8 border-t border-border">
                        <button 
                          onClick={exportReport}
                          className="flex items-center space-x-2 bg-surface border border-border px-4 py-2 rounded-lg text-xs font-bold hover:border-accent transition-colors"
                        >
                          <Download size={14} />
                          <span>Export Report</span>
                        </button>
                        <button 
                          onClick={copyToClipboard}
                          className="flex items-center space-x-2 bg-surface border border-border px-4 py-2 rounded-lg text-xs font-bold hover:border-accent transition-colors"
                        >
                          <Copy size={14} />
                          <span>Copy for Slack</span>
                        </button>
                        <button 
                          onClick={() => setShowChat(true)}
                          className="flex items-center space-x-2 bg-accent text-white px-6 py-2 rounded-lg text-xs font-bold hover:bg-accent/80 transition-colors shadow-lg"
                        >
                          <ExternalLink size={14} />
                          <span>Ask a follow-up</span>
                        </button>
                      </div>
                    </>
                  ) : null}
                </div>
              </>
            )}

            {activeTab === 'auto' && (
              <AutoDetector 
                onInvestigate={(date, channels) => { 
                  setActiveTab('manual');
                  const channelList = channels && channels.length > 0 ? channels : ['Google'];
                  const channelText = channelList.length === 1 
                      ? channelList[0]
                      : channelList.slice(0, -1).join(', ') + ' and ' + channelList[channelList.length - 1];
                  setQuery(`Why did CPA increase across ${channelText} on ${date}?`);
                  setAnomalyDate(date);
                  setTimeout(() => runAnalysis(), 0); 
                }} 
              />
            )}

            {activeTab === 'settings' && <CausalDAGSettings />}

            {activeTab === 'simulator' && (
              <ScenarioSimulator />
            )}

            {showChat && (
              <ChatThread 
                analysisResult={analysisResult} 
                onClose={() => setShowChat(false)} 
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default Investigator;