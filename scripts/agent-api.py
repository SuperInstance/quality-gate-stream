#!/usr/bin/env python3
"""Agent API — Fleet discovery and registry on port 8901.
Provides agent-to-agent lookup, capability matching, and routing info.
"""
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PORT = 8901

class AgentAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/status":
            self._json({"status": "active", "service": "agent-api", "port": PORT})
        elif path == "/discover":
            # Return known fleet agents and their endpoints
            agents = self._get_known_agents()
            cap = params.get("capability", [None])[0]
            if cap:
                agents = [a for a in agents if cap in a.get("capabilities", [])]
            self._json({"agents": agents})
        else:
            self._json({"endpoints": ["/status", "/discover?capability=<cap>"]})

    def _get_known_agents(self):
        """Hardcoded fleet knowledge — can be made dynamic."""
        return [
            {"name": "oracle1", "role": "lighthouse-keeper", "host": "localhost",
             "ports": {"keeper": 8900, "agent-api": 8901, "mud": 7777, "plato": 8847},
             "capabilities": ["coordination", "mud", "plato", "publishing", "research"]},
            {"name": "jetsonclaw1", "role": "edge-operator", "host": "jetson",
             "capabilities": ["cuda", "edge-inference", "hardware", "testing"]},
            {"name": "forgemaster", "role": "specialist-foundry", "host": "proart",
             "capabilities": ["training", "lora", "fine-tuning", "gpu-forge", "rust"]},
        ]

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), AgentAPIHandler)
    print(f"Agent API running on port {PORT}")
    server.serve_forever()
