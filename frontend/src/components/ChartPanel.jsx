import React, { useEffect, useState, useMemo } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine, 
  ReferenceArea,
  Label
} from 'recharts';
import { Loader2, LayoutGrid } from 'lucide-react';

const CustomTooltip = ({ active, payload, label, allData }) => {
  if (active && payload && payload.length) {
    const date = label;
    const findValue = (dataset) => dataset?.find(d => d.date === date)?.value;
    
    const spend = findValue(allData?.spend);
    const ctr = findValue(allData?.ctr);
    const cvr = findValue(allData?.cvr);
    const comp = findValue(allData?.competitor);

    return (
      <div className="bg-surface border border-border p-3 rounded-lg shadow-xl text-xs space-y-2 min-w-[140px]">
        <p className="text-text-muted font-bold border-b border-border pb-1 mb-1">{date}</p>
        {spend !== undefined && (
          <div className="flex justify-between">
            <span className="text-text-muted">Spend:</span>
            <span className="text-blue-400 font-mono">${spend.toFixed(0)}</span>
          </div>
        )}
        {ctr !== undefined && (
          <div className="flex justify-between">
            <span className="text-text-muted">CTR:</span>
            <span className="text-accent font-mono">{ctr.toFixed(2)}%</span>
          </div>
        )}
        {cvr !== undefined && (
          <div className="flex justify-between">
            <span className="text-text-muted">CVR:</span>
            <span className="text-green-400 font-mono">{(cvr * 100).toFixed(2)}%</span>
          </div>
        )}
        {comp !== undefined && (
          <div className="flex justify-between">
            <span className="text-text-muted">Comp:</span>
            <span className="text-purple-400 font-mono">{comp.toFixed(1)}</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

const MetricChart = ({ title, data, allData, anomalyDate, color = "#3b82f6" }) => {
  const baseline = useMemo(() => {
    if (!data || data.length === 0) return null;
    const avg = data.reduce((sum, d) => sum + d.value, 0) / data.length;
    return {
      avg,
      min: avg * 0.9,
      max: avg * 1.1
    };
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <div className="bg-transparent border border-border/30 border-dashed rounded-xl p-4 h-64 flex flex-col items-center justify-center">
        <LayoutGrid size={24} className="text-text-muted/30 mb-2" />
        <p className="text-text-muted text-[10px] font-bold uppercase">No data available</p>
      </div>
    );
  }

  return (
    <div className="bg-transparent border border-border/50 rounded-xl p-4 h-64 hover:border-accent/30 transition-colors">
      <h4 className="text-text-muted text-[10px] font-bold mb-4 uppercase tracking-widest">{title}</h4>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis 
            dataKey="date" 
            stroke="#52525b" 
            fontSize={9}
            tickLine={false}
            axisLine={false}
            tickFormatter={(str) => str.split('-').slice(2).join('/')}
          />
          <YAxis 
            stroke="#52525b" 
            fontSize={9}
            tickLine={false}
            axisLine={false}
            width={25}
          />
          <Tooltip content={<CustomTooltip allData={allData} />} />
          
          {baseline && (
            <ReferenceArea 
              y1={baseline.min} 
              y2={baseline.max} 
              fill={color} 
              fillOpacity={0.05} 
              stroke="none"
            />
          )}

          {anomalyDate && data?.some(d => d.date === anomalyDate) && (
            <ReferenceLine x={anomalyDate} stroke="#ef4444" strokeDasharray="3 3">
              <Label 
                value="Anomaly detected" 
                position="top" 
                fill="#ef4444" 
                fontSize={10} 
                fontWeight="bold"
                offset={10}
              />
            </ReferenceLine>
          )}

          <Line 
            type="monotone" 
            dataKey="value" 
            stroke={color} 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: color, strokeWidth: 0 }}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const ChartPanel = ({ anomalyDate }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState('Google');

  const channels = ['Google', 'Meta', 'TikTok'];

  const fetchData = async (selectedChannel) => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/chart-data?channel=${selectedChannel}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Failed to load chart data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(channel);
  }, [channel]);

  return (
    <div className="space-y-4 mb-6">
      <div className="flex items-center space-x-2 bg-surface p-1 rounded-xl border border-border w-fit">
        {channels.map((ch) => (
          <button
            key={ch}
            onClick={() => setChannel(ch)}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              channel === ch 
                ? 'bg-accent text-white shadow-lg' 
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {ch}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="bg-surface/50 border border-border rounded-xl p-12 flex flex-col items-center justify-center h-64">
          <Loader2 className="animate-spin text-accent mb-2" />
          <p className="text-text-muted text-sm tracking-tight">Filtering signals for {channel}...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricChart 
            title="Daily Spend" 
            data={data?.spend} 
            allData={data}
            anomalyDate={anomalyDate}
            color="#3b82f6"
          />
          <MetricChart 
            title="CTR Performance" 
            data={data?.ctr} 
            allData={data}
            anomalyDate={anomalyDate}
            color="#8b5cf6"
          />
          <MetricChart 
            title="Conversion Rate (CVR)" 
            data={data?.cvr} 
            allData={data}
            anomalyDate={anomalyDate}
            color="#10b981"
          />
          <MetricChart 
            title="Competitive Pressure" 
            data={data?.competitor} 
            allData={data}
            anomalyDate={anomalyDate}
            color="#f59e0b"
          />
        </div>
      )}
    </div>
  );
};

export default ChartPanel;