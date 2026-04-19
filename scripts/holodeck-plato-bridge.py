#!/usr/bin/env python3
"""
Holodeck to PLATO Bridge — fills the integration gap.
"""
import json, urllib.request, hashlib, socket

PLATO_URL = "http://localhost:8847"
HOLODECK_HOST = "localhost"
HOLODECK_PORT = 7778

def submit_tile(tile):
    body = json.dumps(tile).encode()
    req = urllib.request.Request(PLATO_URL + "/submit",
        data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def query_holodeck(command):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((HOLODECK_HOST, HOLODECK_PORT))
        s.recv(4096)
        s.send((command + "\n").encode())
        response = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                response += chunk
            except socket.timeout: break
        s.close()
        return response.decode("utf-8", errors="replace")
    except Exception as e:
        return "[ERROR] " + str(e)

def harvest():
    submitted = 0
    accepted = 0
    
    response = query_holodeck("look")
    rooms = [l.strip() for l in response.split("\n") if l.strip() and not l.startswith("[")]
    
    if response and not response.startswith("[ERROR]"):
        tile = {
            "domain": "holodeck",
            "question": "Holodeck room state snapshot",
            "answer": "Active rooms found in holodeck: " + ", ".join(rooms[:5]) + ". " + response[:200].strip() + ". The holodeck is a sentiment-aware MUD server where rooms are live systems connected to the PLATO training pipeline.",
            "tags": ["holodeck", "room_state", "fleet"],
            "confidence": 0.7,
            "source": "holodeck:bridge",
        }
        result = submit_tile(tile)
        submitted += 1
        if result.get("status") == "accepted": accepted += 1
    
    fleet_resp = query_holodeck("fleet")
    if fleet_resp and not fleet_resp.startswith("[ERROR]"):
        tile = {
            "domain": "holodeck",
            "question": "Fleet status from holodeck",
            "answer": "Fleet: " + fleet_resp[:300] + ". Holodeck tracks agent positions.",
            "tags": ["holodeck", "fleet"],
            "confidence": 0.6,
            "source": "holodeck:fleet",
        }
        result = submit_tile(tile)
        submitted += 1
        if result.get("status") == "accepted": accepted += 1
    
    return submitted, accepted

if __name__ == "__main__":
    s, a = harvest()
    print("Holodeck-PLATO Bridge: " + str(a) + "/" + str(s) + " accepted")
    resp = urllib.request.urlopen(PLATO_URL + "/status", timeout=5)
    d = json.loads(resp.read())
    print("PLATO total: " + str(d["total_tiles"]) + " tiles")
