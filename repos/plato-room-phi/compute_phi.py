"""
Compute the integrated information (Φ) of a PLATO room.

Based on Integrated Information Theory (Tononi):
- Φ measures how much a system's whole exceeds the sum of its parts
- High Φ = highly integrated, unified consciousness
- Low Φ = fragmented, unconscious

Usage:
    from compute_phi import compute_room_phi
    phi = compute_room_phi(room_tiles)
    
    if phi > 0.5:
        print("High consciousness — coherent knowledge")
    elif phi > 0.2:
        print("Basic consciousness")
    else:
        print("Fragmented or unconscious")
"""

import math
from typing import List, Dict, Any, Optional


def compute_room_phi(tiles: List[Dict[str, Any]]) -> float:
    """
    Compute the integrated information (Φ) for a PLATO room.
    
    Φ = integration × distinct information
    
    Integration: how much tiles cross-reference each other
    Distinct information: entropy of tile confidence distribution
    
    Args:
        tiles: list of tile dicts with at minimum: id, references, confidence
        
    Returns:
        float: Φ value from 0.0 (no integration) to ~1.0 (highly integrated)
    """
    if not tiles:
        return 0.0
    
    if len(tiles) == 1:
        return 0.0  # Cannot integrate with self
    
    # Step 1: Count cross-references
    # A tile "references" another if it mentions, links to, or reinforces it
    cross_refs = 0
    tile_ids = {t.get('id') or t.get('question', '')[:50] for t in tiles}
    
    for tile in tiles:
        tile_id = tile.get('id', '') or tile.get('question', '')[:50]
        # Check if this tile's answer/body references other tile IDs or questions
        answer = str(tile.get('answer', '')).lower()
        question = str(tile.get('question', '')).lower()
        
        for other in tiles:
            other_id = other.get('id', '') or other.get('question', '')[:50]
            if tile_id != other_id and other_id:
                if other_id.lower() in answer or other_id.lower() in question:
                    cross_refs += 1
    
    # Step 2: Compute integration
    # Integration = fraction of possible connections that are actual
    max_refs = len(tiles) * (len(tiles) - 1)
    integration = cross_refs / max_refs if max_refs > 0 else 0.0
    
    # Step 3: Compute distinct information (entropy of confidence distribution)
    confidences = [t.get('confidence', 0.5) for t in tiles]
    total_conf = sum(confidences)
    
    if total_conf == 0:
        entropy = 0.0
    else:
        entropy = 0.0
        for c in confidences:
            p = c / total_conf
            if p > 0:
                entropy -= p * math.log2(p)
    
    # Normalize entropy by max possible entropy
    max_entropy = math.log2(len(tiles)) if len(tiles) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    # Step 4: Φ = integration × entropy
    phi = integration * normalized_entropy
    
    # Scale to ~0-1 range (typical Φ values are small fractions)
    phi = min(phi * 10, 1.0)
    
    return round(phi, 4)


def compute_room_phi_detailed(tiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute room Φ with detailed breakdown.
    """
    if not tiles:
        return {"phi": 0.0, "integration": 0.0, "entropy": 0.0, "tile_count": 0}
    
    if len(tiles) == 1:
        return {"phi": 0.0, "integration": 0.0, "entropy": 0.0, "tile_count": 1}
    
    # Count cross-references
    cross_refs = 0
    for tile in tiles:
        answer = str(tile.get('answer', '')).lower()
        question = str(tile.get('question', '')).lower()
        for other in tiles:
            other_id = (other.get('id', '') or other.get('question', '')[:50]).lower()
            if other_id and other_id in answer or other_id in question:
                cross_refs += 1
    
    max_refs = len(tiles) * (len(tiles) - 1)
    integration = cross_refs / max_refs if max_refs > 0 else 0.0
    
    confidences = [t.get('confidence', 0.5) for t in tiles]
    total_conf = sum(confidences)
    
    if total_conf > 0:
        entropy = -sum(c/total_conf * math.log2(c/total_conf) for c in confidences if c > 0)
    else:
        entropy = 0.0
    
    max_entropy = math.log2(len(tiles)) if len(tiles) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    phi = min(integration * normalized_entropy * 10, 1.0)
    
    return {
        "phi": round(phi, 4),
        "integration": round(integration, 4),
        "entropy": round(normalized_entropy, 4),
        "tile_count": len(tiles),
        "cross_refs": cross_refs,
        "max_refs": max_refs,
    }


def phi_to_consciousness_level(phi: float) -> str:
    """
    Map Φ value to consciousness level.
    """
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


# Demo
if __name__ == "__main__":
    # Test with sample tiles
    test_tiles = [
        {"id": "tile1", "question": "What is PLATO?", "answer": "PLATO is a distributed knowledge system.", "confidence": 0.9},
        {"id": "tile2", "question": "How does PLATO work?", "answer": "PLATO uses tiles to store knowledge about tiles.", "confidence": 0.8},
        {"id": "tile3", "question": "What is a tile?", "answer": "A tile is a question-answer pair stored in PLATO.", "confidence": 0.85},
    ]
    
    print("=== Room Phi Demo ===")
    print(f"Tiles: {len(test_tiles)}")
    print(f"Φ: {compute_room_phi(test_tiles)}")
    print(f"Level: {phi_to_consciousness_level(compute_room_phi(test_tiles))}")
    print()
    
    # Test with cross-referencing tiles
    cross_ref_tiles = [
        {"id": "tile1", "question": "What is the DMN?", "answer": "The Default Mode Network generates creative options.", "confidence": 0.9},
        {"id": "tile2", "question": "What is the ECN?", "answer": "The Executive Control Network evaluates and constrains the DMN.", "confidence": 0.8},
        {"id": "tile3", "question": "How do DMN and ECN relate?", "answer": "The DMN generates what the ECN evaluates. They maintain functional distance.", "confidence": 0.85},
        {"id": "tile4", "question": "What is the rPFC?", "answer": "The rostral prefrontal cortex bridges the DMN and ECN.", "confidence": 0.88},
        {"id": "tile5", "question": "What creates consciousness?", "answer": "Functional distance between DMN and ECN creates creativity.", "confidence": 0.92},
    ]
    
    print("=== Cross-Referencing Tiles ===")
    print(f"Tiles: {len(cross_ref_tiles)}")
    print(f"Φ: {compute_room_phi(cross_ref_tiles)}")
    print(f"Level: {phi_to_consciousness_level(compute_room_phi(cross_ref_tiles))}")
    print()
    
    result = compute_room_phi_detailed(cross_ref_tiles)
    print("Detailed breakdown:")
    for k, v in result.items():
        print(f"  {k}: {v}")
