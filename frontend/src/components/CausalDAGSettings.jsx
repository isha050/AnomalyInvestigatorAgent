import React, { useState, useEffect, useRef } from 'react';
import { Loader2, RefreshCw, Save, AlertCircle, CheckCircle2, Info, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

// ── Node type styles ──────────────────────────────────────────────────────────
const TYPE_STYLE = {
  Spend: { ring: '#3b82f6', fill: '#0f1e35', label: '#93c5fd' },
  Baseline: { ring: '#22c55e', fill: '#0a1f12', label: '#86efac' },
  KPI: { ring: '#ef4444', fill: '#2a0f0f', label: '#fca5a5' },
  Contextual: { ring: '#f59e0b', fill: '#221a08', label: '#fcd34d' },
  _default: { ring: '#6366f1', fill: '#12121f', label: '#a5b4fc' },
};

// ── Layout: arrange nodes in columns by type ──────────────────────────────────
function buildLayout(nodes) {
  const COL_ORDER = ['KPI', 'Spend', 'Baseline', 'Contextual'];
  const groups = { KPI: [], Spend: [], Baseline: [], Contextual: [] };

  nodes.forEach(n => {
    const key = COL_ORDER.includes(n.type) ? n.type : 'Contextual';
    groups[key].push(n);
  });

  const NODE_W = 165, NODE_H = 50, COL_GAP = 210, ROW_GAP = 62, PAD = 40;
  const pos = {};

  COL_ORDER.forEach((col, ci) => {
    groups[col].forEach((n, ri) => {
      pos[n.name] = { x: PAD + ci * COL_GAP, y: PAD + ri * ROW_GAP };
    });
  });

  const allPos = Object.values(pos);
  const svgW = allPos.length ? Math.max(...allPos.map(p => p.x)) + NODE_W + PAD : 600;
  const svgH = allPos.length ? Math.max(...allPos.map(p => p.y)) + NODE_H + PAD : 400;

  return { pos, NODE_W, NODE_H, svgW, svgH };
}

// ── DAG Graph component ───────────────────────────────────────────────────────
function DAGGraph({ nodes, edges }) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [drag, setDrag] = useState(null);
  const [hovered, setHovered] = useState(null);

  const { pos, NODE_W, NODE_H } = buildLayout(nodes);

  const hotSet = hovered
    ? new Set(
      edges
        .filter(e => e.sourceNode.name === hovered || e.targetNode.name === hovered)
        .flatMap(e => [e.sourceNode.name, e.targetNode.name])
    )
    : null;

  const onMouseDown = e => {
    if (e.target.closest('.dag-node')) return;
    setDrag({ ox: e.clientX - pan.x, oy: e.clientY - pan.y });
  };
  const onMouseMove = e => {
    if (!drag) return;
    setPan({ x: e.clientX - drag.ox, y: e.clientY - drag.oy });
  };
  const onMouseUp = () => setDrag(null);

  return (
    <div
      className="relative rounded-xl border border-[#2d3748] overflow-hidden bg-[#0d1117]"
      style={{ height: 460 }}
    >
      {/* Controls */}
      <div className="absolute top-3 right-3 z-10 flex gap-1.5">
        {[
          { Icon: ZoomIn, fn: () => setZoom(z => Math.min(z + 0.15, 3)) },
          { Icon: ZoomOut, fn: () => setZoom(z => Math.max(z - 0.15, 0.25)) },
          { Icon: Maximize2, fn: () => { setZoom(1); setPan({ x: 0, y: 0 }); } },
        ].map(({ Icon, fn }, i) => (
          <button
            key={i} onClick={fn}
            className="p-1.5 rounded-lg bg-[#161b22] border border-[#2d3748] text-[#8b9bbb] hover:text-white hover:border-[#3b82f6] transition-colors"
          >
            <Icon size={13} />
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-10 flex gap-3 flex-wrap">
        {Object.entries(TYPE_STYLE)
          .filter(([k]) => k !== '_default')
          .map(([type, s]) => (
            <span
              key={type}
              className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider"
              style={{ color: s.label }}
            >
              <span className="w-2 h-2 rounded-full" style={{ background: s.ring }} />
              {type}
            </span>
          ))}
      </div>

      {/* SVG canvas */}
      <svg
        width="100%" height="100%"
        style={{ cursor: drag ? 'grabbing' : 'grab' }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      >
        <defs>
          <marker id="arr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0 L7,3.5 L0,7 z" fill="#2d3f55" />
          </marker>
          <marker id="arr-hot" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0 L7,3.5 L0,7 z" fill="#3b82f6" />
          </marker>
        </defs>

        <g transform={`translate(${pan.x},${pan.y}) scale(${zoom})`}>
          {/* Edges */}
          {edges.map((edge, i) => {
            const s = pos[edge.sourceNode.name];
            const t = pos[edge.targetNode.name];
            if (!s || !t) return null;
            const hot = hovered && (
              edge.sourceNode.name === hovered || edge.targetNode.name === hovered
            );
            const x1 = s.x + NODE_W, y1 = s.y + NODE_H / 2;
            const x2 = t.x, y2 = t.y + NODE_H / 2;
            const mx = (x1 + x2) / 2;
            return (
              <path
                key={i}
                d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
                fill="none"
                stroke={hot ? '#3b82f6' : '#1e2d40'}
                strokeWidth={hot ? 2 : 1.2}
                markerEnd={hot ? 'url(#arr-hot)' : 'url(#arr)'}
                opacity={hovered && !hot ? 0.12 : 1}
                style={{ transition: 'opacity 0.12s' }}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map(node => {
            const p = pos[node.name];
            if (!p) return null;
            const s = TYPE_STYLE[node.type] || TYPE_STYLE._default;
            const hot = hovered === node.name;
            const fade = hovered && !hotSet.has(node.name);
            const lbl = node.displayName || node.name;
            const short = lbl.length > 19 ? lbl.slice(0, 17) + '…' : lbl;

            return (
              <g
                key={node.name}
                className="dag-node"
                transform={`translate(${p.x},${p.y})`}
                onMouseEnter={() => setHovered(node.name)}
                onMouseLeave={() => setHovered(null)}
                style={{
                  cursor: 'pointer',
                  opacity: fade ? 0.18 : 1,
                  transition: 'opacity 0.12s',
                }}
              >
                <rect
                  width={NODE_W} height={NODE_H} rx={7}
                  fill={s.fill}
                  stroke={hot ? s.ring : s.ring + '66'}
                  strokeWidth={hot ? 2 : 1}
                />
                {/* Type badge */}
                <rect x={7} y={7} width={54} height={13} rx={3} fill={s.ring} opacity={0.18} />
                <text
                  x={34} y={17.5} textAnchor="middle" fontSize={8} fontWeight="700"
                  fill={s.label} style={{ textTransform: 'uppercase', letterSpacing: '0.8px' }}
                >
                  {node.type}
                </text>
                {/* Display name */}
                <text x={NODE_W / 2} y={35} textAnchor="middle" fontSize={11} fontWeight="600" fill="#e2e8f0">
                  {short}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Hover tooltip */}
      {hovered && (() => {
        const node = nodes.find(n => n.name === hovered);
        if (!node) return null;
        const ins = edges.filter(e => e.targetNode.name === hovered).length;
        const outs = edges.filter(e => e.sourceNode.name === hovered).length;
        return (
          <div className="pointer-events-none absolute top-3 left-3 z-20 bg-[#161b22] border border-[#2d3748] rounded-lg px-3 py-2 shadow-xl text-xs">
            <div className="font-bold text-white mb-1">{node.displayName || node.name}</div>
            <div className="text-[#8b9bbb]">
              Type: <span className="text-[#60a5fa]">{node.type}</span>
            </div>
            <div className="text-[#8b9bbb]">In: {ins} &nbsp; Out: {outs}</div>
          </div>
        );
      })()}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
const CausalDAGSettings = () => {
  const [config, setConfig] = useState({
    id: null,
    models: [],
    dagGenerationStrategy: 'AUTO',
    dagGenerationStatus: 'PENDING',
    dagGenerationFailureReason: null,
    dagType: 'MMM',
    lastUpdatedAt: null,
  });
  const [dagGraph, setDagGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [graphLoading, setGraphLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [banner, setBanner] = useState(null);
  const [activeTab, setActiveTab] = useState('config');

  const showBanner = (type, message) => {
    setBanner({ type, message });
    if (type !== 'warning') setTimeout(() => setBanner(null), 4000);
  };

  // ── fetch settings ──────────────────────────────────────────────────────────
  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/causal-dag-settings?dagType=${config.dagType}`);
      const json = await res.json();

      // API returns { data: { id, models, dagGenerationStrategy, ... }, success, errors }
      // json.data is already a plain object — do NOT JSON.parse it
      const raw = json.data;

      if (raw && typeof raw === 'object') {
        setConfig({
          id: raw.id ?? null,
          models: raw.models ?? [],
          dagGenerationStrategy: raw.dagGenerationStrategy ?? 'AUTO',
          dagGenerationStatus: raw.dagGenerationStatus ?? 'PENDING',
          dagGenerationFailureReason: raw.dagGenerationFailureReason ?? null,
          dagType: raw.dagType ?? 'MMM',
          lastUpdatedAt: raw.lastUpdatedAt ?? null,
        });

        // Auto-load graph when status is SUCCESS
        if (raw.dagGenerationStatus === 'SUCCESS') {
          const modelId = raw.models?.[0]?.modelId ? String(raw.models[0].modelId) : '';
          fetchGraph(modelId);
        }
      } else if (json._fallback) {
        showBanner('warning', 'Could not reach Lifesight API — check MMM_WORKSPACE and MMM_APIKEY in your .env');
      }
    } catch (err) {
      console.error('fetchSettings failed', err);
      showBanner('error', 'Failed to load settings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── fetch DAG graph ─────────────────────────────────────────────────────────
  const fetchGraph = async (modelId = '') => {
    setGraphLoading(true);
    try {
      const url = `http://localhost:8000/causal-dag-graph${modelId ? `?modelId=${modelId}` : ''}`;
      const res = await fetch(url);
      const json = await res.json();
      if (json.data) {
        setDagGraph({ nodes: json.data.nodes || [], edges: json.data.edges || [] });
        setActiveTab('graph');
      }
    } catch (err) {
      console.error('fetchGraph failed', err);
    } finally {
      setGraphLoading(false);
    }
  };

  useEffect(() => { fetchSettings(); }, []);

  // ── save settings ───────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch('http://localhost:8000/causal-dag-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      const json = await res.json();
      if (json.success) {
        showBanner('success', 'Settings saved successfully.');
      } else {
        showBanner('error', json.errors?.[0] || 'Failed to save settings');
      }
    } catch (err) {
      showBanner('error', 'Network error: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // ── loading state ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-surface border border-border rounded-xl">
        <Loader2 className="animate-spin text-accent mb-4" size={40} />
        <p className="text-text-muted">Loading DAG settings…</p>
      </div>
    );
  }

  const statusStyle = {
    SUCCESS: 'text-green-400 bg-green-500/10 border-green-500/30',
    PENDING: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    FAILED: 'text-red-400   bg-red-500/10   border-red-500/30',
  }[config.dagGenerationStatus] || 'text-text-muted bg-surface-2 border-border';

  return (
    <div className="space-y-6">
      {/* Banner */}
      {banner && (
        <div className={`p-4 rounded-lg flex items-center gap-3 border text-sm ${banner.type === 'success' ? 'bg-green-500/10 border-green-500/50 text-green-400' :
            banner.type === 'warning' ? 'bg-yellow-500/10 border-yellow-500/50 text-yellow-400' :
              'bg-red-500/10   border-red-500/50   text-red-400'
          }`}>
          {banner.type === 'success' ? <CheckCircle2 size={18} /> :
            banner.type === 'warning' ? <Info size={18} /> : <AlertCircle size={18} />}
          <p className="flex-1">{banner.message}</p>
          <button onClick={() => setBanner(null)} className="text-xs opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-border flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-xl font-bold text-text-primary">Causal DAG Settings</h2>
            <div className={`inline-flex items-center gap-2 mt-2 px-3 py-1 rounded-full border text-xs font-bold ${statusStyle}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current" />
              {config.dagGenerationStatus}
              {config.lastUpdatedAt && (
                <span className="font-normal opacity-60 ml-1">
                  · {new Date(config.lastUpdatedAt).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={fetchSettings}
            className="p-2 hover:bg-surface-2 rounded-lg transition-colors text-text-muted hover:text-text-primary"
            title="Reload"
          >
            <RefreshCw size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          {[
            { id: 'config', label: 'Configuration' },
            {
              id: 'graph',
              label: dagGraph
                ? `Graph · ${dagGraph.nodes.length} nodes / ${dagGraph.edges.length} edges`
                : 'Graph',
            },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-6 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors ${activeTab === t.id
                  ? 'text-accent border-accent'
                  : 'text-text-muted border-transparent hover:text-text-primary'
                }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="p-6 space-y-8">

          {/* ── Configuration tab ───────────────────────────────────────────── */}
          {activeTab === 'config' && (
            <>
              <section>
                <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-4">DAG Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm text-text-muted block">DAG Type</label>
                    <select
                      className="w-full bg-surface-2 border border-border rounded-lg p-2.5 focus:outline-none focus:border-accent text-text-primary"
                      value={config.dagType}
                      onChange={e => setConfig({ ...config, dagType: e.target.value })}
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
                      onChange={e => setConfig({ ...config, dagGenerationStrategy: e.target.value })}
                    >
                      <option value="DEFAULT">DEFAULT</option>
                      <option value="AUTO">AUTO</option>
                      <option value="MANUAL">MANUAL</option>
                      <option value="SCHEDULED">SCHEDULED</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-text-muted block">Generation Status</label>
                    <input
                      readOnly
                      className="w-full bg-surface-2 border border-border rounded-lg p-2.5 text-text-primary opacity-60"
                      value={config.dagGenerationStatus}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-text-muted block">Last Updated</label>
                    <input
                      readOnly
                      className="w-full bg-surface-2 border border-border rounded-lg p-2.5 text-text-primary opacity-60"
                      value={config.lastUpdatedAt ? new Date(config.lastUpdatedAt).toLocaleString() : 'Never'}
                    />
                  </div>
                </div>

                {config.dagGenerationFailureReason && (
                  <div className="mt-4 p-3 bg-red-500/5 border border-red-500/20 rounded-lg text-red-300 text-sm">
                    {config.dagGenerationFailureReason}
                  </div>
                )}
              </section>

              <section>
                <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-4">Models</h3>
                {config.models.length > 0 ? (
                  <div className="space-y-3">
                    {config.models.map((model, idx) => (
                      <div
                        key={idx}
                        className="bg-surface-2 border border-border p-4 rounded-xl flex items-center justify-between gap-4 flex-wrap"
                      >
                        <div>
                          <div className="font-bold text-text-primary text-sm">
                            {model.modelDisplayName || model.modelName}
                          </div>
                          <div className="text-xs text-text-muted mt-0.5">ID: {model.modelId}</div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="bg-surface border border-border text-accent rounded-full px-2.5 py-0.5 text-xs font-bold">
                            {model.source}
                          </span>
                          {config.dagGenerationStatus === 'SUCCESS' && (
                            <button
                              onClick={() => fetchGraph(String(model.modelId))}
                              disabled={graphLoading}
                              className="text-xs bg-accent/10 border border-accent/30 text-accent px-3 py-1 rounded-lg hover:bg-accent/20 transition-colors disabled:opacity-50 flex items-center gap-1.5"
                            >
                              {graphLoading && <Loader2 size={11} className="animate-spin" />}
                              View Graph
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-text-muted italic text-sm">No models configured yet.</p>
                )}
                <p className="mt-3 text-xs text-text-muted flex items-center gap-1.5">
                  <Info size={12} />
                  Model configuration is managed via the Lifesight platform.
                </p>
              </section>

              <div className="pt-4 border-t border-border flex justify-end">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-accent hover:bg-accent/80 disabled:opacity-50 text-white px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2"
                >
                  {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                  {saving ? 'Saving…' : 'Save Settings'}
                </button>
              </div>
            </>
          )}

          {/* ── Graph tab ───────────────────────────────────────────────────── */}
          {activeTab === 'graph' && (
            <>
              {graphLoading ? (
                <div className="flex flex-col items-center justify-center py-16 text-text-muted">
                  <Loader2 className="animate-spin mb-3" size={32} />
                  <span className="text-sm">Loading DAG graph…</span>
                </div>
              ) : dagGraph ? (
                <>
                  <p className="text-xs text-text-muted mb-4">
                    <span className="text-text-primary font-bold">{dagGraph.nodes.length}</span> nodes ·{' '}
                    <span className="text-text-primary font-bold">{dagGraph.edges.length}</span> edges
                    &nbsp;· Drag to pan · Use buttons to zoom · Hover a node to highlight its connections
                  </p>
                  <DAGGraph nodes={dagGraph.nodes} edges={dagGraph.edges} />
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-text-muted gap-3">
                  <Info size={28} className="opacity-40" />
                  <span className="text-sm text-center">
                    No graph loaded yet. Click <strong className="text-text-primary">View Graph</strong> on a model in the Configuration tab.
                  </span>
                </div>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
};

export default CausalDAGSettings;