import React, { useState } from 'react';
import { 
  DollarSign, 
  Brush, 
  Calendar, 
  Target, 
  Settings, 
  AlertCircle, 
  ChevronDown,
  Info,
  HelpCircle
} from 'lucide-react';

const icons = {
  'Spend Analysis': DollarSign,
  'Creative Analysis': Brush,
  'Seasonal Analysis': Calendar,
  'Competitor Analysis': Target,
  'Tech & Tracking': Settings,
};

const MiniSparkline = ({ data, color = 'var(--color-accent)' }) => {
  if (!data || data.length < 2) return null;
  const width = 200;
  const height = 40;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="bg-surface-2 rounded-lg p-3 border border-border/50">
      <div className="flex justify-between items-center mb-2">
        <span className="text-[10px] text-text-muted uppercase font-bold tracking-wider">Domain Trend</span>
        <span className="text-[10px] text-text-muted">{data.length}d</span>
      </div>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="overflow-visible">
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
      </svg>
    </div>
  );
};

const SignalCard = ({ agent, text, severity = 'info', weight = 0, chartData = [] }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const Icon = icons[agent] || AlertCircle;
  
  const lines = text.trim().split('\n');
  const verdict = lines[0];
  const details = lines.slice(1).join('\n').trim();

  const getSeverityStyles = () => {
    switch (severity) {
      case 'critical':
        return { bar: 'bg-red-500', dot: 'bg-red-500', icon: 'text-red-400', bg: 'bg-red-500/5' };
      case 'warning':
        return { bar: 'bg-amber-500', dot: 'bg-amber-500', icon: 'text-amber-400', bg: 'bg-amber-500/5' };
      case 'success':
        return { bar: 'bg-green-500', dot: 'bg-green-500', icon: 'text-green-400', bg: 'bg-green-500/5' };
      default:
        return { bar: 'bg-accent', dot: 'bg-accent', icon: 'text-accent', bg: 'bg-accent/5' };
    }
  };

  const styles = getSeverityStyles();

  return (
    <div className={`relative bg-surface border border-border rounded-xl overflow-hidden shadow-lg transition-all hover:border-accent/30 mb-4`}>
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${styles.bar}`} />
      
      <div className="flex flex-col">
        {/* Summary Row */}
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full text-left p-4 pl-6 flex items-center justify-between hover:bg-surface-2/50 transition-colors"
        >
          <div className="flex items-center space-x-4 flex-1 min-w-0">
            <div className={`p-1.5 rounded-lg ${styles.bg}`}>
              <Icon size={16} className={styles.icon} />
            </div>
            <div className="flex flex-col min-w-0 flex-1">
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">{agent}</span>
                <div className={`h-1.5 w-1.5 rounded-full ${styles.dot}`} />
              </div>
              <p className="text-sm font-bold text-text-primary truncate pr-4">
                {verdict || 'No data available'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {weight > 0 && (
              <div className="hidden sm:flex items-center space-x-1.5 bg-surface-2 border border-border px-2 py-0.5 rounded-full">
                <span className="text-[10px] text-text-muted uppercase font-bold">{weight}%</span>
              </div>
            )}
            <ChevronDown 
              size={18} 
              className={`text-text-muted transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} 
            />
          </div>
        </button>

        {/* Expanded Content */}
        <div className={`grid transition-all duration-300 ease-in-out ${isExpanded ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
          <div className="overflow-hidden">
            <div className="p-6 pl-6 pt-0 border-t border-border/30">
              <div className="pt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                  <div className="flex items-start space-x-3 bg-surface-2/30 p-4 rounded-xl border border-border/50">
                    <Info size={16} className="text-accent mt-1 flex-shrink-0" />
                    <div>
                      <h4 className="text-xs font-bold text-text-muted uppercase mb-1">Detailed Analysis</h4>
                      <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">
                        {details || 'Analysis complete. Review specific domain signals for insights.'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 p-4 rounded-xl border border-dashed border-border/50 group relative">
                    <HelpCircle size={16} className="text-text-muted mt-1 flex-shrink-0" />
                    <div>
                      <h4 className="text-xs font-bold text-text-muted uppercase mb-1">Why this matters</h4>
                      <p className="text-xs text-text-muted leading-relaxed">
                        {agent === 'Spend Analysis' ? 'Budget shifts directly impact CPA velocity and algorithmic learning phases.' :
                         agent === 'Creative Analysis' ? 'Ad fatigue or creative decay often precursors drops in conversion efficiency.' :
                         agent === 'Seasonal Analysis' ? 'External trends can mask or amplify internal performance shifts.' :
                         agent === 'Competitor Analysis' ? 'Auction pressure from competitors increases CPCs regardless of internal quality.' :
                         'Technical tracking issues can result in ghost data or misattribution of performance.'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <MiniSparkline data={chartData} color={styles.icon.replace('text-', 'var(--color-')} />
                  <div className="text-[10px] text-text-muted leading-tight p-2 bg-surface-2 rounded-lg border border-border/30">
                    Visualizing historical trend for {agent.toLowerCase()} over the last 30 days.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignalCard;