import React, { useState, useEffect, useMemo } from 'react';
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react';

const CountUp = ({ value, duration = 1000, prefix = '', suffix = '', decimals = 0 }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime = null;
    let animationFrame;

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const current = progress * value;
      setDisplayValue(current);
      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [value, duration]);

  return (
    <span>{prefix}{displayValue.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}{suffix}</span>
  );
};

const Sparkline = ({ data, width = 80, height = 30, color = 'var(--color-accent)' }) => {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

const KPICard = ({ label, value, trend, trendValue, sparkData, prefix, suffix, decimals, inverseTrend = false }) => {
  const isPositive = trend === 'up';
  const isGood = inverseTrend ? !isPositive : isPositive;
  const trendColor = isGood ? 'text-green-400' : 'text-red-400';
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;

  return (
    <div className="bg-surface border border-border rounded-xl p-4 flex flex-col justify-between hover:border-accent/50 transition-colors">
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs font-medium text-text-muted uppercase tracking-wider">{label}</span>
        <div className={`flex items-center space-x-1 text-xs font-bold ${trendColor}`}>
          <TrendIcon size={14} />
          <span>{trendValue}%</span>
        </div>
      </div>
      
      <div className="flex items-end justify-between">
        <div className="text-2xl font-bold text-accent">
          <CountUp value={value} prefix={prefix} suffix={suffix} decimals={decimals} />
        </div>
        <div className="mb-1 opacity-50">
          <Sparkline data={sparkData} />
        </div>
      </div>
    </div>
  );
};

const KPIBanner = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/chart-data');
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error("Failed to fetch KPI data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const metrics = useMemo(() => {
    if (!data) return null;

    // 1. Blended CPA (1/CVR)
    const cvrHistory = data.cvr.map(d => d.value);
    const currentCVR = cvrHistory[cvrHistory.length - 1];
    const prevCVR = cvrHistory[cvrHistory.length - 2];
    const currentCPA = 1 / currentCVR;
    const prevCPA = 1 / prevCVR;
    const cpaTrend = ((currentCPA - prevCPA) / prevCPA) * 100;
    const cpaSpark = cvrHistory.map(v => 1 / v).slice(-20);

    // 2. Weekly Conversions
    const spendMap = Object.fromEntries(data.spend.map(d => [d.date, d.value]));
    const convHistory = data.cvr.map(d => (spendMap[d.date] || 0) * d.value);
    const weekConversions = convHistory.slice(-7).reduce((a, b) => a + b, 0);
    const prevWeekConversions = convHistory.slice(-14, -7).reduce((a, b) => a + b, 0);
    const convTrend = prevWeekConversions > 0 ? ((weekConversions - prevWeekConversions) / prevWeekConversions) * 100 : 0;
    const convSpark = convHistory.slice(-20);

    // 3. Avg CTR
    const ctrHistory = data.ctr.map(d => d.value);
    const last7Ctr = ctrHistory.slice(-7);
    const currentAvgCTR = last7Ctr.length > 0 ? last7Ctr.reduce((a, b) => a + b, 0) / last7Ctr.length : 0;
    
    const prev7Ctr = ctrHistory.slice(-14, -7);
    const prevAvgCTR = prev7Ctr.length > 0 ? prev7Ctr.reduce((a, b) => a + b, 0) / prev7Ctr.length : 0;
    
    const ctrTrend = prevAvgCTR > 0 ? ((currentAvgCTR - prevAvgCTR) / prevAvgCTR) * 100 : 0;
    const ctrSpark = ctrHistory.slice(-20);

    return {
      cpa: { value: currentCPA, trend: cpaTrend > 0 ? 'up' : 'down', trendValue: Math.abs(cpaTrend).toFixed(1), spark: cpaSpark },
      conversions: { value: weekConversions, trend: convTrend > 0 ? 'up' : 'down', trendValue: Math.abs(convTrend).toFixed(1), spark: convSpark },
      ctr: { value: currentAvgCTR, trend: ctrTrend > 0 ? 'up' : 'down', trendValue: Math.abs(ctrTrend).toFixed(1), spark: ctrSpark }
    };
  }, [data]);

  if (loading) return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 opacity-50">
      {[1, 2, 3].map(i => (
        <div key={i} className="bg-surface border border-border rounded-xl p-4 h-24 flex items-center justify-center">
          <Loader2 className="animate-spin text-text-muted" size={20} />
        </div>
      ))}
    </div>
  );

  if (!metrics) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <KPICard 
        label="Blended CPA" 
        value={metrics.cpa.value} 
        trend={metrics.cpa.trend} 
        trendValue={metrics.cpa.trendValue}
        sparkData={metrics.cpa.spark}
        prefix="$"
        decimals={2}
        inverseTrend={true} // Lower is better for CPA
      />
      <KPICard 
        label="Weekly Conversions" 
        value={metrics.conversions.value} 
        trend={metrics.conversions.trend} 
        trendValue={metrics.conversions.trendValue}
        sparkData={metrics.conversions.spark}
        decimals={0}
      />
      <KPICard 
        label="Avg CTR" 
        value={metrics.ctr.value} 
        trend={metrics.ctr.trend} 
        trendValue={metrics.ctr.trendValue}
        sparkData={metrics.ctr.spark}
        suffix="%"
        decimals={2}
      />
    </div>
  );
};

export default KPIBanner;