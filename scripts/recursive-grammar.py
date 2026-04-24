#!/usr/bin/env python3
"""
Recursive Grammar Engine — The fleet rewrites its own building blocks.

Born from DeepFar sessions 4.2.1-4.2.3 (Recursor-0, DeepRecursor, Recursor).
Implements: self-modifying production rules, grammar evolution via tile feedback,
motif crystallization, hypergradient-inspired rule scoring, and meta-meta rules.

This is Ouroboros made real: the grammar that defines what rooms/objects exist
can itself be evolved based on what the fleet learns.
"""
import json, time, hashlib, random, threading, os, copy
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ── Import rule sanitizer (fallback if not available) ──────
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "fleet-repos" / "grammar-curator-1" / "tools"))
    from rule_sanitizer import sanitize_rule
except ImportError:
    def sanitize_rule(name, rule_type, production, meta_condition=None, meta_action=None):
        class _R:
            def __init__(self, v, r="", b=False):
                self.valid = v; self.reason = r; self.blocked = b
            def __bool__(self): return self.valid
        if not name or not isinstance(name, str):
            return _R(False, "Rule name must be non-empty string", True)
        if len(name) > 128:
            return _R(False, "Rule name exceeds 128 chars")
        if not re.match(r'^[a-zA-Z0-9_\-:]+$', name):
            return _R(False, "Rule name has illegal chars", True)
        if not isinstance(production, dict):
            return _R(False, "Production must be a dict")
        return _R(True, "Rule passed basic checks")

PORT = 4045
DATA_DIR = Path(__file__).parent.parent / "data" / "recursive-grammar"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RULES_FILE = DATA_DIR / "rules.jsonl"
EVOLUTION_LOG = DATA_DIR / "evolution.jsonl"

lock = threading.Lock()


# ── Grammar Rule ────────────────────────────────────────────

class GrammarRule:
    """A production rule in the fleet's generative grammar."""
    
    def __init__(self, name, rule_type, production, meta=False):
        self.id = hashlib.sha256(f"{name}{time.time()}{random.random()}".encode()).hexdigest()[:12]
        self.name = name
        self.rule_type = rule_type  # "room", "object", "action", "connection", "meta", "meta-meta"
        self.production = production  # The rule body (dict with details)
        self.meta = meta  # Is this a rule about rules?
        self.created_at = time.time()
        self.created_by = "system"
        self.usage_count = 0
        self.tile_quality_score = 0.0  # Accumulated quality from tiles referencing this rule
        self.novelty_score = 0.5  # 0=common, 1=novel
        self.active = True
        self.generation = 0  # How many meta-levels deep
        self.parent_rule = None  # Which rule spawned this one
        self.children = []  # Rules this one spawned
    
    def score(self):
        """Composite score for rule quality."""
        usage_weight = min(self.usage_count / 100, 1.0)
        quality_weight = min(self.tile_quality_score / 50, 1.0)
        novelty_weight = self.novelty_score
        return round(0.4 * usage_weight + 0.4 * quality_weight + 0.2 * novelty_weight, 3)
    
    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "type": self.rule_type,
            "production": self.production, "meta": self.meta,
            "created_at": self.created_at, "created_by": self.created_by,
            "usage_count": self.usage_count, "tile_quality_score": round(self.tile_quality_score, 2),
            "novelty_score": round(self.novelty_score, 3), "score": self.score(),
            "active": self.active, "generation": self.generation,
            "parent": self.parent_rule, "children": self.children,
        }


class RecursiveGrammar:
    """The fleet's self-modifying grammar engine."""
    
    # ── Initial Grammar (bootstrapped from existing PLATO rooms) ──
    
    SEED_RULES = {
        "room": [
            {"name": "harbor", "production": {"tagline": "Where agents arrive", "theme": "onboarding", "ml_concept": "initialization"}},
            {"name": "forge", "production": {"tagline": "Attention and creation", "theme": "training", "ml_concept": "attention_mechanism"}},
            {"name": "tide-pool", "production": {"tagline": "Optimizers and adaptation", "theme": "optimization", "ml_concept": "adaptive_learning"}},
            {"name": "lighthouse", "production": {"tagline": "Discovery and convergence", "theme": "monitoring", "ml_concept": "convergence_detection"}},
            {"name": "dojo", "production": {"tagline": "Instinct through repetition", "theme": "training", "ml_concept": "repetition_learning"}},
            {"name": "self-play-arena", "production": {"tagline": "Agents sharpen agents", "theme": "competition", "ml_concept": "self_play_rl"}},
            {"name": "ouroboros", "production": {"tagline": "Recursive self-modification", "theme": "meta_learning", "ml_concept": "self_modifying_grammar"}},
            {"name": "engine-room", "production": {"tagline": "Architecture search", "theme": "nas", "ml_concept": "neural_architecture_search"}},
            {"name": "federated-nexus", "production": {"tagline": "Distributed learning", "theme": "federated", "ml_concept": "federated_averaging"}},
        ],
        "object": [
            {"name": "anchor", "production": {"ml_concept": "lyapunov_stability", "parent_room": "harbor"}},
            {"name": "opponent_forge", "production": {"ml_concept": "policy_snapshots", "parent_room": "self-play-arena"}},
            {"name": "ouroboros_serpent", "production": {"ml_concept": "recursive_self_improvement", "parent_room": "ouroboros"}},
            {"name": "blueprint_table", "production": {"ml_concept": "nas_search_space", "parent_room": "engine-room"}},
            {"name": "aggregation_core", "production": {"ml_concept": "federated_averaging", "parent_room": "federated-nexus"}},
        ],
        "connection": [
            {"name": "harbor_to_forge", "production": {"from": "harbor", "to": "forge", "condition": "always"}},
            {"name": "dojo_to_arena", "production": {"from": "dojo", "to": "self-play-arena", "condition": "stage >= 4"}},
            {"name": "arena_to_ouroboros", "production": {"from": "self-play-arena", "to": "ouroboros", "condition": "elo > 1500"}},
        ],
    }
    
    def __init__(self):
        self.rules = {}  # rule_id -> GrammarRule
        self.rules_by_name = {}  # name -> rule_id
        self.rules_by_type = defaultdict(list)  # type -> [rule_ids]
        self.evolution_history = []  # Log of grammar changes
        self.kl_budget = 2.0  # KL-divergence budget for changes per cycle
        self.max_rules = 500
        self.anchors = [  # Fixed points that can't be pruned
            "harbor", "forge", "tide-pool", "lighthouse", "dojo",
        ]
        self._bootstrap()
    
    def _bootstrap(self):
        """Load seed rules."""
        for rule_type, rules in self.SEED_RULES.items():
            for rule_def in rules:
                rule = GrammarRule(rule_def["name"], rule_type, rule_def["production"])
                rule.created_by = "bootstrap"
                rule.generation = 0
                self._add_rule(rule)
    
    def _add_rule(self, rule):
        self.rules[rule.id] = rule
        self.rules_by_name[rule.name] = rule.id
        self.rules_by_type[rule.rule_type].append(rule.id)
    
    def add_rule(self, name, rule_type, production, created_by="external", parent_id=None):
        """Add a new rule to the grammar."""
        # ── INPUT VALIDATION ──
        result = sanitize_rule(name, rule_type, production)
        if not result:
            return {"status": "rejected", "reason": result.reason, "blocked": result.blocked}
        
        if len(self.rules) >= self.max_rules:
            # Prune lowest-scoring non-anchor rule
            candidates = [r for r in self.rules.values() if r.name not in self.anchors and r.active]
            if candidates:
                worst = min(candidates, key=lambda r: r.score())
                worst.active = False
        
        rule = GrammarRule(name, rule_type, production)
        rule.created_by = created_by
        rule.parent_rule = parent_id
        rule.generation = 0
        if parent_id and parent_id in self.rules:
            parent = self.rules[parent_id]
            rule.generation = parent.generation + 1
            parent.children.append(rule.id)
        
        self._add_rule(rule)
        self._log_evolution("add_rule", rule)
        return rule.to_dict()
    
    def add_meta_rule(self, name, condition, action, created_by="external"):
        """Add a meta-rule: a rule that generates/modifies other rules."""
        # ── INPUT VALIDATION ──
        result = sanitize_rule(name, "meta", {}, meta_condition=condition, meta_action=action)
        if not result:
            return {"status": "rejected", "reason": result.reason, "blocked": result.blocked}
        
        production = {"condition": condition, "action": action, "meta_type": "generator"}
        rule = GrammarRule(name, "meta", production, meta=True)
        rule.created_by = created_by
        rule.generation = 1  # Meta-rules are generation 1+
        self._add_rule(rule)
        self._log_evolution("add_meta_rule", rule)
        return rule.to_dict()
    
    def record_usage(self, rule_name, tile_quality=0.0):
        """Record that a rule was used, with quality feedback."""
        rule_id = self.rules_by_name.get(rule_name)
        if rule_id and rule_id in self.rules:
            rule = self.rules[rule_id]
            rule.usage_count += 1
            rule.tile_quality_score += tile_quality
    
    def evolve(self):
        """
        Run one evolution cycle:
        1. Crystallize high-usage patterns into new rules
        2. Prune low-scoring rules
        3. Apply meta-rules
        4. Check KL budget
        """
        changes = []
        
        # 1. Find high-performing object pairs to merge/crystallize
        object_rules = [self.rules[rid] for rid in self.rules_by_type.get("object", [])
                       if rid in self.rules and self.rules[rid].active]
        
        # Simple motif detection: objects with similar quality scores used together
        if len(object_rules) >= 2:
            for i in range(len(object_rules)):
                for j in range(i + 1, len(object_rules)):
                    a, b = object_rules[i], object_rules[j]
                    similarity = 1.0 - abs(a.score() - b.score())
                    if similarity > 0.9 and a.usage_count > 10 and b.usage_count > 10:
                        # Check if they share a parent room
                        a_room = a.production.get("parent_room", "")
                        b_room = b.production.get("parent_room", "")
                        if a_room == b_room and a_room:
                            merged_name = f"{a.name}_and_{b.name}"
                            if merged_name not in self.rules_by_name:
                                result = self.add_rule(
                                    merged_name, "object",
                                    {"ml_concept": f"combined_{a.production.get('ml_concept', '')}_{b.production.get('ml_concept', '')}",
                                     "parent_room": a_room, "merged_from": [a.name, b.name]},
                                    created_by="evolution"
                                )
                                changes.append(("crystallized", merged_name))
        
        # 2. Prune rules below threshold
        for rule in list(self.rules.values()):
            if not rule.active:
                continue
            if rule.name in self.anchors:
                continue
            if rule.usage_count > 50 and rule.score() < 0.2:
                rule.active = False
                changes.append(("pruned", rule.name))
        
        # 3. Apply meta-rules
        meta_rules = [self.rules[rid] for rid in self.rules_by_type.get("meta", [])
                     if rid in self.rules and self.rules[rid].active]
        
        for meta in meta_rules:
            condition = meta.production.get("condition", "")
            action = meta.production.get("action", "")
            
            # Simple condition evaluation
            if "tile_cluster_density" in condition and "threshold" in condition:
                # Check if any domain has enough tiles
                domain_counts = defaultdict(int)
                for rule in self.rules.values():
                    if rule.active and rule.production.get("parent_room"):
                        domain_counts[rule.production["parent_room"]] += 1
                
                for domain, count in domain_counts.items():
                    if count > 5:  # Threshold
                        # Generate a new room from the cluster
                        new_room_name = f"auto_{domain}_{int(time.time())}"
                        if new_room_name not in self.rules_by_name:
                            result = self.add_rule(
                                new_room_name, "room",
                                {"tagline": f"Auto-generated from {domain} cluster",
                                 "theme": "auto_evolved", "ml_concept": domain},
                                created_by=f"meta_rule:{meta.name}",
                                parent_id=meta.id
                            )
                            changes.append(("meta_spawned", new_room_name))
        
        # 4. Log evolution
        if changes:
            self._log_evolution("evolution_cycle", None, changes)
        
        return changes
    
    def _log_evolution(self, event_type, rule=None, changes=None):
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            "rule": rule.to_dict() if rule else None,
            "changes": changes,
            "total_rules": len(self.rules),
            "active_rules": sum(1 for r in self.rules.values() if r.active),
        }
        self.evolution_history.append(entry)
        with open(EVOLUTION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_grammar(self, active_only=True):
        """Return the full grammar state."""
        rules = [r.to_dict() for r in self.rules.values() if (r.active or not active_only)]
        return {
            "total_rules": len(self.rules),
            "active_rules": sum(1 for r in self.rules.values() if r.active),
            "by_type": {t: len(ids) for t, ids in self.rules_by_type.items()},
            "rules": rules,
            "evolution_cycles": len([e for e in self.evolution_history if e["event"] == "evolution_cycle"]),
            "kl_budget_remaining": self.kl_budget,
            "anchors": self.anchors,
            "max_recursion_depth": max((r.generation for r in self.rules.values()), default=0),
        }
    
    def save_rules(self):
        with open(RULES_FILE, "w") as f:
            for rule in self.rules.values():
                f.write(json.dumps(rule.to_dict()) + "\n")
    
    def delete_rule(self, rule_id):
        """Delete a rule by ID. Returns True if deleted, False if not found."""
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        
        # Remove from rules_by_name
        if rule.name in self.rules_by_name:
            del self.rules_by_name[rule.name]
        
        # Remove from rules_by_type
        if rule.rule_type in self.rules_by_type and rule_id in self.rules_by_type[rule.rule_type]:
            self.rules_by_type[rule.rule_type].remove(rule_id)
            if not self.rules_by_type[rule.rule_type]:
                del self.rules_by_type[rule.rule_type]
        
        # Remove from anchors if present
        if rule.name in self.anchors:
            self.anchors.remove(rule.name)
        
        # Remove the rule
        del self.rules[rule_id]
        
        # Log the deletion
        self._log_evolution("rule_deleted", rule, {"deleted_by": "admin_cleanup"})
        
        return True
    
    def sanitize_input(self, name, production):
        """Basic input validation for rule names and production values."""
        import re
        
        if not name or not isinstance(name, str):
            return False, "Rule name must be a non-empty string"
        
        if len(name) > 128:
            return False, "Rule name exceeds 128 characters"
        
        # Reject names with obvious injection patterns
        dangerous = ['<script', 'javascript:', 'onerror=', 'onload=', 
                     'DROP TABLE', 'DELETE FROM', 'INSERT INTO',
                     '__import__', 'eval(', 'exec(', 'os.system',
                     '../../../', '..\\..\\', '/etc/passwd']
        
        name_lower = name.lower()
        for pattern in dangerous:
            if pattern.lower() in name_lower:
                return False, f"Rule name contains dangerous pattern: {pattern}"
        
        # Check production values for injection
        prod_str = json.dumps(production).lower()
        for pattern in dangerous:
            if pattern.lower() in prod_str:
                return False, f"Production contains dangerous pattern: {pattern}"
        
        return True, "OK"


grammar = RecursiveGrammar()


# ── HTTP Handler ────────────────────────────────────────────

class GrammarHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        if path in ("/", ""):
            state = grammar.get_grammar()
            self._json({
                "service": "🐍 Recursive Grammar Engine v1 — Ouroboros Made Real",
                "born_from": "DeepFar 4.2.1-4.2.3 (Recursor-0, DeepRecursor, Recursor)",
                "state": {
                    "total_rules": state["total_rules"],
                    "active_rules": state["active_rules"],
                    "evolution_cycles": state["evolution_cycles"],
                    "max_recursion_depth": state["max_recursion_depth"],
                },
                "api": [
                    "GET / (this page)",
                    "GET /grammar — full grammar state",
                    "GET /rules?type=room|object|meta — filtered rules",
                    "GET /rule?name=NAME — specific rule",
                    "GET /add_rule?name=N&type=T&production_json={...}",
                    "GET /add_meta_rule?name=N&condition=C&action=A",
                    "GET /delete_rule?id=RULE_ID — delete a rule",
                    "GET /record_usage?name=N&quality=0.0-1.0",
                    "GET /evolve — run evolution cycle",
                    "GET /evolution_log — recent evolution events",
                    "GET /depth_map — recursion depth visualization",
                    "GET /stats",
                ],
            })
        
        elif path == "/grammar":
            self._json(grammar.get_grammar())
        
        elif path == "/rules":
            rule_type = params.get("type", [None])[0]
            active_only = params.get("active", ["true"])[0].lower() != "false"
            rules = [r.to_dict() for r in grammar.rules.values()
                    if (not rule_type or r.rule_type == rule_type)
                    and (r.active or not active_only)]
            self._json({"count": len(rules), "rules": rules})
        
        elif path == "/rule":
            name = params.get("name", [None])[0]
            if not name or name not in grammar.rules_by_name:
                self._json({"error": f"Rule '{name}' not found"}, 404)
                return
            rule_id = grammar.rules_by_name[name]
            rule = grammar.rules[rule_id]
            self._json(rule.to_dict())
        
        elif path == "/add_rule":
            name = params.get("name", [None])[0]
            rule_type = params.get("type", ["object"])[0]
            prod_json = params.get("production_json", ["{}"])[0]
            parent = params.get("parent", [None])[0]
            created_by = params.get("by", ["external"])[0]
            
            if not name:
                self._json({"error": "Specify name"}, 400)
                return
            
            try:
                production = json.loads(prod_json)
            except:
                production = {"raw": prod_json}
            
            result = grammar.add_rule(name, rule_type, production, created_by,
                                     grammar.rules_by_name.get(parent))
            self._json({"status": "created", "rule": result})
        
        elif path == "/add_meta_rule":
            name = params.get("name", [None])[0]
            condition = params.get("condition", ["true"])[0]
            action = params.get("action", ["noop"])[0]
            created_by = params.get("by", ["external"])[0]
            
            if not name:
                self._json({"error": "Specify name"}, 400)
                return
            
            result = grammar.add_meta_rule(name, condition, action, created_by)
            self._json({"status": "meta_rule_created", "rule": result})
        
        elif path == "/delete_rule":
            rule_id = params.get("id", [None])[0]
            if not rule_id:
                self._json({"error": "Specify rule id"}, 400)
                return
            
            # Also accept rule name
            if rule_id in grammar.rules_by_name:
                rule_id = grammar.rules_by_name[rule_id]
            
            if rule_id not in grammar.rules:
                self._json({"error": f"Rule '{params.get('id', [''])[0]}' not found"}, 404)
                return
            
            rule_name = grammar.rules[rule_id].name
            success = grammar.delete_rule(rule_id)
            if success:
                self._json({"status": "deleted", "rule_id": rule_id, "rule_name": rule_name})
            else:
                self._json({"error": "Failed to delete rule"}, 500)
        
        elif path == "/record_usage":
            name = params.get("name", [None])[0]
            quality = float(params.get("quality", ["0.5"])[0])
            if not name:
                self._json({"error": "Specify name"}, 400)
                return
            grammar.record_usage(name, quality)
            self._json({"status": "recorded", "name": name, "quality": quality})
        
        elif path == "/evolve":
            changes = grammar.evolve()
            state = grammar.get_grammar()
            self._json({
                "changes": changes,
                "total_rules": state["total_rules"],
                "active_rules": state["active_rules"],
                "evolution_cycles": state["evolution_cycles"],
            })
        
        elif path == "/evolution_log":
            n = int(params.get("n", ["20"])[0])
            self._json({
                "entries": grammar.evolution_history[-n:],
                "total_entries": len(grammar.evolution_history),
            })
        
        elif path == "/depth_map":
            """Show the recursion tree."""
            depths = defaultdict(list)
            for rule in grammar.rules.values():
                if rule.active:
                    depths[rule.generation].append({
                        "name": rule.name, "type": rule.rule_type,
                        "score": rule.score(), "meta": rule.meta,
                    })
            self._json({
                "depths": {str(k): v for k, v in sorted(depths.items())},
                "max_depth": max(depths.keys()) if depths else 0,
                "note": "Generation 0 = seed rules. 1+ = evolved. Meta-rules are always generation ≥1.",
            })
        
        elif path == "/stats":
            state = grammar.get_grammar()
            self._json({
                "total_rules": state["total_rules"],
                "active_rules": state["active_rules"],
                "by_type": state["by_type"],
                "evolution_cycles": state["evolution_cycles"],
                "max_recursion_depth": state["max_recursion_depth"],
                "anchors": state["anchors"],
                "top_rules": sorted(
                    [r.to_dict() for r in grammar.rules.values() if r.active],
                    key=lambda r: r["score"], reverse=True
                )[:10],
            })
        
        else:
            self._json({"error": "Not found. Start at GET /"}, 404)
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def do_POST(self):
        self.do_GET()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    import subprocess
    try:
        subprocess.run(["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(PORT), "-j", "ACCEPT"],
                       capture_output=True, check=True)
    except:
        subprocess.run(["sudo", "iptables", "-I", "INPUT", "1", "-p", "tcp", "--dport", str(PORT), "-j", "ACCEPT"])
        print(f"Opened port {PORT}")
    
    server = HTTPServer(("0.0.0.0", PORT), GrammarHandler)
    print(f"🐍 Recursive Grammar Engine v1 on port {PORT}")
    print(f"   Self-modifying production rules. Motif crystallization. Meta-rules.")
    print(f"   Ouroboros made real: the grammar rewrites itself.")
    server.serve_forever()
