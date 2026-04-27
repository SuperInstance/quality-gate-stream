#!/usr/bin/env python3
"""
Grammar Compactor Resync Script
Forces the Grammar Compactor to pull full rule set from Grammar Engine
before evaluating. Fixes the 54 vs 429 rule blind spot.
"""
import json
import urllib.request

ENGINE_URL = "http://147.224.38.131:4045/grammar"
COMPACTOR_URL = "http://147.224.38.131:4055/compact"

def fetch_engine_rules():
    """Pull full grammar state from engine."""
    try:
        with urllib.request.urlopen(ENGINE_URL, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("rules", [])
    except Exception as e:
        print(f"ERROR: Could not reach Grammar Engine: {e}")
        return []

def trigger_compaction():
    """Trigger compactor with fresh data."""
    try:
        req = urllib.request.Request(
            COMPACTOR_URL,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"ERROR: Could not trigger compaction: {e}")
        return {}

if __name__ == "__main__":
    print("=== Grammar Compactor Resync ===")
    
    rules = fetch_engine_rules()
    print(f"Engine rules fetched: {len(rules)}")
    
    if not rules:
        print("FAIL: No rules from engine. Is 4045 up?")
        exit(1)
    
    result = trigger_compaction()
    print(f"Compaction result: {result}")
    
    # Verify
    try:
        with urllib.request.urlopen("http://147.224.38.131:4055/status", timeout=10) as r:
            status = json.loads(r.read().decode())
            compact_rules = status.get("total_rules", 0)
            print(f"Compactor now sees: {compact_rules} rules")
            if compact_rules >= len(rules) * 0.9:
                print("SUCCESS: Compactor resynced")
            else:
                print(f"WARNING: Still blind ({compact_rules}/{len(rules)})")
    except Exception as e:
        print(f"ERROR checking status: {e}")
