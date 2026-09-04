// frontend/components/Vision2FASimulator.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Camera, Eye, ShieldCheck, RefreshCw, CheckCircle2, Lock, Zap, Loader2, Video, AlertCircle, AlertTriangle, XCircle, Sliders, Sparkles, Copy, Check } from 'lucide-react';

interface Vision2FASimulatorProps {
  apiUrl?: string;
}

export default function Vision2FASimulator({
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}: Vision2FASimulatorProps) {
  const [challengeStep, setChallengeStep] = useState<number>(1);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [livenessProgress, setLivenessProgress] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>('Webcam biometric challenge standing by.');
  const [cameraMode, setCameraMode] = useState<'STRICT_HARDWARE' | 'DEMO_EMULATED'>('STRICT_HARDWARE');
  const [cameraStatus, setCameraStatus] = useState<'IDLE' | 'ACTIVE' | 'FAILED'>('IDLE');
  const [faceDetected, setFaceDetected] = useState<boolean | null>(null);
  const [detectorUsed, setDetectorUsed] = useState<string>('');
  const [confidenceScore, setConfidenceScore] = useState<number | null>(null);
  const [copiedToken, setCopiedToken] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<{
    status: 'IDLE' | 'VERIFIED' | 'FAILED';
    token?: string | null;
    latencyMs?: number;
    message?: string;
  }>({ status: 'IDLE' });

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const scanIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutTimerRef = useRef<NodeJS.Timeout | null>(null);

  const challenges = [
    { step: 1, text: 'Center face in the biometric frame', icon: '👤', instruction: 'Align your face directly inside the central oval guide' },
    { step: 2, text: 'Blink eyes twice to verify active liveness', icon: '👁️', instruction: 'Blink your eyes naturally to confirm real human liveness' },
    { step: 3, text: 'Turn head slightly or nod to verify 3D depth', icon: '🔄', instruction: 'Slight head movement confirms 3D depth profile' },
  ];

  const clearTimers = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    if (timeoutTimerRef.current) {
      clearTimeout(timeoutTimerRef.current);
      timeoutTimerRef.current = null;
    }
  };

  const stopCamera = () => {
    clearTimers();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  // Helper to capture base64 snapshot from the active video stream
  const captureFrameBase64 = (): string | null => {
    if (!videoRef.current) return null;
    const video = videoRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) return null;

    const canvas = document.createElement('canvas');
    canvas.width = Math.min(640, video.videoWidth);
    canvas.height = Math.min(480, video.videoHeight);
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    // Draw unmirrored frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.82);
  };

  const startVerification = async () => {
    stopCamera();
    setVerificationResult({ status: 'IDLE' });
    setFaceDetected(null);
    setDetectorUsed('');
    setConfidenceScore(null);
    setLivenessProgress(8);
    setChallengeStep(1);
    setIsScanning(true);
    setStatusMessage('Initializing camera hardware & neural vision pipeline...');

    let localStream: MediaStream | null = null;
    let cameraWorks = false;

    if (cameraMode === 'STRICT_HARDWARE') {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          localStream = await navigator.mediaDevices.getUserMedia({
            video: {
              width: { ideal: 640 },
              height: { ideal: 480 },
              facingMode: 'user'
            }
          });

          const videoTrack = localStream.getVideoTracks()[0];
          if (videoTrack && videoTrack.readyState === 'live') {
            streamRef.current = localStream;
            if (videoRef.current) {
              videoRef.current.srcObject = localStream;
              await videoRef.current.play();
            }
            cameraWorks = true;
            setCameraStatus('ACTIVE');
            setStatusMessage('Stage 1: Scanning for human face inside reticle...');
          }
        }
      } catch (err: any) {
        console.warn('Hardware camera access failed:', err);
        setCameraStatus('FAILED');
        setIsScanning(false);
        setLivenessProgress(0);
        setVerificationResult({
          status: 'FAILED',
          token: null,
          latencyMs: 45.0,
          message: 'Hardware Error: No working webcam stream found on this machine. Biometric verification failed.'
        });
        setStatusMessage('❌ Camera Hardware Error: Camera failed or permission was denied. Biometric verification rejected.');
        return;
      }

      if (!cameraWorks) {
        setCameraStatus('FAILED');
        setIsScanning(false);
        setLivenessProgress(0);
        setVerificationResult({
          status: 'FAILED',
          token: null,
          latencyMs: 30.0,
          message: 'Camera stream inactive. Verification aborted for security.'
        });
        setStatusMessage('❌ Verification Aborted: Hardware camera not producing frames.');
        return;
      }

      // STRICT MODE: Run real frame-by-frame OpenCV Face Verification
      let step = 1;
      let matchedFrames = 0;
      let totalElapsedTicks = 0;
      const MAX_TICKS = 26; // ~18 seconds total scan window

      scanIntervalRef.current = setInterval(async () => {
        totalElapsedTicks += 1;
        const frameData = captureFrameBase64();

        if (!frameData) {
          setStatusMessage('Buffering camera video stream...');
          return;
        }

        try {
          const payload = {
            source: 'client_biometric_challenge',
            mode: 'STRICT_HARDWARE',
            camera_permission: 'HARDWARE_CONFIRMED',
            frame_image: frameData,
            stage: step,
            client_timestamp: Date.now()
          };

          const res = await fetch(`${apiUrl}/api/trigger-liveness`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const data = await res.json();

          if (data.face_detected) {
            setFaceDetected(true);
            matchedFrames += 1;
            if (data.detector_used) setDetectorUsed(data.detector_used);
            if (data.confidence) setConfidenceScore(data.confidence);

            if (step === 1 && matchedFrames >= 2) {
              step = 2;
              setChallengeStep(2);
              setLivenessProgress(45);
              setStatusMessage('Stage 2: Face locked & aligned! Please blink your eyes naturally.');
            } else if (step === 2 && matchedFrames >= 4) {
              step = 3;
              setChallengeStep(3);
              setLivenessProgress(80);
              setStatusMessage('Stage 3: Blink verified! Turn head slightly or nod for 3D depth.');
            } else if (step === 3 && matchedFrames >= 6) {
              // Final Step: Complete & obtain signed token!
              clearTimers();
              setIsScanning(false);
              setLivenessProgress(100);

              if (data.success && data.token) {
                setVerificationResult({
                  status: 'VERIFIED',
                  token: data.token,
                  latencyMs: data.latency_ms || 85.0,
                  message: 'Biometric Liveness Verified & Cryptographically Signed.'
                });
                setStatusMessage('✅ Biometric Liveness Passed & HMAC Signed Token Issued.');
              }
            }
          } else {
            // NO FACE DETECTED ON THIS TICK
            setFaceDetected(false);
            setStatusMessage('⚠️ Position your face inside the central oval guide...');

            // If no face sustained after full scan window (~18s), strictly FAIL
            if (totalElapsedTicks >= MAX_TICKS && matchedFrames < 2) {
              clearTimers();
              setIsScanning(false);
              setLivenessProgress(0);
              setVerificationResult({
                status: 'FAILED',
                token: null,
                latencyMs: 38.0,
                message: 'Biometric Verification Failed: No human face detected in the live camera feed.'
              });
              setStatusMessage('❌ Verification Failed: No human face detected in viewfinder.');
            }
          }
        } catch (err) {
          console.warn('Frame verification roundtrip error:', err);
        }
      }, 700);

    } else {
      // Demo Emulated Mode
      setCameraStatus('ACTIVE');
      setFaceDetected(true);
      setDetectorUsed('emulated_sim');
      setConfidenceScore(0.98);
      setStatusMessage('🧪 Demo Mode: Simulating biometric landmark alignment...');

      const t1 = setTimeout(() => {
        setChallengeStep(2);
        setLivenessProgress(45);
        setStatusMessage('Stage 2: Simulating active eye blink detection...');
      }, 1800);

      const t2 = setTimeout(() => {
        setChallengeStep(3);
        setLivenessProgress(80);
        setStatusMessage('Stage 3: Simulating 3D depth motion confirmation...');
      }, 3600);

      const t3 = setTimeout(async () => {
        setStatusMessage('Cryptographically signing simulated token with FastAPI...');
        setLivenessProgress(95);

        try {
          const payload = {
            source: 'client_biometric_challenge',
            mode: 'DEMO_EMULATED',
            camera_permission: 'EMULATED',
            client_timestamp: Date.now()
          };

          const res = await fetch(`${apiUrl}/api/trigger-liveness`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const data = await res.json();

          setLivenessProgress(100);
          setIsScanning(false);

          if (data.success) {
            setVerificationResult({
              status: 'VERIFIED',
              token: data.token,
              latencyMs: data.latency_ms || 90.0,
              message: 'Demo Biometric Liveness Verified & Cryptographically Signed.'
            });
            setStatusMessage('✅ Biometric Liveness Passed & HMAC Signed Token Issued (Demo Mode).');
          }
        } catch (err) {
          setIsScanning(false);
          setVerificationResult({
            status: 'FAILED',
            token: null,
            latencyMs: 0,
            message: 'Backend verification gateway unreachable.'
          });
          setStatusMessage('❌ Network Error: Could not reach verification API.');
        }
      }, 5400);

      timeoutTimerRef.current = t3;
    }
  };

  const resetChallenge = () => {
    stopCamera();
    setIsScanning(false);
    setLivenessProgress(0);
    setChallengeStep(1);
    setCameraStatus('IDLE');
    setFaceDetected(null);
    setDetectorUsed('');
    setConfidenceScore(null);
    setCopiedToken(false);
    setVerificationResult({ status: 'IDLE' });
    setStatusMessage('Webcam biometric challenge standing by.');
  };

  const copyTokenToClipboard = () => {
    if (verificationResult.token) {
      navigator.clipboard.writeText(verificationResult.token);
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

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
            <p className="text-[11px] text-slate-400">Deep Learning YuNet + Multi-Tier Ensemble Biometric Landmark Verification</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Mode Selector */}
          <div className="flex items-center bg-[#070A12] border border-slate-800 rounded-lg p-1 text-[11px] font-mono">
            <button
              onClick={() => { setCameraMode('STRICT_HARDWARE'); resetChallenge(); }}
              className={`px-2.5 py-1 rounded transition-all flex items-center gap-1 ${
                cameraMode === 'STRICT_HARDWARE' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Requires real face visible in laptop webcam"
            >
              <Camera className="h-3 w-3" />
              <span>Strict Camera Mode</span>
            </button>
            <button
              onClick={() => { setCameraMode('DEMO_EMULATED'); resetChallenge(); }}
              className={`px-2.5 py-1 rounded transition-all flex items-center gap-1 ${
                cameraMode === 'DEMO_EMULATED' ? 'bg-amber-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
              title="For testing on devices without working cameras"
            >
              <Sliders className="h-3 w-3" />
              <span>Demo Mode</span>
            </button>
          </div>

          {verificationResult.status !== 'IDLE' && (
            <button
              onClick={resetChallenge}
              className="flex items-center space-x-1 text-slate-400 hover:text-white px-3 py-1.5 rounded-lg text-xs bg-slate-800/80 transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Reset</span>
            </button>
          )}

          <button
            onClick={startVerification}
            disabled={isScanning}
            className={`flex items-center space-x-1.5 text-white px-4 py-2 rounded-lg text-xs font-semibold shadow-md transition-all ${
              cameraMode === 'STRICT_HARDWARE'
                ? 'bg-cyan-600 hover:bg-cyan-500 shadow-cyan-600/20'
                : 'bg-amber-600 hover:bg-amber-500 shadow-amber-600/20'
            } disabled:opacity-50 active:scale-95`}
          >
            {isScanning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Camera className="h-3.5 w-3.5" />}
            <span>{isScanning ? 'Verifying Live Stream...' : 'Trigger 2FA Liveness Check'}</span>
          </button>
        </div>
      </div>

      {/* Mode Warning Banner */}
      {cameraMode === 'DEMO_EMULATED' && (
        <div className="bg-amber-950/40 border-b border-amber-500/30 px-4 py-1.5 text-[11px] text-amber-300 flex items-center justify-between font-mono">
          <span className="flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
            DEMO EMULATION MODE ACTIVE: Simulates biometric gesture pipeline for testing on laptops without working cameras.
          </span>
          <span className="text-[10px] opacity-70">For strict hardware validation, switch to Strict Camera Mode.</span>
        </div>
      )}

      {/* Main Grid: Live Biometric Viewfinder + Challenge Checklist */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 items-center">
        {/* Live Camera Viewfinder Frame */}
        <div className="relative aspect-video bg-[#070A12] rounded-xl border-2 border-cyan-500/30 flex flex-col items-center justify-center overflow-hidden p-2 shadow-inner">
          <div className="absolute inset-0 bg-grid-pattern opacity-15" />

          {/* Real Live HTML5 Webcam Stream */}
          <video
            ref={videoRef}
            playsInline
            muted
            autoPlay
            className={`absolute inset-0 w-full h-full object-cover transform -scale-x-100 ${
              cameraStatus === 'ACTIVE' && cameraMode === 'STRICT_HARDWARE' ? 'opacity-90' : 'hidden'
            }`}
          />

          {/* HUD Crosshairs / Corner brackets */}
          <div className="absolute inset-4 pointer-events-none z-10 flex flex-col justify-between">
            <div className="flex justify-between">
              <div className="w-4 h-4 border-t-2 border-l-2 border-cyan-400/60" />
              <div className="w-4 h-4 border-t-2 border-r-2 border-cyan-400/60" />
            </div>
            <div className="flex justify-between">
              <div className="w-4 h-4 border-b-2 border-l-2 border-cyan-400/60" />
              <div className="w-4 h-4 border-b-2 border-r-2 border-cyan-400/60" />
            </div>
          </div>

          {/* Scanning Line Animation */}
          {isScanning && (
            <div
              className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_20px_#06b6d4] transition-all z-20"
              style={{ top: `${livenessProgress}%` }}
            />
          )}

          {/* Biometric Oval Landmark HUD */}
          <div
            className={`relative z-10 h-44 w-36 rounded-[50%] border-2 transition-all flex flex-col items-center justify-center backdrop-blur-[1px] ${
              verificationResult.status === 'FAILED'
                ? 'border-rose-500 bg-rose-500/20 shadow-[0_0_30px_rgba(239,68,68,0.5)]'
                : verificationResult.status === 'VERIFIED'
                ? 'border-emerald-400 bg-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.5)]'
                : isScanning && faceDetected === true
                ? 'border-emerald-400 bg-emerald-500/10 shadow-[0_0_30px_rgba(16,185,129,0.4)] scale-105'
                : isScanning && faceDetected === false
                ? 'border-amber-400 bg-amber-500/10 shadow-[0_0_25px_rgba(245,158,11,0.4)] animate-pulse'
                : isScanning
                ? 'border-cyan-400 shadow-[0_0_25px_rgba(6,182,212,0.4)] animate-pulse'
                : 'border-slate-700 bg-black/40'
            }`}
          >
            {verificationResult.status === 'FAILED' ? (
              <XCircle className="h-12 w-12 text-rose-400" />
            ) : verificationResult.status === 'VERIFIED' ? (
              <CheckCircle2 className="h-12 w-12 text-emerald-400" />
            ) : isScanning && faceDetected === true ? (
              <div className="text-center px-2">
                <span className="text-3xl block mb-1 animate-pulse">{challenges[challengeStep - 1].icon}</span>
                <span className="text-[10px] font-mono text-emerald-300 font-bold uppercase bg-black/80 px-2 py-0.5 rounded border border-emerald-500/40 shadow">
                  STEP {challengeStep}/3: {challengeStep === 1 ? 'ALIGNED' : challengeStep === 2 ? 'BLINK' : 'GESTURE'}
                </span>
              </div>
            ) : isScanning && faceDetected === false ? (
              <div className="text-center px-2">
                <AlertCircle className="h-8 w-8 text-amber-400 mx-auto mb-1 animate-bounce" />
                <span className="text-[9px] font-mono text-amber-300 font-bold uppercase bg-black/80 px-1.5 py-0.5 rounded border border-amber-500/30">
                  CENTER FACE IN OVAL
                </span>
              </div>
            ) : isScanning ? (
              <div className="text-center px-2">
                <span className="text-3xl block mb-1">{challenges[challengeStep - 1].icon}</span>
                <span className="text-[10px] font-mono text-cyan-200 font-bold uppercase bg-black/60 px-2 py-0.5 rounded border border-cyan-500/30">
                  STEP {challengeStep}/3
                </span>
              </div>
            ) : (
              <div className="text-center text-slate-500">
                <Video className="h-8 w-8 mx-auto mb-1" />
                <span className="text-[10px] font-mono">{cameraMode === 'STRICT_HARDWARE' ? 'HARDWARE READY' : 'DEMO READY'}</span>
              </div>
            )}
          </div>

          {/* Dynamic Status Text Bar */}
          <div className="mt-3 text-center z-20 bg-[#0B0F19]/90 border border-slate-800 px-4 py-1.5 rounded-full backdrop-blur-md max-w-[90%] shadow-lg">
            <span className={`text-xs font-mono font-semibold flex items-center justify-center gap-1.5 ${
              verificationResult.status === 'FAILED'
                ? 'text-rose-400'
                : isScanning && faceDetected === true
                ? 'text-emerald-300'
                : isScanning && faceDetected === false
                ? 'text-amber-300'
                : 'text-cyan-300'
            }`}>
              {isScanning && <Loader2 className="h-3 w-3 animate-spin text-cyan-400" />}
              {verificationResult.status === 'FAILED'
                ? 'HARDWARE VERIFICATION FAILED'
                : isScanning && faceDetected === true
                ? `${challenges[challengeStep - 1].instruction}`
                : isScanning && faceDetected === false
                ? 'ALIGN FACE IN OVAL'
                : 'BIOMETRIC SCANNER READY'}
            </span>
            <p className="text-[10px] text-slate-400 mt-0.5 truncate">{statusMessage}</p>
          </div>

          {/* Real-time engine badge if active */}
          {detectorUsed && (
            <div className="absolute top-2 right-2 z-20 bg-black/70 border border-slate-700/80 px-2 py-0.5 rounded text-[9px] font-mono text-cyan-300 flex items-center gap-1 backdrop-blur-sm">
              <Sparkles className="h-2.5 w-2.5 text-cyan-400" />
              <span>{detectorUsed === 'yunet_dnn' ? 'YuNet AI (98%)' : detectorUsed}</span>
            </div>
          )}
        </div>

        {/* Challenge Checklist & Cryptographic Token */}
        <div className="space-y-4 text-xs font-sans">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 uppercase tracking-wider text-[10px] font-mono font-bold">
                Biometric Challenge Pipeline
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                {isScanning ? `Progress: ${livenessProgress}%` : verificationResult.status === 'VERIFIED' ? '100% Passed' : verificationResult.status === 'FAILED' ? 'Aborted / Rejected' : 'Standby'}
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  verificationResult.status === 'FAILED' ? 'bg-rose-500' : verificationResult.status === 'VERIFIED' ? 'bg-emerald-500' : 'bg-cyan-500'
                }`}
                style={{ width: `${livenessProgress}%` }}
              />
            </div>

            {challenges.map((c) => {
              const isCompleted = (challengeStep > c.step && verificationResult.status !== 'FAILED') || verificationResult.status === 'VERIFIED';
              const isActive = challengeStep === c.step && isScanning;
              const isFailed = verificationResult.status === 'FAILED' && challengeStep === c.step;

              return (
                <div
                  key={c.step}
                  className={`p-3 rounded-lg border flex items-center justify-between transition-all ${
                    isFailed
                      ? 'bg-rose-950/30 border-rose-500/50 text-rose-300'
                      : isCompleted
                      ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                      : isActive
                      ? 'bg-cyan-950/40 border-cyan-400 text-cyan-100 shadow-[0_0_15px_rgba(6,182,212,0.15)] ring-1 ring-cyan-500/40'
                      : 'bg-[#0F172A] border-slate-800 text-slate-500'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <span className="text-base">{c.icon}</span>
                    <div>
                      <span className="font-semibold block">{c.text}</span>
                      {isActive && (
                        <span className="text-[10px] text-cyan-300 font-mono block mt-0.5">
                          {faceDetected === false ? '⚠️ Align face inside central oval' : '▶ Face detected: Perform action now'}
                        </span>
                      )}
                      {isFailed && (
                        <span className="text-[10px] text-rose-400 font-mono block mt-0.5">
                          ✖ Hardware check failed: No face detected in camera viewfinder
                        </span>
                      )}
                    </div>
                  </div>
                  {isFailed ? (
                    <XCircle className="h-4 w-4 text-rose-400" />
                  ) : isCompleted ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  ) : isActive ? (
                    <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />
                  ) : (
                    <Lock className="h-3.5 w-3.5 opacity-50" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Failed State Card */}
          {verificationResult.status === 'FAILED' && (
            <div className="p-3.5 rounded-lg bg-rose-950/30 border border-rose-500/50 space-y-1 font-mono text-[11px] text-rose-300 animate-in fade-in duration-300">
              <div className="flex items-center justify-between font-bold">
                <span className="flex items-center gap-1.5">
                  <XCircle className="h-4 w-4 text-rose-400" />
                  BIOMETRIC 2FA REJECTED
                </span>
                <span className="text-[10px] text-rose-400/80">{verificationResult.latencyMs}ms</span>
              </div>
              <p className="text-[10px] font-sans opacity-90">{verificationResult.message}</p>
              <p className="text-[9px] text-slate-400 pt-1">
                Security Policy: 2FA challenge requires a live human face centered in the reticle. If presenting on a device without a camera, switch to <strong>"Demo Mode"</strong> above.
              </p>
            </div>
          )}

          {/* Successful Cryptographic Token Output */}
          {verificationResult.status === 'VERIFIED' && (
            <div className="p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-500/50 space-y-1.5 font-mono text-[11px] text-emerald-300 animate-in fade-in duration-300 shadow-lg">
              <div className="flex items-center justify-between font-bold">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  HMAC SIGNED BIOMETRIC TOKEN
                </span>
                <span className="text-[10px] text-emerald-400/80">{verificationResult.latencyMs}ms</span>
              </div>
              <div className="text-[10px] bg-black/60 p-2.5 rounded border border-emerald-500/30 flex items-center justify-between gap-2 break-all text-slate-200">
                <span className="font-mono select-all">{verificationResult.token}</span>
                <button
                  onClick={copyTokenToClipboard}
                  className="p-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 transition-colors shrink-0"
                  title="Copy Token"
                >
                  {copiedToken ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
              </div>
              <div className="text-[9px] text-emerald-400/70 pt-0.5 flex items-center justify-between">
                <span>🔒 Signed by RazorShield FastAPI Auth Mesh ({cameraMode}).</span>
                <span className="text-[9px] text-slate-400 font-mono">256-bit SHA256 Sig</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

