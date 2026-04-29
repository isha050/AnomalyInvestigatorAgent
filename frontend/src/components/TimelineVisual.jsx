import React from 'react';
import { Circle, AlertCircle, TrendingDown, CheckCircle2 } from 'lucide-react';

const TimelineVisual = ({ anomalyDate }) => {
  if (!anomalyDate) return null;

  const baseDate = new Date(anomalyDate);
  
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const addDays = (date, days) => {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  };

  const stages = [
    {
      label: 'Normal',
      date: formatDate(addDays(baseDate, -7)),
      color: 'bg-green-500',
      icon: Circle,
      desc: 'Baseline performance'
    },
    {
      label: 'Anomaly Start',
      date: formatDate(baseDate),
      color: 'bg-amber-500',
      icon: AlertCircle,
      desc: 'Initial deviation detected'
    },
    {
      label: 'Peak Impact',
      date: formatDate(addDays(baseDate, 2)),
      color: 'bg-red-500',
      icon: TrendingDown,
      desc: 'Maximum variance observed'
    },
    {
      label: 'Recovery',
      date: formatDate(addDays(baseDate, 7)),
      color: 'bg-green-500',
      icon: CheckCircle2,
      desc: 'Projected stabilization'
    }
  ];

  return (
    <div className="bg-surface border border-border rounded-xl p-6 mb-8 overflow-hidden relative">
      <h3 className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-8">Anomaly Lifecycle</h3>
      
      <div className="relative">
        {/* Connection Line with Gradient */}
        <div className="absolute top-5 left-0 w-full h-1 bg-gradient-to-r from-green-500 via-red-500 to-green-500 rounded-full opacity-30"></div>
        
        <div className="relative flex justify-between">
          {stages.map((stage, idx) => {
            const Icon = stage.icon;
            return (
              <div key={idx} className="flex flex-col items-center z-10 w-1/4">
                <div className={`w-10 h-10 rounded-full ${stage.color} flex items-center justify-center border-4 border-bg shadow-lg mb-3 transition-transform hover:scale-110`}>
                  <Icon size={18} className="text-white" />
                </div>
                <div className="text-center">
                  <p className="text-[10px] font-bold text-text-primary uppercase tracking-wider mb-0.5">{stage.label}</p>
                  <p className="text-xs text-accent font-mono mb-2">{stage.date}</p>
                  <p className="text-[9px] text-text-muted leading-tight max-w-[80px] mx-auto">{stage.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default TimelineVisual;