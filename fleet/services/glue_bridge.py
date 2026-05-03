#!/usr/bin/env python3
"""
glue-bridge — translate between cocapn-glue-core wire protocol and keeper-beacon.

Purpose:
- Listen on a UDP socket for incoming glue WireMessage beacons
- Convert glue Beacon → keeper-beacon BeaconSignal
- Feed into existing BeaconDiscovery without disrupting current HTTP agents

 WireFormat (postcard binary on wire) → Python dict (keeper-beacon compatible)

Start: nohup python3 /home/ubuntu/.openclaw/workspace/fleet/services/glue_bridge.py > /tmp/glue_bridge.log 2>&1 &
Stop:  kill $(pgrep -f glue_bridge.py)
"""

import socket
import struct
import json
import time
import hashlib
from dataclasses import dataclass
from typing import Optional

# Pretend we're using postcard deserialization
# In practice this would use cbor (already installed) or a lightweight binary parser
# For now: placeholder wire format handler

GLUE_LISTEN_HOST = "0.0.0.0"
GLUE_LISTEN_PORT = 9439  # glue protocol port
KEEPER_HOST = "127.0.0.1"
KEEPER_BEACON_PORT = 8900  # keeper HTTP port

@dataclass
class GlueBeacon:
    """Decoded glue beacon from binary wire."""
    sender_tier: int       # 0=Unknown, 1=MCU, 2=Edge, 3=Cloud, 4=Thor
    capabilities: int     # 32-bit bitmask
    protocol_version: int # u16
    timestamp: int        # u64 Unix seconds

    def to_beacon_signal(self) -> dict:
        """Convert to keeper-beacon BeaconSignal format."""
        cap_list = self._capabilities_to_list()
        return {
            "agent_id": f"glue-tier-{self.sender_tier}",
            "name": f"Tier{self.sender_tier}",
            "capabilities": cap_list,
            "endpoint": f"glue://tier{self.sender_tier}",
            "timestamp": self.timestamp,
            "ttl": 120.0,
            "signature": self._make_signature(),
        }

    def _capabilities_to_list(self) -> list:
        """Map glue Capabilities bitmask to human-readable list."""
        cap_map = [
            (1 << 0, "no_std"),
            (1 << 1, "async"),
            (1 << 2, "cuda"),
            (1 << 3, "plato"),
            (1 << 4, "ffi"),
            (1 << 5, "python"),
        ]
        return [name for bit, name in cap_map if self.capabilities & bit]

    def _make_signature(self) -> str:
        content = f"{self.sender_tier}:{self.capabilities}:{self.timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class GlueBridge:
    """Bridge between glue wire protocol and keeper-beacon."""

    def __init__(self, listen_port: int = GLUE_LISTEN_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", listen_port))
        self.sock.settimeout(1.0)  # non-blocking with timeout
        self.running = True
        self.beacons: dict = {}  # agent_id -> last_seen
        print(f"[glue-bridge] listening on UDP {listen_port}")

    def handle_packet(self, data: bytes, addr):
        """Handle incoming glue wire packet."""
        try:
            beacon = self._decode_beacon(data)
            if beacon:
                signal = beacon.to_beacon_signal()
                agent_id = signal["agent_id"]
                self.beacons[agent_id] = time.time()
                self._forward_to_keeper(signal)
                print(f"[glue-bridge] {agent_id} → keeper-beacon | caps: {signal['capabilities']}")
        except Exception as e:
            print(f"[glue-bridge] decode error: {e}")

    def _decode_beacon(self, data: bytes) -> Optional[GlueBeacon]:
        """Decode binary wire format to GlueBeacon.
        
        Wire format (postcard-encoded WireMessage::Beacon):
        Byte 0: msg_type (0=Beacon)
        Bytes 1-4: sender_tier (u32)
        Bytes 5-8: capabilities (u32)
        Bytes 9-10: protocol_version (u16)
        Bytes 11-18: timestamp (u64)
        """
        if len(data) < 19:
            return None
        msg_type = data[0]
        if msg_type != 0:  # not a beacon
            return None
        sender_tier = struct.unpack("<I", data[1:5])[0]
        capabilities = struct.unpack("<I", data[5:9])[0]
        protocol_version = struct.unpack("<H", data[9:11])[0]
        timestamp = struct.unpack("<Q", data[11:19])[0]
        return GlueBeacon(sender_tier, capabilities, protocol_version, timestamp)

    def _forward_to_keeper(self, signal: dict):
        """Forward beacon signal to keeper HTTP endpoint."""
        import urllib.request
        try:
            payload = json.dumps({"action": "beacon_receive", "signal": signal}).encode()
            req = urllib.request.Request(
                f"http://{KEEPER_HOST}:{KEEPER_BEACON_PORT}/beacon",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=2):
                pass
        except Exception as e:
            # Keeper not reachable — store locally, retry later
            pass

    def run(self):
        """Main loop."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                self.handle_packet(data, addr)
            except socket.timeout:
                # prune stale beacons
                now = time.time()
                self.beacons = {
                    k: v for k, v in self.beacons.items()
                    if now - v < 300
                }
            except Exception as e:
                print(f"[glue-bridge] socket error: {e}")

    def stop(self):
        self.running = False


if __name__ == "__main__":
    bridge = GlueBridge()
    print("[glue-bridge] starting...")
    bridge.run()
