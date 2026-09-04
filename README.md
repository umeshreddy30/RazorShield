# RazorShield 🛡️
### Autonomous Multi-Agent Fraud Defense & Real-Time Risk Intelligence Engine

> **Razorpay AI Buildathon — Enterprise Multi-Agent Fraud & Risk Prevention Platform**  
> *"Autonomous AI agents investigating high-velocity transactions, syndicate fraud rings, and checkout anomalies with sub-15ms decision latency."*

[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js%2014-black?style=flat&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.120-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph%20Multi--Agent-orange?style=flat)](https://github.com/langchain-ai/langgraph)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20%2F%20Motor-47A248?style=flat&logo=mongodb)](https://www.mongodb.com/)
[![XGBoost](https://img.shields.io/badge/ML%20Engine-XGBoost%20Quantized-blue?style=flat)](https://xgboost.ai/)
[![WebSockets](https://img.shields.io/badge/Streaming-WebSockets%20Real--Time-6366F1?style=flat)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

---

## ⚠️ Defense-Only Statement

This is an **autonomous defensive risk & fraud intelligence platform** designed for fintech payment gateways and merchant checkouts. All data used is **100% synthetic**; no real user PII is ever ingested or exposed.

---

## 1. System Overview

Traditional fraud engines rely on static rule engines or offline batch models that flag suspicious orders too late. **RazorShield** pivots fraud defense into an **Autonomous Multi-Agent Investigation Mesh**:

1. **Sub-15ms Real-Time Ingestion**: Evaluates transaction velocity, IP proxies, device emulators, and transaction amount using a high-throughput **XGBoost** inference model.
2. **Autonomous LangGraph Multi-Agent Mesh**: Rather than returning a black-box number, specialized AI agents actively investigate high-risk cases by querying MongoDB historical logs, traversing fraud ring entity graphs, analyzing unstructured order notes with NLP, and formulating a legally auditable case verdict (`APPROVE`, `TRIGGER_2FA`, `BLOCK`).
3. **Live "Agent Thinking" Streaming**: Streams the AI agents' intermediate reasoning tokens, database tool calls, and cluster findings in real time over **WebSockets** to a futuristic dark-mode **Next.js Execution Terminal**.

---

## 2. Multi-Agent Architecture & Data Flow

```
                                 [Incoming Payment / Transaction]
                                                 │
                                                 ▼
                             ┌───────────────────────────────────────┐
                             │    FastAPI Gateway (/api/v1/score)    │
                             │   • In-memory XGBoost Vectorizer      │
                             │   • Sub-15ms Latency SLA Guarantee    │
                             └───────────────────┬───────────────────┘
                                                 │
                                      [If Risk Score > 40.0]
                                                 │
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        LangGraph Multi-Agent State Machine                             │
│                                                                                        │
│   ┌───────────────────────────┐      WebSocket Stream      ┌───────────────────────┐   │
│   │     Supervisor Agent      │ ─── (/ws/investigate) ───> │ Next.js AI Terminal   │   │
│   │  • Deconstructs case      │                            │  • Live typing logs   │   │
│   │  • Dispatches sub-agents  │                            │  • Tool argument peek │   │
│   └─────────────┬─────────────┘                            └───────────────────────┘   │
│                 │                                                                      │
│                 ▼                                                                      │
│   ┌───────────────────────────┐      Async Tool Call       ┌───────────────────────┐   │
│   │   Data Retrieval Agent    │ ─────────────────────────> │ MongoDB / Motor       │   │
│   │  • User history & tenure  │                            │  • Customer Profiles  │   │
│   │  • Prior chargeback count │ <───────────────────────── │  • Dispute Logs       │   │
│   └─────────────┬─────────────┘      Historical Metrics    └───────────────────────┘   │
│                 │                                                                      │
│                 ▼                                                                      │
│   ┌───────────────────────────┐      Graph Traversal       ┌───────────────────────┐   │
│   │   Fraud Ring Graph Agent  │ ─────────────────────────> │ Entity Graph Subgraph │   │
│   │  • IP proxy collisions    │                            │  • Shared Devices     │   │
│   │  • Emulators & stolen BIN │ <───────────────────────── │  • Proxy Clusters     │   │
│   └─────────────┬─────────────┘      Collision Flags       └───────────────────────┘   │
│                 │                                                                      │
│                 ▼                                                                      │
│   ┌───────────────────────────┐      Semantic Extraction   ┌───────────────────────┐   │
│   │     NLP Context Scorer    │ ─────────────────────────> │ Urgency & Intent Tree │   │
│   │  • "Rush overnight gift"  │                            │  • High-Risk Keyword  │   │
│   │  • Anomaly intent flags   │ <───────────────────────── │  • Context Score      │   │
│   └─────────────┬─────────────┘      NLP Risk Vector       └───────────────────────┘   │
│                 │                                                                      │
│                 ▼                                                                      │
│   ┌───────────────────────────┐      Final Synthesis       ┌───────────────────────┐   │
│   │      Decision Agent       │ ─────────────────────────> │ Case Verdict Verdict: │   │
│   │  • Synthesizes evidence   │                            │  • APPROVE (0-39)     │   │
│   │  • Computes confidence %  │                            │  • TRIGGER_2FA (40-74)│   │
│   │  • Emits action protocol  │                            │  • BLOCK (75-100)     │   │
│   └───────────────────────────┘                            └───────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The 5 Core Engineering Features

### 🤖 1. Real-Time Transaction Scoring Engine (`backend/train_xgboost.py` & `main.py`)
- High-throughput XGBoost tree classifier trained on synthetic e-commerce payment telemetry.
- **Validation AUC: 0.9170**.
- In-memory vectorized model serving with **sub-15ms latency** per transaction.

### 👁️ 2. Advanced Vision 2FA with Liveness Detection (`frontend/components/Vision2FASimulator.tsx`)
- Biometric challenge-response protocol for borderline risk transactions (Scores 40–74).
- Facial landmark wireframe challenge tracking **blink count** and **head turn angles** (15° rotation) with OpenCV/MediaPipe compatibility running locally on host hardware.
- Cryptographic handshake token exchange for payment capture.

### 🕸️ 3. Interactive Fraud Ring Graph Visualizer (`frontend/components/FraudRingGraph.tsx`)
- Interactive HTML5 Canvas physics force-directed graph.
- Visualizes entity collisions: datacenter proxies, headless Linux emulators, shared customer IDs, and stolen card hashes.
- Interactive node inspector displaying cluster threat risk % and shared multi-account collision details.

### 📝 4. NLP-Driven Risk Analysis on Unstructured Metadata (`backend/agents/tools.py`)
- Evaluates merchant memos, shipping instructions, and customer order notes.
- Extracts urgency cues (`"rush overnight"`, `"bypass call"`, `"leave with neighbor"`) and computes an NLP risk vector blended into the composite decision.

### ⚡ 5. Production-Ready Dark-Mode Command Center (`frontend/app/page.tsx`)
- Cyberpunk fintech dark UI (`#070A12` canvas, glassmorphism cards, glowing status pills).
- Bi-directional WebSockets (`/ws/investigate` and `/ws/alerts`) with automatic exponential backoff reconnection.
- Live KPI counters (Total Evaluated, Fraud Intercept Rate %, Prevented Financial Loss in ₹, Average Latency ms).

---

## 4. Repository Structure

```text
razorshield/
├── backend/                       # FastAPI & LangGraph Autonomous Engine
│   ├── agents/
│   │   ├── __init__.py           # Agent package initializer
│   │   ├── state.py              # InvestigationState & AgentThoughtFrame schemas
│   │   ├── tools.py              # MongoDB query tools, Graph ring traversal, NLP parser
│   │   └── workflow.py           # LangGraph StateGraph & thought streaming generator
│   ├── main.py                   # FastAPI REST & WebSocket endpoints
│   ├── test_multi_agent.py       # End-to-end multi-agent verification script
│   └── train_xgboost.py          # Synthetic data generator & XGBoost model trainer
│
├── frontend/                      # Next.js 14 Production Web Application
│   ├── app/
│   │   ├── globals.css           # Custom futuristic dark theme & scrollbar styling
│   │   ├── layout.tsx            # App root layout
│   │   └── page.tsx              # Master Multi-Agent Command Center
│   ├── components/
│   │   ├── AgentExecutionTerminal.tsx  # Live Agent Thinking WebSocket Terminal
│   │   ├── FraudRingGraph.tsx          # Interactive HTML5 Canvas Force Graph Visualizer
│   │   ├── RealTimeScoreFeed.tsx       # Live Telemetry Stream & KPI Diagnostic Drawer
│   │   └── Vision2FASimulator.tsx      # MediaPipe Biometric 2FA Liveness Challenge
│   ├── package.json              # Next.js dependencies
│   ├── tailwind.config.js        # Custom fintech color palette
│   └── tsconfig.json             # TypeScript configuration
│
├── models/                        # Pre-trained ML artifacts (XGBoost, Encoders, LightGBM)
├── data/                          # Dataset schemas & processed splits
├── app/                           # Alternative Streamlit app (with Agent Investigation tab)
└── requirements.txt               # Unified Python dependencies (LangGraph, FastAPI, etc.)
```

---

## 5. Getting Started & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Train / Refresh XGBoost Model
```bash
python backend/train_xgboost.py
```

### 3. Launch FastAPI Multi-Agent Backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*API is accessible at [http://localhost:8000](http://localhost:8000)*  
*Swagger Documentation available at [http://localhost:8000/docs](http://localhost:8000/docs)*  
*Agent WebSocket Stream: `ws://localhost:8000/ws/investigate`*

### 4. Launch Next.js Frontend Command Center
```bash
cd frontend
npm install
npm run dev
```
*Open [http://localhost:3000](http://localhost:3000) in your browser.*

---

## 6. Verification & Automated Testing

Run the multi-agent investigation verification script:
```bash
python backend/test_multi_agent.py
```

**Expected Output**:
```text
[Supervisor] (AGENT_ASSIGNED) -> Supervisor: New case received for txn 'txn_test_agent_001'...
[DataRetrievalAgent] (TOOL_INVOKED) -> Querying MongoDB collections 'customer_profiles'...
[DataRetrievalAgent] (TOOL_RESULT) -> MongoDB query complete: Found 4 lifetime transactions...
[GraphAgent] (TOOL_INVOKED) -> Executing graph cluster traversal on IP '103.21.124.89'...
[GraphAgent] (TOOL_RESULT) -> Graph analysis concluded: [ALERT] HIGH RISK: Syndicate collision!
[NLPAnalyzer] (THINKING) -> Parsing unstructured notes: "Urgent rush dispatch"...
[NLPAnalyzer] (TOOL_RESULT) -> NLP scan complete. Intent: SUSPICIOUS_URGENCY, Risk: 90%
[DecisionAgent] (THINKING) -> Synthesizing full evidence ledger...
[DecisionAgent] (DECISION_REACHED) -> Final Verdict reached: [BLOCK] (Risk: 88.5/100, Confidence: 88%)
[Supervisor] (INVESTIGATION_COMPLETE) -> Investigation lifecycle concluded.

Investigation Duration: ~540 ms
[SUCCESS] All multi-agent assertions passed!
```

---

## 7. Cloud Deployment Guide

- **Next.js Frontend**: Deploy directly to [Vercel](https://vercel.com) by connecting your GitHub repo.
- **FastAPI Backend**: Deploy to [Render](https://render.com), [Railway](https://railway.app), or AWS EC2 using `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
- **Streamlit Alternative**: Deploy directly to [Streamlit Cloud](https://share.streamlit.io) with main file path `app/streamlit_app.py`.

---

## 8. License & Disclaimer

This project was built for the **Razorpay AI Buildathon**. It is a risk-intelligence engineering demonstration and is not an official Razorpay product. All trademarks belong to their respective owners.
