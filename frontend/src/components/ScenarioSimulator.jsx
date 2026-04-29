import React, { useState, useEffect, useRef } from 'react';
import { Loader2, TrendingUp, TrendingDown, Info } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, ReferenceLine, Dot } from 'recharts';
import SummaryBubble from './SummaryBubble';

const ScenarioSimulator = () => {
  const [models, setModels] = useState(null);
  const [allocations, setAllocations] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSummary, setShowSummary] = useState(false);

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    if (result) {
      const timer = setTimeout(() => setShowSummary(true), 10);
      return () => clearTimeout(timer);
    } else {
      setShowSummary(false);
    }
  }, [result]);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/scenario-models');
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      setModels(data);
      
      // Initialize allocations with midpoint
      const initialAllocations = {};
      Object.keys(data.models).forEach(channel => {
        const model = data.models[channel];
        initialAllocations[channel] = Math.round((model.min_spend + model.max_spend) / 2);
      });
      setAllocations(initialAllocations);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ allocations })
      });
      if (!response.ok) throw new Error('Simulation failed');
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAllocationChange = (channel, value) => {
    setAllocations(prev => ({
      ...prev,
      [channel]: Number(value)
    }));
  };

  if (!models && loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  if (error && !models) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500 rounded-lg text-red-200">
        Error: {error}
      </div>
    );
  }

  const totalBudget = Object.values(allocations).reduce((sum, val) => sum + val, 0);

  const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  const formatNumber = (val) => new Intl.NumberFormat('en-US').format(val);

  const DeltaBadge = ({ current, baseline, type = 'cpa' }) => {
    if (baseline === 0) return null;
    const diff = current - baseline;
    const pct = (diff / baseline) * 100;
    
    // For CPA, lower is better. For others, higher is better.
    const isImproved = type === 'cpa' ? diff < 0 : diff > 0;
    const colorClass = isImproved ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10';
    
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ml-2 ${colorClass}`}>
        {isImproved ? <TrendingDown size={12} className="mr-1" /> : <TrendingUp size={12} className="mr-1" />}
        {Math.abs(pct).toFixed(1)}%
      </span>
    );
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">Scenario Simulator</h2>
        <button
          onClick={runSimulation}
          disabled={loading}
          className="bg-accent hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-semibold flex items-center transition-colors shadow-lg"
        >
          {loading ? <Loader2 className="animate-spin mr-2" size={20} /> : null}
          Run Simulation
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-900/20 border border-red-500 rounded-lg text-red-200">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Allocation Controls */}
        <div className="lg:col-span-2 bg-surface border border-border rounded-xl p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-6 text-text-primary flex items-center">
            Budget Allocation
            <Info size={16} className="ml-2 text-text-muted" />
          </h3>
          
          <div className="space-y-6">
            {models && models.channels.map(channel => {
              const model = models.models[channel];
              const skipReason = models.skipped_channels[channel];
              
              if (skipReason) {
                return (
                  <div key={channel} className="space-y-2 opacity-40 cursor-not-allowed grayscale">
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-sm font-medium text-text-primary uppercase tracking-wider flex items-center">
                        {channel}
                        <span className="ml-3 text-[10px] bg-surface-2 px-1.5 py-0.5 rounded text-text-muted border border-border">SKIPPED</span>
                      </label>
                      <div className="text-xs text-text-muted italic">Insufficient historical data to model this channel.</div>
                    </div>
                    <div className="w-full h-2 bg-surface-2 rounded-lg" />
                  </div>
                );
              }

              if (!model) return null;
              
              return (
                <div key={channel} className="space-y-2">
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-text-primary uppercase tracking-wider">
                      {channel}
                      <span className="ml-3 text-xs text-text-muted font-normal">R² {model.r_squared.toFixed(2)}</span>
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1.5 text-text-muted text-sm">$</span>
                      <input
                        type="number"
                        value={allocations[channel] || 0}
                        onChange={(e) => handleAllocationChange(channel, e.target.value)}
                        className="bg-surface-2 border border-border rounded px-7 py-1 text-sm text-right w-32 focus:border-accent outline-none"
                      />
                    </div>
                  </div>

                  {/* Sparkline */}
                  <div className="h-10 w-full bg-surface-2/30 rounded relative overflow-hidden">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={model.history}>
                        <Line 
                          type="monotone" 
                          dataKey="spend" 
                          stroke="#3b82f6" 
                          strokeWidth={2} 
                          dot={false}
                          activeDot={false}
                          isAnimationActive={false}
                        />
                        {/* Reference Line for current allocation */}
                        {/* We map current spend to the index based on historical range roughly */}
                        {/* Prompt: "vertical dashed line on the sparkline at the point on the x-axis proportional to where the current slider value sits" */}
                        {(() => {
                            const currentSpend = allocations[channel] || 0;
                            const xRatio = (currentSpend - 0) / (model.max_spend * 1.5);
                            const historyLen = model.history.length;
                            const xVal = xRatio * (historyLen - 1);
                            return (
                                <ReferenceLine x={xVal} stroke="#3b82f6" strokeDasharray="3 3" />
                            );
                        })()}
                        {/* Small dot on last point */}
                        <Line 
                          dataKey="spend" 
                          stroke="none" 
                          dot={(props) => {
                            const { index } = props;
                            if (index === model.history.length - 1) {
                              return <Dot {...props} r={3} fill="#3b82f6" stroke="none" />;
                            }
                            return null;
                          }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  <input
                    type="range"
                    min="0"
                    max={Math.round(model.max_spend * 1.5)}
                    step="100"
                    value={allocations[channel] || 0}
                    onChange={(e) => handleAllocationChange(channel, e.target.value)}
                    className="w-full h-2 bg-surface-2 rounded-lg appearance-none cursor-pointer accent-accent"
                  />
                </div>
              );
            })}
          </div>

          <div className="mt-8 pt-6 border-t border-border flex justify-between items-center">
            <span className="text-text-muted uppercase text-xs font-bold tracking-widest">Total Budget</span>
            <span className="text-2xl font-bold text-accent">{formatCurrency(totalBudget)}</span>
          </div>
        </div>

        {/* Results Overview */}
        {result && (
          <div className={`space-y-6 transition-all duration-300 ${showSummary ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'}`}>
            <div className="bg-surface border border-border rounded-xl p-6 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-accent"></div>
              <h4 className="text-sm font-bold text-text-muted uppercase mb-4">Scenario Summary</h4>
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-text-muted uppercase mb-1">Blended CPA</div>
                  <div className="text-2xl font-bold flex items-center">
                    {formatCurrency(result.scenario_summary.blended_cpa)}
                    <DeltaBadge 
                      current={result.scenario_summary.blended_cpa} 
                      baseline={result.baseline_summary.blended_cpa} 
                      type="cpa" 
                    />
                  </div>
                </div>
                <div>
                  <div className="text-xs text-text-muted uppercase mb-1">Total Conversions</div>
                  <div className="text-2xl font-bold flex items-center">
                    {formatNumber(result.scenario_summary.total_conversions.toFixed(2))}
                    <DeltaBadge 
                      current={result.scenario_summary.total_conversions} 
                      baseline={result.baseline_summary.total_conversions} 
                      type="conversions" 
                    />
                  </div>
                </div>
                <div>
                  <div className="text-xs text-text-muted uppercase mb-1">Total Spend</div>
                  <div className="text-xl font-bold">{formatCurrency(result.scenario_summary.total_spend)}</div>
                </div>
              </div>
            </div>

            <div className="bg-surface/50 border border-border rounded-xl p-6 shadow-xl">
              <h4 className="text-sm font-bold text-text-muted uppercase mb-4">Baseline Summary</h4>
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-text-muted uppercase mb-1">Blended CPA</div>
                  <div className="text-xl font-bold text-text-primary opacity-80">{formatCurrency(result.baseline_summary.blended_cpa)}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted uppercase mb-1">Total Conversions</div>
                  <div className="text-xl font-bold text-text-primary opacity-80">{formatNumber(result.baseline_summary.total_conversions.toFixed(2))}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted uppercase mb-1">Total Spend</div>
                  <div className="text-lg font-bold text-text-primary opacity-80">{formatCurrency(result.baseline_summary.total_spend)}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Narration */}
      {result && result.narration && (
        <SummaryBubble text={result.narration} />
      )}

      {/* Detailed Table */}
      {result && (
        <div className="bg-surface border border-border rounded-xl shadow-xl overflow-hidden">
          <div className="p-6 border-b border-border">
            <h3 className="text-lg font-semibold text-text-primary">Channel Breakdown</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-2/50 text-text-muted text-xs uppercase tracking-wider">
                  <th className="px-6 py-4 font-bold">Channel</th>
                  <th className="px-6 py-4 font-bold">Spend</th>
                  <th className="px-6 py-4 font-bold">Predicted CVR</th>
                  <th className="px-6 py-4 font-bold">Est. Conversions</th>
                  <th className="px-6 py-4 font-bold">Est. CPA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {result.scenario.map((s) => {
                  const b = result.baseline.find(x => x.channel === s.channel) || { spend: 0, predicted_cvr: 0, estimated_conversions: 0, estimated_cpa: 0 };
                  return (
                    <tr key={s.channel} className="hover:bg-surface-2/30 transition-colors">
                      <td className="px-6 py-4 font-semibold text-text-primary">
                        {s.channel}
                        {s.extrapolation_warning && (
                          <div className="text-[10px] text-amber-400 font-normal flex items-center mt-1">
                            <Info size={10} className="mr-1" /> Extrapolated
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-text-primary">{formatCurrency(s.spend)}</div>
                        <div className="text-[10px] text-text-muted flex items-center">
                          Base: {formatCurrency(b.spend)}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-text-primary">{(s.predicted_cvr * 100).toFixed(2)}%</div>
                        <DeltaBadge current={s.predicted_cvr} baseline={b.predicted_cvr} type="cvr" />
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-text-primary">{s.estimated_conversions.toFixed(2)}</div>
                        <DeltaBadge current={s.estimated_conversions} baseline={b.estimated_conversions} type="conversions" />
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-text-primary">
                          {s.estimated_cpa !== null ? formatCurrency(s.estimated_cpa) : 'N/A'}
                        </div>
                        {s.estimated_cpa !== null && <DeltaBadge current={s.estimated_cpa} baseline={b.estimated_cpa} type="cpa" />}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScenarioSimulator;
