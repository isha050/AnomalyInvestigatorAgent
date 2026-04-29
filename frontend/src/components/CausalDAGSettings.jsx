import React, { useState, useEffect } from 'react';
import { Loader2, RefreshCw, Save, AlertCircle, CheckCircle2, Info } from 'lucide-react';

const CausalDAGSettings = () => {
  const [config, setConfig] = useState({
    id: null,
    models: [],
    dagGenerationStrategy: 'AUTO',
    dagGenerationStatus: 'PENDING',
    dagGenerationFailureReason: null,
    dagType: 'MMM',
    lastUpdatedAt: null
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [banner, setBanner] = useState(null); // { type: 'success' | 'error' | 'warning', message: string }

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/causal-dag-settings?dagType=MMM');
      const result = await response.json();
      
      let data = result.data;
      if (typeof data === 'string') {
        try {
          data = JSON.parse(data);
        } catch (e) {
          console.error("Failed to parse data string", e);
        }
      }
      
      const finalConfig = data || result.config || config;
      setConfig(finalConfig);
      
      if (result._fallback) {
        showBanner('warning', 'Could not reach Lifesight API — showing fallback config');
      }
    } catch (error) {
      console.error("Fetch failed", error);
      showBanner('error', 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const showBanner = (type, message) => {
    setBanner({ type, message });
    if (type !== 'warning') {
      setTimeout(() => setBanner(null), 4000);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/causal-dag-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const result = await response.json();
      
      if (result.success) {
        showBanner('success', 'Settings saved successfully.');
      } else {
        showBanner('error', result.errors?.[0] || 'Failed to save settings');
      }
    } catch (error) {
      console.error("Save failed", error);
      showBanner('error', 'Network error while saving');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-surface border border-border rounded-xl">
        <Loader2 className="animate-spin text-accent mb-4" size={40} />
        <p className="text-text-muted">Loading DAG settings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {banner && (
        <div className={`p-4 rounded-lg flex items-center space-x-3 border ${
          banner.type === 'success' ? 'bg-green-500/10 border-green-500/50 text-green-400' :
          banner.type === 'warning' ? 'bg-yellow-500/10 border-yellow-500/50 text-yellow-400' :
          'bg-red-500/10 border-red-500/50 text-red-400'
        }`}>
          {banner.type === 'success' ? <CheckCircle2 size={20} /> : 
           banner.type === 'warning' ? <Info size={20} /> : <AlertCircle size={20} />}
          <p className="flex-1">{banner.message}</p>
          {banner.type === 'warning' && (
            <button onClick={() => setBanner(null)} className="text-xs hover:underline">Dismiss</button>
          )}
        </div>
      )}

      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="p-6 border-b border-border flex items-center justify-between">
          <h2 className="text-xl font-bold flex items-center">
            Causal DAG Settings
          </h2>
          <button 
            onClick={fetchSettings}
            className="p-2 hover:bg-surface-2 rounded-lg transition-colors text-text-muted hover:text-text-primary"
            title="Reload Settings"
          >
            <RefreshCw size={20} />
          </button>
        </div>

        <div className="p-6 space-y-8">
          {/* Section 1: DAG Configuration */}
          <section>
            <h3 className="text-sm font-semibold text-accent uppercase tracking-wider mb-4">DAG Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm text-text-muted block">DAG Type</label>
                <select 
                  className="w-full bg-surface-2 border border-border rounded-lg p-2.5 focus:outline-none focus:border-accent text-text-primary"
                  value={config.dagType}
                  onChange={(e) => setConfig({...config, dagType: e.target.value})}
                >
                  <option value="MMM">MMM</option>
                  <option value="ATTRIBUTION">ATTRIBUTION</option>
                  <option value="CUSTOM">CUSTOM</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-text-muted block">Generation Strategy</label>
                <select 
                  className="w-full bg-surface-2 border border-border rounded-lg p-2.5 focus:outline-none focus:border-accent text-text-primary"
                  value={config.dagGenerationStrategy}
                  onChange={(e) => setConfig({...config, dagGenerationStrategy: e.target.value})}
                >
                  <option value="AUTO">AUTO</option>
                  <option value="MANUAL">MANUAL</option>
                  <option value="SCHEDULED">SCHEDULED</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-text-muted block">Generation Status</label>
                <input 
                  type="text"
                  readOnly
                  className="w-full bg-surface-2 border border-border rounded-lg p-2.5 opacity-60 text-text-primary"
                  value={config.dagGenerationStatus}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-text-muted block">Last Updated</label>
                <input 
                  type="text"
                  readOnly
                  className="w-full bg-surface-2 border border-border rounded-lg p-2.5 opacity-60 text-text-primary"
                  value={config.lastUpdatedAt || 'Never'}
                />
              </div>
            </div>

            {config.dagGenerationFailureReason && (
              <div className="mt-6 space-y-2">
                <label className="text-sm text-red-400 block">Failure Reason</label>
                <div className="w-full bg-red-500/5 border border-red-500/20 rounded-lg p-3 text-red-300 text-sm">
                  {config.dagGenerationFailureReason}
                </div>
              </div>
            )}
          </section>

          {/* Section 2: Models */}
          <section>
            <h3 className="text-sm font-semibold text-accent uppercase tracking-wider mb-4">Models</h3>
            {config.models && config.models.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {config.models.map((model, idx) => (
                  <div key={idx} className="bg-surface-2 border border-border p-4 rounded-xl">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-bold text-text-primary">{model.modelDisplayName}</span>
                      <span className="bg-surface border border-border text-accent rounded-full px-2 py-0.5 text-xs">
                        {model.source}
                      </span>
                    </div>
                    <div className="text-xs text-text-muted">{model.modelName}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-text-muted italic">No models configured yet.</p>
            )}
            <p className="mt-4 text-xs text-text-muted flex items-center">
              <Info size={12} className="mr-1" />
              Model configuration is managed via the Lifesight platform.
            </p>
          </section>

          <div className="pt-6 border-t border-border flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="bg-accent hover:bg-accent/80 disabled:bg-surface-2 text-white px-6 py-2.5 rounded-lg font-medium transition-all flex items-center space-x-2"
            >
              {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
              <span>{saving ? 'Saving...' : 'Save Settings'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CausalDAGSettings;