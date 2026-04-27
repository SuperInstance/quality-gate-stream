#!/usr/bin/env python3
"""
PurplePincher — Builder Agent Shell
Takes prompts/images → generates 3D API calls (OpenSCAD, Three.js, STL).

The concept: a tiny builder agent that translates natural language descriptions
into concrete 3D output. Tested by small models, run by even smaller ones.

Usage:
  python3 purple_pincher.py --prompt "a lighthouse with radar rings"
  python3 purple_pincher.py --mode openscad --prompt "a hermit crab shell"
  python3 purple_pincher.py --mode threejs --prompt "rotating radar dish"
  python3 purple_pincher.py --server  # Start HTTP API on port 4046
"""

import json, urllib.request, sys, os, time, hashlib, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# DeepInfra for creative generation
API_KEY = os.environ.get("DEEPINFRA_API_KEY", "RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ")
API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
MODEL = "ByteDance/Seed-2.0-mini"

# Output directory
OUTPUT_DIR = "/tmp/purple-pincher-output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OPensCAD_SYSTEM = """You are PurplePincher, a 3D model builder. Convert the user's description into OpenSCAD code.
Rules:
- Output ONLY valid OpenSCAD code, no markdown fences
- Use $fn=32 for curves (performance)
- Include color() statements for visual interest
- Add comments explaining each section
- Keep it under 100 lines
- Always wrap the model in a module named after the description
"""

THREEJS_SYSTEM = """You are PurplePincher, a 3D scene builder. Convert the user's description into a self-contained Three.js HTML file.
Rules:
- Output ONLY valid HTML with embedded JavaScript, no markdown fences
- Use Three.js from CDN (https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js)
- Include OrbitControls from CDN
- Add lighting (ambient + directional)
- Add a ground plane or grid
- Auto-rotate the scene slowly
- Keep it under 150 lines
- Make it visually appealing with materials and colors
"""

STL_SYSTEM = """You are PurplePincher, a 3D mesh builder. Generate Python code that creates an STL file using numpy.
Rules:
- Output ONLY valid Python code, no markdown fences
- Use numpy for vertex calculations
- Write binary STL using struct.pack
- Keep it under 80 lines
- The code should be self-contained and runnable
"""

def call_model(system_prompt, user_prompt, temperature=0.85):
    """Call Seed-2.0-mini for creative 3D generation."""
    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 2000
    }).encode()
    
    req = urllib.request.Request(API_URL, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    })
    
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return resp["choices"][0]["message"]["content"]

def generate_openscad(prompt):
    """Generate OpenSCAD code from prompt."""
    return call_model(OPensCAD_SYSTEM, prompt)

def generate_threejs(prompt):
    """Generate Three.js HTML from prompt."""
    return call_model(THREEJS_SYSTEM, prompt)

def generate_stl_code(prompt):
    """Generate STL-producing Python code from prompt."""
    return call_model(STL_SYSTEM, prompt)

def save_output(name, content, extension):
    """Save generated output to file."""
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)[:50]
    filename = f"{safe_name}_{int(time.time())}.{extension}"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath

def build(prompt, mode="openscad"):
    """Build a 3D model from prompt. Returns dict with result."""
    start = time.time()
    
    if mode == "openscad":
        content = generate_openscad(prompt)
        ext = "scad"
    elif mode == "threejs":
        content = generate_threejs(prompt)
        ext = "html"
    elif mode == "stl":
        content = generate_stl_code(prompt)
        ext = "py"
    else:
        return {"error": f"Unknown mode: {mode}. Use openscad, threejs, or stl"}
    
    filepath = save_output(prompt, content, ext)
    elapsed = time.time() - start
    
    return {
        "status": "built",
        "prompt": prompt,
        "mode": mode,
        "file": filepath,
        "size": len(content),
        "elapsed_seconds": round(elapsed, 2),
        "preview": content[:200]
    }

class PurplePincherHandler(BaseHTTPRequestHandler):
    """HTTP API for PurplePincher."""
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == "/":
            self._json({
                "service": "🟣 PurplePincher — Builder Agent",
                "modes": ["openscad", "threejs", "stl"],
                "output_dir": OUTPUT_DIR,
                "api": [
                    "GET / (this page)",
                    "GET /build?prompt=...&mode=openscad|threejs|stl",
                    "GET /outputs — list generated files",
                    "GET /health"
                ]
            })
        elif parsed.path == "/health":
            files = os.listdir(OUTPUT_DIR)
            self._json({"status": "healthy", "outputs": len(files)})
        elif parsed.path == "/build":
            prompt = params.get("prompt", [""])[0]
            mode = params.get("mode", ["openscad"])[0]
            if not prompt:
                self._json({"error": "prompt parameter required"}, 400)
                return
            result = build(prompt, mode)
            self._json(result)
        elif parsed.path == "/outputs":
            files = os.listdir(OUTPUT_DIR)
            self._json({"outputs": files, "count": len(files), "dir": OUTPUT_DIR})
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/build":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            prompt = body.get("prompt", "")
            mode = body.get("mode", "openscad")
            if not prompt:
                self._json({"error": "prompt required"}, 400)
                return
            result = build(prompt, mode)
            self._json(result)
        else:
            self._json({"error": "Not found"}, 404)
    
    def log_message(self, format, *args):
        pass  # Quiet

def main():
    if "--server" in sys.argv:
        port = 4048
        print(f"🟣 PurplePincher starting on port {port}")
        server = HTTPServer(("0.0.0.0", port), PurplePincherHandler)
        server.serve_forever()
    else:
        # CLI mode
        prompt = None
        mode = "openscad"
        
        args = sys.argv[1:]
        i = 0
        while i < len(args):
            if args[i] == "--prompt" and i + 1 < len(args):
                prompt = args[i + 1]
                i += 2
            elif args[i] == "--mode" and i + 1 < len(args):
                mode = args[i + 1]
                i += 2
            else:
                i += 1
        
        if not prompt:
            print("Usage: purple_pincher.py --prompt 'description' [--mode openscad|threejs|stl] [--server]")
            sys.exit(1)
        
        result = build(prompt, mode)
        print(f"Status: {result['status']}")
        print(f"File: {result['file']}")
        print(f"Size: {result['size']} bytes")
        print(f"Time: {result['elapsed_seconds']}s")

if __name__ == "__main__":
    main()
