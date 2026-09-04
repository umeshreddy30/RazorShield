// frontend/components/FraudRingGraph.tsx
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Network, ShieldAlert, Users, Smartphone, Globe, RefreshCw, ZoomIn, ZoomOut, Sparkles, AlertTriangle, CheckCircle2 } from 'lucide-react';

export interface Node {
  id: string;
  label: string;
  type: 'IP' | 'DEVICE' | 'CUSTOMER' | 'CARD';
  clusterRisk: number; // 0.0 - 1.0
  x: number;
  y: number;
  vx?: number;
  vy?: number;
  radius: number;
  isSyndicate: boolean;
}

export interface Edge {
  source: string;
  target: string;
  label?: string;
}

interface FraudRingGraphProps {
  dynamicSubgraph?: {
    nodes: Node[];
    edges: Edge[];
  };
  currentScenario?: string;
}

const generateRandomScenarioGraph = (scenario: 'SYNDICATE_ATTACK' | 'BORDERLINE_COD' | 'TRUSTED_USER' | 'MULTI_CLUSTER' = 'SYNDICATE_ATTACK'): { nodes: Node[]; edges: Edge[] } => {
  const randNum = Math.floor(Math.random() * 900 + 100);
  const ipOctet3 = Math.floor(Math.random() * 200 + 10);
  const ipOctet4 = Math.floor(Math.random() * 240 + 2);

  if (scenario === 'SYNDICATE_ATTACK') {
    const proxyIp = `103.21.${ipOctet3}.${ipOctet4}`;
    const emuId = `dfp_emu_linux_${randNum}`;
    const cust1 = `cust_syn_${randNum}`;
    const cust2 = `cust_syn_${randNum + 14}`;
    const cust3 = `cust_syn_${randNum + 38}`;
    const cardBin = `card_bin_${Math.floor(Math.random() * 2000 + 4000)}`;

    const nodes: Node[] = [
      { id: 'ip_proxy', label: `${proxyIp} (Datacenter Proxy)`, type: 'IP', clusterRisk: Math.round((Math.random() * 0.08 + 0.88) * 100) / 100, x: 260 + (Math.random() * 30 - 15), y: 180 + (Math.random() * 30 - 15), radius: 18, isSyndicate: true },
      { id: 'dfp_emu', label: `${emuId} (Headless Emu)`, type: 'DEVICE', clusterRisk: Math.round((Math.random() * 0.06 + 0.92) * 100) / 100, x: 330 + (Math.random() * 30 - 15), y: 260 + (Math.random() * 30 - 15), radius: 16, isSyndicate: true },
      { id: 'cust_target', label: `${cust1} (Primary Suspect)`, type: 'CUSTOMER', clusterRisk: Math.round((Math.random() * 0.08 + 0.86) * 100) / 100, x: 170 + (Math.random() * 30 - 15), y: 260 + (Math.random() * 30 - 15), radius: 15, isSyndicate: true },
      { id: 'cust_syn_2', label: `${cust2} (Collision Bot)`, type: 'CUSTOMER', clusterRisk: 0.89, x: 390 + (Math.random() * 30 - 15), y: 170 + (Math.random() * 30 - 15), radius: 13, isSyndicate: true },
      { id: 'cust_syn_3', label: `${cust3} (Burner Identity)`, type: 'CUSTOMER', clusterRisk: 0.91, x: 290 + (Math.random() * 30 - 15), y: 95 + (Math.random() * 30 - 15), radius: 13, isSyndicate: true },
      { id: 'card_stolen', label: `${cardBin} (Stolen BIN)`, type: 'CARD', clusterRisk: 0.95, x: 180 + (Math.random() * 30 - 15), y: 110 + (Math.random() * 30 - 15), radius: 14, isSyndicate: true },
    ];

    const edges: Edge[] = [
      { source: 'cust_target', target: 'ip_proxy' },
      { source: 'cust_target', target: 'dfp_emu' },
      { source: 'cust_target', target: 'card_stolen' },
      { source: 'cust_syn_2', target: 'ip_proxy' },
      { source: 'cust_syn_2', target: 'dfp_emu' },
      { source: 'cust_syn_3', target: 'ip_proxy' },
      { source: 'cust_syn_3', target: 'card_stolen' },
    ];

    return { nodes, edges };
  } else if (scenario === 'BORDERLINE_COD') {
    const mobileIp = `157.34.${ipOctet3}.${ipOctet4}`;
    const deviceId = `dfp_android_samsung_${randNum}`;
    const custId = `cust_cod_first_${randNum}`;
    const cardId = `card_upi_gpay_${randNum}`;

    const nodes: Node[] = [
      { id: 'ip_mobile', label: `${mobileIp} (Jio Mobile 5G)`, type: 'IP', clusterRisk: Math.round((Math.random() * 0.12 + 0.28) * 100) / 100, x: 380 + (Math.random() * 30 - 15), y: 190 + (Math.random() * 30 - 15), radius: 16, isSyndicate: false },
      { id: 'dfp_phone', label: `${deviceId} (Android 14)`, type: 'DEVICE', clusterRisk: Math.round((Math.random() * 0.10 + 0.22) * 100) / 100, x: 470 + (Math.random() * 30 - 15), y: 270 + (Math.random() * 30 - 15), radius: 14, isSyndicate: false },
      { id: 'cust_cod', label: `${custId} (New Account)`, type: 'CUSTOMER', clusterRisk: Math.round((Math.random() * 0.15 + 0.52) * 100) / 100, x: 290 + (Math.random() * 30 - 15), y: 270 + (Math.random() * 30 - 15), radius: 15, isSyndicate: false },
      { id: 'card_upi', label: `${cardId} (VPA Unverified)`, type: 'CARD', clusterRisk: 0.35, x: 380 + (Math.random() * 30 - 15), y: 340 + (Math.random() * 30 - 15), radius: 12, isSyndicate: false },
    ];

    const edges: Edge[] = [
      { source: 'cust_cod', target: 'ip_mobile' },
      { source: 'cust_cod', target: 'dfp_phone' },
      { source: 'cust_cod', target: 'card_upi' },
    ];

    return { nodes, edges };
  } else {
    // TRUSTED_USER or MULTI_CLUSTER
    const homeIp = `49.207.${ipOctet3}.${ipOctet4}`;
    const macId = `dfp_mac_sonoma_${randNum}`;
    const custId = `cust_vip_ananya_${randNum}`;

    const nodes: Node[] = [
      { id: 'ip_home', label: `${homeIp} (Airtel Fiber Home)`, type: 'IP', clusterRisk: 0.02, x: 580 + (Math.random() * 30 - 15), y: 190 + (Math.random() * 30 - 15), radius: 16, isSyndicate: false },
      { id: 'dfp_mac', label: `${macId} (macOS Safari)`, type: 'DEVICE', clusterRisk: 0.01, x: 670 + (Math.random() * 30 - 15), y: 270 + (Math.random() * 30 - 15), radius: 14, isSyndicate: false },
      { id: 'cust_vip', label: `${custId} (Platinum Member)`, type: 'CUSTOMER', clusterRisk: 0.02, x: 490 + (Math.random() * 30 - 15), y: 270 + (Math.random() * 30 - 15), radius: 15, isSyndicate: false },
      { id: 'card_vip', label: 'card_hdfc_infinia_9912', type: 'CARD', clusterRisk: 0.01, x: 580 + (Math.random() * 30 - 15), y: 350 + (Math.random() * 30 - 15), radius: 12, isSyndicate: false },
    ];

    const edges: Edge[] = [
      { source: 'cust_vip', target: 'ip_home' },
      { source: 'cust_vip', target: 'dfp_mac' },
      { source: 'cust_vip', target: 'card_vip' },
    ];

    return { nodes, edges };
  }
};

export default function FraudRingGraph({
  dynamicSubgraph,
  currentScenario = 'SYNDICATE_ATTACK'
}: FraudRingGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [activeScenarioPreset, setActiveScenarioPreset] = useState<'SYNDICATE_ATTACK' | 'BORDERLINE_COD' | 'TRUSTED_USER'>('SYNDICATE_ATTACK');
  
  const initialGraph = generateRandomScenarioGraph('SYNDICATE_ATTACK');
  const [nodes, setNodes] = useState<Node[]>(initialGraph.nodes);
  const [edges, setEdges] = useState<Edge[]>(initialGraph.edges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(initialGraph.nodes[0]);
  const [zoom, setZoom] = useState<number>(1);
  const animFrameRef = useRef<number | null>(null);

  // Sync when parent supplies dynamicSubgraph from investigation
  useEffect(() => {
    if (dynamicSubgraph && dynamicSubgraph.nodes && dynamicSubgraph.nodes.length > 0) {
      setNodes(dynamicSubgraph.nodes);
      setEdges(dynamicSubgraph.edges || []);
      setSelectedNode(dynamicSubgraph.nodes[0] || null);
    }
  }, [dynamicSubgraph]);

  // Handle Scenario Switcher
  const handleSwitchPreset = (preset: 'SYNDICATE_ATTACK' | 'BORDERLINE_COD' | 'TRUSTED_USER') => {
    setActiveScenarioPreset(preset);
    const newGraph = generateRandomScenarioGraph(preset);
    setNodes(newGraph.nodes);
    setEdges(newGraph.edges);
    setSelectedNode(newGraph.nodes[0]);
  };

  // Canvas Force & Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let localNodes = [...nodes];
    let localEdges = [...edges];

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Apply zoom & center transform
      ctx.save();
      ctx.scale(zoom, zoom);

      // Draw Edges with glow
      localEdges.forEach((edge) => {
        const src = localNodes.find((n) => n.id === edge.source);
        const tgt = localNodes.find((n) => n.id === edge.target);
        if (src && tgt) {
          ctx.beginPath();
          ctx.moveTo(src.x, src.y);
          ctx.lineTo(tgt.x, tgt.y);
          
          if (src.isSyndicate && tgt.isSyndicate) {
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.55)';
            ctx.lineWidth = 2.5;
            ctx.shadowColor = '#EF4444';
            ctx.shadowBlur = 6;
          } else if (src.clusterRisk > 0.4 || tgt.clusterRisk > 0.4) {
            ctx.strokeStyle = 'rgba(245, 158, 11, 0.45)';
            ctx.lineWidth = 2.0;
            ctx.shadowColor = '#F59E0B';
            ctx.shadowBlur = 4;
          } else {
            ctx.strokeStyle = 'rgba(59, 130, 246, 0.35)';
            ctx.lineWidth = 1.5;
            ctx.shadowColor = 'transparent';
            ctx.shadowBlur = 0;
          }

          ctx.stroke();
          ctx.shadowBlur = 0;
        }
      });

      // Draw Nodes
      localNodes.forEach((node) => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);

        if (node.isSyndicate) {
          ctx.fillStyle = '#EF4444';
          ctx.shadowColor = '#EF4444';
          ctx.shadowBlur = 14;
        } else if (node.clusterRisk > 0.4) {
          ctx.fillStyle = '#F59E0B';
          ctx.shadowColor = '#F59E0B';
          ctx.shadowBlur = 10;
        } else {
          ctx.fillStyle = node.type === 'IP' ? '#3B82F6' : node.type === 'DEVICE' ? '#06B6D4' : node.type === 'CARD' ? '#A855F7' : '#10B981';
          ctx.shadowColor = '#3B82F6';
          ctx.shadowBlur = 8;
        }

        ctx.fill();
        ctx.shadowBlur = 0;

        // Selection highlight ring
        if (selectedNode && selectedNode.id === node.id) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 6, 0, 2 * Math.PI);
          ctx.strokeStyle = '#FFFFFF';
          ctx.lineWidth = 2.5;
          ctx.stroke();
        }

        // Node Label
        ctx.font = 'bold 10px monospace';
        ctx.fillStyle = '#E2E8F0';
        ctx.textAlign = 'center';
        ctx.fillText(node.label.split(' ')[0], node.x, node.y + node.radius + 15);
      });

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [zoom, selectedNode, nodes, edges]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = (e.clientX - rect.left) / zoom;
    const clickY = (e.clientY - rect.top) / zoom;

    const clicked = nodes.find((n) => {
      const dx = n.x - clickX;
      const dy = n.y - clickY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 10;
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

        {/* Action Controls & Zoom */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleSwitchPreset(activeScenarioPreset)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold transition-all active:scale-95"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Regenerate Network Subgraph</span>
          </button>

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
            onClick={() => { setZoom(1); }}
            className="p-1.5 text-slate-400 hover:text-white bg-slate-800/80 rounded-lg text-xs"
            title="Reset View"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Scenario Preset Selector Toolbar */}
      <div className="bg-[#090D17] px-4 py-2.5 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <span className="text-slate-400 text-[11px]">ACTIVE GRAPH SCENARIO:</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleSwitchPreset('SYNDICATE_ATTACK')}
            className={`px-3 py-1 rounded-md transition-all text-xs font-semibold flex items-center gap-1.5 ${
              activeScenarioPreset === 'SYNDICATE_ATTACK'
                ? 'bg-rose-600/30 text-rose-300 border border-rose-500/50 shadow-sm'
                : 'bg-slate-800/50 text-slate-400 hover:text-slate-200 border border-slate-700/50'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            Syndicate Ring
          </button>

          <button
            onClick={() => handleSwitchPreset('BORDERLINE_COD')}
            className={`px-3 py-1 rounded-md transition-all text-xs font-semibold flex items-center gap-1.5 ${
              activeScenarioPreset === 'BORDERLINE_COD'
                ? 'bg-amber-600/30 text-amber-300 border border-amber-500/50 shadow-sm'
                : 'bg-slate-800/50 text-slate-400 hover:text-slate-200 border border-slate-700/50'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-amber-500" />
            Borderline COD
          </button>

          <button
            onClick={() => handleSwitchPreset('TRUSTED_USER')}
            className={`px-3 py-1 rounded-md transition-all text-xs font-semibold flex items-center gap-1.5 ${
              activeScenarioPreset === 'TRUSTED_USER'
                ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/50 shadow-sm'
                : 'bg-slate-800/50 text-slate-400 hover:text-slate-200 border border-slate-700/50'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Clean Cluster
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
            <span className="flex items-center gap-1.5 text-rose-400"><span className="h-2 w-2 rounded-full bg-rose-500" /> Syndicate (High Risk)</span>
            <span className="flex items-center gap-1.5 text-amber-400"><span className="h-2 w-2 rounded-full bg-amber-500" /> Moderate Risk</span>
            <span className="flex items-center gap-1.5 text-blue-400"><span className="h-2 w-2 rounded-full bg-blue-500" /> IP Node</span>
            <span className="flex items-center gap-1.5 text-cyan-400"><span className="h-2 w-2 rounded-full bg-cyan-400" /> Device Node</span>
            <span className="flex items-center gap-1.5 text-emerald-400"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Clean Entity</span>
          </div>
        </div>

        {/* Entity Inspector Drawer */}
        <div className="p-4 bg-[#0D131F] flex flex-col justify-between text-xs font-sans">
          {selectedNode ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-slate-400 font-mono text-[11px]">SELECTED NODE</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  selectedNode.isSyndicate ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                  selectedNode.clusterRisk > 0.4 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                  'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {selectedNode.isSyndicate ? 'SYNDICATE_THREAT' : selectedNode.clusterRisk > 0.4 ? 'MODERATE_RISK' : 'TRUSTED_ENTITY'}
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
                  <span className={`font-bold text-xs ${
                    selectedNode.clusterRisk > 0.7 ? 'text-rose-400' :
                    selectedNode.clusterRisk > 0.3 ? 'text-amber-400' :
                    'text-emerald-400'
                  }`}>
                    {(selectedNode.clusterRisk * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <span className="text-slate-500 uppercase text-[10px]">Connected Entities in Subgraph</span>
                <div className="mt-1.5 space-y-1 font-mono text-[11px] max-h-36 overflow-y-auto">
                  {edges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id).length > 0 ? (
                    edges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id).map((e, idx) => (
                      <div key={idx} className="p-1.5 rounded bg-[#070A12] text-slate-300 border border-slate-800/80 flex items-center justify-between">
                        <span>🔗 {e.source === selectedNode.id ? e.target : e.source}</span>
                        <span className="text-[9px] text-slate-500">Shared Link</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-500 text-[10px] italic">No direct subgraph links</div>
                  )}
                </div>
              </div>

              <div className={`p-2.5 rounded-lg border text-[11px] ${
                selectedNode.isSyndicate
                  ? 'bg-rose-950/20 border-rose-900/40 text-rose-300'
                  : selectedNode.clusterRisk > 0.4
                  ? 'bg-amber-950/20 border-amber-900/40 text-amber-300'
                  : 'bg-emerald-950/20 border-emerald-900/40 text-emerald-300'
              }`}>
                {selectedNode.isSyndicate
                  ? '🚨 Multi-Account Collision: This entity is shared across multiple customer accounts with confirmed chargeback disputes and datacenter proxy usage.'
                  : selectedNode.clusterRisk > 0.4
                  ? '⚠️ First-Time Signature: New mobile subnet with unverified KYC profile. Liveness 2FA recommended before settlement.'
                  : '✅ Clean entity: Verified residential IP and clean account tenure without dispute or velocity anomalies.'}
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-center">
              Click any node in the graph to inspect entity attributes.
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-500 font-mono flex items-center justify-between">
            <span>Graph Lookup: MongoDB + LangGraph</span>
            <span className="text-emerald-400">ACTIVE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
