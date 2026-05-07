import React, { useState, useEffect } from 'react';
import { Loader2, AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react';

const AutoDetector = ({ onInvestigate }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({ anomalies: [], total_dates_scanned: 30, multi_channel_dates: [], channels_scanned: [] });
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/auto-detect');
        if (!response.ok) {
          throw new Error('Failed to fetch anomalies');
        }
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8 bg-surface border border-border rounded-lg">
        <Loader2 className="animate-spin text-text-muted w-8 h-8" />
        <span className="ml-3 text-text-primary">Scanning for anomalies...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-surface border border-border rounded-lg text-red-500">
        Error: {error}
      </div>
    );
  }

  const { anomalies, total_dates_scanned, multi_channel_dates, channels_scanned } = data;

  if (anomalies.length === 0) {
    return (
      <div className="p-8 bg-surface border border-border rounded-lg flex flex-col items-center justify-center text-green-500">
        <CheckCircle className="w-12 h-12 mb-2" />
        <span className="text-lg">No anomalies in last {total_dates_scanned} days</span>
      </div>
    );
  }

  const filteredAnomalies = anomalies.filter(anomaly => {
    if (filter === "all") return true;
    if (filter === "multi_channel") return anomaly.correlation_type === "multi_channel_event";
    return anomaly.severity === filter;
  });

  const getSeverityConfig = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return { icon: <AlertTriangle className="w-4 h-4 mr-1" />, bg: '#ef4444', text: 'HIGH' };
      case 'medium':
        return { icon: <AlertCircle className="w-4 h-4 mr-1" />, bg: '#f59e0b', text: 'MEDIUM' };
      case 'low':
      default:
        return { icon: <Info className="w-4 h-4 mr-1" />, bg: '#3b82f6', text: 'LOW' };
    }
  };

  const FilterButton = ({ label, value }) => (
    <button
      onClick={() => setFilter(value)}
      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
        filter === value ? 'bg-accent text-white' : 'bg-surface-2 border border-border text-text-muted'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="bg-bg p-4 space-y-4">
      <div className="flex flex-wrap gap-2 mb-2">
        <FilterButton label="All" value="all" />
        <FilterButton label="Multi-Channel" value="multi_channel" />
        <FilterButton label="High" value="high" />
        <FilterButton label="Medium" value="medium" />
        <FilterButton label="Low" value="low" />
      </div>

      <div className="text-xs text-text-muted">
        Showing {filteredAnomalies.length} of {anomalies.length} anomalies across {channels_scanned.length} channels · {multi_channel_dates.length} multi-channel events detected
      </div>

      <div className="space-y-3">
        {filteredAnomalies.map((anomaly, index) => {
          const sevConfig = getSeverityConfig(anomaly.severity);
          const isMultiChannel = anomaly.correlation_type === "multi_channel_event";
          
          return (
            <div 
              key={index} 
              className={`bg-surface border rounded-lg p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-sm transition-all ${
                isMultiChannel ? 'border-purple-500/50' : 'border-border'
              }`}
            >
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-text-primary text-lg">{anomaly.date}</span>
                  <div className="flex items-center gap-1.5">
                    <span 
                      className="inline-flex items-center px-2 py-0.5 rounded text-white text-xs font-bold"
                      style={{ backgroundColor: sevConfig.bg }}
                    >
                      {sevConfig.icon}
                      {sevConfig.text}
                    </span>
                    {isMultiChannel && (
                      <span 
                        className="inline-flex items-center px-2 py-0.5 rounded text-white text-xs font-bold"
                        style={{ backgroundColor: '#7c3aed' }}
                      >
                        MULTI-CHANNEL
                      </span>
                    )}
                  </div>
                </div>

                {anomaly.affected_channels && anomaly.affected_channels.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {anomaly.affected_channels.map((channel, idx) => (
                      <span key={idx} className="bg-surface-2 border border-border text-text-muted px-2 py-0.5 rounded text-xs font-medium">
                        {channel}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  {anomaly.signals && anomaly.signals.map((signal, idx) => (
                    <span key={idx} className="bg-bg border border-border text-text-muted px-2 py-1 rounded text-xs font-medium">
                      {signal}
                    </span>
                  ))}
                </div>
              </div>
              <button 
                onClick={() => isMultiChannel ? onInvestigate(anomaly.date, anomaly.affected_channels) : onInvestigate(anomaly.date)}
                className="whitespace-nowrap bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors text-sm"
              >
                {isMultiChannel ? 'Investigate All Channels →' : 'Investigate →'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AutoDetector;
