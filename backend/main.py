# backend/main.py
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import xgboost as xgb
import numpy as np

from backend.agents.workflow import execute_agent_investigation, create_investigation_graph
from backend.agents.state import InvestigationResult

app = FastAPI(
    title="RazorShield Autonomous Multi-Agent Risk Intelligence API",
    version="2.0.0",
    description="Autonomous Multi-Agent Fraud Investigation & Real-Time Scoring Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Global State & In-Memory Model Cache
# ---------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent

class MLInferenceEngine:
    def __init__(self, model_filename: str = "xgboost_fraud_v1.json"):
        self.bst = xgb.Booster()
        model_path = ROOT_DIR / "models" / model_filename
        try:
            self.bst.load_model(str(model_path))
            self.feature_order = [
                "amount", "account_age_days", "device_trust_score",
                "ip_velocity_1h", "txn_velocity_1h", "is_vpn_proxy",
                "failed_attempts_24h", "billing_shipping_match"
            ]
            print(f"[ML-CORE] Model loaded into memory from {model_path}")
        except Exception as e:
            print(f"[ML-WARN] Model load warning: {e}. Fallback scoring enabled.")
            self.bst = None

    def predict_score(self, features: Dict[str, float]) -> float:
        if not self.bst:
            return min(1.0, max(0.0, (features["amount"] / 50000.0) * 0.5 + (0.5 if features["is_vpn_proxy"] else 0.0)))
        
        arr = np.array([[features[k] for k in self.feature_order]], dtype=np.float32)
        dmatrix = xgb.DMatrix(arr, feature_names=self.feature_order)
        prob = float(self.bst.predict(dmatrix)[0])
        return prob

ml_engine = MLInferenceEngine()

# ---------------------------------------------------------
# WebSocket Connection Pool Managers
# ---------------------------------------------------------
class ChannelManager:
    def __init__(self, name: str):
        self.name = name
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[{self.name}] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[{self.name}] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        tasks = [connection.send_text(payload) for connection in list(self.active_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res, conn in zip(results, list(self.active_connections)):
            if isinstance(res, Exception):
                self.disconnect(conn)

alerts_manager = ChannelManager("WS-ALERTS")
investigation_manager = ChannelManager("WS-AGENT-THINKING")

# In-memory store for investigation audit cases
INVESTIGATION_CASES: Dict[str, Any] = {}

# ---------------------------------------------------------
# Pydantic Request / Response Contracts
# ---------------------------------------------------------
class TransactionPayload(BaseModel):
    transaction_id: str = Field(..., example="txn_rzp_9841209")
    merchant_id: str = Field(..., example="mer_enterprise_01")
    customer_id: Optional[str] = Field(default="cust_88129", example="cust_88129")
    amount: float = Field(..., ge=1.0, example=4850.0)
    account_age_days: float = Field(..., ge=0, example=3.0)
    device_trust_score: float = Field(..., ge=0.0, le=1.0, example=0.25)
    ip_velocity_1h: int = Field(..., ge=0, example=4)
    txn_velocity_1h: int = Field(..., ge=0, example=3)
    is_vpn_proxy: bool = Field(..., example=True)
    failed_attempts_24h: int = Field(..., ge=0, example=2)
    billing_shipping_match: bool = Field(..., example=False)
    customer_email: str = Field(..., example="buyer@example.com")
    ip_address: str = Field(..., example="103.21.124.89")
    device_fingerprint: Optional[str] = Field(default="dfp_a7b29c011e4", example="dfp_a7b29c011e4")
    order_category: Optional[str] = Field(default="ELECTRONICS", example="ELECTRONICS")
    notes: Optional[str] = Field(default="", example="Urgent overnight courier please")

class ScoringResponse(BaseModel):
    transaction_id: str
    ml_fraud_score: float
    composite_risk_score: float
    decision: str  # APPROVE, CHALLENGE_2FA, BLOCK
    latency_ms: float
    flags: List[str]
    timestamp: float

# ---------------------------------------------------------
# System Root Status
# ---------------------------------------------------------
@app.get("/")
def root_status():
    return {
        "status": "active",
        "system": "RazorShield Autonomous Multi-Agent Risk Intelligence Core",
        "version": "2.0.0",
        "endpoints": {
            "score": "/api/v1/score (POST)",
            "investigate": "/api/v1/investigate (POST)",
            "cases": "/api/v1/cases (GET)",
            "websocket_alerts": "/ws/alerts (WS)",
            "websocket_agent_thinking": "/ws/investigate (WS)",
            "simulate": "/api/v1/mock/simulate (POST)",
            "docs": "/docs"
        }
    }

# ---------------------------------------------------------
# 1. Real-Time Transaction Scoring Endpoint (Fast Scoring)
# ---------------------------------------------------------
@app.post("/api/v1/score", response_model=ScoringResponse, status_code=status.HTTP_200_OK)
async def score_transaction(payload: TransactionPayload):
    start_time = time.perf_counter()
    
    features = {
        "amount": payload.amount,
        "account_age_days": payload.account_age_days,
        "device_trust_score": payload.device_trust_score,
        "ip_velocity_1h": float(payload.ip_velocity_1h),
        "txn_velocity_1h": float(payload.txn_velocity_1h),
        "is_vpn_proxy": 1.0 if payload.is_vpn_proxy else 0.0,
        "failed_attempts_24h": float(payload.failed_attempts_24h),
        "billing_shipping_match": 1.0 if payload.billing_shipping_match else 0.0
    }
    
    fraud_prob = ml_engine.predict_score(features)
    composite_score = round(fraud_prob * 100, 1)
    
    flags = []
    if payload.is_vpn_proxy:
        flags.append("VPN_PROXY_DETECTED")
    if payload.ip_velocity_1h >= 4:
        flags.append("HIGH_IP_VELOCITY")
    if not payload.billing_shipping_match:
        flags.append("BILLING_SHIPPING_MISMATCH")
    if payload.amount > 25000:
        flags.append("LARGE_TRANSACTION_VALUE")
        
    if composite_score > 75.0 or (payload.is_vpn_proxy and payload.ip_velocity_1h >= 5):
        decision = "BLOCK"
    elif composite_score >= 40.0:
        decision = "CHALLENGE_2FA"
    else:
        decision = "APPROVE"
        
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    response_data = ScoringResponse(
        transaction_id=payload.transaction_id,
        ml_fraud_score=round(fraud_prob, 4),
        composite_risk_score=composite_score,
        decision=decision,
        latency_ms=latency_ms,
        flags=flags,
        timestamp=time.time()
    )
    
    # Broadcast to Alert subscribers
    asyncio.create_task(alerts_manager.broadcast({
        "event_type": "TRANSACTION_SCORED",
        "data": {
            "transaction_id": payload.transaction_id,
            "merchant_id": payload.merchant_id,
            "customer_id": payload.customer_id,
            "amount": payload.amount,
            "customer_email": payload.customer_email,
            "ip_address": payload.ip_address,
            "composite_risk_score": composite_score,
            "decision": decision,
            "latency_ms": latency_ms,
            "flags": flags,
            "timestamp": time.time()
        }
    }))
    
    return response_data

# ---------------------------------------------------------
# 2. Autonomous Multi-Agent Investigation Endpoint (LangGraph)
# ---------------------------------------------------------
@app.post("/api/v1/investigate", response_model=InvestigationResult, status_code=status.HTTP_200_OK)
async def investigate_transaction(payload: TransactionPayload):
    """
    Triggers an autonomous multi-agent fraud investigation workflow.
    Streams reasoning steps over WebSockets (/ws/investigate) and returns synthesized verdict.
    """
    async def thought_broadcaster(frame: Dict[str, Any]):
        await investigation_manager.broadcast(frame)
        
    result = await execute_agent_investigation(
        transaction_id=payload.transaction_id,
        customer_id=payload.customer_id or "cust_unknown",
        merchant_id=payload.merchant_id,
        transaction_data=payload.model_dump(),
        emit_callback=thought_broadcaster
    )
    
    INVESTIGATION_CASES[result.transaction_id] = result.model_dump()
    return result

@app.get("/api/v1/cases/{transaction_id}")
async def get_investigation_case(transaction_id: str):
    if transaction_id not in INVESTIGATION_CASES:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    return INVESTIGATION_CASES[transaction_id]

# ---------------------------------------------------------
# 3. WebSockets Gateways
# ---------------------------------------------------------
@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await alerts_manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({
            "event_type": "SYSTEM_CONNECTED",
            "message": "Connected to RazorShield Real-Time Risk Stream"
        }))
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"event_type": "PONG"}))
    except WebSocketDisconnect:
        alerts_manager.disconnect(websocket)
    except Exception:
        alerts_manager.disconnect(websocket)

@app.websocket("/ws/investigate")
async def websocket_investigate_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint that streams real-time intermediate agent thoughts,
    database tool calls, graph scans, and decision synthesis tokens.
    """
    await investigation_manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({
            "event_type": "SYSTEM_CONNECTED",
            "agent_name": "Supervisor",
            "thought": "Terminal attached to RazorShield Autonomous Multi-Agent Mesh.",
            "timestamp": time.time()
        }))
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"event_type": "PONG"}))
    except WebSocketDisconnect:
        investigation_manager.disconnect(websocket)
    except Exception:
        investigation_manager.disconnect(websocket)

# ---------------------------------------------------------
# Mock Stream / Demo Triggers
# ---------------------------------------------------------
@app.post("/api/v1/mock/simulate")
async def simulate_traffic(count: int = 3, trigger_agents: bool = True):
    import random
    scored_items = []
    for i in range(count):
        is_fraud_case = random.random() < 0.40
        payload = TransactionPayload(
            transaction_id=f"txn_{int(time.time()*1000)}_{random.randint(100, 999)}",
            merchant_id="mer_razor_prime",
            customer_id="cust_88129" if is_fraud_case else "cust_trusted_01",
            amount=round(random.uniform(12000, 85000), 2) if is_fraud_case else round(random.uniform(500, 4500), 2),
            account_age_days=random.uniform(0.5, 5) if is_fraud_case else random.uniform(50, 400),
            device_trust_score=round(random.uniform(0.05, 0.35), 2) if is_fraud_case else round(random.uniform(0.7, 0.98), 2),
            ip_velocity_1h=random.randint(4, 9) if is_fraud_case else random.randint(0, 2),
            txn_velocity_1h=random.randint(5, 12) if is_fraud_case else random.randint(1, 3),
            is_vpn_proxy=True if is_fraud_case else False,
            failed_attempts_24h=random.randint(2, 6) if is_fraud_case else random.randint(0, 1),
            billing_shipping_match=False if is_fraud_case else True,
            customer_email="syndicate_buyer@tempmail.com" if is_fraud_case else "trusted_client@gmail.com",
            ip_address="103.21.124.89" if is_fraud_case else "49.207.210.12",
            device_fingerprint="dfp_a7b29c011e4" if is_fraud_case else "dfp_mac_9921",
            notes="Urgent rush gift dispatch, leave at reception" if is_fraud_case else "Standard domestic delivery"
        )
        # Fast score
        res = await score_transaction(payload)
        scored_items.append(res)
        
        # Trigger Multi-Agent Investigation if requested
        if trigger_agents:
            asyncio.create_task(investigate_transaction(payload))
            
        await asyncio.sleep(0.4)
    return {"status": "success", "processed_count": len(scored_items)}
