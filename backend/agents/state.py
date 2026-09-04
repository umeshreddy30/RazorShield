# backend/agents/state.py
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field
import operator
from typing import Annotated

class AgentThoughtFrame(BaseModel):
    event_type: str = Field(..., description="Type of event: AGENT_ASSIGNED, THINKING, TOOL_INVOKED, TOOL_RESULT, DECISION_REACHED, INVESTIGATION_COMPLETE")
    agent_name: str = Field(..., description="Agent triggering event: Supervisor, DataRetrievalAgent, GraphAgent, NLPAnalyzer, DecisionAgent")
    transaction_id: str
    thought: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    timestamp: float
    data: Optional[Dict[str, Any]] = None

class InvestigationResult(BaseModel):
    transaction_id: str
    customer_id: str
    merchant_id: str
    verdict: str  # "APPROVE", "BLOCK", "TRIGGER_2FA"
    composite_risk_score: float  # 0.0 to 100.0
    confidence: float  # 0.0 to 1.0
    executive_summary: str
    flags: List[str]
    recommended_actions: List[str]
    evidence_breakdown: Dict[str, Any]
    thought_trail: List[Dict[str, Any]]
    investigation_duration_ms: float
    status: str

class InvestigationState(TypedDict):
    transaction_id: str
    customer_id: str
    merchant_id: str
    transaction_data: Dict[str, Any]
    history_data: Optional[Dict[str, Any]]
    graph_data: Optional[Dict[str, Any]]
    nlp_data: Optional[Dict[str, Any]]
    ml_score_data: Optional[Dict[str, Any]]
    agent_thought_stream: Annotated[List[Dict[str, Any]], operator.add]
    verdict: Optional[str]
    composite_risk_score: Optional[float]
    confidence: Optional[float]
    executive_summary: Optional[str]
    flags: Annotated[List[str], operator.add]
    recommended_actions: Annotated[List[str], operator.add]
    investigation_start_time: float
    investigation_end_time: Optional[float]
    status: str
    error: Optional[str]
