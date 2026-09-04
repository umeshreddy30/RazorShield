// frontend/app/page.tsx
'use client';

import React, { useState } from 'react';
import {
  Shield,
  Terminal,
  Network,
  Activity,
  Eye,
  Cpu,
  Database,
  Wifi,
  Sparkles,
  ArrowUpRight,
  ExternalLink,
} from 'lucide-react';
import AgentExecutionTerminal from '@/components/AgentExecutionTerminal';
import FraudRingGraph from '@/components/FraudRingGraph';
import RealTimeScoreFeed from '@/components/RealTimeScoreFeed';
import Vision2FASimulator from '@/components/Vision2FASimulator';

export default function RazorShieldCommandCenter() {
  const [activeTab, setActiveTab] = useState<'AGENTS' | 'GRAPH' | 'FEED' | 'VISION'>('AGENTS');

  return (
    <div className="min-h-screen bg-[#070A12] bg-grid-pattern text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Banner & Header */}
      <header className="border-b border-slate-800/80 bg-[#0B0F19]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Logo & System Title */}
          <div className="flex items-center space-x-3.5">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/25 ring-1 ring-white/20">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-black tracking-tight text-white">RazorShield</h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm">
                  AUTONOMOUS AGENT MESH v2.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Next-Gen Multi-Agent Fraud Defense & Low-Latency Risk Gateway
              </p>
            </div>
          </div>

          {/* Live Node Indicators */}
          <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-[#0F172A] border border-slate-800 text-slate-300">
              <Cpu className="h-3.5 w-3.5 text-indigo-400" />
              <span>LangGraph: <span className="text-emerald-400">ONLINE</span></span>
            </div>
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-[#0F172A] border border-slate-800 text-slate-300">
              <Database className="h-3.5 w-3.5 text-cyan-400" />
              <span>MongoDB: <span className="text-emerald-400">ACTIVE</span></span>
            </div>
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-[#0F172A] border border-slate-800 text-slate-300">
              <Wifi className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              <span>Gateway: <span className="text-blue-400">PORT 8000</span></span>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 transition-all font-semibold"
            >
              <span>Swagger Docs</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>

        {/* Tab Navigation Strip */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 border-t border-slate-800/60 overflow-x-auto">
          <button
            onClick={() => setActiveTab('AGENTS')}
            className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'AGENTS'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <Terminal className="h-4 w-4" />
            <span>🤖 Autonomous Agent Terminal</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono">LIVE MESH</span>
          </button>

          <button
            onClick={() => setActiveTab('GRAPH')}
            className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'GRAPH'
                ? 'border-purple-500 text-purple-400 bg-purple-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <Network className="h-4 w-4" />
            <span>🕸️ Fraud Ring Visualizer</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">FEATURE 3</span>
          </button>

          <button
            onClick={() => setActiveTab('FEED')}
            className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'FEED'
                ? 'border-blue-500 text-blue-400 bg-blue-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>⚡ Real-Time Scoring Stream</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono">FEATURE 1 & 5</span>
          </button>

          <button
            onClick={() => setActiveTab('VISION')}
            className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'VISION'
                ? 'border-cyan-500 text-cyan-400 bg-cyan-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <Eye className="h-4 w-4" />
            <span>👁️ Vision 2FA & Liveness</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono">FEATURE 2</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Dynamic Tab Render */}
        {activeTab === 'AGENTS' && (
          <div className="space-y-6">
            <AgentExecutionTerminal />
          </div>
        )}

        {activeTab === 'GRAPH' && (
          <div className="space-y-6">
            <FraudRingGraph />
          </div>
        )}

        {activeTab === 'FEED' && (
          <div className="space-y-6">
            <RealTimeScoreFeed />
          </div>
        )}

        {activeTab === 'VISION' && (
          <div className="space-y-6">
            <Vision2FASimulator />
          </div>
        )}

        {/* Feature Architecture Matrix Footer */}
        <section className="bg-[#0F172A]/70 border border-slate-800/80 rounded-xl p-6 backdrop-blur-md">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-cyan-400" />
                RazorShield Enterprise Architecture Matrix
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Full-Stack Hackathon Implementation Mapping</p>
            </div>
            <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300">
              5 OF 5 ADVANCED FEATURES COMPLETE
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-xs font-sans">
            <div className="p-3 rounded-lg bg-[#070A12] border border-slate-800/80 space-y-1">
              <span className="text-blue-400 font-mono font-bold text-[11px]">Feature 1: ML Scoring Engine</span>
              <p className="text-slate-400 text-[11px]">
                In-memory XGBoost classifier with sub-15ms vectorized prediction & continuous risk thresholds.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[#070A12] border border-slate-800/80 space-y-1">
              <span className="text-cyan-400 font-mono font-bold text-[11px]">Feature 2: Vision 2FA Liveness</span>
              <p className="text-slate-400 text-[11px]">
                OpenCV + MediaPipe facial landmark challenge with gesture recognition & host hardware binding.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[#070A12] border border-slate-800/80 space-y-1">
              <span className="text-purple-400 font-mono font-bold text-[11px]">Feature 3: Fraud Ring Graph</span>
              <p className="text-slate-400 text-[11px]">
                Interactive HTML5 Canvas topology visualizer mapping shared proxies, emulators & card collisions.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[#070A12] border border-slate-800/80 space-y-1">
              <span className="text-amber-400 font-mono font-bold text-[11px]">Feature 4: NLP Risk Analyzer</span>
              <p className="text-slate-400 text-[11px]">
                Autonomous NLP analyzer extracting urgency cues and intent flags from order metadata memos.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[#070A12] border border-slate-800/80 space-y-1">
              <span className="text-emerald-400 font-mono font-bold text-[11px]">Feature 5: WebSocket Dashboard</span>
              <p className="text-slate-400 text-[11px]">
                Zero-refresh WebSocket pipeline with live telemetry streaming and auto-reconnect backoff.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[#070A12] border border-indigo-500/30 space-y-1">
              <span className="text-indigo-400 font-mono font-bold text-[11px]">Multi-Agent Orchestrator</span>
              <p className="text-slate-400 text-[11px]">
                LangGraph StateGraph executing autonomous data retrieval, graph traversal & decision synthesis.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
