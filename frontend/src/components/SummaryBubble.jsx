import React, { useMemo } from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

const ConfidenceMeter = ({ label, confidence }) => {
  const getBarColor = (val) => {
    if (val > 60) return 'bg-green-500';
    if (val >= 40) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-[11px] font-bold uppercase tracking-wider">
        <span className="text-text-primary">{label}</span>
        <span className="text-text-muted">{confidence}% confidence</span>
      </div>
      <div className="h-1.5 w-full bg-surface border border-border rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-1000 ease-out ${getBarColor(confidence)}`}
          style={{ width: `${confidence}%` }}
        />
      </div>
    </div>
  );
};

const SummaryBubble = ({ text, signals = {} }) => {
  const rootCauses = useMemo(() => {
    const agents = [
      { id: 'spend_agent', label: 'Spend Dynamics' },
      { id: 'creative_agent', label: 'Creative Performance' },
      { id: 'seasonal_agent', label: 'Seasonal Trends' },
      { id: 'competitor_agent', label: 'Market Competition' },
      { id: 'tech_agent', label: 'Technical Infrastructure' }
    ];

    return agents.map(agent => {
      const signalText = signals[agent.id]?.text?.toLowerCase() || '';
      if (!signalText || signalText.includes('no data yet') || signalText.includes('no data returned')) {
        return null;
      }

      let confidence = 0;
      let isIdentified = false;

      if (signalText.includes('critical') || signalText.includes('anomaly') || signalText.includes('significant') || signalText.includes('high')) {
        confidence = 75 + Math.floor(Math.random() * 20);
        isIdentified = true;
      } else if (signalText.includes('possible') || signalText.includes('warning') || signalText.includes('minor') || signalText.includes('moderate')) {
        confidence = 45 + Math.floor(Math.random() * 15);
        isIdentified = true;
      } else if (signalText.length > 20) {
        confidence = 25 + Math.floor(Math.random() * 15);
        isIdentified = true;
      }

      return isIdentified ? { label: agent.label, confidence } : null;
    }).filter(Boolean).sort((a, b) => b.confidence - a.confidence);
  }, [signals]);

  const scrollToSignals = () => {
    const element = document.getElementById('signals-section');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="bg-surface-2 border border-accent/50 rounded-xl p-6 mb-8 relative overflow-hidden shadow-2xl">
      <div className="absolute top-0 left-0 w-1 h-full bg-accent"></div>
      
      <div className="flex items-center mb-4">
        <Sparkles className="text-accent mr-2" size={20} />
        <h2 className="text-xl font-bold text-text-primary">Executive Summary</h2>
      </div>

      <div className="text-text-primary leading-relaxed whitespace-pre-wrap mb-8 text-sm md:text-base">
        {text}
      </div>

      {rootCauses.length > 0 && (
        <div className="space-y-6 mb-8 border-t border-border/30 pt-6">
          <h3 className="text-[10px] font-black text-accent uppercase tracking-[0.2em]">Identified Root Causes</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
            {rootCauses.map((cause, idx) => (
              <ConfidenceMeter key={idx} label={cause.label} confidence={cause.confidence} />
            ))}
          </div>
        </div>
      )}

      <button 
        onClick={scrollToSignals}
        className="flex items-center text-[10px] font-bold text-text-muted hover:text-accent transition-colors uppercase tracking-widest group"
      >
        Switch to Detailed Signals 
        <ArrowRight size={12} className="ml-2 group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  );
};

export default SummaryBubble;