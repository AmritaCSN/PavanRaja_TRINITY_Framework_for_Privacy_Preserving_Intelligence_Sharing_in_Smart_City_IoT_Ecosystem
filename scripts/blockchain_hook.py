#!/usr/bin/env python3.10
"""
TRINITY FRAMEWORK — Phase 6: Blockchain Integration
blockchain_hook.py — SHA-256 model hashing + Fabric ledger recording

After each FL aggregation round:
  1. Serialize global model weights
  2. Compute SHA-256 hash
  3. POST to API Bridge /submit-hash → Hyperledger Fabric city-intel-channel
  4. Log TxID per round
"""
import hashlib,json,logging,time,requests,io,sys
from pathlib import Path
import torch,numpy as np

log=logging.getLogger('TRINITY.blockchain')
API_BASE='http://localhost:3000'

def hash_model(state_dict) -> str:
    """SHA-256 of serialized model weights (deterministic)."""
    buf=io.BytesIO()
    torch.save(state_dict, buf)
    return hashlib.sha256(buf.getvalue()).hexdigest()

def submit_to_fabric(round_num, model_hash, algo, privacy_mode,
                     epsilon_spent, global_accuracy, global_f1, latency_seconds,
                     participants=None, timeout=10):
    """POST model hash to API Bridge → Hyperledger Fabric."""
    if participants is None:
        participants=['site-1','site-2','site-3']
    payload={
        'round':          round_num,
        'model_hash':     model_hash,
        'participants':   participants,
        'algorithm':      algo,
        'privacy_mode':   privacy_mode,
        'epsilon_spent':  epsilon_spent or 0.0,
        'global_accuracy':global_accuracy,
        'global_f1':      global_f1,
        'latency_seconds':latency_seconds,
        'metadata':       {'framework':'TRINITY','version':'1.0'},
    }
    try:
        r=requests.post(f'{API_BASE}/submit-hash',json=payload,timeout=timeout)
        if r.status_code==201:
            data=r.json()
            log.info(f"  Blockchain: round={round_num} tx_id={data.get('tx_id','N/A')[:16]}...")
            return data.get('tx_id'), data.get('ledger_key')
        else:
            log.warning(f"  Blockchain API error {r.status_code}: {r.text[:100]}")
            return None, None
    except requests.exceptions.ConnectionError:
        log.warning(f"  Blockchain API unreachable — recording hash locally only")
        return None, None
    except Exception as e:
        log.warning(f"  Blockchain submit error: {e}")
        return None, None

def verify_hash(round_num, claimed_hash, timeout=10):
    """Verify a model hash against the Fabric ledger."""
    try:
        r=requests.post(f'{API_BASE}/verify-hash',
                        json={'round':round_num,'claimed_hash':claimed_hash},
                        timeout=timeout)
        if r.status_code==200:
            return r.json()
        return {'match':False,'error':r.text}
    except Exception as e:
        return {'match':False,'error':str(e)}

def get_audit_summary(timeout=10):
    """Retrieve audit summary from Fabric ledger."""
    try:
        r=requests.get(f'{API_BASE}/audit-summary',timeout=timeout)
        return r.json() if r.status_code==200 else {}
    except:
        return {}
