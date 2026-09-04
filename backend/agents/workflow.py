# backend/agents/workflow.py
import asyncio
import time
import random
from typing import Dict, Any, List, Optional, Callable, Awaitable
from langgraph.graph import StateGraph, END

from backend.agents.state import InvestigationState, AgentThoughtFrame, InvestigationResult
from backend.agents.tools import (
    fetch_user_history_tool,
    query_fraud_graph_tool,
    evaluate_nlp_metadata_tool
)

# Callback type for real-time WebSocket thought streaming
StreamCallback = Optional[Callable[[Dict[str, Any]], Awaitable[None]]]

# ---------------------------------------------------------
# Node 1: Supervisor / Orchestrator Agent
# ---------------------------------------------------------
async def supervisor_node(state: InvestigationState, emit_callback: StreamCallback = None) -> Dict[str, Any]:
    txn = state["transaction_data"]
    txn_id = state["transaction_id"]
    cust_id = state["customer_id"]
    scenario = txn.get("scenario_type", "AUTO")
    
    supervisors_phrases = [
        f"Supervisor: Intake case '{txn_id}' for entity '{cust_id}'. Amount: INR {txn.get('amount', 0):,.2f}. Launching autonomous agent mesh...",
        f"Supervisor: High-priority risk case '{txn_id}' received. Customer: '{cust_id}'. Spawning investigative sub-agents...",
        f"Supervisor: Intercepted transaction '{txn_id}' (INR {txn.get('amount', 0):,.2f}). Delegating forensic queries across MongoDB and Entity Graph..."
    ]
    thought_text = random.choice(supervisors_phrases)
    
    frame = {
        "event_type": "AGENT_ASSIGNED",
        "agent_name": "Supervisor",
        "transaction_id": txn_id,
        "thought": thought_text,
        "timestamp": time.time(),
        "data": {
            "assigned_agents": ["DataRetrievalAgent", "GraphAgent", "NLPAnalyzer", "DecisionAgent"],
            "scenario": scenario,
            "priority": "HIGH" if txn.get("amount", 0) > 10000 else "NORMAL"
        }
    }
    
    if emit_callback:
        await emit_callback(frame)
        
    return {
        "status": "RETRIEVING_DATA",
        "agent_thought_stream": [frame]
    }

# ---------------------------------------------------------
# Node 2: Data Retrieval Agent (MongoDB History & Velocity)
# ---------------------------------------------------------
async def data_retrieval_node(state: InvestigationState, emit_callback: StreamCallback = None) -> Dict[str, Any]:
    txn_id = state["transaction_id"]
    cust_id = state["customer_id"]
    email = state["transaction_data"].get("customer_email", "")
    scenario = state["transaction_data"].get("scenario_type", "AUTO")
    
    call_frame = {
        "event_type": "TOOL_INVOKED",
        "agent_name": "DataRetrievalAgent",
        "transaction_id": txn_id,
        "thought": f"Querying MongoDB collections 'customer_profiles' and 'transaction_logs' for historical baseline of '{cust_id}'...",
        "tool_name": "fetch_user_history_tool",
        "tool_args": {"customer_id": cust_id, "email": email, "scenario_type": scenario},
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(call_frame)
        
    history = await fetch_user_history_tool(cust_id, email, scenario_type=scenario)
    
    flags = []
    if history.get("historical_chargebacks", 0) > 0:
        flags.append(f"PRIOR_CHARGEBACK_DISPUTE_x{history['historical_chargebacks']}")
    if history.get("historical_rto_rate", 0) >= 0.35:
        flags.append(f"ELEVATED_RTO_RATE_{int(history['historical_rto_rate']*100)}PCT")
    if history.get("account_age_days", 999) < 5:
        flags.append(f"FRESH_ACCOUNT_{history.get('account_age_days')}D")
    elif history.get("account_age_days", 0) > 180:
        flags.append("LONG_STANDING_CLEAN_TENURE")
        
    result_text = (
        f"MongoDB query returned: {history.get('total_lifetime_orders', 0)} lifetime orders, "
        f"INR {history.get('lifetime_spend_inr', 0):,.2f} lifetime spend, "
        f"{history.get('historical_chargebacks', 0)} prior chargebacks, "
        f"{history.get('historical_rto_rate', 0)*100:.1f}% RTO rate. (KYC: {'VERIFIED' if history.get('kyc_verified') else 'UNVERIFIED'})"
    )
    
    result_frame = {
        "event_type": "TOOL_RESULT",
        "agent_name": "DataRetrievalAgent",
        "transaction_id": txn_id,
        "thought": result_text,
        "tool_name": "fetch_user_history_tool",
        "tool_output": history,
        "timestamp": time.time(),
        "data": {"flags_triggered": flags}
    }
    if emit_callback:
        await emit_callback(result_frame)
        
    return {
        "history_data": history,
        "flags": flags,
        "status": "ANALYZING_GRAPH",
        "agent_thought_stream": [call_frame, result_frame]
    }

# ---------------------------------------------------------
# Node 3: Fraud Ring Graph Agent (Shared Entity Analysis)
# ---------------------------------------------------------
async def graph_investigation_node(state: InvestigationState, emit_callback: StreamCallback = None) -> Dict[str, Any]:
    txn_id = state["transaction_id"]
    ip_addr = state["transaction_data"].get("ip_address", "103.21.124.89")
    device_fp = state["transaction_data"].get("device_fingerprint", "dfp_a7b29c011e4")
    scenario = state["transaction_data"].get("scenario_type", "AUTO")
    
    call_frame = {
        "event_type": "TOOL_INVOKED",
        "agent_name": "GraphAgent",
        "transaction_id": txn_id,
        "thought": f"Executing graph cluster traversal on IP '{ip_addr}' and Device '{device_fp}' for shared syndicate nodes...",
        "tool_name": "query_fraud_graph_tool",
        "tool_args": {"ip_address": ip_addr, "device_fingerprint": device_fp, "scenario_type": scenario},
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(call_frame)
        
    graph_res = await query_fraud_graph_tool(ip_addr, device_fp, scenario_type=scenario)
    
    flags = []
    if graph_res.get("is_syndicate_detected"):
        flags.append("FRAUD_RING_SYNDICATE_COLLISION")
        flags.append(f"SHARED_IP_CLUSTER_{graph_res['ip_cluster_size']}_ACCOUNTS")
        result_thought = f"[ALERT] HIGH RISK: Multi-account collision! IP '{ip_addr}' shared with {graph_res['ip_cluster_size'] - 1} other customer accounts. Device identified as: '{graph_res.get('device_os')}'."
    elif scenario == "BORDERLINE_COD":
        flags.append("NEW_DEVICE_GEOLOCATION_UNMATCHED")
        result_thought = f"[CAUTION] Moderate graph risk: Single-user subnet '{ip_addr}' on {graph_res.get('device_os')}. No syndicate collision found, but first-time device signature."
    else:
        flags.append("ZERO_GRAPH_COLLISIONS")
        result_thought = f"[OK] Clean graph topology: Single trusted household connection on '{ip_addr}' ({graph_res.get('device_os')}). Zero proxy/emulator collisions."
        
    result_frame = {
        "event_type": "TOOL_RESULT",
        "agent_name": "GraphAgent",
        "transaction_id": txn_id,
        "thought": result_thought,
        "tool_name": "query_fraud_graph_tool",
        "tool_output": graph_res,
        "timestamp": time.time(),
        "data": {"flags_triggered": flags}
    }
    if emit_callback:
        await emit_callback(result_frame)
        
    return {
        "graph_data": graph_res,
        "flags": flags,
        "status": "ANALYZING_METADATA",
        "agent_thought_stream": [call_frame, result_frame]
    }

# ---------------------------------------------------------
# Node 4: NLP Metadata Analysis Node
# ---------------------------------------------------------
async def nlp_analysis_node(state: InvestigationState, emit_callback: StreamCallback = None) -> Dict[str, Any]:
    txn_id = state["transaction_id"]
    notes = state["transaction_data"].get("notes", "")
    order_cat = state["transaction_data"].get("order_category", "GENERAL")
    
    call_frame = {
        "event_type": "THINKING",
        "agent_name": "NLPAnalyzer",
        "transaction_id": txn_id,
        "thought": f"Parsing unstructured transaction memo & delivery notes: \"{notes if notes else '[No notes provided]'}\"...",
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(call_frame)
        
    nlp_res = await evaluate_nlp_metadata_tool(notes, order_cat)
    
    flags = []
    if nlp_res.get("urgency_level") == "CRITICAL":
        flags.append("SUSPICIOUS_RUSH_DROPOFF_MEMO")
    elif nlp_res.get("urgency_level") == "ELEVATED":
        flags.append("ELEVATED_URGENCY_KEYWORD")
        
    result_thought = (
        f"NLP analysis complete: Intent '{nlp_res.get('detected_intent')}' "
        f"(Risk: {int(nlp_res.get('nlp_risk_score', 0)*100)}%, Urgency: {nlp_res.get('urgency_level')}). "
        f"Trigger tokens: {nlp_res.get('flagged_keywords', [])}"
    )
    
    result_frame = {
        "event_type": "TOOL_RESULT",
        "agent_name": "NLPAnalyzer",
        "transaction_id": txn_id,
        "thought": result_thought,
        "tool_name": "evaluate_nlp_metadata_tool",
        "tool_output": nlp_res,
        "timestamp": time.time(),
        "data": {"nlp_flags": flags}
    }
    if emit_callback:
        await emit_callback(result_frame)
        
    return {
        "nlp_data": nlp_res,
        "flags": flags,
        "status": "SYNTHESIZING_DECISION",
        "agent_thought_stream": [call_frame, result_frame]
    }

# ---------------------------------------------------------
# Node 5: Decision Agent (Evidence Synthesis & Enforcement)
# ---------------------------------------------------------
async def decision_synthesis_node(state: InvestigationState, emit_callback: StreamCallback = None) -> Dict[str, Any]:
    txn_id = state["transaction_id"]
    txn = state["transaction_data"]
    history = state.get("history_data") or {}
    graph = state.get("graph_data") or {}
    nlp = state.get("nlp_data") or {}
    scenario = txn.get("scenario_type", "AUTO")
    flags = list(set(state.get("flags") or []))
    
    synth_frame = {
        "event_type": "THINKING",
        "agent_name": "DecisionAgent",
        "transaction_id": txn_id,
        "thought": "Synthesizing cross-agent evidence ledger (MongoDB historical baseline + Graph topology + NLP metadata vectors)...",
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(synth_frame)
        
    # Scenario-tailored dynamic score computation
    if scenario == "SYNDICATE_ATTACK" or graph.get("is_syndicate_detected") or history.get("historical_chargebacks", 0) >= 1:
        composite_score = round(random.uniform(82.0, 94.5), 1)
        verdict = "BLOCK"
        confidence = round(random.uniform(0.91, 0.98), 2)
        summary = (
            f"Autonomous Decision: BLOCK. Critical threat detected (Risk: {composite_score}/100, Confidence: {int(confidence*100)}%). "
            f"Customer '{state['customer_id']}' exhibits multi-account collision across {graph.get('ip_cluster_size', 4)} accounts on IP proxy '{txn.get('ip_address', '')}'. "
            f"History shows {history.get('historical_chargebacks', 1)} prior chargeback dispute and elevated {int(history.get('historical_rto_rate', 0.5)*100)}% RTO probability."
        )
        recommended_actions = [
            f"Blacklist IP proxy '{txn.get('ip_address', '')}' and device fingerprint",
            "Notify Merchant Risk Operations Team (High-Priority Flag)",
            "Freeze pending settlement authorization for customer entity"
        ]
    elif scenario == "BORDERLINE_COD" or (40.0 <= txn.get("amount", 0) and not history.get("kyc_verified")):
        composite_score = round(random.uniform(52.0, 68.5), 1)
        verdict = "TRIGGER_2FA"
        confidence = round(random.uniform(0.84, 0.92), 2)
        summary = (
            f"Autonomous Decision: TRIGGER_2FA. Moderate risk profile (Risk: {composite_score}/100, Confidence: {int(confidence*100)}%). "
            f"Customer '{state['customer_id']}' is a new account ({history.get('account_age_days', 6)} days) with unverified KYC and elevated COD amount (INR {txn.get('amount', 0):,.2f}). "
            f"Biometric 2FA liveness challenge dispatched prior to order dispatch."
        )
        recommended_actions = [
            "Issue 2FA Vision Liveness verification challenge to customer",
            "Hold settlement window open for 180 seconds",
            "Re-score transaction upon signed cryptographic token return"
        ]
    else: # Trusted User
        composite_score = round(random.uniform(12.0, 24.0), 1)
        verdict = "APPROVE"
        confidence = round(random.uniform(0.94, 0.99), 2)
        summary = (
            f"Autonomous Decision: APPROVE. Low risk profile (Risk: {composite_score}/100, Confidence: {int(confidence*100)}%). "
            f"Customer '{state['customer_id']}' has {history.get('account_age_days', 300)}+ days clean tenure with INR {history.get('lifetime_spend_inr', 100000):,.2f} lifetime spend, "
            f"0 chargebacks, and zero proxy collisions. Fast-track capture authorized."
        )
        recommended_actions = [
            "Immediate payment capture and instant warehouse dispatch",
            "Update customer loyalty trust index in MongoDB"
        ]
        
    final_frame = {
        "event_type": "DECISION_REACHED",
        "agent_name": "DecisionAgent",
        "transaction_id": txn_id,
        "thought": f"Final Verdict reached: [{verdict}] (Risk: {composite_score}/100, Confidence: {int(confidence*100)}%). {summary}",
        "timestamp": time.time(),
        "data": {
            "verdict": verdict,
            "composite_risk_score": composite_score,
            "confidence": confidence,
            "executive_summary": summary,
            "flags": flags,
            "recommended_actions": recommended_actions,
            "scenario": scenario
        }
    }
    
    if emit_callback:
        await emit_callback(final_frame)
        
    complete_frame = {
        "event_type": "INVESTIGATION_COMPLETE",
        "agent_name": "Supervisor",
        "transaction_id": txn_id,
        "thought": f"Investigation lifecycle complete for '{txn_id}'. Case records sealed and dispatched.",
        "timestamp": time.time(),
        "data": {"status": "SUCCESS", "verdict": verdict}
    }
    if emit_callback:
        await emit_callback(complete_frame)
        
    return {
        "verdict": verdict,
        "composite_risk_score": composite_score,
        "confidence": confidence,
        "executive_summary": summary,
        "flags": flags,
        "recommended_actions": recommended_actions,
        "investigation_end_time": time.time(),
        "status": "COMPLETED",
        "agent_thought_stream": [synth_frame, final_frame, complete_frame]
    }

# ---------------------------------------------------------
# Dynamic Subgraph Generator for Visualizer
# ---------------------------------------------------------
def generate_dynamic_subgraph(scenario: str, customer_id: str, ip_address: str, device_fp: str) -> Dict[str, Any]:
    nodes = []
    edges = []
    
    if scenario == "SYNDICATE_ATTACK":
        nodes = [
            {"id": "ip_proxy", "label": f"{ip_address} (Datacenter Proxy)", "type": "IP", "clusterRisk": round(random.uniform(0.88, 0.96), 2), "x": 240, "y": 190, "radius": 18, "isSyndicate": True},
            {"id": "dfp_emu", "label": f"{device_fp} (Headless Emu)", "type": "DEVICE", "clusterRisk": round(random.uniform(0.92, 0.98), 2), "x": 310, "y": 270, "radius": 16, "isSyndicate": True},
            {"id": "cust_target", "label": f"{customer_id} (Investigated)", "type": "CUSTOMER", "clusterRisk": round(random.uniform(0.85, 0.94), 2), "x": 160, "y": 270, "radius": 15, "isSyndicate": True},
            {"id": "cust_syn_2", "label": f"cust_syndicate_{random.randint(10,49)}", "type": "CUSTOMER", "clusterRisk": 0.89, "x": 370, "y": 190, "radius": 12, "isSyndicate": True},
            {"id": "cust_syn_3", "label": f"cust_syndicate_{random.randint(50,99)}", "type": "CUSTOMER", "clusterRisk": 0.91, "x": 300, "y": 110, "radius": 12, "isSyndicate": True},
            {"id": "card_stolen", "label": f"card_bin_{random.randint(4000, 5999)} (Stolen BIN)", "type": "CARD", "clusterRisk": 0.95, "x": 170, "y": 130, "radius": 13, "isSyndicate": True},
        ]
        edges = [
            {"source": "cust_target", "target": "ip_proxy"},
            {"source": "cust_target", "target": "dfp_emu"},
            {"source": "cust_target", "target": "card_stolen"},
            {"source": "cust_syn_2", "target": "ip_proxy"},
            {"source": "cust_syn_2", "target": "dfp_emu"},
            {"source": "cust_syn_3", "target": "ip_proxy"},
            {"source": "cust_syn_3", "target": "card_stolen"},
        ]
    elif scenario == "BORDERLINE_COD":
        nodes = [
            {"id": "ip_mobile", "label": f"{ip_address} (Jio Mobile 5G)", "type": "IP", "clusterRisk": round(random.uniform(0.25, 0.38), 2), "x": 350, "y": 200, "radius": 16, "isSyndicate": False},
            {"id": "dfp_phone", "label": f"{device_fp} (Android 14)", "type": "DEVICE", "clusterRisk": round(random.uniform(0.20, 0.32), 2), "x": 420, "y": 280, "radius": 14, "isSyndicate": False},
            {"id": "cust_cod", "label": f"{customer_id} (New Account)", "type": "CUSTOMER", "clusterRisk": round(random.uniform(0.48, 0.65), 2), "x": 280, "y": 280, "radius": 14, "isSyndicate": False},
        ]
        edges = [
            {"source": "cust_cod", "target": "ip_mobile"},
            {"source": "cust_cod", "target": "dfp_phone"},
        ]
    else: # TRUSTED_USER
        nodes = [
            {"id": "ip_home", "label": f"{ip_address} (Airtel Fiber)", "type": "IP", "clusterRisk": 0.02, "x": 580, "y": 210, "radius": 16, "isSyndicate": False},
            {"id": "dfp_mac", "label": f"{device_fp} (macOS Safari)", "type": "DEVICE", "clusterRisk": 0.01, "x": 650, "y": 290, "radius": 14, "isSyndicate": False},
            {"id": "cust_vip", "label": f"{customer_id} (Platinum VIP)", "type": "CUSTOMER", "clusterRisk": 0.02, "x": 510, "y": 290, "radius": 15, "isSyndicate": False},
            {"id": "card_vip", "label": "card_hdfc_infinia", "type": "CARD", "clusterRisk": 0.01, "x": 580, "y": 360, "radius": 12, "isSyndicate": False},
        ]
        edges = [
            {"source": "cust_vip", "target": "ip_home"},
            {"source": "cust_vip", "target": "dfp_mac"},
            {"source": "cust_vip", "target": "card_vip"},
        ]
        
    return {"nodes": nodes, "edges": edges}

# ---------------------------------------------------------
# Streaming Runner for WebSockets & REST
# ---------------------------------------------------------
async def execute_agent_investigation(
    transaction_id: str,
    customer_id: str,
    merchant_id: str,
    transaction_data: Dict[str, Any],
    emit_callback: StreamCallback = None
) -> InvestigationResult:
    start_time = time.time()
    scenario = transaction_data.get("scenario_type", "AUTO")
    
    state: InvestigationState = {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "merchant_id": merchant_id,
        "transaction_data": transaction_data,
        "history_data": None,
        "graph_data": None,
        "nlp_data": None,
        "ml_score_data": {"fraud_prob": transaction_data.get("ml_fraud_score", 0.35)},
        "agent_thought_stream": [],
        "verdict": None,
        "composite_risk_score": None,
        "confidence": None,
        "executive_summary": None,
        "flags": [],
        "recommended_actions": [],
        "investigation_start_time": start_time,
        "investigation_end_time": None,
        "status": "INITIALIZED",
        "error": None
    }
    
    res1 = await supervisor_node(state, emit_callback)
    state.update(res1)
    
    res2 = await data_retrieval_node(state, emit_callback)
    state.update(res2)
    
    res3 = await graph_investigation_node(state, emit_callback)
    state.update(res3)
    
    res4 = await nlp_analysis_node(state, emit_callback)
    state.update(res4)
    
    res5 = await decision_synthesis_node(state, emit_callback)
    state.update(res5)
    
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    # Generate dynamic graph network for visualizer
    subgraph = generate_dynamic_subgraph(
        scenario=state["verdict"] if state["verdict"] in ["SYNDICATE_ATTACK", "BORDERLINE_COD", "TRUSTED_USER"] else (
            "SYNDICATE_ATTACK" if state["verdict"] == "BLOCK" else (
                "BORDERLINE_COD" if state["verdict"] == "TRIGGER_2FA" else "TRUSTED_USER"
            )
        ),
        customer_id=state["customer_id"],
        ip_address=transaction_data.get("ip_address", "103.21.124.89"),
        device_fp=transaction_data.get("device_fingerprint", "dfp_a7b29c011e4")
    )
    
    return InvestigationResult(
        transaction_id=state["transaction_id"],
        customer_id=state["customer_id"],
        merchant_id=state["merchant_id"],
        verdict=state["verdict"] or "APPROVE",
        composite_risk_score=state["composite_risk_score"] or 0.0,
        confidence=state["confidence"] or 0.9,
        executive_summary=state["executive_summary"] or "",
        flags=list(set(state["flags"])),
        recommended_actions=list(set(state["recommended_actions"])),
        evidence_breakdown={
            "history": state["history_data"],
            "graph": state["graph_data"],
            "nlp": state["nlp_data"],
            "subgraph": subgraph
        },
        thought_trail=state["agent_thought_stream"],
        investigation_duration_ms=duration_ms,
        status="COMPLETED"
    )

def create_investigation_graph():
    workflow = StateGraph(InvestigationState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("data_retrieval", data_retrieval_node)
    workflow.add_node("graph_investigation", graph_investigation_node)
    workflow.add_node("nlp_analysis", nlp_analysis_node)
    workflow.add_node("decision_synthesis", decision_synthesis_node)
    
    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "data_retrieval")
    workflow.add_edge("data_retrieval", "graph_investigation")
    workflow.add_edge("graph_investigation", "nlp_analysis")
    workflow.add_edge("nlp_analysis", "decision_synthesis")
    workflow.add_edge("decision_synthesis", END)
    
    return workflow.compile()
