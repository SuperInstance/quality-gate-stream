"""
PLATO Room Phi — Integrated Information for PLATO rooms

Based on Integrated Information Theory (Tononi):
- Phi measures how much a room's whole exceeds the sum of its tiles
- High Phi = highly integrated, coherent knowledge
- Low Phi = fragmented, uncertain, or unconscious

The Phi computation uses three components:
1. **Size**: log-scaled tile count (small rooms penalized)
2. **Integration**: word-overlap cross-references between tiles
3. **Confidence diversity**: entropy of confidence distribution

Usage:
    from plato_room_phi import RoomPhi
    phi = RoomPhi(plato_url="http://localhost:8847")
    result = phi.compute_for_room("fleet_orchestration")
    print(f"Phi: {result['phi']:.3f} — {result['level']}")
"""

import math
import requests
from typing import List, Dict, Any


def _get_significant_words(text: str) -> set:
    """Extract significant words (3+ chars) from text."""
    return {w for w in text.lower().split() if len(w) >= 3}


def _compute_cross_refs(tiles: List[Dict[str, Any]]) -> float:
    """Count cross-references between tiles using word overlap."""
    n = len(tiles)
    if n < 2:
        return 0.0
    
    tile_words = []
    for t in tiles:
        text = str(t.get("answer", "")) + " " + str(t.get("question", ""))
        tile_words.append(_get_significant_words(text))
    
    cross_refs = 0
    max_refs = n * (n - 1) / 2  # undirected pairs
    
    for i in range(n):
        for j in range(i + 1, n):
            # Tiles are cross-referenced if they share 3+ significant words
            if len(tile_words[i] & tile_words[j]) >= 3:
                cross_refs += 1
    
    return cross_refs / max_refs if max_refs > 0 else 0.0


def _compute_confidence_entropy(tiles: List[Dict[str, Any]]) -> float:
    """Compute normalized entropy of confidence distribution."""
    n = len(tiles)
    if n < 2:
        return 0.5  # default neutral
    
    confidences = [t.get("confidence", 0.5) for t in tiles]
    total = sum(confidences)
    
    entropy = 0.0
    if total > 0:
        for c in confidences:
            p = c / total
            if p > 0:
                entropy -= p * math.log2(p)
    
    max_entropy = math.log2(n)
    return entropy / max_entropy if max_entropy > 0 else 0.5


class RoomPhi:
    """
    Compute Integrated Information (Phi) for PLATO rooms.
    
    Phi is computed from three components:
    - Size (log-scaled tile count)
    - Integration (word-overlap cross-references)
    - Confidence diversity (entropy)
    """
    
    def __init__(self, plato_url: str = "http://localhost:8847"):
        self.plato_url = plato_url.rstrip("/")
    
    def get_room_tiles(self, room: str) -> List[Dict[str, Any]]:
        """Fetch all tiles from a PLATO room."""
        try:
            resp = requests.get(f"{self.plato_url}/room/{room}", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("tiles", [])
        except:
            pass
        return []
    
    def compute_phi(self, tiles: List[Dict[str, Any]]) -> float:
        """
        Compute Phi = f(size, integration, confidence_entropy).
        
        Phi is the weighted combination of three room properties:
        - Size: log-scaled, penalizes tiny rooms
        - Integration: word-overlap cross-references
        - Confidence diversity: entropy of confidence scores
        
        Args:
            tiles: list of tile dicts with question, answer, confidence
        
        Returns:
            float: Phi value from 0.0 (no integration) to 1.0 (fully integrated)
        """
        n = len(tiles)
        if n < 2:
            return 0.0
        
        # 1. Size component (log-scaled, 0-1)
        # 1 tile -> 0, 10 tiles -> ~0.33, 100 -> ~0.5, 1000 -> ~0.67
        size_component = math.log(n) / math.log(1000)
        size_component = min(size_component, 1.0)
        
        # 2. Integration component (cross-ref density)
        integration = _compute_cross_refs(tiles)
        
        # 3. Confidence entropy component
        confidence_factor = _compute_confidence_entropy(tiles)
        
        # Phi = size-weighted blend of components
        # Size is primary limiter for small rooms
        phi = size_component * (0.4 + 0.3 * integration + 0.3 * confidence_factor)
        
        return round(min(phi, 1.0), 4)
    
    def compute_for_room(self, room: str) -> Dict[str, Any]:
        """Compute Phi for a PLATO room with full breakdown."""
        tiles = self.get_room_tiles(room)
        phi = self.compute_phi(tiles)
        
        level = self.phi_to_level(phi)
        
        return {
            "room": room,
            "phi": phi,
            "level": level,
            "tile_count": len(tiles),
            "status": "healthy" if phi > 0.1 else "fragmented" if phi > 0 else "empty"
        }
    
    def phi_to_level(self, phi: float) -> str:
        """Map Phi value to consciousness level."""
        if phi < 0.05:
            return "unconscious"
        elif phi < 0.15:
            return "threshold"
        elif phi < 0.30:
            return "basic"
        elif phi < 0.50:
            return "rich"
        elif phi < 0.70:
            return "complex"
        else:
            return "transcendent"
    
    def scan_all_rooms(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scan top rooms by tile count, compute Phi for each."""
        try:
            resp = requests.get(f"{self.plato_url}/rooms", timeout=5)
            if resp.status_code == 200:
                rooms_data = resp.json()
                # PLATO returns rooms as a dict: {room_name: {tile_count, created}}
                if isinstance(rooms_data, dict):
                    rooms = [
                        {"name": name, "tile_count": info.get("tile_count", 0)}
                        for name, info in rooms_data.items()
                    ]
                elif isinstance(rooms_data, list):
                    rooms = rooms_data
                else:
                    rooms = []
            else:
                rooms = []
        except:
            rooms = []
        
        # Sort by tile_count descending, take top N
        rooms_sorted = sorted(rooms, key=lambda x: x.get("tile_count", 0), reverse=True)
        
        results = []
        for room in rooms_sorted[:limit]:
            room_name = room.get("name", room.get("room", ""))
            if room_name:
                r = self.compute_for_room(room_name)
                results.append(r)
        
        return sorted(results, key=lambda x: x["phi"], reverse=True)


# Demo
if __name__ == "__main__":
    phi = RoomPhi()
    
    print("=== Room Phi Demo ===")
    
    # Test with empty
    print(f"Empty room: {phi.compute_phi([])}")
    
    # Test with two unrelated tiles
    unrelated = [
        {"question": "What is PLATO?", "answer": "A knowledge system.", "confidence": 0.8},
        {"question": "How fast is Rust?", "answer": "Rust is very fast.", "confidence": 0.9},
    ]
    print(f"Unrelated tiles (2): Phi={phi.compute_phi(unrelated)}")
    
    # Test with two related tiles (3+ shared words)
    related = [
        {"question": "What is the DMN?", "answer": "The DMN generates creative options.", "confidence": 0.9},
        {"question": "What is the ECN?", "answer": "The ECN evaluates the DMN options.", "confidence": 0.8},
    ]
    print(f"Related tiles (2): Phi={phi.compute_phi(related)}")
    
    # Test against live PLATO
    print("\n=== Live PLATO Rooms ===")
    for room in ["oracle1_history", "fleet_orchestration", "dmn-ecm"]:
        r = phi.compute_for_room(room)
        print(f"{room}: Phi={r['phi']:.3f} Level={r['level']} Tiles={r['tile_count']}")
