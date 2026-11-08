import React, { useState, useEffect } from 'react';
import {
  Share2,
  AlertTriangle,
  Info,
  Sliders,
  RefreshCw,
  Maximize2,
  Layers,
  Network
} from 'lucide-react';
import { api } from '../api';

export default function GraphView() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fusionWeight, setFusionWeight] = useState(0.15);
  const [selectedNode, setSelectedNode] = useState(null);

  const fetchGraph = async (w = fusionWeight) => {
    try {
      setLoading(true);
      const res = await api.getGraphAnalysis(50, w);
      setGraphData(res);
      if (res.nodes && res.nodes.length > 0) {
        setSelectedNode(res.nodes[0]);
      }
    } catch (err) {
      console.error('Failed to load graph analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph(fusionWeight);
  }, []);

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    setFusionWeight(val);
  };

  const handleApplyWeight = () => {
    fetchGraph(fusionWeight);
  };

  const stats = graphData?.connectivity_statistics || {};

  // Layout simulation for nodes in SVG
  const nodes = graphData?.network_topology?.nodes || graphData?.nodes || [];
  const links = graphData?.network_topology?.links || graphData?.links || [];

  // Deterministic circular/cluster positions for SVG rendering
  const width = 640;
  const height = 420;
  const cx = width / 2;
  const cy = height / 2;

  const positionedNodes = nodes.map((node, i) => {
    const angle = (i / Math.max(1, nodes.length)) * 2 * Math.PI;
    const r = 120 + ((i % 3) * 45);
    const x = cx + r * Math.cos(angle);
    const y = cy + r * Math.sin(angle);
    return { ...node, x, y };
  });

  const nodeMap = new Map(positionedNodes.map(n => [n.id, n]));

  return (
    <div className="space-y-6">
      {/* Prominent Mandatory Dataset Limitation Banner */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start space-x-3.5 shadow-sm">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200/90 leading-relaxed">
          <strong className="text-amber-300 font-semibold block mb-1">
            Research Disclaimer & Dataset Topology Notes:
          </strong>
          The IEEE-CIS Fraud Detection dataset does not provide verified customer identities or explicit syndicate labels.
          All graph relationships in this module use <code>card1</code> as an <strong>anonymized relationship proxy</strong>.
          High graph connectivity indicates shared attribute patterns, <em>not proven criminal syndicates</em>.
          The PyTorch Geometric GCN model serves as a complementary graph analysis module alongside XGBoost.
        </div>
      </div>

      {/* Connectivity Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-navy-900 border border-slate-800 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Transaction Nodes</span>
          <div className="text-xl font-bold font-mono text-indigo-400 mt-1">
            {stats.num_nodes || nodes.length}
          </div>
          <span className="text-[11px] text-slate-500">Evaluated events</span>
        </div>

        <div className="p-4 rounded-xl bg-navy-900 border border-slate-800 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Relationship Edges</span>
          <div className="text-xl font-bold font-mono text-blue-400 mt-1">
            {stats.num_edges || links.length}
          </div>
          <span className="text-[11px] text-slate-500">Shared card1 proxies</span>
        </div>

        <div className="p-4 rounded-xl bg-navy-900 border border-slate-800 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Connected Clusters</span>
          <div className="text-xl font-bold font-mono text-amber-400 mt-1">
            {stats.connected_components_count || 1}
          </div>
          <span className="text-[11px] text-slate-500">Sub-components</span>
        </div>

        <div className="p-4 rounded-xl bg-navy-900 border border-slate-800 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Score Fusion</span>
          <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
            {(fusionWeight * 100).toFixed(0)}% GCN
          </div>
          <span className="text-[11px] text-slate-500">{((1 - fusionWeight) * 100).toFixed(0)}% XGBoost</span>
        </div>
      </div>

      {/* Main Grid: Interactive Network Canvas + Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SVG Network Canvas */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Network className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-white">Proxy Relationship Topology</h3>
            </div>
            <div className="flex items-center space-x-3 text-xs font-medium">
              <span className="flex items-center space-x-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span>High Risk</span>
              </span>
              <span className="flex items-center space-x-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span>Medium</span>
              </span>
              <span className="flex items-center space-x-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>Low</span>
              </span>
            </div>
          </div>

          {/* SVG Visualizer */}
          <div className="relative my-4 flex items-center justify-center bg-navy-950/70 rounded-xl border border-slate-800 overflow-hidden">
            {loading ? (
              <div className="h-96 flex items-center justify-center space-x-2 text-slate-400 text-xs font-medium">
                <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Computing PyTorch Geometric GCN inference...</span>
              </div>
            ) : (
              <svg width={width} height={height} className="max-w-full">
                {/* Edges */}
                <g stroke="#1e293b" strokeWidth="1.5" strokeOpacity="0.7">
                  {links.map((link, i) => {
                    const src = nodeMap.get(link.source);
                    const tgt = nodeMap.get(link.target);
                    if (!src || !tgt) return null;
                    return (
                      <line
                        key={i}
                        x1={src.x}
                        y1={src.y}
                        x2={tgt.x}
                        y2={tgt.y}
                      />
                    );
                  })}
                </g>

                {/* Nodes */}
                <g>
                  {positionedNodes.map((node) => {
                    const isSelected = selectedNode?.id === node.id;
                    const finalRisk = node.final_risk || node.xgboost_probability || 0.05;
                    const fillColor =
                      finalRisk >= 0.5 ? '#f43f5e' : finalRisk >= 0.3 ? '#f59e0b' : '#10b981';

                    return (
                      <circle
                        key={node.id}
                        cx={node.x}
                        cy={node.y}
                        r={isSelected ? 10 : 7}
                        fill={fillColor}
                        stroke={isSelected ? '#818cf8' : '#0d1527'}
                        strokeWidth={isSelected ? 3 : 1.5}
                        className="cursor-pointer transition-transform hover:scale-125"
                        onClick={() => setSelectedNode(node)}
                      >
                        <title>{`Transaction: ${node.id}\nRisk: ${(finalRisk * 100).toFixed(1)}%\nProxy card1: ${node.card1_proxy}`}</title>
                      </circle>
                    );
                  })}
                </g>
              </svg>
            )}
          </div>

          {/* Configurable fusion slider */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3 w-2/3">
              <Sliders className="w-4 h-4 text-indigo-400 shrink-0" />
              <div className="w-full">
                <div className="flex justify-between text-xs text-slate-400 mb-1 font-medium">
                  <span>GCN Fusion Weight (w): <strong className="text-indigo-400 font-mono">{fusionWeight.toFixed(2)}</strong></span>
                  <span className="text-[10px] text-slate-500 font-mono">Score = (1-w)·XGB + w·GCN</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.5"
                  step="0.05"
                  value={fusionWeight}
                  onChange={handleSliderChange}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>
            </div>

            <button
              onClick={handleApplyWeight}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-navy-950 border border-slate-700/80 hover:border-indigo-500 text-xs font-semibold text-slate-200 hover:text-indigo-300 transition-all shadow-sm"
            >
              Recalculate
            </button>
          </div>
        </div>

        {/* Node Inspection Sidebar */}
        <div className="p-6 rounded-2xl bg-navy-900 border border-slate-800 space-y-5 shadow-sm">
          <div className="flex items-center space-x-2 pb-4 border-b border-slate-800 text-white font-bold text-sm">
            <Info className="w-4 h-4 text-indigo-400" />
            <span>Node Relationship Inspector</span>
          </div>

          {selectedNode ? (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-navy-950 border border-slate-800 font-mono text-xs space-y-2">
                <div className="text-slate-500 text-[10px] uppercase font-bold">Transaction Node</div>
                <div className="text-indigo-300 font-bold break-all">{selectedNode.id}</div>
                <div className="flex justify-between pt-2 border-t border-slate-800/80 text-slate-400">
                  <span>Amount:</span>
                  <span className="text-white font-bold">${parseFloat(selectedNode.amount || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Card1 Proxy:</span>
                  <span className="text-indigo-300 font-bold">{selectedNode.card1_proxy}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Degree Centrality:</span>
                  <span className="text-slate-200 font-semibold">{selectedNode.degree_centrality || 2} links</span>
                </div>
              </div>

              {/* Score Fusion Breakdown */}
              <div className="p-4 rounded-xl bg-navy-950 border border-slate-800 space-y-2.5">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Score Fusion Calculation
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">XGBoost Prob:</span>
                  <span className="font-mono text-slate-200 font-bold">
                    {((selectedNode.xgboost_probability || 0.1) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">GCN Relationship Score:</span>
                  <span className="font-mono text-indigo-400 font-bold">
                    {((selectedNode.gcn_score || 0.12) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-xs pt-2 border-t border-slate-800 font-semibold">
                  <span className="text-white">Fused Risk Score:</span>
                  <span className="font-mono text-rose-400 font-bold">
                    {((selectedNode.final_risk || 0.1) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs font-medium">
              Click any transaction node in the graph canvas to inspect relational properties.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
