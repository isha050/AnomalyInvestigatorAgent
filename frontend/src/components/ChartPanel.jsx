import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';

const MetricChart = ({ title, data }) => (
  <div className="bg-surface border border-border rounded-lg p-4 h-64">
    <h4 className="text-text-muted text-xs font-medium mb-2 uppercase tracking-tight">{title}</h4>
    <ResponsiveContainer width="100%" height="90%">
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" vertical={false} />
        <XAxis 
          dataKey="date" 
          stroke="#a1a1aa" 
          fontSize={10}
          tickLine={false}
          axisLine={false}
          tickFormatter={(str) => str.split('-').slice(1).join('/')}
        />
        <YAxis 
          stroke="#a1a1aa" 
          fontSize={10}
          tickLine={false}
          axisLine={false}
          width={30}
        />
        <Tooltip 
          contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', fontSize: '12px' }}
          itemStyle={{ color: '#eeeeee' }}
          labelStyle={{ color: '#a1a1aa' }}
        />
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke="#3b82f6" 
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: '#3b82f6' }}
        />
      </LineChart>
    </ResponsiveContainer>
  </div>
);

const ChartPanel = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/chart-data')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load chart data", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-surface border border-border rounded-xl p-12 flex flex-col items-center justify-center mb-6 h-64">
        <Loader2 className="animate-spin text-accent mb-2" />
        <p className="text-text-muted text-sm">Loading market data...</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <MetricChart title="Daily Spend (Google)" data={data?.spend} />
      <MetricChart title="CTR Trend" data={data?.ctr} />
      <MetricChart title="CVR Trend" data={data?.cvr} />
      <MetricChart title="Market Interest (Comp.)" data={data?.competitor} />
    </div>
  );
};

export default ChartPanel;
