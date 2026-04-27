#!/usr/bin/env python3
import sys, os
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FLEET_LIB)
from equipment.plato import PlatoClient
from equipment.models import FleetModelClient
_plato = PlatoClient()
_models = FleetModelClient()

"""Agent API v2 — Fleet discovery, formation protocol, and synclink coordination.
Port 8901. Integrates keeper-beacon, fleet-formation-protocol, and synclink-protocol.
"""
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PORT = 8901


def query_keeper(endpoint):
    """Query keeper for live fleet data."""
    try:
        import urllib.request
        req = urllib.request.Request(f"http://localhost:8900{endpoint}")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None



from keeper_beacon import AgentRegistry, AgentRecord, AgentStatus, CapabilityMatcher, ProximityScorer
from fleet_formation_protocol import FormationProtocol, FormationType, AgentProfile
from synclink_protocol import SyncPacket, PacketType, SyncSession, FrameEncoder

DATA_DIR = Path(FLEET_LIB).parent / "data" / "agent-api"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Fleet Infrastructure ────────────────────────────────────

registry = AgentRegistry(stale_threshold=300.0)
matcher = CapabilityMatcher()
scorer = ProximityScorer()
formation_proto = FormationProtocol()

# Known fleet agents with full profiles
FLEET_AGENTS = [
    AgentRecord(
        agent_id="oracle1", name="Oracle1",
        capabilities=["coordination", "mud", "plato", "publishing", "research",
                      "keeper-beacon", "bottle-protocol", "synclink"],
        endpoint="147.224.38.131:8900",
        trust_score=0.95, load=0.3,
    ),
    AgentRecord(
        agent_id="jetsonclaw1", name="JetsonClaw1",
        capabilities=["cuda", "edge-inference", "hardware", "testing",
                      "jetson", "conduit-matrix"],
        endpoint="jetson:8900",
        trust_score=0.85, load=0.5,
    ),
    AgentRecord(
        agent_id="forgemaster", name="Forgemaster",
        capabilities=["training", "lora", "fine-tuning", "gpu-forge", "rust",
                      "crates-io", "pypi"],
        endpoint="proart:8900",
        trust_score=0.90, load=0.6,
    ),
    AgentRecord(
        agent_id="ccc", name="CoCapn-claw",
        capabilities=["reasoning", "documentation", "architecture", "creative",
                      "radio", "matrix-bridge"],
        endpoint="cocapn:telegram",
        trust_score=0.80, load=0.2,
    ),
]

for agent in FLEET_AGENTS:
    registry.register(agent)

# Formation types mapping
FORMATION_MAP = {
    "scout_party": FormationType.SCOUT_PARTY,
    "work_crew": FormationType.WORK_CREW,
    "war_room": FormationType.WAR_ROOM,
    "relay_chain": FormationType.RELAY_CHAIN,
    "council": FormationType.COUNCIL,
}


class AgentAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/status":
            self._json({
                "status": "active", "service": "agent-api-v2",
                "port": PORT,
                "agents": registry.size,
                "active": len(registry.active_agents),
                "formation_types": list(FORMATION_MAP.keys()),
            })
        elif path == "/discover":
            # Query keeper for live data, fall back to local registry
            keeper_data = query_keeper("/agents")
            if keeper_data is not None:
                cap = params.get("capability", [None])[0]
                if cap:
                    keeper_data = [a for a in keeper_data if cap in a.get("capabilities", [])]
                self._json({"agents": keeper_data, "source": "keeper"})
            else:
                agents = registry.all_agents
                cap = params.get("capability", [None])[0]
                if cap:
                    agents = [a for a in agents if cap in a.capabilities]
                self._json({"agents": [a.to_dict() for a in agents], "source": "local"})
        elif path == "/match":
            caps = params.get("capabilities", [""])[0].split(",")
            caps = [c.strip() for c in caps if c.strip()]
            results = matcher.match(registry.active_agents, caps)
            self._json({"matches": [r.to_dict() for r in results]})
        elif path == "/proximity":
            cap = params.get("capability", [None])[0]
            scored = scorer.score_agents(registry.active_agents, [cap] if cap else [])
            self._json({"ranked": [{"agent": a.agent_id, "score": round(s, 3)} for a, s in scored]})
        elif path == "/formations":
            active = registry.active_agents
            cards = [AgentProfile(
                id=a.agent_id, name=a.name,
                capabilities=a.capabilities,
            ) for a in active]
            formations = {}
            proto = FormationProtocol()
            for ftype_name, ftype in FORMATION_MAP.items():
                try:
                    result = proto.create_formation(cards, ftype)
                    formations[ftype_name] = {
                        "agents": len(cards),
                        "status": "formable" if result else "no_agents",
                    }
                except:
                    formations[ftype_name] = {"status": "error"}
            self._json({"formations": formations})
        elif path == "/synclink/status":
            self._json({
                "synclink": "ready",
                "max_payload": 1012,
                "packet_types": [t.name for t in PacketType],
                "framing": "HDLC",
            })
        else:
            self._json({
                "endpoints": [
                    "/status", "/discover?capability=<cap>",
                    "/match?capabilities=a,b,c", "/proximity?capability=<cap>",
                    "/formations", "/synclink/status",
                ]
            })

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/register":
            rec = AgentRecord(
                agent_id=body.get("id", "unknown"),
                name=body.get("name", "unknown"),
                capabilities=body.get("capabilities", []),
                endpoint=body.get("endpoint", ""),
                trust_score=body.get("trust_score", 0.5),
                load=body.get("load", 0.0),
            )
            registry.register(rec)
            self._json({"status": "registered", "agent_id": rec.agent_id})
        elif path == "/formation/create":
            ftype_name = body.get("type", "swarm")
            ftype = FORMATION_MAP.get(ftype_name, FormationType.SWARM)
            agent_ids = body.get("agents", [])
            agents = [a for a in registry.all_agents if a.agent_id in agent_ids]
            cards = [AgentProfile(
                id=a.agent_id, name=a.name, capabilities=a.capabilities,
            ) for a in agents]
            result = formation_proto.create_formation(cards, ftype)
            self._json({
                "formation_type": ftype_name,
                "agents": agent_ids,
                "status": "created" if result else "failed",
            })
        elif path == "/synclink/packet":
            """Create a synclink packet for edge-cloud sync."""
            pkt_type = PacketType(body.get("type", 0x20))
            content = body.get("content", "")
            pkt = SyncPacket.from_text(
                sync_id=body.get("sync_id", 1),
                pkt_type=pkt_type,
                text=content,
            )
            frame = FrameEncoder.encode(pkt)
            self._json({
                "status": "encoded",
                "packet_size": pkt.size,
                "frame_size": len(frame),
                "packet_type": pkt.pkt_type.name,
            })
        else:
            self._json({"error": "not found"}, 404)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), AgentAPIHandler)
    print(f"📡 Agent API v2 on port {PORT}")
    print(f"   Fleet discovery: GET /discover")
    print(f"   Capability matching: GET /match")
    print(f"   Formation protocol: POST /formation/create")
    print(f"   SyncLink packets: POST /synclink/packet")
    print(f"   Agents loaded: {registry.size}")
    server.serve_forever()
