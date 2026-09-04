// frontend/components/Vision2FASimulator.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Camera, Eye, ShieldCheck, RefreshCw, CheckCircle2, Lock, Zap } from 'lucide-react';

export default function Vision2FASimulator() {
  const [challengeStep, setChallengeStep] = useState<number>(1);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [livenessProgress, setLivenessProgress] = useState<number>(0);
  const [verificationResult, setVerificationResult] = useState<{
    status: 'IDLE' | 'VERIFIED' | 'FAILED';
    token?: string;
    latencyMs?: number;
  }>({ status: 'IDLE' });

  const challenges = [
    { step: 1, text: 'Center face in the biometric frame', icon: '👤' },
    { step: 2, text: 'Blink eyes twice to verify active liveness', icon: '👁️' },
    { step: 3, text: 'Turn head slightly to the left (15°)', icon: '🔄' },
  ];

  const startVerification = () => {
    setIsScanning(true);
    setLivenessProgress(0);
    setChallengeStep(1);
    setVerificationResult({ status: 'IDLE' });
  };

  useEffect(() => {
    if (!isScanning) return;

    const timer = setInterval(() => {
      setLivenessProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          setIsScanning(false);
          setVerificationResult({
            status: 'VERIFIED',
            token: `v2fa_live_token_${Date.now()}`,
            latencyMs: 142.5,
          });
          return 100;
        }
        if (prev === 35) setChallengeStep(2);
        if (prev === 70) setChallengeStep(3);
        return prev + 5;
      });
    }, 120);

    return () => clearInterval(timer);
  }, [isScanning]);

  return (
    <div className="w-full bg-[#0B0F19] text-slate-100 rounded-xl border border-slate-800 shadow-2xl overflow-hidden font-sans">
      {/* Header */}
      <div className="bg-[#111827] px-4 py-3 border-b border-slate-800 flex flex-wrap justify-between items-center gap-3">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-md shadow-cyan-500/20">
            <Eye className="h-4 w-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              Vision-Based 2FA & Liveness Verification
              <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">FEATURE 2</span>
            </h2>
            <p className="text-[11px] text-slate-400">MediaPipe & OpenCV Facial Landmark Challenge for High-Risk Orders</p>
          </div>
        </div>

        <button
          onClick={startVerification}
          disabled={isScanning}
          className="flex items-center space-x-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-md shadow-cyan-600/20 transition-colors"
        >
          <Camera className="h-3.5 w-3.5" />
          <span>{isScanning ? 'Verifying Hardware...' : 'Trigger 2FA Liveness Check'}</span>
        </button>
      </div>

      {/* Main Grid: Biometric Viewfinder + Challenge Tracker */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 items-center">
        {/* Viewfinder Frame */}
        <div className="relative aspect-video bg-[#070A12] rounded-xl border-2 border-dashed border-cyan-500/40 flex flex-col items-center justify-center overflow-hidden">
          {/* Animated Scanning Grid */}
          <div className="absolute inset-0 bg-grid-pattern opacity-20" />

          {isScanning && (
            <div
              className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#06b6d4] transition-all"
              style={{ top: `${livenessProgress}%` }}
            />
          )}

          {/* Biometric Oval Landmark */}
          <div className={`h-40 w-32 rounded-[50%] border-2 transition-all flex items-center justify-center ${
            isScanning ? 'border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.3)] animate-pulse' :
            verificationResult.status === 'VERIFIED' ? 'border-emerald-400 bg-emerald-500/10' : 'border-slate-700'
          }`}>
            {verificationResult.status === 'VERIFIED' ? (
              <CheckCircle2 className="h-12 w-12 text-emerald-400" />
            ) : isScanning ? (
              <span className="text-2xl">{challenges[challengeStep - 1].icon}</span>
            ) : (
              <Camera className="h-8 w-8 text-slate-600" />
            )}
          </div>

          <div className="mt-3 text-center z-10">
            <span className="text-xs font-mono text-cyan-300 font-semibold">
              {isScanning ? `LIVENESS STEP ${challengeStep}/3` : verificationResult.status === 'VERIFIED' ? 'BIOMETRIC PASS' : 'VIEWFINDER STANDBY'}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {isScanning ? challenges[challengeStep - 1].text : 'Runs locally on host via OpenCV for seamless webcam access'}
            </p>
          </div>
        </div>

        {/* Challenge Sequence & Token Proof */}
        <div className="space-y-4 text-xs font-sans">
          <div className="space-y-2">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-mono">Liveness Verification Pipeline</span>
            {challenges.map((c) => (
              <div
                key={c.step}
                className={`p-3 rounded-lg border flex items-center justify-between transition-all ${
                  challengeStep > c.step || verificationResult.status === 'VERIFIED'
                    ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                    : challengeStep === c.step && isScanning
                    ? 'bg-cyan-950/30 border-cyan-500 text-cyan-200'
                    : 'bg-[#0F172A] border-slate-800 text-slate-500'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <span className="text-base">{c.icon}</span>
                  <span className="font-semibold">{c.text}</span>
                </div>
                {challengeStep > c.step || verificationResult.status === 'VERIFIED' ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                  <Lock className="h-3.5 w-3.5 opacity-50" />
                )}
              </div>
            ))}
          </div>

          {/* Verification Token Output */}
          {verificationResult.status === 'VERIFIED' && (
            <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/40 space-y-1 font-mono text-[11px] text-emerald-300">
              <div className="flex items-center justify-between font-bold">
                <span>✅ HANDSHAKE TOKEN ISSUED</span>
                <span>{verificationResult.latencyMs}ms</span>
              </div>
              <div className="text-[10px] opacity-80 break-all">{verificationResult.token}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
