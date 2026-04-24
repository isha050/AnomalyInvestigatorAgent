import React from 'react';
import { Sparkles } from 'lucide-react';

const SummaryBubble = ({ text }) => {
  return (
    <div className="bg-surface-2 border border-accent/50 rounded-xl p-6 mb-8 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full bg-accent"></div>
      <div className="flex items-center mb-3">
        <Sparkles className="text-accent mr-2" size={20} />
        <h2 className="text-xl font-bold text-text-primary">Executive Summary</h2>
      </div>
      <div className="text-text-primary leading-relaxed whitespace-pre-wrap">
        {text}
      </div>
    </div>
  );
};

export default SummaryBubble;
