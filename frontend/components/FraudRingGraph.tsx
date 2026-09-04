// frontend/components/FraudRingGraph.tsx
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Network, ShieldAlert, Users, Smartphone, Globe, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react';

interface Node {
  id: string;
  label: string;
  type: 'IP' | 'DEVICE' | 'CUSTOMER' | 'CARD';
  clusterRisk: number; // 0.0 - 1.0
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  isSyndicate: boolean;
}

interface Edge {
  source: string;
  target: string;
  label?: string;
}

const INITIAL_NODES: Node[] = [
  // Syndicate Cluster (High Risk)
  { id: 'ip_103_21', label: '103.21.124.89 (Datacenter Proxy)', type: 'IP', clusterRisk: 0.92, x: 220, y: 180, vx: 0, vy: 0, radius: 18, isSyndicate: true },
  { id: 'dfp_linux_emu', label: 'dfp_a7b29c011e4 (Headless Linux)', type: 'DEVICE', clusterRisk: 0.95, x: 280, y: 260, vx: 0, vy: 0, radius: 16, isSyndicate: true },
  { id: 'cust_88129', label: 'cust_88129 (Recent Chargeback)', type: 'CUSTOMER', clusterRisk: 0.88, x: 150, y: 260, vx: 0, vy: 0, radius: 14, isSyndicate: true },
  { id: 'cust_syn_02', label: 'cust_syndicate_02', type: 'CUSTOMER', clusterRisk: 0.85, x: 340, y: 180, vx: 0, vy: 0, radius: 12, isSyndicate: true },
  { id: 'cust_syn_03', label: 'cust_syndicate_03', type: 'CUSTOMER', clusterRisk: 0.90, x: 280, y: 100, vx: 0, vy: 0, radius: 12, isSyndicate: true },
  { id: 'card_hash_88', label: 'card_hash_8821 (Stolen BIN)', type: 'CARD', clusterRisk: 0.94, x: 160, y: 120, vx: 0, vy: 0, radius: 13, isSyndicate: true },

  // Legitimate Cluster (Low Risk)
  { id: 'ip_clean_49', label: '49.207.210.12 (Airtel Broadband)', type: 'IP', clusterRisk: 0.05, x: 620, y: 200, vx: 0, vy: 0, radius: 16, isSyndicate: false },
  { id: 'dfp_mac_99', label: 'dfp_mac_9921 (macOS Safari)', type: 'DEVICE', clusterRisk: 0.02, x: 690, y: 270, vx: 0, vy: 0, radius: 14, isSyndicate: false },
  { id: 'cust_trusted', label: 'cust_trusted_01 (420-Day Age)', type: 'CUSTOMER', clusterRisk: 0.03, x: 550, y: 270, vx: 0, vy: 0, radius: 15, isSyndicate: false },
  { id: 'card_trusted', label: 'card_hdfc_platinum', type: 'CARD', clusterRisk: 0.01, x: 620, y: 340, vx: 0, vy: 0, radius: 12, isSyndicate: false },
];

const INITIAL_EDGES: Edge[] = [
  // Syndicate linkages
  { source: 'cust_88129', target: 'ip_103_21' },
  { source: 'cust_88129', target: 'dfp_linux_emu' },
  { source: 'cust_88129', target: 'card_hash_88' },
  { source: 'cust_syn_02', target: 'ip_103_21' },
  { source: 'cust_syn_02', target: 'dfp_linux_emu' },
  { source: 'cust_syn_03', target: 'ip_103_21' },
  { source: 'cust_syn_03', target: 'card_hash_88' },

  // Clean cluster linkages
  { source: 'cust_trusted', target: 'ip_clean_49' },
  { source: 'cust_trusted', target: 'dfp_mac_99' },
  { source: 'cust_trusted', target: 'card_trusted' },
];

export default function FraudRingGraph() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [nodes, setNodes] = useState<Node[]>(INITIAL_NODES);
  const [selectedNode, setSelectedNode] = useState<Node | null>(INITIAL_NODES[0]);
  const [zoom, setZoom] = useState<number>(1);
  const animFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let localNodes = [...INITIAL_NODES];

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Apply zoom & center transform
      ctx.save();
      ctx.scale(zoom, zoom);

      // Draw Edges
      INITIAL_EDGES.forEach((edge) => {
        const src = localNodes.find((n) => n.id === edge.source);
        const tgt = localNodes.find((n) => n.id === edge.target);
        if (src && tgt) {
          ctx.beginPath();
          ctx.moveTo(src.x, src.y);
          ctx.lineTo(tgt.x, tgt.y);
          ctx.strokeStyle = src.isSyndicate && tgt.isSyndicate ? 'rgba(239, 68, 68, 0.45)' : 'rgba(59, 130, 246, 0.3)';
          ctx.lineWidth = src.isSyndicate && tgt.isSyndicate ? 2.5 : 1.5;
          ctx.stroke();
        }
      });

      // Draw Nodes
      localNodes.forEach((node) => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);

        if (node.isSyndicate) {
          ctx.fillStyle = '#EF4444';
          ctx.shadowColor = '#EF4444';
          ctx.shadowBlur = 12;
        } else {
          ctx.fillStyle = node.type === 'IP' ? '#3B82F6' : node.type === 'DEVICE' ? '#06B6D4' : '#10B981';
          ctx.shadowColor = '#3B82F6';
          ctx.shadowBlur = 6;
        }

        ctx.fill();
        ctx.shadowBlur = 0;

        // Selection highlight ring
        if (selectedNode && selectedNode.id === node.id) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 6, 0, 2 * Math.PI);
          ctx.strokeStyle = '#FFFFFF';
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Node Label
        ctx.font = '10px monospace';
        ctx.fillStyle = '#CBD5E1';
        ctx.textAlign = 'center';
        ctx.fillText(node.label.split(' ')[0], node.x, node.y + node.radius + 14);
      });

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [zoom, selectedNode]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = (e.clientX - rect.left) / zoom;
    const clickY = (e.clientY - rect.top) / zoom;

    const clicked = nodes.find((n) => {
      const dx = n.x - clickX;
      const dy = n.y - clickY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 8;
    });

    if (clicked) setSelectedNode(clicked);
  };

  return (
    <div className="w-full bg-[#0B0F19] text-slate-100 rounded-xl border border-slate-800 shadow-2xl overflow-hidden font-sans">
      {/* Header */}
      <div className="bg-[#111827] px-4 py-3 border-b border-slate-800 flex flex-wrap justify-between items-center gap-3">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center shadow-md shadow-purple-500/20">
            <Network className="h-4 w-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              Entity Fraud Ring & Graph Network Visualizer
              <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">FEATURE 3</span>
            </h2>
            <p className="text-[11px] text-slate-400">Real-Time Subgraph Topology & Shared Device/IP Collisions</p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setZoom((z) => Math.min(1.6, z + 0.1))}
            className="p-1.5 text-slate-400 hover:text-white bg-slate-800/80 rounded-lg text-xs"
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.7, z - 0.1))}
            className="p-1.5 text-slate-400 hover:text-white bg-slate-800/80 rounded-lg text-xs"
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <button
            onClick={() => { setZoom(1); setSelectedNode(INITIAL_NODES[0]); }}
            className="p-1.5 text-slate-400 hover:text-white bg-slate-800/80 rounded-lg text-xs"
            title="Reset View"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Content Grid: Canvas + Entity Inspector Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3">
        <div className="lg:col-span-2 relative bg-[#070A12] border-b lg:border-b-0 lg:border-r border-slate-800 flex items-center justify-center p-2">
          <canvas
            ref={canvasRef}
            width={800}
            height={420}
            onClick={handleCanvasClick}
            className="w-full h-auto cursor-pointer rounded-lg"
          />

          {/* Canvas overlay legend */}
          <div className="absolute bottom-4 left-4 flex flex-wrap gap-2 text-[10px] font-mono bg-[#0B0F19]/90 border border-slate-800 px-3 py-1.5 rounded-lg backdrop-blur-md">
            <span className="flex items-center gap-1.5 text-rose-400"><span className="h-2 w-2 rounded-full bg-rose-500" /> Syndicate Cluster</span>
            <span className="flex items-center gap-1.5 text-blue-400"><span className="h-2 w-2 rounded-full bg-blue-500" /> IP Node</span>
            <span className="flex items-center gap-1.5 text-cyan-400"><span className="h-2 w-2 rounded-full bg-cyan-400" /> Device Fingerprint</span>
            <span className="flex items-center gap-1.5 text-emerald-400"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Clean User</span>
          </div>
        </div>

        {/* Entity Inspector Drawer */}
        <div className="p-4 bg-[#0D131F] flex flex-col justify-between text-xs font-sans">
          {selectedNode ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-slate-400 font-mono text-[11px]">SELECTED NODE</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  selectedNode.isSyndicate ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {selectedNode.isSyndicate ? 'SYNDICATE_THREAT' : 'TRUSTED_ENTITY'}
                </span>
              </div>

              <div>
                <span className="text-slate-500 uppercase text-[10px]">Entity Identifier</span>
                <p className="font-mono text-slate-100 font-bold mt-0.5 break-all">{selectedNode.label}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 font-mono">
                <div className="bg-[#070A12] p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[9px] block">NODE TYPE</span>
                  <span className="text-blue-400 font-bold text-xs">{selectedNode.type}</span>
                </div>
                <div className="bg-[#070A12] p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[9px] block">CLUSTER THREAT</span>
                  <span className={`font-bold text-xs ${selectedNode.clusterRisk > 0.7 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {(selectedNode.clusterRisk * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <span className="text-slate-500 uppercase text-[10px]">Connected Entities in Subgraph</span>
                <div className="mt-1.5 space-y-1 font-mono text-[11px]">
                  {INITIAL_EDGES.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id).map((e, idx) => (
                    <div key={idx} className="p-1.5 rounded bg-[#070A12] text-slate-300 border border-slate-800/80 flex items-center justify-between">
                      <span>🔗 {e.source === selectedNode.id ? e.target : e.source}</span>
                      <span className="text-[9px] text-slate-500">Shared Link</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-900/40 text-[11px] text-rose-300">
                {selectedNode.isSyndicate
                  ? '🚨 Multi-Account Collision: This entity is shared across 4 distinct customer accounts with 1 confirmed chargeback dispute.'
                  : '✅ Clean entity: No historical dispute or velocity anomalies registered.'}
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-center">
              Click any node in the graph to inspect entity attributes.
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-500 font-mono">
            Powered by MongoDB $graphLookup & RazorShield Mesh
          </div>
        </div>
      </div>
    </div>
  );
}
