# backend/agents/tools.py
import asyncio
import time
import os
import re
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Client Setup with graceful in-memory fallback
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client: Optional[AsyncIOMotorClient] = None
db: Optional[Any] = None

try:
    mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=1000)
    db = mongo_client["razorshield_db"]
except Exception:
    mongo_client = None
    db = None

# Mock Database Store for fallback / demo execution
MOCK_CUSTOMER_PROFILES: Dict[str, Dict[str, Any]] = {
    "cust_88129": {
        "customer_id": "cust_88129",
        "account_age_days": 12,
        "total_lifetime_orders": 4,
        "lifetime_spend_inr": 8200.0,
        "historical_chargebacks": 1,
        "historical_rto_count": 2,
        "historical_rto_rate": 0.50,
        "known_ips": ["103.21.124.89", "103.21.124.90"],
        "known_devices": ["dfp_a7b29c011e4"],
        "kyc_verified": False,
        "risk_tier": "HIGH"
    },
    "cust_trusted_01": {
        "customer_id": "cust_trusted_01",
        "account_age_days": 420,
        "total_lifetime_orders": 38,
        "lifetime_spend_inr": 142000.0,
        "historical_chargebacks": 0,
        "historical_rto_count": 1,
        "historical_rto_rate": 0.026,
        "known_ips": ["49.207.210.12"],
        "known_devices": ["dfp_mac_9921"],
        "kyc_verified": True,
        "risk_tier": "LOW"
    }
}

MOCK_FRAUD_RING_GRAPH: Dict[str, Dict[str, Any]] = {
    "103.21.124.89": {
        "ip_address": "103.21.124.89",
        "associated_customers": ["cust_88129", "cust_syndicate_02", "cust_syndicate_03", "cust_bot_99"],
        "associated_cards": ["card_hash_8821", "card_hash_9901", "card_hash_1102"],
        "total_attempts_24h": 18,
        "is_datacenter_proxy": True,
        "threat_cluster_score": 0.89
    },
    "dfp_a7b29c011e4": {
        "device_fingerprint": "dfp_a7b29c011e4",
        "associated_customers": ["cust_88129", "cust_syndicate_02"],
        "device_os": "Linux / Headless Chrome",
        "is_emulator": True,
        "threat_cluster_score": 0.94
    }
}

async def fetch_user_history_tool(customer_id: str, email: str = "") -> Dict[str, Any]:
    """
    Data Retrieval Agent Tool:
    Autonomously queries MongoDB for customer history, velocity, dispute metrics, and past chargebacks.
    """
    await asyncio.sleep(0.18)  # simulate DB network trip
    
    # 1. Attempt live MongoDB query if active
    if db is not None:
        try:
            profile = await db.customer_profiles.find_one({"customer_id": customer_id})
            if profile:
                profile["_id"] = str(profile["_id"])
                return {"source": "mongodb_live", "data": profile}
        except Exception:
            pass  # Fall back to simulated profile
            
    # 2. Mock / In-Memory Profile Fallback
    if customer_id in MOCK_CUSTOMER_PROFILES:
        profile = MOCK_CUSTOMER_PROFILES[customer_id]
        return {
            "source": "mongodb_mock_store",
            "customer_id": customer_id,
            "account_age_days": profile["account_age_days"],
            "total_lifetime_orders": profile["total_lifetime_orders"],
            "lifetime_spend_inr": profile["lifetime_spend_inr"],
            "historical_chargebacks": profile["historical_chargebacks"],
            "historical_rto_rate": profile["historical_rto_rate"],
            "kyc_verified": profile["kyc_verified"],
            "risk_tier": profile["risk_tier"]
        }
    
    # Dynamic profile for new/unknown customer IDs
    return {
        "source": "mongodb_new_account",
        "customer_id": customer_id,
        "account_age_days": 1.0,
        "total_lifetime_orders": 1,
        "lifetime_spend_inr": 0.0,
        "historical_chargebacks": 0,
        "historical_rto_rate": 0.0,
        "kyc_verified": False,
        "risk_tier": "UNVERIFIED"
    }

async def query_fraud_graph_tool(ip_address: str, device_fingerprint: str) -> Dict[str, Any]:
    """
    Fraud Ring Graph Agent Tool:
    Traverses graph entity relationships across shared IPs, device fingerprints, and payment instruments.
    """
    await asyncio.sleep(0.15)
    
    ip_data = MOCK_FRAUD_RING_GRAPH.get(ip_address, {
        "ip_address": ip_address,
        "associated_customers": [1],
        "associated_cards": [1],
        "total_attempts_24h": 1,
        "is_datacenter_proxy": False,
        "threat_cluster_score": 0.05
    })
    
    device_data = MOCK_FRAUD_RING_GRAPH.get(device_fingerprint, {
        "device_fingerprint": device_fingerprint,
        "associated_customers": [1],
        "device_os": "Standard Browser",
        "is_emulator": False,
        "threat_cluster_score": 0.05
    })
    
    is_syndicate = (
        len(ip_data.get("associated_customers", [])) >= 3
        or device_data.get("is_emulator", False)
        or ip_data.get("threat_cluster_score", 0) > 0.7
    )
    
    return {
        "is_syndicate_detected": is_syndicate,
        "ip_cluster_size": len(ip_data.get("associated_customers", [])),
        "ip_is_proxy": ip_data.get("is_datacenter_proxy", False),
        "device_is_emulator": device_data.get("is_emulator", False),
        "ip_cluster_risk": ip_data.get("threat_cluster_score", 0.05),
        "device_cluster_risk": device_data.get("threat_cluster_score", 0.05),
        "connected_accounts": list(set(ip_data.get("associated_customers", []) + device_data.get("associated_customers", [])))
    }

async def evaluate_nlp_metadata_tool(notes: str, order_category: str = "") -> Dict[str, Any]:
    """
    NLP Metadata Risk Analyzer Tool:
    Runs semantic keyword and sentiment extraction on order notes, shipping instructions, and merchant memos.
    """
    await asyncio.sleep(0.12)
    if not notes:
        return {
            "nlp_risk_score": 0.05,
            "detected_intent": "STANDARD_ORDER",
            "flagged_keywords": [],
            "urgency_level": "LOW"
        }
    
    notes_lower = notes.lower()
    high_risk_triggers = ["urgent", "rush", "overnight", "dont call", "gift receiver", "bypass", "leave outside", "fast dispatch", "hotel room", "fake"]
    matched = [w for w in high_risk_triggers if re.search(r'\b' + re.escape(w) + r'\b', notes_lower)]
    
    risk_score = min(0.95, 0.2 + len(matched) * 0.35) if matched else 0.10
    urgency = "CRITICAL" if len(matched) >= 2 else ("ELEVATED" if matched else "NORMAL")
    
    return {
        "nlp_risk_score": round(risk_score, 2),
        "detected_intent": "SUSPICIOUS_URGENCY" if matched else "LEGITIMATE_NOTE",
        "flagged_keywords": matched,
        "urgency_level": urgency
    }
