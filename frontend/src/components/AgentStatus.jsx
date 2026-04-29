import React from 'react';
import { Loader2, CheckCircle2 } from 'lucide-react';

const AgentStatus = ({ agentConfig, signals }) => {
  const scrollToAgent = (id) => {
    const element = document.getElementById(`card-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {agentConfig.map((agent) => {
        const state = signals[agent.id];
        const isRunning = state?.loading;
        const isDone = !isRunning && state?.text && state.text !== 'No data returned.';
        const label = agent.label.split(' ')[0]; // Just "Spend", "Creative", etc.

        return (
          <button
            key={agent.id}
            onClick={() => scrollToAgent(agent.id)}
            className="flex items-center space-x-2 bg-surface-2 border border-border px-3 py-1.5 rounded-full hover:border-accent transition-all group"
          >
            <div className="relative flex items-center justify-center">
              {isRunning ? (
                <Loader2 size={12} className="animate-spin text-accent" />
              ) : isDone ? (
                <CheckCircle2 size={12} className="text-green-400" />
              ) : (
                <>
                  <span className="h-2 w-2 rounded-full bg-green-500"></span>
                  <span className="absolute h-2 w-2 rounded-full bg-green-500 animate-ping opacity-75"></span>
                </>
              )}
            </div>
            <span className="text-xs font-medium text-text-muted group-hover:text-text-primary transition-colors">
              {label}
            </span>
          </button>
        );
      })}
    </div>
  );
};

export default AgentStatus;