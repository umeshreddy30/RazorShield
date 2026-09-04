# backend/test_multi_agent.py
import asyncio
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents.workflow import execute_agent_investigation

async def run_test():
    print("[TEST] Starting Multi-Agent Investigation Unit Test...")
    events_received = []

    async def log_callback(event):
        events_received.append(event)
        print(f"[{event.get('agent_name', 'AGENT')}] ({event.get('event_type')}) -> {event.get('thought')}")

    test_payload = {
        "transaction_id": "txn_test_agent_001",
        "customer_id": "cust_88129",
        "merchant_id": "mer_test_01",
        "amount": 45000.0,
        "customer_email": "syndicate_member@tempmail.com",
        "ip_address": "103.21.124.89",
        "device_fingerprint": "dfp_a7b29c011e4",
        "notes": "Urgent rush dispatch, leave with neighbor",
        "is_vpn_proxy": True,
        "ml_fraud_score": 0.88
    }

    result = await execute_agent_investigation(
        transaction_id=test_payload["transaction_id"],
        customer_id=test_payload["customer_id"],
        merchant_id=test_payload["merchant_id"],
        transaction_data=test_payload,
        emit_callback=log_callback
    )

    print("\n" + "="*60)
    print(" INVESTIGATION COMPLETED SUCCESSFULLY")
    print("="*60)
    print(f"Verdict: {result.verdict}")
    print(f"Composite Risk Score: {result.composite_risk_score}/100")
    print(f"Confidence: {result.confidence*100:.0f}%")
    print(f"Executive Summary: {result.executive_summary}")
    print(f"Flags Triggered: {result.flags}")
    print(f"Recommended Actions: {result.recommended_actions}")
    print(f"Total Agent Frames Emitted: {len(events_received)}")
    print(f"Investigation Duration: {result.investigation_duration_ms} ms")
    
    assert result.verdict in ["BLOCK", "TRIGGER_2FA", "APPROVE"], "Invalid verdict returned"
    assert len(events_received) >= 5, "Expected at least 5 agent thought events"
    print("\n[SUCCESS] All multi-agent assertions passed!")

if __name__ == "__main__":
    asyncio.run(run_test())
