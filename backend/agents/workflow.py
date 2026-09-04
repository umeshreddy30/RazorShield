# backend/agents/workflow.py
import asyncio
import time
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
    
    thought_text = f"Supervisor: New case received for txn '{txn_id}' (Customer: '{cust_id}', Amount: INR {txn.get('amount', 0):,.2f}). Dispatching autonomous agents for deep investigation."
    
    frame = {
        "event_type": "AGENT_ASSIGNED",
        "agent_name": "Supervisor",
        "transaction_id": txn_id,
        "thought": thought_text,
        "timestamp": time.time(),
        "data": {
            "assigned_agents": ["DataRetrievalAgent", "GraphAgent", "NLPAnalyzer", "DecisionAgent"],
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
    
    # 1. Thought: Initiating query
    call_frame = {
        "event_type": "TOOL_INVOKED",
        "agent_name": "DataRetrievalAgent",
        "transaction_id": txn_id,
        "thought": f"Querying MongoDB collections 'customer_profiles' and 'transaction_logs' for historical behavior of '{cust_id}'...",
        "tool_name": "fetch_user_history_tool",
        "tool_args": {"customer_id": cust_id, "email": email},
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(call_frame)
        
    history = await fetch_user_history_tool(cust_id, email)
    
    # Evaluate flags
    flags = []
    if history.get("historical_chargebacks", 0) > 0:
        flags.append(f"PRIOR_CHARGEBACK_HISTORY_{history['historical_chargebacks']}")
    if history.get("historical_rto_rate", 0) >= 0.35:
        flags.append(f"ELEVATED_RTO_RISK_{int(history['historical_rto_rate']*100)}PCT")
    if history.get("account_age_days", 999) < 5:
        flags.append("FRESH_ACCOUNT_UNDER_5_DAYS")
        
    result_frame = {
        "event_type": "TOOL_RESULT",
        "agent_name": "DataRetrievalAgent",
        "transaction_id": txn_id,
        "thought": f"MongoDB query complete: Found {history.get('total_lifetime_orders', 0)} lifetime transactions, {history.get('historical_chargebacks', 0)} prior chargebacks, {history.get('historical_rto_rate', 0)*100:.0f}% historical RTO rate.",
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
    ip_addr = state["transaction_data"].get("ip_address", "127.0.0.1")
    device_fp = state["transaction_data"].get("device_fingerprint", "dfp_default")
    
    call_frame = {
        "event_type": "TOOL_INVOKED",
        "agent_name": "GraphAgent",
        "transaction_id": txn_id,
        "thought": f"Executing graph cluster traversal on IP '{ip_addr}' and Device Fingerprint '{device_fp}' for shared syndicate nodes...",
        "tool_name": "query_fraud_graph_tool",
        "tool_args": {"ip_address": ip_addr, "device_fingerprint": device_fp},
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(call_frame)
        
    graph_res = await query_fraud_graph_tool(ip_addr, device_fp)
    
    flags = []
    if graph_res.get("is_syndicate_detected"):
        flags.append("FRAUD_RING_SYNDICATE_MATCH")
    if graph_res.get("ip_cluster_size", 1) >= 3:
        flags.append(f"SHARED_IP_CLUSTER_{graph_res['ip_cluster_size']}_USERS")
    if graph_res.get("device_is_emulator"):
        flags.append("EMULATOR_BROWSER_FINGERPRINT")
        
    result_frame = {
        "event_type": "TOOL_RESULT",
        "agent_name": "GraphAgent",
        "transaction_id": txn_id,
        "thought": f"Graph analysis concluded: {'[ALERT] HIGH RISK: Syndicate collision detected across multiple customer IDs!' if graph_res.get('is_syndicate_detected') else '[OK] Low graph collision. No active ring detected.'}",
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
        "thought": f"Parsing unstructured notes and order context: \"{notes if notes else '[No notes provided]'}\"...",
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(call_frame)
        
    nlp_res = await evaluate_nlp_metadata_tool(notes, order_cat)
    
    flags = []
    if nlp_res.get("urgency_level") == "CRITICAL":
        flags.append("ANOMALOUS_URGENCY_KEYWORDS")
        
    result_frame = {
        "event_type": "TOOL_RESULT",
        "agent_name": "NLPAnalyzer",
        "transaction_id": txn_id,
        "thought": f"NLP scan complete. Intent: {nlp_res.get('detected_intent')}, Risk: {nlp_res.get('nlp_risk_score')*100:.0f}%, Trigger words: {nlp_res.get('flagged_keywords')}",
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
    flags = list(set(state.get("flags") or []))
    
    # 1. Synthesis Thought
    synth_frame = {
        "event_type": "THINKING",
        "agent_name": "DecisionAgent",
        "transaction_id": txn_id,
        "thought": "Synthesizing full evidence ledger (MongoDB historical baseline + Graph entity clusters + NLP risk signals)...",
        "timestamp": time.time()
    }
    if emit_callback:
        await emit_callback(synth_frame)
        
    # Calculate composite score from agent evidence
    base_ml_score = state.get("ml_score_data", {}).get("fraud_prob", 0.3)
    graph_risk = graph.get("ip_cluster_risk", 0.1)
    nlp_risk = nlp.get("nlp_risk_score", 0.05)
    rto_risk = history.get("historical_rto_rate", 0.0)
    
    composite_score = (base_ml_score * 40.0) + (graph_risk * 35.0) + (nlp_risk * 15.0) + (rto_risk * 10.0)
    
    # Trigger overrides
    if graph.get("is_syndicate_detected") or history.get("historical_chargebacks", 0) >= 2:
        composite_score = max(composite_score, 88.5)
        
    composite_score = round(min(100.0, max(0.0, composite_score)), 1)
    confidence = round(0.85 + (len(flags) * 0.03), 2)
    confidence = min(0.99, confidence)
    
    recommended_actions = []
    
    if composite_score >= 75.0:
        verdict = "BLOCK"
        summary = (
            f"Autonomous Decision: BLOCK. Transaction exhibits severe risk factors ({composite_score}/100). "
            f"Key drivers: {', '.join(flags[:3]) if flags else 'Anomalous velocity and entity linkage'}. "
            f"Linked to high-risk cluster with {graph.get('ip_cluster_size', 1)} associated accounts."
        )
        recommended_actions.extend([
            "Blacklist device fingerprint and IP address",
            "Notify merchant risk operations team",
            "Freeze pending settlements for customer entity"
        ])
    elif composite_score >= 40.0:
        verdict = "TRIGGER_2FA"
        summary = (
            f"Autonomous Decision: TRIGGER_2FA. Moderate risk detected ({composite_score}/100). "
            f"New account or elevated velocity detected. Liveness and biometric challenge recommended prior to capture."
        )
        recommended_actions.extend([
            "Issue 2FA Liveness verification prompt to user",
            "Hold authorization window open for 180 seconds",
            "Re-evaluate risk upon challenge completion"
        ])
    else:
        verdict = "APPROVE"
        summary = (
            f"Autonomous Decision: APPROVE. Low risk profile ({composite_score}/100). "
            f"Customer has clean historical tenure and no syndicate collisions. Fast-track settlement approved."
        )
        recommended_actions.extend([
            "Immediate capture and settlement",
            "Log positive trust telemetry into MongoDB"
        ])
        
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
            "recommended_actions": recommended_actions
        }
    }
    
    if emit_callback:
        await emit_callback(final_frame)
        
    complete_frame = {
        "event_type": "INVESTIGATION_COMPLETE",
        "agent_name": "Supervisor",
        "transaction_id": txn_id,
        "thought": "Investigation lifecycle concluded. Case records sealed and dispatched.",
        "timestamp": time.time(),
        "data": {"status": "SUCCESS"}
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
# Build LangGraph StateGraph
# ---------------------------------------------------------
def create_investigation_graph():
    builder = StateGraph(InvestigationState)
    
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("data_retrieval", data_retrieval_node)
    builder.add_node("graph_investigation", graph_investigation_node)
    builder.add_node("nlp_analysis", nlp_analysis_node)
    builder.add_node("decision_synthesis", decision_synthesis_node)
    
    builder.set_entry_point("supervisor")
    builder.add_edge("supervisor", "data_retrieval")
    builder.add_edge("data_retrieval", "graph_investigation")
    builder.add_edge("graph_investigation", "nlp_analysis")
    builder.add_edge("nlp_analysis", "decision_synthesis")
    builder.add_edge("decision_synthesis", END)
    
    return builder.compile()

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
    
    # Execute sequential agent nodes with live event streaming
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
            "nlp": state["nlp_data"]
        },
        thought_trail=state["agent_thought_stream"],
        investigation_duration_ms=duration_ms,
        status="COMPLETED"
    )
