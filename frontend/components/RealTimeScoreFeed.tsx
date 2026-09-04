// frontend/components/RealTimeScoreFeed.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Shield, ShieldAlert, ShieldCheck, Zap, Activity, ExternalLink, RefreshCw, Layers } from 'lucide-react';

export interface TransactionAlert {
  transaction_id: string;
  merchant_id: string;
  amount: number;
  customer_email: string;
  ip_address: string;
  composite_risk_score: number;
  decision: 'APPROVE' | 'CHALLENGE_2FA' | 'BLOCK';
  latency_ms: number;
  flags: string[];
  timestamp: number;
}

export default function RealTimeScoreFeed({
  wsUrl = process.env.NEXT_PUBLIC_WS_ALERTS_URL || 'ws://localhost:8000/ws/alerts',
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}) {
  const [transactions, setTransactions] = useState<TransactionAlert[]>([]);
  const [selectedTxn, setSelectedTxn] = useState<TransactionAlert | null>(null);
  const [metrics, setMetrics] = useState({
    totalCount: 0,
    blockedCount: 0,
    challengedCount: 0,
    avgLatency: 0,
    preventedLoss: 0,
  });
  const [isConnected, setIsConnected] = useState<boolean>(false);

  useEffect(() => {
    let reconnectTimer: NodeJS.Timeout;
    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        ws.onopen = () => setIsConnected(true);
        ws.onmessage = (e) => {
          try {
            const parsed = JSON.parse(e.data);
            if (parsed.event_type === 'TRANSACTION_SCORED') {
              const alert: TransactionAlert = parsed.data;
              setTransactions((prev) => [alert, ...prev.slice(0, 49)]);
              setMetrics((prev) => {
                const newTotal = prev.totalCount + 1;
                const isBlocked = alert.decision === 'BLOCK';
                const isChallenged = alert.decision === 'CHALLENGE_2FA';
                return {
                  totalCount: newTotal,
                  blockedCount: prev.blockedCount + (isBlocked ? 1 : 0),
                  challengedCount: prev.challengedCount + (isChallenged ? 1 : 0),
                  avgLatency: Number(((prev.avgLatency * prev.totalCount + alert.latency_ms) / newTotal).toFixed(1)),
                  preventedLoss: prev.preventedLoss + (isBlocked ? alert.amount : 0),
                };
              });
            }
          } catch (err) {
            console.error(err);
          }
        };
        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimer = setTimeout(connect, 3000);
        };
      } catch (err) {
        console.error(err);
      }
    };
    connect();
    return () => clearTimeout(reconnectTimer);
  }, [wsUrl]);

  const triggerSimulate = async () => {
    try {
      await fetch(`${apiUrl}/api/v1/mock/simulate?count=5`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const fraudRate = metrics.totalCount > 0 ? ((metrics.blockedCount / metrics.totalCount) * 100).toFixed(1) : '0.0';

  return (
    <div className="space-y-6 font-sans">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between items-start text-slate-400 text-xs font-medium">
            <span>TOTAL EVALUATED</span>
            <Activity className="h-4 w-4 text-blue-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white font-mono">{metrics.totalCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Live XGBoost scoring pipeline</div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between items-start text-slate-400 text-xs font-medium">
            <span>FRAUD INTERCEPT RATE</span>
            <ShieldAlert className="h-4 w-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-400 font-mono">{fraudRate}%</div>
          <div className="text-[11px] text-slate-500 mt-1">{metrics.blockedCount} critical threats intercepted</div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between items-start text-slate-400 text-xs font-medium">
            <span>PREVENTED FINANCIAL LOSS</span>
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
            ₹{metrics.preventedLoss.toLocaleString('en-IN')}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Saved from RTO & dispute chargebacks</div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between items-start text-slate-400 text-xs font-medium">
            <span>AVG INFERENCE LATENCY</span>
            <Zap className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-400 font-mono">{metrics.avgLatency} ms</div>
          <div className="text-[11px] text-slate-500 mt-1">In-memory vectorized evaluation</div>
        </div>
      </div>

      {/* Main Feed Table & Diagnostic Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#111827] border border-slate-800 rounded-xl overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Live Transaction Telemetry Feed</h2>
              <p className="text-[11px] text-slate-400">Pushed in real-time over WebSocket gateway</p>
            </div>
            <button
              onClick={triggerSimulate}
              className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-md shadow-blue-600/30 transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Simulate Batch (5x)</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0D131F] text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">TXN ID / Customer</th>
                  <th className="p-3">Amount</th>
                  <th className="p-3">Risk Score</th>
                  <th className="p-3">Decision</th>
                  <th className="p-3">Latency</th>
                  <th className="p-3 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-500">
                      Waiting for incoming transactions... Click "Simulate Batch" above to start stream.
                    </td>
                  </tr>
                ) : (
                  transactions.map((txn) => (
                    <tr
                      key={txn.transaction_id}
                      onClick={() => setSelectedTxn(txn)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="p-3">
                        <div className="font-semibold text-slate-200">{txn.transaction_id}</div>
                        <div className="text-[11px] text-slate-500 font-sans">{txn.customer_email}</div>
                      </td>
                      <td className="p-3 font-semibold text-slate-200">
                        ₹{txn.amount.toLocaleString('en-IN')}
                      </td>
                      <td className="p-3">
                        <span
                          className={`font-bold ${
                            txn.composite_risk_score > 75
                              ? 'text-rose-400'
                              : txn.composite_risk_score >= 40
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }`}
                        >
                          {txn.composite_risk_score}/100
                        </span>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            txn.decision === 'BLOCK'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : txn.decision === 'CHALLENGE_2FA'
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          }`}
                        >
                          {txn.decision}
                        </span>
                      </td>
                      <td className="p-3 text-slate-400">{txn.latency_ms}ms</td>
                      <td className="p-3 text-right">
                        <button className="text-blue-400 hover:text-blue-300 p-1">
                          <ExternalLink className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Diagnostic Drawer */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col text-xs font-sans">
          <h2 className="text-sm font-semibold text-slate-200 pb-3 border-b border-slate-800">
            Real-Time Signal Diagnostic Panel
          </h2>

          {selectedTxn ? (
            <div className="mt-4 space-y-4">
              <div>
                <span className="text-slate-500 uppercase tracking-wider text-[10px] font-mono">Transaction Case ID</span>
                <p className="font-mono text-sm text-blue-400 font-bold">{selectedTxn.transaction_id}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 font-mono">
                <div className="bg-[#0B0F19] p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">IP ADDRESS</span>
                  <span className="text-slate-200 font-bold">{selectedTxn.ip_address}</span>
                </div>
                <div className="bg-[#0B0F19] p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">EVALUATION SLA</span>
                  <span className="text-slate-200 font-bold">{selectedTxn.latency_ms} ms</span>
                </div>
              </div>

              <div>
                <span className="text-slate-500 uppercase tracking-wider text-[10px] font-mono">Triggered Risk Flags</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {selectedTxn.flags.length > 0 ? (
                    selectedTxn.flags.map((flag) => (
                      <span key={flag} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 text-[10px] font-mono">
                        {flag}
                      </span>
                    ))
                  ) : (
                    <span className="text-emerald-400 text-[11px]">No anomalous risk flags triggered</span>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] font-mono">Autonomous Gateway Decision</span>
                <div className={`mt-2 p-3 rounded-lg border text-xs font-semibold ${
                  selectedTxn.decision === 'BLOCK'
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                    : selectedTxn.decision === 'CHALLENGE_2FA'
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                }`}>
                  {selectedTxn.decision === 'BLOCK' && '🛑 Transaction Terminated. IP & Device Fingerprint blacklisted.'}
                  {selectedTxn.decision === 'CHALLENGE_2FA' && '⚠️ High-Risk Action: MediaPipe/OpenCV Liveness verification dispatched.'}
                  {selectedTxn.decision === 'APPROVE' && '✅ Approved for instant payment capture and settlement.'}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-500">
              <Layers className="h-8 w-8 text-slate-700 mb-2" />
              <p className="text-xs">Click any transaction in the live feed to inspect real-time SHAP features and flags.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
