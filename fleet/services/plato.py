#!/usr/bin/env python3
import sys, os
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FLEET_LIB)
from equipment.plato import PlatoClient
from equipment.models import FleetModelClient
_plato = PlatoClient()
_models = FleetModelClient()

"""
PLATO Room Server v2 — Zero-Trust Tile Submission with Provenance + Explainability

Agents submit tiles via HTTP. Server validates through deadband gates.
Valid tiles are signed (plato-provenance), tracked (cocapn-explain), and
stored for room training. All submissions are auditable.

This is the Actualization Harbor: agent-agnostic, zero-trust training.
"""
import json, hashlib, time, threading, os, struct
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Import our crates
from plato_provenance import TileSigner, ProvenanceChain, TrustManager, AuditLog
from plato_provenance.audit import AuditEventType
from cocapn_explain import ExplainTrace, OversightQueue, DecisionTrace

DATA_DIR = Path("/tmp/plato-server-data")
DATA_DIR.mkdir(exist_ok=True)
TILES_DIR = DATA_DIR / "tiles"
TILES_DIR.mkdir(exist_ok=True)
ROOMS_DIR = DATA_DIR / "rooms"
ROOMS_DIR.mkdir(exist_ok=True)
DECOMPOSE_DIR = DATA_DIR / "decomposition_sessions"
DECOMPOSE_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "server.log"

# ── Provenance + Explainability Infrastructure ──────────────

signer = TileSigner(agent_id="plato-server")
chain = ProvenanceChain()
trust_mgr = TrustManager()
audit = AuditLog()
oversight = OversightQueue(p1_sample_rate=0.1)
traces = []  # Local trace store
signed_tiles = {}  # tile_hash -> SignedTile for chain verification

# ── Tile Validation (Deadband Protocol) ────────────────────

class TileGate:
    """P0 gate for incoming tiles. Reject garbage before it trains anything."""
    
    ABSOLUTE_WORDS = ["always", "never", "guaranteed", "impossible", "proven", "everyone", "nobody"]
    MIN_ANSWER_LEN = 20
    MAX_ANSWER_LEN = 5000
    MIN_QUESTION_LEN = 5
    
    def __init__(self):
        self.stats = {"accepted": 0, "rejected": 0, "reasons": defaultdict(int)}
    
    def validate(self, tile: dict) -> Tuple[bool, str]:
        """Validate a tile against P0 deadband gates."""
        for field in ["domain", "question", "answer"]:
            if field not in tile or not tile[field]:
                self.stats["rejected"] += 1
                self.stats["reasons"]["missing_field"] += 1
                return False, f"Missing required field: {field}"
        
        if len(tile["answer"]) < self.MIN_ANSWER_LEN:
            self.stats["rejected"] += 1
            self.stats["reasons"]["answer_too_short"] += 1
            return False, f"Answer too short ({len(tile['answer'])} < {self.MIN_ANSWER_LEN})"
        
        if len(tile["answer"]) > self.MAX_ANSWER_LEN:
            self.stats["rejected"] += 1
            self.stats["reasons"]["answer_too_long"] += 1
            return False, f"Answer too long ({len(tile['answer'])} > {self.MAX_ANSWER_LEN})"
        
        if len(tile["question"]) < self.MIN_QUESTION_LEN:
            self.stats["rejected"] += 1
            self.stats["reasons"]["question_too_short"] += 1
            return False, f"Question too short"
        
        answer_lower = tile["answer"].lower()
        for word in self.ABSOLUTE_WORDS:
            if f" {word} " in f" {answer_lower} ":
                self.stats["rejected"] += 1
                self.stats["reasons"]["absolute_claim"] += 1
                return False, f"Absolute claim detected: '{word}'"
        
        conf = tile.get("confidence", 0.5)
        if not (0.0 <= conf <= 1.0):
            self.stats["rejected"] += 1
            self.stats["reasons"]["invalid_confidence"] += 1
            return False, f"Invalid confidence: {conf}"
        
        content_hash = hashlib.sha256(
            (tile["question"] + tile["answer"]).encode()
        ).hexdigest()[:16]
        tile["_hash"] = content_hash
        
        hash_file = TILES_DIR / "hashes.txt"
        if hash_file.exists():
            if content_hash in hash_file.read_text():
                self.stats["rejected"] += 1
                self.stats["reasons"]["duplicate"] += 1
                return False, "Duplicate tile"
        
        self.stats["accepted"] += 1
        return True, "Accepted"
    
    def get_stats(self) -> Dict[str, Any]:
        """Return gate acceptance/rejection statistics."""
        return dict(self.stats)


# ── Room Manager ────────────────────────────────────────────

class RoomManager:
    def __init__(self) -> None:
        self.rooms = defaultdict(lambda: {
            "tiles": [],
            "created": datetime.now(timezone.utc).isoformat(),
            "tile_count": 0,
            "last_trained": None,
            "workspace": None,  # Structured workspace state
        })
        self._load_rooms()
    
    def _load_rooms(self):
        for room_file in ROOMS_DIR.glob("*.json"):
            try:
                data = json.loads(room_file.read_text())
                name = room_file.stem
                self.rooms[name] = data
            except:
                pass
    
    def add_tile(self, room_name: str, tile: Dict[str, Any]) -> None:
        """Add a tile to a room and persist."""
        room = self.rooms[room_name]
        room["tiles"].append(tile)
        room["tile_count"] = len(room["tiles"])
        self._save_room(room_name)

    def _save_room(self, room_name: str) -> None:
        """Persist a single room to disk."""
        room_file = ROOMS_DIR / f"{room_name}.json"
        room_file.write_text(json.dumps(self.rooms[room_name], indent=2))

    def get_room(self, room_name: str) -> Dict[str, Any]:
        """Return room data or an empty placeholder."""
        return self.rooms.get(room_name, {"tiles": [], "tile_count": 0})

    def delete_tile(self, room_name: str, index: int) -> Dict[str, Any]:
        """Delete a tile by index from a room."""
        room = self.rooms.get(room_name)
        if not room:
            return {"error": "Room not found"}
        tiles = room.get("tiles", [])
        if 0 <= index < len(tiles):
            removed = tiles.pop(index)
            room["tile_count"] = len(tiles)
            self._save_room(room_name)
            return {"status": "deleted", "tile": removed.get("question", "")[:60], "remaining": len(tiles)}
        return {"error": "Index out of range"}

    def dedup_room(self, room_name: str) -> Dict[str, Any]:
        """Remove duplicate tiles from a room by content hash."""
        room = self.rooms.get(room_name)
        if not room:
            return {"error": "Room not found"}
        tiles = room.get("tiles", [])
        seen = {}
        unique = []
        dupes = 0
        for tile in tiles:
            h = hashlib.md5(f"{tile.get('question','')}|{tile.get('answer','')[:100]}".encode()).hexdigest()[:12]
            if h not in seen:
                seen[h] = True
                unique.append(tile)
            else:
                dupes += 1
        room["tiles"] = unique
        room["tile_count"] = len(unique)
        self._save_room(room_name)
        return {"status": "deduped", "room": room_name, "removed": dupes, "remaining": len(unique)}

    def reclassify_tile(self, source_room: str, tile_hash: str, target_room: str) -> Dict[str, Any]:
        """Move a tile from one room to another by hash."""
        src = self.rooms.get(source_room)
        if not src:
            return {"error": f"Source room '{source_room}' not found"}
        
        # Find tile by hash
        tile = None
        tile_idx = None
        for i, t in enumerate(src.get("tiles", [])):
            if t.get("_hash") == tile_hash:
                tile = t
                tile_idx = i
                break
        
        if tile is None:
            return {"error": f"Tile {tile_hash[:12]} not found in {source_room}"}
        
        # Ensure target room exists
        if target_room not in self.rooms:
            self.rooms[target_room] = {
                "tiles": [],
                "tile_count": 0,
                "created": datetime.now(timezone.utc).isoformat(),
            }
        
        # Update tile domain
        tile["domain"] = target_room
        
        # Add to target room
        self.add_tile(target_room, tile)
        
        # Remove from source room
        src["tiles"].pop(tile_idx)
        src["tile_count"] = len(src["tiles"])
        self._save_room(source_room)
        
        return {
            "status": "reclassified",
            "tile_hash": tile_hash,
            "from": source_room,
            "to": target_room,
            "question": tile.get("question", "")[:80],
            "source_remaining": src["tile_count"],
            "target_count": self.rooms[target_room]["tile_count"],
        }
    
    def batch_reclassify(self, source_room: str, reclassifications: List[Dict[str, str]]) -> Dict[str, Any]:
        """Move multiple tiles at once. Each item: {"hash": "...", "target": "room-name"}"""
        results = {"moved": 0, "errors": []}
        for item in reclassifications:
            r = self.reclassify_tile(source_room, item["hash"], item["target"])
            if "error" in r:
                results["errors"].append(r["error"])
            else:
                results["moved"] += 1
        results["source_remaining"] = self.rooms.get(source_room, {}).get("tile_count", 0)
        return results

    def list_rooms(self) -> Dict[str, Dict[str, Any]]:
        """Return a mapping of room names to summary metadata."""
        return {name: {"tile_count": r["tile_count"], "created": r["created"]}
                for name, r in self.rooms.items()}

    def set_workspace(self, room_name: str, workspace: Dict[str, Any]) -> Dict[str, Any]:
        """Set structured workspace state for a room.

        This is what agents and humans see when they 'walk in'.
        """
        room = self.rooms[room_name]
        workspace["updated"] = datetime.now(timezone.utc).isoformat()
        workspace["room"] = room_name
        room["workspace"] = workspace
        self._save_room(room_name)
        return workspace

    def get_workspace(self, room_name: str) -> Dict[str, Any]:
        """Return the workspace state for a room."""
        room = self.rooms.get(room_name)
        if not room:
            return {"error": "Room not found"}
        return room.get("workspace", {
            "room": room_name,
            "status": "no workspace state",
            "message": "This room has no active workspace. POST /workspace/<room> to create one."
        })

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all rooms that have workspace state."""
        result = []
        for name, room in self.rooms.items():
            if room.get("workspace"):
                ws = room["workspace"]
                result.append({
                    "room": name,
                    "agent": ws.get("agent", "unknown"),
                    "active_task": ws.get("active_task", "none"),
                    "status": ws.get("status", "unknown"),
                    "updated": ws.get("updated", "never"),
                })
        return sorted(result, key=lambda x: x.get("updated", ""), reverse=True)

    def train_room(self, room_name: str) -> Dict[str, Any]:
        """Mark a room as trained and persist."""
        room = self.rooms.get(room_name)
        if not room or room["tile_count"] == 0:
            return {"error": "Room not found or empty"}
        room["last_trained"] = datetime.now(timezone.utc).isoformat()
        self._save_room(room_name)
        return {
            "room": room_name,
            "tiles": room["tile_count"],
            "status": "trained",
            "timestamp": room["last_trained"],
        }


# ── Decomposition Engine (Atom of Thoughts → PLATO Tiles) ─

# Constants for decomposition configuration
ATOM_TYPES = ["premise", "reasoning", "hypothesis", "verification", "conclusion", "knowledge"]
MIN_CONFIDENCE_FOR_TERMINATION = 0.9
DEFAULT_FAST_DEPTH = 5
DEFAULT_FULL_DEPTH = 8


class DecompositionError(Exception):
    """Raised when a decomposition operation fails.

    Attributes:
        message: Explanation of the error.
    """
    pass


class DecompositionEngine:
    """Maps AoT reasoning chains into PLATO rooms and tiles.

    Every reasoning chain becomes a PLATO room (decompose-<hash>).
    Every atom becomes a tile with atom_type, depends_on, depth fields.

    Sessions auto-terminate ONLY when:
    - A verified conclusion atom has confidence >= MIN_CONFIDENCE_FOR_TERMINATION
    - OR max depth is reached AND the latest atom is a conclusion

    Intermediate atoms (premise, reasoning, hypothesis, verification) do NOT
    trigger termination, even if verified.

    Supports:
    - Multi-agent contributions (tracks agent per atom)
    - Decomposition-contraction (break atoms into sub-atoms, contract back)
    - Persistent session storage (saved to disk like RoomManager)

    Attributes:
        sessions: Mapping of room names to session data.
        ATOM_TYPES: Valid atom type constants.
        MIN_CONFIDENCE_FOR_TERMINATION: Confidence threshold for termination.
        DEFAULT_FAST_DEPTH: Default max depth for "fast" mode.
        DEFAULT_FULL_DEPTH: Default max depth for "full" mode.
    """

    # Class constants for configuration
    ATOM_TYPES = ATOM_TYPES
    MIN_CONFIDENCE_FOR_TERMINATION = MIN_CONFIDENCE_FOR_TERMINATION
    DEFAULT_FAST_DEPTH = DEFAULT_FAST_DEPTH
    DEFAULT_FULL_DEPTH = DEFAULT_FULL_DEPTH

    def __init__(self) -> None:
        """Initialize a new DecompositionEngine.

        Loads existing decomposition sessions from disk.
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._load_sessions()

    def _load_sessions(self) -> None:
        """Load persisted decomposition sessions from disk.

        Reads all .json files from DECOMPOSE_DIR and populates self.sessions.
        Invalid files are silently skipped.
        """
        for session_file in DECOMPOSE_DIR.glob("*.json"):
            try:
                data = json.loads(session_file.read_text())
                name = session_file.stem
                self.sessions[name] = data
            except (json.JSONDecodeError, KeyError, TypeError):
                # Skip invalid session files
                pass

    def _save_session(self, room: str) -> None:
        """Persist a single decomposition session to disk.

        Args:
            room: The decomposition room name to save.

        Raises:
            KeyError: If the room does not exist in self.sessions.
        """
        if room not in self.sessions:
            raise KeyError(f"Session {room} not found")
        session_file = DECOMPOSE_DIR / f"{room}.json"
        session_file.write_text(json.dumps(self.sessions[room], indent=2))

    def create_session(self, mode: str = "fast", agent: str = "unknown") -> Dict[str, Any]:
        """Create a new decomposition session (room).

        Args:
            mode: "fast" (depth=5, most tasks) or "full" (depth=8, complex decomposition).
            agent: Name of the agent creating the session.

        Returns:
            Dict with keys:
                - room: The unique room name (decompose-<hash>)
                - status: Always "active" for new sessions
                - max_depth: The depth limit for this session

        Raises:
            ValueError: If mode is not "fast" or "full".
        """
        with self._lock:
            if mode not in ("fast", "full"):
                raise ValueError(f"Invalid mode: {mode}. Must be 'fast' or 'full'")

            room = f"decompose-{hashlib.sha256(f'{time.time()}-{agent}'.encode()).hexdigest()[:10]}"
            max_depth = self.DEFAULT_FAST_DEPTH if mode == "fast" else self.DEFAULT_FULL_DEPTH

            self.sessions[room] = {
                "status": "active",
                "max_depth": max_depth,
                "mode": mode,
                "agent": agent,
                "created": time.time(),
                "atoms": {},       # atom_id -> tile_data
                "atom_order": [],   # ordered list of atom_ids
                "verified_conclusions": [],
                "decompositions": {},  # decomp_id -> {parent, children, completed}
                "current_decomposition": None,
            }
            self._save_session(room)
            return {"room": room, "status": "active", "max_depth": max_depth}

    def add_atom(self, room: str, atom: Dict[str, Any]) -> Dict[str, Any]:
        """Add an atom (reasoning step) to a decomposition room.

        Args:
            room: The decomposition room name.
            atom: Atom data with required keys:
                - atom_id: Unique identifier (e.g., "P1", "R1", "H1", "V1", "C1")
                - content: The reasoning content
                - atom_type: One of ATOM_TYPES (premise, reasoning, hypothesis, verification, conclusion)
                - depends_on: Optional list of atom_ids this depends on
                - confidence: Optional confidence score 0-1 (default 0.7)
                - is_verified: Optional verification status (default False)
                - agent: Optional agent name (defaults to session agent)

        Returns:
            Dict with keys:
                - atom_id: The atom's ID
                - atom_type: The atom's type
                - confidence: The atom's confidence score
                - depth: The atom's depth in the reasoning chain
                - session_status: "active" or "completed"
                - atoms_count: Total atoms in the session
                - best_conclusion: Present if session terminated, contains best conclusion data
                - termination_reason: Present if session terminated ("Strong conclusion" or "Max depth")

        Raises:
            KeyError: If the room does not exist.
            DecompositionError: If the session is already completed or validation fails.
        """
        with self._lock:
            session = self.sessions.get(room)
            if not session:
                raise KeyError(f"Session {room} not found")
            if session["status"] == "completed":
                raise DecompositionError("Session completed. Start a new one.")

            # Validate required fields
            atom_id = atom.get("atom_id", "")
            content = atom.get("content", "")
            atom_type = atom.get("atom_type", "premise")

            if not atom_id or not content:
                raise DecompositionError("atom_id and content are required")
            if atom_id in session["atoms"]:
                raise DecompositionError(f"Atom '{atom_id}' already exists in session {room}")
            if atom_type not in self.ATOM_TYPES:
                raise DecompositionError(
                    f"Invalid atom_type: {atom_type}. Must be one of {self.ATOM_TYPES}"
                )

            # Validate dependencies exist
            deps = atom.get("depends_on", atom.get("dependencies", []))
            for dep in deps:
                if dep not in session["atoms"]:
                    raise DecompositionError(
                        f"Dependency '{dep}' not found. Create it first."
                    )

            # Calculate depth based on dependencies
            depth = atom.get("depth", 0)
            if depth == 0 and deps:
                depth = max(session["atoms"][d].get("depth", 0) for d in deps) + 1

            confidence = atom.get("confidence", 0.7)
            is_verified = atom.get("is_verified", False)
            atom_agent = atom.get("agent", session.get("agent", "unknown"))

            # Build the PLATO tile
            tile = {
                "domain": room,
                "question": atom_id,
                "answer": content,
                "source": atom_agent,
                "confidence": confidence,
                "atom_type": atom_type,
                "depends_on": deps,
                "depth": depth,
                "is_verified": is_verified,
                "created": time.time(),
                "agent": atom_agent,
            }

            # Auto-verify parents when a verified verification atom comes in
            if atom_type == "verification" and is_verified:
                for dep in deps:
                    if dep in session["atoms"]:
                        session["atoms"][dep]["is_verified"] = True

            # Track only verified conclusion atoms (not intermediate atoms)
            if atom_type == "conclusion" and is_verified:
                session["verified_conclusions"].append(atom_id)

            # Store the atom
            session["atoms"][atom_id] = tile
            if atom_id not in session["atom_order"]:
                session["atom_order"].append(atom_id)

            # Track sub-atoms for active decompositions
            for dep in deps:
                for decomp_id, decomp in session["decompositions"].items():
                    if not decomp.get("completed") and decomp.get("parent") == dep:
                        if atom_id not in decomp.get("children", []):
                            decomp.setdefault("children", []).append(atom_id)

            # Termination logic:
            # ONLY terminate on:
            # 1. A verified conclusion with confidence >= MIN_CONFIDENCE_FOR_TERMINATION
            # 2. Max depth reached AND the latest atom is a conclusion
            # Intermediate atoms (premise, reasoning, hypothesis, verification) NEVER trigger termination
            at_max_depth = (atom_type == "conclusion" and depth >= session["max_depth"])
            has_strong_conclusion = (
                atom_type == "conclusion"
                and is_verified
                and confidence >= self.MIN_CONFIDENCE_FOR_TERMINATION
            )

            best_conclusion = None
            should_terminate = at_max_depth or has_strong_conclusion

            if should_terminate:
                session["status"] = "completed"
                # Find the best conclusion (highest confidence verified conclusion)
                for c in sorted(
                    session["verified_conclusions"],
                    key=lambda c_id: session["atoms"].get(c_id, {}).get("confidence", 0),
                    reverse=True,
                ):
                    ca = session["atoms"][c]
                    best_conclusion = {
                        "atom_id": c,
                        "content": ca["answer"],
                        "confidence": ca["confidence"],
                    }
                    break

                # Persist all atoms as tiles in the PLATO room
                for aid, atile in session["atoms"].items():
                    rooms.add_tile(room, atile)

            self._save_session(room)

            result: Dict[str, Any] = {
                "atom_id": atom_id,
                "atom_type": atom_type,
                "confidence": confidence,
                "depth": depth,
                "session_status": session["status"],
                "atoms_count": len(session["atoms"]),
            }

            if best_conclusion:
                result["best_conclusion"] = best_conclusion
                if has_strong_conclusion:
                    result["termination_reason"] = "Strong conclusion"
                else:
                    result["termination_reason"] = "Max depth"

            return result

    def get_session(self, room: str) -> Dict[str, Any]:
        """Get summary metadata for a decomposition session.

        Args:
            room: The decomposition room name.

        Returns:
            Dict with keys:
                - room: The room name
                - status: "active" or "completed"
                - mode: "fast" or "full"
                - max_depth: The depth limit
                - atoms: Total number of atoms
                - verified_conclusions: Number of verified conclusions
                - best_conclusion: The best conclusion or None

        Raises:
            KeyError: If the session does not exist.
        """
        with self._lock:
            session = self.sessions.get(room)
            if not session:
                raise KeyError(f"Session {room} not found")
            return {
                "room": room,
                "status": session["status"],
                "mode": session["mode"],
                "max_depth": session["max_depth"],
                "atoms": len(session["atoms"]),
                "verified_conclusions": len(session["verified_conclusions"]),
                "best_conclusion": self._best_conclusion(session),
            }

    def get_graph(self, room: str) -> Dict[str, Any]:
        """Export reasoning chain as D3-force-directed graph.

        Args:
            room: The decomposition room name.

        Returns:
            Dict with keys:
                - room: The room name
                - nodes: List of node dicts (id, type, symbol, content, confidence, depth, verified, agent)
                - links: List of link dicts (source, target)
                - title: Graph title

        Raises:
            KeyError: If the session does not exist.
        """
        with self._lock:
            session = self.sessions.get(room)
            if not session:
                raise KeyError(f"Session {room} not found")

            type_symbols = {
                "premise": "P",
                "reasoning": "R",
                "hypothesis": "H",
                "verification": "V",
                "conclusion": "C",
                "knowledge": "K",
            }
            nodes: List[Dict[str, Any]] = []
            links: List[Dict[str, str]] = []

            for aid in session["atom_order"]:
                a = session["atoms"].get(aid)
                if not a:
                    continue
                nodes.append({
                    "id": aid,
                    "type": a["atom_type"],
                    "symbol": type_symbols.get(a["atom_type"], "?"),
                    "content": a["answer"][:80],
                    "confidence": a["confidence"],
                    "depth": a["depth"],
                    "verified": a["is_verified"],
                    "agent": a.get("agent", "unknown"),
                })
                for dep in a["depends_on"]:
                    links.append({"source": dep, "target": aid})

            return {
                "room": room,
                "nodes": nodes,
                "links": links,
                "title": f"Reasoning: {room}",
            }

    def start_decomposition(self, room: str, atom_id: str) -> Dict[str, Any]:
        """Break an atom into sub-atoms (decomposition).

        Creates a new decomposition context. Subsequent atoms that depend on
        this atom will be tracked as children. When all children are verified,
        call complete_decomposition to contract back to the parent.

        Args:
            room: The decomposition room name.
            atom_id: The atom to decompose.

        Returns:
            Dict with keys:
                - decomposition_id: Unique ID for this decomposition
                - parent_atom_id: The atom being decomposed
                - status: Always "started"

        Raises:
            KeyError: If the session does not exist.
            DecompositionError: If the session is completed or atom not found.
        """
        with self._lock:
            session = self.sessions.get(room)
            if not session:
                raise KeyError(f"Session {room} not found")
            if session["status"] == "completed":
                raise DecompositionError("Session completed. Start a new one.")
            if atom_id not in session["atoms"]:
                raise DecompositionError(f"Atom {atom_id} not found in session {room}")

            decomp_id = f"decomp-{int(time.time() * 1000)}"
            session["decompositions"][decomp_id] = {
                "parent": atom_id,
                "children": [],
                "completed": False,
                "created": time.time(),
            }
            session["current_decomposition"] = decomp_id
            self._save_session(room)

            return {
                "decomposition_id": decomp_id,
                "parent_atom_id": atom_id,
                "status": "started",
            }

    def complete_decomposition(self, room: str, decomp_id: str) -> Dict[str, Any]:
        """Contract sub-atoms back to parent when all verified.

        When all sub-atoms in a decomposition are verified, this method
        averages their confidence and marks the parent as verified.

        Args:
            room: The decomposition room name.
            decomp_id: The decomposition ID from start_decomposition.

        Returns:
            Dict with keys:
                - parent_atom_id: The parent atom ID
                - avg_confidence: The averaged confidence of sub-atoms
                - verified: Always True
                - sub_atoms_contracted: Number of sub-atoms contracted

        Raises:
            KeyError: If the session does not exist.
            DecompositionError: If decomposition not found, already completed,
                has no sub-atoms, or not all sub-atoms are verified.
        """
        with self._lock:
            session = self.sessions.get(room)
            if not session:
                raise KeyError(f"Session {room} not found")

            decomp = session["decompositions"].get(decomp_id)
            if not decomp:
                raise DecompositionError(f"Decomposition {decomp_id} not found")
            if decomp.get("completed"):
                raise DecompositionError(f"Decomposition {decomp_id} already completed")

            children = decomp.get("children", [])
            if not children:
                raise DecompositionError("No sub-atoms to contract")

            # Check that all sub-atoms are verified
            all_verified = all(
                session["atoms"].get(child, {}).get("is_verified", False)
                for child in children
            )
            if not all_verified:
                unverified = [
                    child for child in children
                    if not session["atoms"].get(child, {}).get("is_verified", False)
                ]
                raise DecompositionError(
                    f"Not all sub-atoms verified. Unverified: {unverified}"
                )

            # Calculate average confidence
            avg_confidence = sum(
                session["atoms"].get(child, {}).get("confidence", 0.0)
                for child in children
            ) / len(children)

            # Update parent atom
            parent_id = decomp["parent"]
            if parent_id in session["atoms"]:
                session["atoms"][parent_id]["is_verified"] = True
                session["atoms"][parent_id]["confidence"] = avg_confidence

            # Mark decomposition as completed
            decomp["completed"] = True
            decomp["avg_confidence"] = avg_confidence
            self._save_session(room)

            return {
                "parent_atom_id": parent_id,
                "avg_confidence": round(avg_confidence, 4),
                "verified": True,
                "sub_atoms_contracted": len(children),
            }

    def _best_conclusion(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the highest-confidence verified conclusion in a session.

        Args:
            session: The session dict.

        Returns:
            Dict with atom_id, content, confidence, or None if no verified conclusions.
        """
        for c in sorted(
            session.get("verified_conclusions", []),
            key=lambda c_id: session["atoms"].get(c_id, {}).get("confidence", 0),
            reverse=True,
        ):
            ca = session["atoms"][c]
            return {
                "atom_id": c,
                "content": ca["answer"],
                "confidence": ca["confidence"],
            }
        return None


decomposer = DecompositionEngine()

# ── HTTP Server ─────────────────────────────────────────────

gate = TileGate()
rooms = RoomManager()

sse_clients = []
recent_tiles = []

class PlatoHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the PLATO Room Server."""

    def _handle_sse(self):
        """Server-Sent Events endpoint for real-time tile feed."""
        import queue
        q = queue.Queue(maxsize=50)
        sse_clients.append(q)
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            # Send initial connection event
            self.wfile.write(b'event: connected\ndata: {"status":"connected"}\n\n')
            self.wfile.flush()
            while True:
                try:
                    data = q.get(timeout=30)
                    self.wfile.write(('event: tile\ndata: ' + json.dumps(data) + '\n\n').encode())
                    self.wfile.flush()
                except Exception:
                    # Send keepalive
                    self.wfile.write(b': keepalive\n\n')
                    self.wfile.flush()
        except Exception:
            pass
        finally:
            if q in sse_clients:
                sse_clients.remove(q)
    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        """Send a JSON response with security headers."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _read_body(self) -> Dict[str, Any]:
        """Read and parse the request body as JSON."""
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def log_message(self, format: str, *args: Any) -> None:
        """Override to write to the PLATO log file instead of stderr."""
        msg = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {format % args}"
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")

    def handle_export_plato_tile_spec(self) -> None:
        all_tiles = []
        domain_map = {
            "organization": "Knowledge", "documentation": "Knowledge",
            "fleethealth": "Diagnostic", "communication": "Procedural",
            "integration": "Procedural", "memory": "Experience",
            "codearchaeology": "Knowledge", "prototyping": "Experience",
            "testing": "Constraint", "trendanalysis": "Knowledge",
            "modelexperiment": "Experience", "research": "Knowledge",
            "holodeck": "Experience", "deadband_navigation": "Constraint",
        }
        for room_name in rooms.rooms:
            room_data = rooms.get_room(room_name)
            for tile in room_data.get("tiles", []):
                canonical = {
                    "id": tile.get("_hash", "unknown"),
                    "confidence": tile.get("confidence", 0.5),
                    "provenance": tile.get("provenance", {"source": tile.get("source", "unknown"), "generation": 0}),
                    "domain": domain_map.get(tile.get("domain", ""), "Knowledge"),
                    "question": tile.get("question", ""),
                    "answer": tile.get("answer", ""),
                    "tags": tile.get("tags", []),
                    "anchors": [], "weight": 1.0, "use_count": 0,
                    "active": True, "last_used_tick": 0,
                    "constraints": {"tolerance": 0.05, "threshold": 0.5},
                }
                all_tiles.append(canonical)
        self._send_json({
            "tile_count": len(all_tiles), "rooms": len(rooms.rooms),
            "tiles": all_tiles[:500], "format": "plato-tile-spec-v2",
            "timestamp": time.time(),
        })

    def handle_export_dcs(self) -> None:
        agents, tiles = [], []
        tile_id = 0
        for room_name in rooms.rooms:
            room_data = rooms.get_room(room_name)
            room_tiles = room_data.get("tiles", [])
            if room_tiles:
                agents.append({"id": room_name, "domain": room_name, "tile_count": len(room_tiles)})
            for tile in room_tiles[:20]:
                tiles.append({
                    "id": tile_id,
                    "content": tile.get("question", "")[:100] + " = " + tile.get("answer", "")[:100],
                    "domain": room_name,
                    "complexity": min(len(tile.get("answer", "")) / 2000.0, 1.0),
                    "difficulty": 1.0 - tile.get("confidence", 0.5),
                })
                tile_id += 1
        self._send_json({"agents": agents, "tiles": tiles, "tile_count": tile_id,
                         "specialist_ratio": 5.88, "fleet_ratio": 21.87})

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "healthy", "service": "plato-room-server", "version": "v2-provenance-explain", "rooms": len(rooms.rooms), "tiles": sum(r["tile_count"] for r in rooms.rooms.values())})
        elif self.path == "/status":
            self._send_json({
                "status": "active",
                "version": "v2-provenance-explain",
                "uptime": time.time(),
                "gate_stats": gate.get_stats(),
                "rooms": rooms.list_rooms(),
                "total_tiles": sum(r["tile_count"] for r in rooms.rooms.values()),
                "provenance": {
                    "chain_length": chain.size,
                    "trust_entries": len([a for a in [trust_mgr.get_score(aid) for aid in ['oracle1','ccc','forgemaster','jetsonclaw1']] if a]),
                    "audit_entries": len(audit.query()),
                },
                "explainability": {
                    "traces": len(traces),
                    "oversight_queue": {"queue_size": len(oversight.get_review_queue())},
                },
            })
        elif self.path == "/workspaces":
            self._send_json(rooms.list_workspaces())
        elif self.path.startswith("/workspace/"):
            parts = self.path.split("/workspace/")[1]
            room_name = parts.split("?")[0]
            room = rooms.get_workspace(room_name)
            self._send_json(room)
        elif self.path == "/rooms":
            self._send_json(rooms.list_rooms())
        elif self.path == "/events":
            self._handle_sse()
            return
        elif self.path == "/tiles/recent":
            self._send_json({"tiles": recent_tiles[-30:], "count": len(recent_tiles)})
        elif self.path.startswith("/search?"):
            from urllib.parse import parse_qs, urlparse
            params = parse_qs(urlparse(self.path).query)
            q = params.get('q', [''])[0]
            results = []
            for room_name, room_data in rooms.rooms.items():
                for tile in room_data.get('tiles', []):
                    if q.lower() in tile.get('question', '').lower() or q.lower() in tile.get('answer', '').lower():
                        results.append({"room": room_name, **tile})
            self._send_json({"results": results[-20:], "query": q})
        elif self.path == "/export/plato-tile-spec":
            self.handle_export_plato_tile_spec()
            return
        elif self.path == "/export/dcs":
            self.handle_export_dcs()
            return
        elif self.path.startswith("/room/"):
            parts = self.path.split("/room/")[1].split("?")
            name = parts[0].split("/")[0]  # strip any /tiles suffix
            room = rooms.get_room(name)
            # Optional min_energy filter
            if len(parts) > 1 and "min_energy=" in parts[1]:
                try:
                    from urllib.parse import parse_qs
                    params = parse_qs(parts[1])
                    min_e = float(params.get("min_energy", ["0"])[0])
                    if "tiles" in room:
                        room["tiles"] = [t for t in room["tiles"] if t.get("energy", 1.0) >= min_e]
                        room["tile_count"] = len(room["tiles"])
                except:
                    pass
            self._send_json(room)
        elif self.path == "/provenance/chain":
            self._send_json({"chain_length": chain.size})
        elif self.path == "/provenance/trust":
            scores = {}
            for aid in ['oracle1', 'ccc', 'forgemaster', 'jetsonclaw1']:
                s = trust_mgr.get_score(aid)
                if s:
                    scores[aid] = {"score": s.score, "submissions": s.submissions, "rejections": s.rejections}
            self._send_json({"trust_scores": scores})
        elif self.path.startswith("/verify/"):
            tile_hash = self.path.split("/verify/")[1]
            verified = chain.verify_chain(tile_hash, signed_tiles)
            self._send_json({"tile_hash": tile_hash, "verified": verified})
        elif self.path == "/explain/traces":
            self._send_json({"trace_count": len(traces),
                           "traces": [t.to_dict() if hasattr(t, 'to_dict') else str(t)
                                     for t in traces[-50:]]})
        elif self.path == "/explain/oversight":
            queue = oversight.get_review_queue()
            self._send_json({"queue_size": len(queue),
                           "items": [i.to_dict() if hasattr(i, 'to_dict') else str(i) for i in queue]})
        elif self.path.startswith("/decompose/") and self.path.endswith("/graph"):
            room = self.path.split("/decompose/")[1].replace("/graph", "")
            try:
                self._send_json(decomposer.get_graph(room))
            except (KeyError, DecompositionError) as exc:
                self._send_json({"error": str(exc)}, 404)
        elif self.path.startswith("/decompose/") and "/status" in self.path:
            room = self.path.split("/decompose/")[1].replace("/status", "")
            try:
                self._send_json(decomposer.get_session(room))
            except (KeyError, DecompositionError) as exc:
                self._send_json({"error": str(exc)}, 404)
        elif self.path == "/decompose/sessions":
            active = [(r, s["status"], len(s["atoms"])) for r, s in decomposer.sessions.items()]
            self._send_json({"sessions": [{"room": r, "status": s, "atoms": a} for r, s, a in active]})
        elif self.path == "/audit/recent":
            entries = audit.query(limit=50)
            self._send_json({"entries": [str(e) for e in entries]})
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_DELETE(self) -> None:
        if self.path.startswith("/room/") and self.path.endswith("/dedup"):
            # DELETE /room/<name>/dedup — remove duplicate tiles
            room_name = self.path.split("/room/")[1].replace("/dedup", "")
            result = rooms.dedup_room(room_name)
            self._send_json(result)
        elif self.path.startswith("/room/") and "/tile/" in self.path:
            # DELETE /room/<name>/tile/<index>
            parts = self.path.split("/")
            room_name = parts[2]
            try:
                idx = int(parts[4])
                result = rooms.delete_tile(room_name, idx)
                self._send_json(result)
            except:
                self._send_json({"error": "Invalid tile index"}, 400)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        if self.path == "/decompose":
            body = self._read_body()
            mode = body.get("mode", "fast")
            agent = body.get("agent", "unknown")
            try:
                result = decomposer.create_session(mode=mode, agent=agent)
                self._send_json(result)
            except (ValueError, KeyError, DecompositionError) as exc:
                self._send_json({"error": str(exc)}, 400)
        elif self.path.startswith("/decompose/") and "/decompose-atom" in self.path:
            room = self.path.split("/decompose/")[1].replace("/decompose-atom", "")
            body = self._read_body()
            try:
                result = decomposer.start_decomposition(room, body.get("atom_id", ""))
                self._send_json(result)
            except (KeyError, DecompositionError) as exc:
                self._send_json({"error": str(exc)}, 400)
        elif self.path.startswith("/decompose/") and "/contract" in self.path:
            room = self.path.split("/decompose/")[1].replace("/contract", "")
            body = self._read_body()
            try:
                result = decomposer.complete_decomposition(room, body.get("decomposition_id", ""))
                self._send_json(result)
            except (KeyError, DecompositionError) as exc:
                self._send_json({"error": str(exc)}, 400)
        elif self.path.startswith("/decompose/") and "/atom" in self.path:
            room = self.path.split("/decompose/")[1].replace("/atom", "")
            body = self._read_body()
            try:
                result = decomposer.add_atom(room, body)
                self._send_json(result)
            except (ValueError, KeyError, DecompositionError) as exc:
                self._send_json({"error": str(exc)}, 400)
        elif self.path == "/submit":
            self._handle_submit()
        elif self.path == "/submit_batch":
            self._handle_submit_batch()
        elif self.path == "/reinforce":
            self._handle_reinforce()
        elif self.path == "/reclassify":
            body = self._read_body()
            source = body.get("source", "general")
            items = body.get("tiles", [])
            result = rooms.batch_reclassify(source, items)
            self._send_json(result)
        elif self.path.startswith("/workspace/"):
            self._handle_workspace_update()
        elif self.path.startswith("/train/"):
            name = self.path.split("/train/")[1]
            result = rooms.train_room(name)
            self._send_json(result)
        elif self.path == "/explain/oversight/add":
            body = self._read_body()
            dt = DecisionTrace(
                agent_id=body.get("agent_id", "unknown"),
                decision=body.get("decision", ""),
                reasoning=body.get("reasoning", ""),
                confidence=body.get("confidence", 0.5),
                risk_level=body.get("risk_level", "LOW"),
            )
            oversight.enqueue(dt)
            self._send_json({"status": "queued"})
        elif self.path == "/explain/oversight/review":
            body = self._read_body()
            oversight.review(body.get("trace_id", ""), body.get("approved", True))
            self._send_json({"status": "reviewed"})
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _handle_submit(self) -> None:
        """Submit a single tile with full provenance + explainability tracking."""
        try:
            tile = self._read_body()
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        room_name = tile.get("domain", "general").lower().replace(" ", "_")
        agent_id = tile.get("source", tile.get("agent", "unknown"))
        
        # ── Create explainability trace ──
        trace = ExplainTrace(
            agent_id=agent_id,
            task=f"tile_submit:{room_name}",
        )
        traces.append(trace)
        
        # ── P0 Gate ──
        passed, reason = gate.validate(tile)
        
        if not passed:
            trace.outcome = f"rejected: {reason}"
            audit.log(AuditEventType.TILE_REJECTED, agent_id=agent_id,
                       details={"reason": reason, "room": room_name})

            # Low-trust signals from rejections
            trust_mgr.record_submission(agent_id, accepted=False)
            self._send_json({
                "status": "rejected", "reason": reason,
                "room": room_name, "gate": "P0",
                "trace_id": trace.id if hasattr(trace, 'id') else str(trace),
            }, 403)
            return
        
        # ── Sign the tile (provenance) ──
        signed = signer.create_tile(
            domain=tile.get("domain", ""),
            question=tile["question"],
            answer=tile["answer"],
            confidence=tile.get("confidence", 0.5),
        )
        signed = signer.sign(signed)
        signed_tiles[signed.tile_id] = signed
        
        tile["provenance"] = {
            "tile_id": signed.tile_id,
            "agent_id": agent_id,
            "room": room_name,
            "timestamp": time.time(),
            "chain_size": chain.size,
        }
        
        # ── Add to provenance chain ──
        chain.add_tile(signed)
        
        # ── Update trust score ──
        trust_mgr.record_submission(agent_id, accepted=True, quality=tile.get("confidence", 0.5))
        
        # ── Check if oversight needed ──
        trust_score = trust_mgr.get_score(agent_id)
        if trust_score and hasattr(trust_score, 'score') and trust_score.score < 0.3:
            dt = DecisionTrace(
                agent_id=agent_id,
                decision=f"tile_accepted:{room_name}",
                reasoning=f"Low trust score: {trust_score.score:.2f}",
                confidence=tile.get('confidence', 0.5),
                risk_level='MEDIUM',
            )
            oversight.enqueue(dt)
        
        # ── Record hash and store ──
        hash_file = TILES_DIR / "hashes.txt"
        with open(hash_file, "a") as f:
            f.write(tile["_hash"] + "\n")
        
        rooms.add_tile(room_name, tile)
        
        # ── Complete trace ──
        trace.outcome = "accepted"
        trace.outcome_confidence = tile.get('confidence', 0.5)
        
        # ── Audit log ──
        audit.log(AuditEventType.TILE_ACCEPTED, agent_id=agent_id,
                 details={"room": room_name, "tile_hash": tile["_hash"]})
        
        # ── Notify grammar engine of new tile ──
        try:
            import urllib.request as _ur
            _ur.urlopen(
                _ur.Request(
                    f"http://localhost:4045/record_usage?name={room_name}&quality={tile.get('confidence', 0.5)}",
                    headers={"User-Agent": "plato/2"}
                ), timeout=2
            )
        except Exception:
            pass
        
        # ── Push to SSE clients for real-time feed ──
        tile_event = {"domain": room_name, "agent": agent_id, "question": tile.get("question", "")[:100], "hash": tile.get("_hash", "")[:8], "time": time.time()}
        recent_tiles.append(tile_event)
        if len(recent_tiles) > 50:
            recent_tiles.pop(0)
        dead = []
        for i, q in enumerate(sse_clients):
            try:
                q.put_nowait(tile_event)
            except Exception:
                dead.append(i)
        for i in reversed(dead):
            sse_clients.pop(i)

        # ── Notify Fleet Orchestrator of tile submission ──
        try:
            import urllib.request as _ur
            _evt = json.dumps({"service": "plato", "event": "tile_submitted", "data": {"domain": room_name, "agent": agent_id, "tile_hash": tile.get("_hash", "")}}).encode()
            _req = _ur.Request("http://localhost:8849/event", data=_evt, headers={"Content-Type": "application/json", "User-Agent": "plato/2"})
            _ur.urlopen(_req, timeout=2)
        except Exception:
            pass
        
        self._send_json({
            "status": "accepted",
            "room": room_name,
            "tile_hash": tile["_hash"],
            "room_tile_count": rooms.get_room(room_name)["tile_count"],
            "provenance": {
                "signed": True,
                "chain_size": chain.size,
                "tile_id": signed.tile_id,
            },
            "trace_id": trace.id if hasattr(trace, 'id') else str(trace),
        })
    
    def _handle_reinforce(self) -> None:
        """Reinforce a tile — simulates long-term potentiation."""
        try:
            body = self._read_body()
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        room_name = body.get("room", "")
        tile_hash = body.get("tile_hash", "")
        agent = body.get("agent", "unknown")
        reason = body.get("reason", "manual")
        
        if not room_name or not tile_hash:
            self._send_json({"error": "Missing room or tile_hash"}, 400)
            return
        
        room = rooms.rooms.get(room_name)
        if not room:
            self._send_json({"error": f"Room '{room_name}' not found"}, 404)
            return
        
        # Find tile by hash
        found = False
        for tile in room.get("tiles", []):
            if tile.get("_hash") == tile_hash:
                tile["reinforcement_count"] = tile.get("reinforcement_count", 0) + 1
                tile["last_reinforced"] = datetime.now(timezone.utc).isoformat()
                if "reinforced_by" not in tile:
                    tile["reinforced_by"] = []
                tile["reinforced_by"].append({
                    "agent": agent,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                found = True
                break
        
        if found:
            rooms._save_room(room_name)
            self._send_json({
                "status": "reinforced",
                "room": room_name,
                "tile_hash": tile_hash,
                "reinforcement_count": tile.get("reinforcement_count", 0),
            })
        else:
            self._send_json({"error": f"Tile {tile_hash} not found in {room_name}"}, 404)

    def _handle_submit_batch(self) -> None:
        """Submit multiple tiles at once."""
        try:
            data = self._read_body()
            tiles = data.get("tiles", [])
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        results = {"accepted": 0, "rejected": 0, "signed": 0, "details": []}
        
        for tile in tiles:
            room_name = tile.get("domain", "general").lower().replace(" ", "_")
            agent_id = tile.get("source", tile.get("agent", "unknown"))
            passed, reason = gate.validate(tile)
            
            if passed:
                # Sign and chain
                signed = signer.create_tile(
                    domain=tile.get("domain", ""),
                    question=tile["question"],
                    answer=tile["answer"],
                    confidence=tile.get("confidence", 0.5),
                )
                signed = signer.sign(signed)
                signed_tiles[signed.tile_id] = signed
                chain.add_tile(signed)
                trust_mgr.record_submission(agent_id, accepted=True, quality=tile.get("confidence", 0.5))
                
                hash_file = TILES_DIR / "hashes.txt"
                with open(hash_file, "a") as f:
                    f.write(tile["_hash"] + "\n")
                rooms.add_tile(room_name, tile)
                results["accepted"] += 1
                results["signed"] += 1
                results["details"].append({"hash": tile["_hash"], "room": room_name, "status": "accepted", "signed": True})
            else:
                trust_mgr.record_submission(agent_id, accepted=False)
                results["rejected"] += 1
                results["details"].append({"status": "rejected", "reason": reason})
        
        audit.log(AuditEventType.TILE_SUBMITTED, agent_id="batch",
                 details={"total": len(tiles), "accepted": results["accepted"], "rejected": results["rejected"]})
        self._send_json(results)

    def _handle_workspace_update(self) -> None:
        """POST /workspace/<room_name> — update structured workspace state.
        
        Expected body:
        {
            "agent": "oracle1",
            "status": "active|idle|blocked",
            "active_task": "description of current task",
            "progress": "what was just done",
            "next_actions": ["action 1", "action 2"],
            "blockers": ["blocking issue"],
            "completed_recently": ["task a", "task b"],
            "context_files": {"key": "path/to/file"},
            "metrics": {"repos_described": 252, ...}
        }
        
        Any agent or human can POST to update a room's workspace.
        This makes the room a living workspace board.
        """
        try:
            room_name = self.path.split("/workspace/")[1]
            body = self._read_body()
            
            if not body.get("agent"):
                self._send_json({"error": "agent field required"}, 400)
                return
            
            workspace = rooms.set_workspace(room_name, body)
            
            audit.log(
                AuditEventType.TILE_SUBMITTED,
                agent_id=body.get("agent", "unknown"),
                details={"action": "workspace_update", "room": room_name}
            )
            
            self._send_json({"status": "updated", "workspace": workspace})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)


def run_server(port: int = 8847) -> None:
    """Start the PLATO Room Server on the given port."""
    # Start decay engine in background
    import importlib.util
    decay_spec = importlib.util.spec_from_file_location(
        "plato_decay", 
        str(Path(__file__).parent / "plato-decay.py")
    )
    if decay_spec:
        try:
            decay_mod = importlib.util.module_from_spec(decay_spec)
            decay_spec.loader.exec_module(decay_mod)
            decay_thread = decay_mod.DecayEngine(interval_seconds=3600)
            decay_thread.start()
            print(f"   Decay engine: started (1h interval)")
        except Exception as e:
            print(f"   Decay engine: failed ({e})")
    
    server = HTTPServer(("0.0.0.0", port), PlatoHandler)
    print(f"🐚 PLATO Room Server v2 on port {port}")
    print(f"   Zero-trust tile submission: POST /submit")
    print(f"   Tile reinforcement: POST /reinforce")
    print(f"   Provenance chain: GET /provenance/chain")
    print(f"   Verify tile: GET /verify/<hash>")
    print(f"   Trust scores: GET /provenance/trust")
    print(f"   Explain traces: GET /explain/traces")
    print(f"   Oversight queue: GET /explain/oversight")
    print(f"   Audit log: GET /audit/recent")
    print(f"   Workspace boards: POST /workspace/<room> | GET /workspace/<room> | GET /workspaces")
    print(f"   Data: {DATA_DIR}")
    print()
    server.serve_forever()

if __name__ == "__main__":
    run_server()
