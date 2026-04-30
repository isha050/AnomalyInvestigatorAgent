import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

const MMMStatus = () => {
  const [status, setStatus] = useState('loading');
  const [modelId, setModelId] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/mmm-status')
      .then(res => res.json())
      .then(data => {
        setStatus(data.status);
        setModelId(data.model_id || null);
      })
      .catch(() => setStatus('unavailable'));
  }, []);

  if (status === 'loading') {
    return (
      <div className="flex items-center gap-1 text-text-muted text-xs mt-1">
        <Loader2 className="animate-spin" size={12} />
        <span>Checking MMM connection...</span>
      </div>
    );
  }

  if (status === 'ok') {
    return (
      <div className="flex items-center gap-1 text-green-400 text-xs mt-1">
        <CheckCircle size={12} />
        <span>MMM data connected {modelId ? `· ${modelId}` : ''}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1 text-text-muted text-xs mt-1">
      <XCircle size={12} />
      <span>MMM data not available — using agent signals only</span>
    </div>
  );
};

export default MMMStatus;
