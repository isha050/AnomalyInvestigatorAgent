import React, { useState, useEffect } from 'react';
import { Loader2, AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react';

const AutoDetector = ({ onInvestigate }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({ anomalies: [], total_dates_scanned: 30 });
  const [error, setError] = useState(null);

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

  const { anomalies, total_dates_scanned } = data;

  if (anomalies.length === 0) {
    return (
      <div className="p-8 bg-surface border border-border rounded-lg flex flex-col items-center justify-center text-green-500">
        <CheckCircle className="w-12 h-12 mb-2" />
        <span className="text-lg">No anomalies in last {total_dates_scanned} days</span>
      </div>
    );
  }

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

  return (
    <div className="bg-bg p-4 space-y-4">
      <h2 className="text-xl font-bold text-text-primary mb-4">
        {anomalies.length} {anomalies.length === 1 ? 'anomaly' : 'anomalies'} detected across {total_dates_scanned} dates scanned
      </h2>
      <div className="space-y-3">
        {anomalies.map((anomaly, index) => {
          const sevConfig = getSeverityConfig(anomaly.severity);
          
          return (
            <div key={index} className="bg-surface border border-border p-4 rounded-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-sm">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-text-primary text-lg">{anomaly.date}</span>
                  <span 
                    className="inline-flex items-center px-2 py-0.5 rounded text-white text-xs font-bold"
                    style={{ backgroundColor: sevConfig.bg }}
                  >
                    {sevConfig.icon}
                    {sevConfig.text}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {anomaly.signals && anomaly.signals.map((signal, idx) => (
                    <span key={idx} className="bg-bg border border-border text-text-muted px-2 py-1 rounded text-xs font-medium">
                      {signal}
                    </span>
                  ))}
                </div>
              </div>
              <button 
                onClick={() => onInvestigate(anomaly.date)}
                className="whitespace-nowrap bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors text-sm"
              >
                Investigate &rarr;
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AutoDetector;
