// frontend/components/AgentExecutionTerminal.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Shield, Cpu, Database, Network, FileText, CheckCircle2, AlertTriangle, XCircle, Play, Trash2, ArrowDown } from 'lucide-react';

export interface AgentFrame {
  event_type: 'SYSTEM_CONNECTED' | 'AGENT_ASSIGNED' | 'THINKING' | 'TOOL_INVOKED' | 'TOOL_RESULT' | 'DECISION_REACHED' | 'INVESTIGATION_COMPLETE' | 'PONG';
  agent_name: 'Supervisor' | 'DataRetrievalAgent' | 'GraphAgent' | 'NLPAnalyzer' | 'DecisionAgent' | string;
  transaction_id?: string;
  thought: string;
  tool_name?: string;
  tool_args?: Record<string, any>;
  tool_output?: Record<string, any>;
  timestamp: number;
  data?: any;
}

interface AgentExecutionTerminalProps {
  wsUrl?: string;
  apiUrl?: string;
  onInvestigationComplete?: (subgraph: any, scenario: string) => void;
}

export default function AgentExecutionTerminal({
  wsUrl = process.env.NEXT_PUBLIC_WS_AGENT_URL || 'ws://localhost:8000/ws/investigate',
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  onInvestigationComplete
}: AgentExecutionTerminalProps) {
  const [logs, setLogs] = useState<AgentFrame[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [activeVerdict, setActiveVerdict] = useState<{
    verdict: string;
    riskScore: number;
    summary: string;
    txnId: string;
    scenario?: string;
  } | null>(null);

  const terminalEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll terminal log
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Connect WebSocket to Agent Stream
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const frame: AgentFrame = JSON.parse(event.data);
            if (frame.event_type === 'PONG') return;

            setLogs((prev) => [...prev, frame]);

            if (frame.event_type === 'DECISION_REACHED' && frame.data) {
              setActiveVerdict({
                verdict: frame.data.verdict,
                riskScore: frame.data.composite_risk_score,
                summary: frame.data.executive_summary,
                txnId: frame.transaction_id || 'N/A',
                scenario: frame.data.scenario
              });
              setIsInvestigating(false);
            }
          } catch (e) {
            console.error('Error parsing agent frame:', e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        console.error('WebSocket connection failed:', err);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [wsUrl]);

  // Trigger dynamic autonomous investigation by scenario archetype
  const triggerInvestigation = async (scenario: 'SYNDICATE_ATTACK' | 'BORDERLINE_COD' | 'TRUSTED_USER') => {
    setIsInvestigating(true);
    setActiveScenario(scenario);
    setActiveVerdict(null);

    let payload: any;
    const randSuffix = Math.floor(Math.random() * 900 + 100);
    const txnId = `txn_${Date.now()}_${randSuffix}`;

    if (scenario === 'SYNDICATE_ATTACK') {
      payload = {
        transaction_id: txnId,
        merchant_id: 'mer_enterprise_prime',
        customer_id: `cust_syn_${Math.floor(Math.random() * 80 + 10)}`,
        amount: Math.round((Math.random() * 35000 + 35000) * 100) / 100, // ₹35,000 - ₹70,000
        account_age_days: Math.round(Math.random() * 3 * 10) / 10,
        device_trust_score: Math.round((Math.random() * 0.20 + 0.05) * 100) / 100,
        ip_velocity_1h: Math.floor(Math.random() * 5 + 5),
        txn_velocity_1h: Math.floor(Math.random() * 6 + 6),
        is_vpn_proxy: true,
        failed_attempts_24h: Math.floor(Math.random() * 3 + 3),
        billing_shipping_match: false,
        customer_email: `syndicate_actor_${randSuffix}@tempmail.org`,
        ip_address: `103.21.${Math.floor(Math.random() * 200 + 10)}.${Math.floor(Math.random() * 250 + 1)}`,
        device_fingerprint: `dfp_emu_linux_${randSuffix}`,
        notes: 'Urgent rush express dispatch! Do not call phone, drop with security guard immediately.',
        scenario_type: 'SYNDICATE_ATTACK',
        order_category: 'ELECTRONICS'
      };
    } else if (scenario === 'BORDERLINE_COD') {
      payload = {
        transaction_id: txnId,
        merchant_id: 'mer_retail_direct',
        customer_id: `cust_cod_first_${randSuffix}`,
        amount: Math.round((Math.random() * 4000 + 4500) * 100) / 100, // ₹4,500 - ₹8,500
        account_age_days: Math.round(Math.random() * 12 + 2),
        device_trust_score: Math.round((Math.random() * 0.25 + 0.45) * 100) / 100,
        ip_velocity_1h: 2,
        txn_velocity_1h: 1,
        is_vpn_proxy: false,
        failed_attempts_24h: 1,
        billing_shipping_match: true,
        customer_email: `rahul.sharma.${randSuffix}@gmail.com`,
        ip_address: `157.34.${Math.floor(Math.random() * 180 + 10)}.${Math.floor(Math.random() * 250 + 1)}`,
        device_fingerprint: `dfp_android_samsung_${randSuffix}`,
        notes: 'Cash on delivery. Call 10 minutes before arriving at home address.',
        scenario_type: 'BORDERLINE_COD',
        order_category: 'FASHION_APPAREL'
      };
    } else {
      // TRUSTED_USER
      payload = {
        transaction_id: txnId,
        merchant_id: 'mer_enterprise_prime',
        customer_id: `cust_vip_ananya_${randSuffix}`,
        amount: Math.round((Math.random() * 3000 + 1200) * 100) / 100, // ₹1,200 - ₹4,200
        account_age_days: Math.round(Math.random() * 300 + 180),
        device_trust_score: Math.round((Math.random() * 0.08 + 0.91) * 100) / 100,
        ip_velocity_1h: 1,
        txn_velocity_1h: 1,
        is_vpn_proxy: false,
        failed_attempts_24h: 0,
        billing_shipping_match: true,
        customer_email: `ananya.deshmukh.${randSuffix}@gmail.com`,
        ip_address: `49.207.${Math.floor(Math.random() * 180 + 10)}.${Math.floor(Math.random() * 250 + 1)}`,
        device_fingerprint: `dfp_mac_safari_${randSuffix}`,
        notes: 'Standard registered delivery to residential address.',
        scenario_type: 'TRUSTED_USER',
        order_category: 'BOOKS_ESSENTIALS'
      };
    }

    try {
      const resp = await fetch(`${apiUrl}/api/v1/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (resp.ok) {
        const result = await resp.json();
        if (result?.evidence_breakdown?.subgraph && onInvestigationComplete) {
          onInvestigationComplete(result.evidence_breakdown.subgraph, scenario);
        }
      }
    } catch (e) {
      console.error('Failed to trigger investigation:', e);
      setIsInvestigating(false);
    }
  };

  const getAgentBadge = (name: string) => {
    switch (name) {
      case 'Supervisor':
        return <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center gap-1 font-mono text-[10px]"><Cpu className="h-3 w-3" /> SUPERVISOR</span>;
      case 'DataRetrievalAgent':
        return <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center gap-1 font-mono text-[10px]"><Database className="h-3 w-3" /> DATA_AGENT (MongoDB)</span>;
      case 'GraphAgent':
        return <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 border border-purple-500/30 flex items-center gap-1 font-mono text-[10px]"><Network className="h-3 w-3" /> GRAPH_AGENT</span>;
      case 'NLPAnalyzer':
        return <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 font-mono text-[10px]"><FileText className="h-3 w-3" /> NLP_ANALYZER</span>;
      case 'DecisionAgent':
        return <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-mono text-[10px]"><Shield className="h-3 w-3" /> DECISION_ENGINE</span>;
      default:
        return <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-300 font-mono text-[10px]">{name}</span>;
    }
  };

  return (
    <div className="w-full bg-[#0B0F19] text-slate-100 rounded-xl border border-slate-800 shadow-2xl overflow-hidden font-sans">
      {/* Top Header Bar */}
      <div className="bg-[#111827] px-4 py-3 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <Terminal className="h-4 w-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              Autonomous Agent Investigation Terminal
              <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">LANGGRAPH CORE</span>
            </h2>
            <p className="text-[11px] text-slate-400">Dynamic Multi-Agent Reasoning, Tool Execution & State Machine Stream</p>
          </div>
        </div>

        {/* Live Status + Clear button */}
        <div className="flex items-center space-x-2">
          <div className={`flex items-center space-x-1.5 text-[11px] px-2.5 py-1 rounded-full border font-mono ${
            isConnected ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}>
            <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-ping' : 'bg-rose-400'}`} />
            <span>{isConnected ? 'STREAM_CONNECTED' : 'DISCONNECTED'}</span>
          </div>

          <button
            onClick={() => { setLogs([]); setActiveVerdict(null); setActiveScenario(null); }}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            title="Clear Logs"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* 3 Dynamic Scenario Action Controls */}
      <div className="bg-[#0D1424] px-4 py-3 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
          <span>SELECT DEMO SCENARIO:</span>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Button 1: Syndicate Attack */}
          <button
            onClick={() => triggerInvestigation('SYNDICATE_ATTACK')}
            disabled={isInvestigating}
            className="flex items-center space-x-2 bg-gradient-to-r from-rose-700 to-rose-600 hover:from-rose-600 hover:to-rose-500 disabled:opacity-50 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-md shadow-rose-900/30 transition-all border border-rose-500/30 active:scale-95"
          >
            <span className="h-2 w-2 rounded-full bg-rose-300 animate-pulse" />
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>Simulate Syndicate Attack</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-rose-200 ml-1">HIGH RISK</span>
          </button>

          {/* Button 2: Borderline COD */}
          <button
            onClick={() => triggerInvestigation('BORDERLINE_COD')}
            disabled={isInvestigating}
            className="flex items-center space-x-2 bg-gradient-to-r from-amber-700 to-amber-600 hover:from-amber-600 hover:to-amber-500 disabled:opacity-50 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-md shadow-amber-900/30 transition-all border border-amber-500/30 active:scale-95"
          >
            <span className="h-2 w-2 rounded-full bg-amber-300 animate-pulse" />
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>Simulate Borderline COD</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-amber-200 ml-1">TRIGGER 2FA</span>
          </button>

          {/* Button 3: Clean Order */}
          <button
            onClick={() => triggerInvestigation('TRUSTED_USER')}
            disabled={isInvestigating}
            className="flex items-center space-x-2 bg-gradient-to-r from-emerald-700 to-emerald-600 hover:from-emerald-600 hover:to-emerald-500 disabled:opacity-50 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-md shadow-emerald-900/30 transition-all border border-emerald-500/30 active:scale-95"
          >
            <span className="h-2 w-2 rounded-full bg-emerald-300 animate-pulse" />
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>Simulate Clean Order</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-emerald-200 ml-1">APPROVE</span>
          </button>
        </div>
      </div>

      {/* Terminal Viewport */}
      <div className="h-96 overflow-y-auto p-4 bg-[#080C14] font-mono text-xs space-y-3 relative">
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center space-y-2">
            <Cpu className="h-8 w-8 text-slate-700 animate-pulse" />
            <p className="text-xs">Agent mesh standing by on WebSocket channel <code>/ws/investigate</code>.</p>
            <p className="text-[11px] text-slate-600">Click "Investigate Syndicate Case" above to observe live multi-agent reasoning.</p>
          </div>
        ) : (
          logs.map((log, index) => (
            <div
              key={index}
              className="p-2.5 rounded-lg bg-[#0F172A]/70 border border-slate-800/80 hover:border-slate-700 transition-all space-y-1.5"
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <div className="flex items-center space-x-2">
                  {getAgentBadge(log.agent_name)}
                  <span className="text-slate-500 uppercase tracking-wide">[{log.event_type}]</span>
                  {log.tool_name && (
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold text-[9px]">
                      Tool: {log.tool_name}
                    </span>
                  )}
                </div>
                <span className="text-slate-500">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
              </div>

              {/* Thought Text */}
              <p className={`text-slate-200 text-xs leading-relaxed font-sans ${
                log.event_type === 'DECISION_REACHED' ? 'font-bold text-white' : ''
              }`}>
                {log.thought}
              </p>

              {/* Tool Arguments / Output Collapsible Preview */}
              {(log.tool_args || log.tool_output) && (
                <div className="mt-1.5 p-2 rounded bg-[#070B12] border border-slate-900 font-mono text-[10px] text-cyan-300/90 overflow-x-auto">
                  {log.tool_args && (
                    <div><span className="text-slate-500">args:</span> {JSON.stringify(log.tool_args)}</div>
                  )}
                  {log.tool_output && (
                    <div><span className="text-slate-500">return:</span> {JSON.stringify(log.tool_output)}</div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>

      {/* Real-Time Verdict Bar */}
      {activeVerdict && (
        <div className={`px-4 py-3 border-t flex items-center justify-between gap-4 ${
          activeVerdict.verdict === 'BLOCK'
            ? 'bg-rose-950/30 border-rose-900/50 text-rose-300'
            : activeVerdict.verdict === 'TRIGGER_2FA'
            ? 'bg-amber-950/30 border-amber-900/50 text-amber-300'
            : 'bg-emerald-950/30 border-emerald-900/50 text-emerald-300'
        }`}>
          <div className="flex items-center space-x-3">
            {activeVerdict.verdict === 'BLOCK' ? <XCircle className="h-5 w-5 text-rose-400" /> :
             activeVerdict.verdict === 'TRIGGER_2FA' ? <AlertTriangle className="h-5 w-5 text-amber-400" /> :
             <CheckCircle2 className="h-5 w-5 text-emerald-400" />}
            <div>
              <div className="text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                VERDICT: {activeVerdict.verdict}
                <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-black/40 border border-current">
                  Risk Score: {activeVerdict.riskScore}/100
                </span>
              </div>
              <p className="text-[11px] opacity-90 font-sans mt-0.5">{activeVerdict.summary}</p>
            </div>
          </div>

          <div className="text-right font-mono text-[10px] opacity-70">
            CASE: {activeVerdict.txnId}
          </div>
        </div>
      )}
    </div>
  );
}
