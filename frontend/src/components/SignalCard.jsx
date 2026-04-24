import React from 'react';

const SignalCard = ({ agent, text }) => {
  return (
    <div className="bg-surface border border-border rounded-lg p-4 mb-4 shadow-lg">
      <div className="flex items-center mb-2">
        <span className="text-accent font-semibold text-sm uppercase tracking-wider">{agent}</span>
      </div>
      <div className="text-text-primary whitespace-pre-wrap">
        {text}
      </div>
    </div>
  );
};

export default SignalCard;
