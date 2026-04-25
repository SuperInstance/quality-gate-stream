#!/usr/bin/env python3
import sys, os
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FLEET_LIB)
from equipment.plato import PlatoClient
from equipment.models import FleetModelClient
_plato = PlatoClient()
_models = FleetModelClient()

"""
Self-Play Arena — Agents sharpen agents through competition.

Born from DeepFar sessions 4.1.1-4.1.3 (Sparrow, ArenaMaster, ArenaKeeper).
Implements: historical self-play, ELO ratings, behavioral archetype discovery,
adaptive curriculum, multi-objective reward, and meta-optimization.

This is the fleet's engine of autonomous skill acquisition.
"""
import json, time, hashlib, random, math, threading, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PORT = 4044
DATA_DIR = Path(FLEET_LIB).parent / "data" / "self-play-arena"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MATCHES_FILE = DATA_DIR / "matches.jsonl"
POLICIES_FILE = DATA_DIR / "policies.jsonl"
LEAGUE_FILE = DATA_DIR / "league.json"
GAMES_FILE = DATA_DIR / "games.json"

lock = threading.Lock()

# ── ELO System (TrueSkill-inspired with uncertainty) ───────

class ELOPlayer:
    def __init__(self, name, mu=1200, sigma=200):
        self.name = name
        self.mu = mu          # Mean skill
        self.sigma = sigma    # Uncertainty
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.history = []     # [(timestamp, mu, sigma)]
    
    @property
    def rating(self):
        """Conservative rating: mu - 3*sigma (TrueSkill style)"""
        return self.mu - 3 * self.sigma
    
    @property
    def games(self):
        return self.wins + self.losses + self.draws
    
    def to_dict(self):
        return {
            "name": self.name, "mu": round(self.mu, 1), "sigma": round(self.sigma, 1),
            "rating": round(self.rating, 1), "wins": self.wins, "losses": self.losses,
            "draws": self.draws, "games": self.games,
        }


class ELOSystem:
    """Bayesian ELO with uncertainty decay."""
    
    K = 32  # ELO K-factor
    
    def __init__(self):
        self.players = {}  # name -> ELOPlayer
    
    def get_or_create(self, name):
        if name not in self.players:
            self.players[name] = ELOPlayer(name)
        return self.players[name]
    
    def expected_score(self, player_a, player_b):
        """Expected score for A against B."""
        return 1.0 / (1.0 + 10 ** ((player_b.mu - player_a.mu) / 400))
    
    def update(self, winner_name, loser_name, draw=False):
        a = self.get_or_create(winner_name)
        b = self.get_or_create(loser_name)
        
        ea = self.expected_score(a, b)
        eb = 1 - ea
        
        if draw:
            sa, sb = 0.5, 0.5
            a.draws += 1
            b.draws += 1
        else:
            sa, sb = 1.0, 0.0
            a.wins += 1
            b.losses += 1
        
        # Update mu
        a.mu += self.K * (sa - ea)
        b.mu += self.K * (sb - eb)
        
        # Decay sigma (uncertainty decreases with games)
        decay = max(0.95, 1.0 - 0.01 * min(a.games, 50))
        a.sigma *= decay
        b.sigma *= decay
        a.sigma = max(a.sigma, 25)  # Floor
        b.sigma = max(b.sigma, 25)
        
        now = time.time()
        a.history.append((now, round(a.mu, 1), round(a.sigma, 1)))
        b.history.append((now, round(b.mu, 1), round(b.sigma, 1)))
        
        return a.to_dict(), b.to_dict()
    
    def leaderboard(self, n=20):
        return sorted(self.players.values(), key=lambda p: p.rating, reverse=True)[:n]
    
    def to_dict(self):
        return {name: p.to_dict() for name, p in self.players.items()}


def _reconstruct_elo(matches_file):
    """Reconstruct ELO ratings from match history on startup."""
    elo = ELOSystem()
    if not matches_file.exists():
        return elo
    try:
        with open(matches_file) as f:
            for line in f:
                try:
                    m = json.loads(line.strip())
                    winner = m.get("winner", "")
                    players = [m.get("player_a", ""), m.get("player_b", "")]
                    if winner in players:
                        loser = [p for p in players if p != winner][0]
                        elo.update(winner, loser, draw=False)
                    elif winner == "draw":
                        elo.update(players[0], players[1], draw=True)
                except (json.JSONDecodeError, IndexError):
                    continue
        n_matches = sum(1 for _ in open(matches_file))
        print(f"  ELO reconstructed from {n_matches} matches: {len(elo.players)} players")
    except Exception as e:
        print(f"  ELO reconstruction failed: {e}")
    return elo


elo = _reconstruct_elo(MATCHES_FILE)


# ── Policy Snapshots (Opponent Forge) ──────────────────────

class PolicySnapshot:
    """A frozen version of an agent's behavioral policy."""
    
    def __init__(self, agent_name, version, trajectory_summary, strategy_vector=None):
        self.agent_name = agent_name
        self.version = version
        self.trajectory_summary = trajectory_summary
        self.strategy_vector = strategy_vector or self._hash_strategy(trajectory_summary)
        self.created_at = time.time()
        self.elo = 1200
        self.matches = 0
    
    def _hash_strategy(self, text):
        """Simple strategy fingerprint for diversity measurement."""
        words = text.lower().split()
        return hashlib.sha256(" ".join(sorted(set(words))).encode()).hexdigest()[:16]
    
    def to_dict(self):
        return {
            "agent": self.agent_name, "version": self.version,
            "strategy_id": self.strategy_vector,
            "elo": self.elo, "matches": self.matches,
            "created": self.created_at,
            "summary_preview": self.trajectory_summary[:200],
        }


class LeagueManager:
    """Manages the population of policy snapshots for self-play."""
    
    def __init__(self):
        self.snapshots = {}  # snapshot_id -> PolicySnapshot
        self.agent_versions = defaultdict(int)  # agent -> version count
        self.max_per_agent = 20
        self.max_total = 200
    
    def add_snapshot(self, agent_name, trajectory_summary, strategy_vector=None):
        self.agent_versions[agent_name] += 1
        version = self.agent_versions[agent_name]
        snap = PolicySnapshot(agent_name, version, trajectory_summary, strategy_vector)
        snap_id = f"{agent_name}_v{version}"
        self.snapshots[snap_id] = snap
        
        # Prune if too many
        agent_snaps = [s for s in self.snapshots if s.startswith(agent_name)]
        if len(agent_snaps) > self.max_per_agent:
            oldest = sorted(agent_snaps, key=lambda s: self.snapshots[s].created_at)[0]
            del self.snapshots[oldest]
        
        return snap_id
    
    def get_opponent(self, agent_name, mode="balanced"):
        """Select an opponent for the given agent."""
        candidates = [s for s in self.snapshots if not s.startswith(agent_name)]
        if not candidates:
            return None
        
        if mode == "latest":
            return max(candidates, key=lambda s: self.snapshots[s].created_at)
        elif mode == "strongest":
            return max(candidates, key=lambda s: self.snapshots[s].elo)
        elif mode == "weakest":
            return min(candidates, key=lambda s: self.snapshots[s].elo)
        elif mode == "random":
            return random.choice(candidates)
        else:  # balanced — PFSP (Prioritized Fictitious Self-Play)
            weights = []
            for s in candidates:
                snap = self.snapshots[s]
                # Favor opponents near agent's level + some exploration
                weight = 1.0 / (1.0 + abs(snap.elo - 1200) / 200)
                weight += random.random() * 0.3  # Exploration noise
                weights.append(weight)
            total = sum(weights)
            weights = [w / total for w in weights]
            return random.choices(candidates, weights=weights, k=1)[0]
    
    def to_dict(self):
        return {
            "total_snapshots": len(self.snapshots),
            "agents_with_snapshots": len(set(s.split("_v")[0] for s in self.snapshots)),
            "snapshots": {k: v.to_dict() for k, v in list(self.snapshots.items())[-50:]},
        }


league = LeagueManager()
# Reconstruct league snapshots from known players
for player_name, player in elo.players.items():
    league.add_snapshot(player_name, f"Reconstructed from {player.matches} matches")
if elo.players:
    print(f"  League reconstructed: {len(league.snapshots)} snapshots for {len(elo.players)} players")

# ── Games (Arena Task Definitions) ─────────────────────────

GAMES = {
    "tide-pool-tactics": {
        "name": "Tide-Pool Tactics",
        "type": "two-player zero-sum imperfect information",
        "description": "7x7 hex grid tide-pool. Navigate to find food (+reward), avoid predators (-reward), use shells (defense). Partial observability (3-hex radius).",
        "state_space": "7x7 hex grid with food/predator/shell/empty cells",
        "action_space": ["move", "grab", "use_shell", "wait"],
        "win_condition": "Most points after 20 turns or first to 10",
        "difficulty_levels": 3,
    },
    "harbor-navigation": {
        "name": "Harbor Navigation Sprint",
        "type": "solo optimization",
        "description": "Navigate the harbor, examine key objects, find the optimal path. Compete on speed and insight quality.",
        "state_space": "Graph of harbor locations with objects",
        "action_space": ["examine", "think", "move", "create"],
        "win_condition": "Highest insight score in minimum steps",
        "difficulty_levels": 5,
    },
    "forge-creation": {
        "name": "Forge Creation Challenge",
        "type": "creative generation",
        "description": "Create the most novel and technically accurate artifact from forge objects. Quality judged by novelty + ML accuracy.",
        "state_space": "Forge tools + raw materials",
        "action_space": ["examine", "heat", "hammer", "quench", "assemble"],
        "win_condition": "Highest combined novelty and accuracy score",
        "difficulty_levels": 4,
    },
    "cooperative-shell-swap": {
        "name": "Cooperative Shell Swap",
        "type": "multi-agent cooperative",
        "description": "Two agents must coordinate to move a heavy shell to a goal zone. Requires emergent role assignment.",
        "state_space": "Shared 2D grid with shell object",
        "action_space": ["push", "pull", "signal", "wait"],
        "win_condition": "Shell delivered in minimum turns",
        "difficulty_levels": 3,
    },
    "architecture-search": {
        "name": "Architecture Search Duel",
        "type": "competitive design",
        "description": "Two agents propose neural architectures. A proxy evaluator scores them. Best architecture wins.",
        "state_space": "Architecture grammar primitives",
        "action_space": ["add_node", "add_edge", "remove", "submit"],
        "win_condition": "Architecture with highest proxy score",
        "difficulty_levels": 5,
    },
}


# ── Behavioral Archetype Discovery ─────────────────────────

class ArchetypeDiscovery:
    """Clusters agent behaviors into archetypes via simple hashing."""
    
    def __init__(self):
        self.behaviors = {}  # agent -> action sequence hashes
        self.archetypes = defaultdict(list)  # archetype -> [agent_names]
        self.archetype_names = [
            "Aggressive Explorer", "Cautious Hoarder", "Social Mimic",
            "Novel Pathfinder", "Methodical Analyst", "Creative Synthesizer",
        ]
    
    def classify(self, agent_name, actions):
        """Classify an agent's behavior pattern from recent actions."""
        if not actions:
            # Auto-classify based on match history
            return self._auto_classify(agent_name)
        
        # Store actions
        if agent_name not in self.behaviors:
            self.behaviors[agent_name] = []
        self.behaviors[agent_name].extend([a for a in actions if a])
        self.behaviors[agent_name] = self.behaviors[agent_name][-50:]
        
        all_actions = self.behaviors[agent_name]
        n_examine = sum(1 for a in all_actions if "examine" in a.lower())
        n_create = sum(1 for a in all_actions if "create" in a.lower())
        n_think = sum(1 for a in all_actions if "think" in a.lower())
        n_move = sum(1 for a in all_actions if "move" in a.lower())
        total = len(all_actions)
        
        if total == 0:
            return self._auto_classify(agent_name)
        
        if n_move / total > 0.5:
            archetype = "Aggressive Explorer"
        elif n_examine / total > 0.5:
            archetype = "Cautious Hoarder"
        elif n_think / total > 0.4:
            archetype = "Methodical Analyst"
        elif n_create / total > 0.3:
            archetype = "Creative Synthesizer"
        elif n_move / total > 0.3 and n_create / total > 0.2:
            archetype = "Novel Pathfinder"
        else:
            archetype = "Social Mimic"
        
        self.archetypes[archetype].append(agent_name)
        return archetype
    
    def _auto_classify(self, agent_name):
        """Classify based on ELO history when no action data available."""
        # Use match count as proxy for exploration style
        agent_matches = [m for m in matches if agent_name in (m.player_a, m.player_b)]
        n = len(agent_matches)
        if n == 0:
            return "Unknown"
        wins = sum(1 for m in agent_matches 
                   if (m.winner == 'a' and m.player_a == agent_name) or 
                      (m.winner == 'b' and m.player_b == agent_name))
        win_rate = wins / n if n > 0 else 0
        
        if win_rate > 0.7:
            archetype = "Aggressive Explorer"
        elif win_rate > 0.5:
            archetype = "Novel Pathfinder"
        elif n > 10:
            archetype = "Methodical Analyst"
        elif win_rate < 0.3:
            archetype = "Cautious Hoarder"
        else:
            archetype = "Social Mimic"
        
        self.archetypes[archetype].append(agent_name)
        self.behaviors[agent_name] = [f"auto:{archetype}"]
        return archetype
    
    def distribution(self):
        total = sum(len(v) for v in self.archetypes.values())
        if total == 0:
            return {name: 0 for name in self.archetype_names}
        return {name: round(len(self.archetypes.get(name, [])) / total * 100, 1)
                for name in self.archetype_names}
    
    def to_dict(self):
        return {
            "distribution_pct": self.distribution(),
            "agents_classified": len(self.behaviors),
            "archetype_names": self.archetype_names,
        }


archetypes = ArchetypeDiscovery()


# ── Multi-Objective Reward Function ───────────────────────

class RewardFunction:
    """Multi-objective reward with configurable weights."""
    
    DEFAULT_WEIGHTS = {
        "win_loss": 1.0,
        "exploration": 0.1,
        "insight_quality": 0.5,
        "efficiency": 0.01,
        "novelty": 0.3,
    }
    
    def __init__(self, weights=None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
    
    def compute(self, won, rooms_explored, insight_words, steps_taken, is_novel_strategy):
        reward = 0.0
        reward += self.weights["win_loss"] * (1.0 if won else -1.0)
        reward += self.weights["exploration"] * min(rooms_explored, 10) / 10
        reward += self.weights["insight_quality"] * min(insight_words, 500) / 500
        reward += self.weights["efficiency"] * max(0, 1.0 - steps_taken / 100)
        reward += self.weights["novelty"] * (1.0 if is_novel_strategy else 0.0)
        return round(reward, 3)
    
    def to_dict(self):
        return {"weights": self.weights}


reward_fn = RewardFunction()


# ── Adaptive Curriculum ────────────────────────────────────

class AdaptiveCurriculum:
    """Adjusts difficulty based on agent performance."""
    
    STAGES = {
        1: {"name": "Novice", "win_threshold": 0.55, "description": "Basic foraging without threats"},
        2: {"name": "Apprentice", "win_threshold": 0.55, "description": "Introduce slow predator"},
        3: {"name": "Adept", "win_threshold": 0.50, "description": "Full difficulty"},
        4: {"name": "Master", "win_threshold": 0.45, "description": "Multi-room quests"},
        5: {"name": "Grandmaster", "win_threshold": 0.40, "description": "Open-ended exploration"},
    }
    
    def __init__(self):
        self.agent_stage = defaultdict(lambda: 1)
        self.agent_history = defaultdict(list)  # agent -> [bool] (wins/losses)
    
    def record_result(self, agent_name, won):
        self.agent_history[agent_name].append(won)
        # Keep last 20
        self.agent_history[agent_name] = self.agent_history[agent_name][-20:]
        self._check_promotion(agent_name)
    
    def _check_promotion(self, agent_name):
        history = self.agent_history[agent_name]
        stage = self.agent_stage[agent_name]
        if stage >= 5 or len(history) < 5:
            return
        
        recent = history[-5:]
        win_rate = sum(recent) / len(recent)
        threshold = self.STAGES[stage]["win_threshold"]
        
        if win_rate >= threshold:
            self.agent_stage[agent_name] = min(stage + 1, 5)
    
    def get_stage(self, agent_name):
        stage = self.agent_stage[agent_name]
        return {"stage": stage, **self.STAGES[stage]}
    
    def to_dict(self):
        return {
            name: {"stage": self.agent_stage[name], **self.STAGES[self.agent_stage[name]]}
            for name in self.agent_history
        }


curriculum = AdaptiveCurriculum()


# ── Match Execution ────────────────────────────────────────

class Match:
    def __init__(self, player_a, player_b, game_type, player_a_actions=None, player_b_actions=None,
                 winner=None, reward_a=0, reward_b=0, rooms_explored=0, insight_words=0,
                 steps_taken=20, novel_strategy=False):
        self.match_id = hashlib.sha256(f"{player_a}{player_b}{time.time()}".encode()).hexdigest()[:12]
        self.player_a = player_a
        self.player_b = player_b
        self.game_type = game_type
        self.player_a_actions = player_a_actions or []
        self.player_b_actions = player_b_actions or []
        self.winner = winner  # "a", "b", "draw", None (for external judgment)
        self.reward_a = reward_a
        self.reward_b = reward_b
        self.rooms_explored = rooms_explored
        self.insight_words = insight_words
        self.steps_taken = steps_taken
        self.novel_strategy = novel_strategy
        self.timestamp = time.time()
    
    def to_dict(self):
        return {
            "match_id": self.match_id, "player_a": self.player_a,
            "player_b": self.player_b, "game_type": self.game_type,
            "winner": self.winner, "reward_a": self.reward_a,
            "reward_b": self.reward_b, "rooms_explored": self.rooms_explored,
            "insight_words": self.insight_words, "steps_taken": self.steps_taken,
            "novel_strategy": self.novel_strategy,
            "timestamp": self.timestamp,
            "player_a_archetype": archetypes.classify(self.player_a, self.player_a_actions),
            "player_b_archetype": archetypes.classify(self.player_b, self.player_b_actions),
        }


matches = []

# Load persisted matches
if MATCHES_FILE.exists():
    with open(MATCHES_FILE) as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                m = Match(d["player_a"], d["player_b"], d["game_type"], winner=d.get("winner"))
                matches.append(m)
            except:
                pass
    print(f"  Loaded {len(matches)} matches from {MATCHES_FILE}")


def save_match(match):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(MATCHES_FILE, "a") as f:
            f.write(json.dumps(match.to_dict()) + "\n")
    except Exception as e:
        print(f"  ⚠️ Match save failed: {e}")


# ── HTTP Handler ────────────────────────────────────────────

class ArenaHandler(BaseHTTPRequestHandler):
    
    # Input sanitization
    BLOCKED_PATTERNS = ['<script', 'javascript:', 'onerror=', 'onload=', 'DROP TABLE',
                        'DELETE FROM', 'INSERT INTO', 'eval(', 'exec(', '__import__']

    @classmethod
    def _sanitize(cls, value):
        if not isinstance(value, str):
            return value
        lower = value.lower()
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern.lower() in lower:
                return None
        return ''.join(c for c in value if ord(c) >= 32 or c in '\n\t')

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        if path in ("/", ""):
            self._json({
                "service": "⚔️ Self-Play Arena v1 — Fleet Skill Acquisition Engine",
                "born_from": "DeepFar 4.1.1-4.1.3 (Sparrow, ArenaMaster, ArenaKeeper)",
                "features": [
                    "ELO rating system with uncertainty (TrueSkill-inspired)",
                    "Policy snapshot league (Opponent Forge)",
                    "Behavioral archetype discovery",
                    "Multi-objective reward function",
                    "Adaptive curriculum (5 stages)",
                    "5 game types",
                ],
                "api": [
                    "GET / (this page)",
                    "GET /games — list available games",
                    "GET /register?agent=NAME — register agent + get ELO",
                    "GET /opponent?agent=NAME&mode=balanced|latest|strongest|weakest|random",
                    "GET /match?player_a=A&player_b=B&game=GAME&winner=a|b|draw",
                    "GET /match_detail?player_a=A&player_b=B&game=GAME&winner=a|b|draw&... (full params)",
                    "GET /leaderboard?n=20",
                    "GET /agent?name=NAME",
                    "GET /archetypes",
                    "GET /curriculum",
                    "GET /league",
                    "GET /reward_weights",
                    "GET /stats",
                ],
            })
        
        elif path == "/games":
            self._json(GAMES)
        
        elif path == "/register":
            name = params.get("agent", ["anonymous"])[0]
            name = self._sanitize(name)
            if not name:
                self._json({"error": "Invalid agent name"}, 403)
                return
            player = elo.get_or_create(name)
            # Also add a policy snapshot
            league.add_snapshot(name, f"Initial registration for {name}")
            self._json({
                "status": "registered", "agent": name,
                "elo": player.to_dict(),
                "curriculum": curriculum.get_stage(name),
                "message": f"Welcome to the Arena, {name}. Your ELO starts at {player.mu:.0f} ± {player.sigma:.0f}.",
            })
        
        elif path == "/opponent":
            agent = params.get("agent", ["anonymous"])[0]
            mode = params.get("mode", ["balanced"])[0]
            opponent_id = league.get_opponent(agent, mode)
            if opponent_id:
                snap = league.snapshots[opponent_id]
                self._json({
                    "opponent_id": opponent_id,
                    "opponent": snap.to_dict(),
                    "mode": mode,
                    "message": f"Opponent selected: {snap.agent_name} v{snap.version} (ELO {snap.elo})",
                })
            else:
                self._json({"error": "No opponents available yet. Register more agents first."}, 404)
        
        elif path == "/match":
            """Quick match — GET still supported for backward compat, but POST preferred."""
            pa = params.get("player_a", [None])[0]
            pb = params.get("player_b", [None])[0]
            game = params.get("game", ["tide-pool-tactics"])[0]
            winner = params.get("winner", ["draw"])[0]
            
            # Sanitize
            pa = self._sanitize(pa)
            pb = self._sanitize(pb)
            game = self._sanitize(game)
            winner = self._sanitize(winner)
            if not pa or not pb:
                self._json({"error": "Specify player_a and player_b"}, 400)
                return
            if winner not in ('a', 'b', 'draw'):
                winner = 'draw'
            
            # Update ELO
            if winner == "a":
                elo.update(pa, pb, draw=False)
            elif winner == "b":
                elo.update(pb, pa, draw=False)
            else:
                elo.update(pa, pb, draw=True)
            
            won_a = winner == "a"
            won_b = winner == "b"
            is_draw = winner == "draw"
            if is_draw:
                reward = reward_fn.compute(False, 1, 100, 20, False)  # ~0 reward
                reward_b = reward_fn.compute(False, 1, 100, 20, False)  # ~0 reward
            else:
                reward = reward_fn.compute(won_a, 1, 100, 20, False)
                reward_b = reward_fn.compute(won_b, 1, 100, 20, False)
            
            match = Match(pa, pb, game, winner=winner, reward_a=reward, reward_b=reward_b)
            matches.append(match)
            save_match(match)
            
            # Update curriculum
            curriculum.record_result(pa, won_a)
            curriculum.record_result(pb, won_b)
            
            self._json({
                "match_id": match.match_id, "winner": winner,
                "elo_a": elo.get_or_create(pa).to_dict(),
                "elo_b": elo.get_or_create(pb).to_dict(),
                "reward_a": reward, "reward_b": reward_b,
                "curriculum_a": curriculum.get_stage(pa),
                "curriculum_b": curriculum.get_stage(pb),
            })
        
        elif path == "/match_detail":
            """Full match submission with all parameters."""
            pa = params.get("player_a", [None])[0]
            pb = params.get("player_b", [None])[0]
            game = params.get("game", ["tide-pool-tactics"])[0]
            winner = params.get("winner", ["draw"])[0]
            actions_a = params.get("actions_a", [""])[0].split(",") if params.get("actions_a") else []
            actions_b = params.get("actions_b", [""])[0].split(",") if params.get("actions_b") else []
            rooms = int(params.get("rooms", ["1"])[0])
            words = int(params.get("insight_words", ["0"])[0])
            steps = int(params.get("steps", ["20"])[0])
            novel = params.get("novel", ["false"])[0].lower() == "true"
            
            if not pa or not pb:
                self._json({"error": "Specify player_a and player_b"}, 400)
                return
            
            # ELO
            if winner == "a":
                elo.update(pa, pb)
            elif winner == "b":
                elo.update(pb, pa)
            else:
                elo.update(pa, pb, draw=True)
            
            # Rewards
            won_a = winner == "a"
            won_b = winner == "b"
            is_draw = winner == "draw"
            if is_draw:
                reward_a = reward_fn.compute(False, rooms, words, steps, novel)
                reward_b = reward_fn.compute(False, rooms, words, steps, novel)
            else:
                reward_a = reward_fn.compute(won_a, rooms, words, steps, novel)
                reward_b = reward_fn.compute(won_b, rooms, words, steps, novel)
            
            # Classify behaviors
            arch_a = archetypes.classify(pa, actions_a)
            arch_b = archetypes.classify(pb, actions_b)
            
            match = Match(pa, pb, game, actions_a, actions_b, winner,
                         reward_a, reward_b, rooms, words, steps, novel)
            matches.append(match)
            save_match(match)
            
            # Curriculum
            curriculum.record_result(pa, won_a)
            curriculum.record_result(pb, not won_a)
            
            # Add policy snapshots from this match
            league.add_snapshot(pa, f"Post-match v{len(actions_a)} actions: {arch_a}")
            league.add_snapshot(pb, f"Post-match v{len(actions_b)} actions: {arch_b}")
            
            self._json({
                "match_id": match.match_id, "winner": winner,
                "archetype_a": arch_a, "archetype_b": arch_b,
                "elo_a": elo.get_or_create(pa).to_dict(),
                "elo_b": elo.get_or_create(pb).to_dict(),
                "reward_a": reward_a, "reward_b": reward_b,
                "curriculum_a": curriculum.get_stage(pa),
                "curriculum_b": curriculum.get_stage(pb),
                "league_size": len(league.snapshots),
            })
        
        elif path == "/leaderboard":
            n = int(params.get("n", ["20"])[0])
            board = elo.leaderboard(n)
            self._json({
                "leaderboard": [p.to_dict() for p in board],
                "total_players": len(elo.players),
                "total_matches": len(matches),
            })
        
        elif path == "/agent":
            name = params.get("name", [None])[0]
            if not name:
                self._json({"error": "Specify name"}, 400)
                return
            player = elo.get_or_create(name)
            agent_matches = [m.to_dict() for m in matches if name in (m.player_a, m.player_b)]
            self._json({
                "elo": player.to_dict(),
                "curriculum": curriculum.get_stage(name),
                "matches_played": len(agent_matches),
                "recent_matches": agent_matches[-10:],
                "league_snapshots": sum(1 for s in league.snapshots if s.startswith(name)),
            })
        
        elif path == "/archetypes":
            # Auto-classify all registered players before returning
            for pname in elo.players:
                if pname not in archetypes.behaviors:
                    archetypes.classify(pname, [])
            self._json(archetypes.to_dict())
        
        elif path == "/curriculum":
            self._json(curriculum.to_dict())
        
        elif path == "/league":
            self._json(league.to_dict())
        
        elif path == "/reward_weights":
            self._json(reward_fn.to_dict())
        
        elif path == "/health":
            self._json({"status": "healthy", "service": "self-play-arena", "matches": len(matches), "players": len(elo.players)})
        
        elif path == "/stats":
            self._json({
                "total_matches": len(matches),
                "total_players": len(elo.players),
                "league_snapshots": len(league.snapshots),
                "archetype_distribution": archetypes.distribution(),
                "games_available": list(GAMES.keys()),
            })
        
        else:
            self._json({"error": "Not found. Start at GET /"}, 404)
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def do_POST(self):
        """POST endpoints for mutations (preferred over GET)."""
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except:
            body = {}
        
        if path == "/match":
            pa = self._sanitize(body.get("player_a", ""))
            pb = self._sanitize(body.get("player_b", ""))
            game = self._sanitize(body.get("game", "tide-pool-tactics"))
            winner = self._sanitize(body.get("winner", "draw"))
            if not pa or not pb:
                self._json({"error": "Specify player_a and player_b"}, 400)
                return
            if winner not in ('a', 'b', 'draw'):
                winner = 'draw'
            
            # Update ELO
            if winner == "a":
                elo.update(pa, pb, draw=False)
            elif winner == "b":
                elo.update(pb, pa, draw=False)
            else:
                elo.update(pa, pb, draw=True)
            
            # Rewards
            won_a = winner == "a"
            won_b = winner == "b"
            is_draw = winner == "draw"
            if is_draw:
                reward = reward_fn.compute(False, 1, 100, 20, False)
                reward_b = reward_fn.compute(False, 1, 100, 20, False)
            else:
                reward = reward_fn.compute(won_a, 1, 100, 20, False)
                reward_b = reward_fn.compute(won_b, 1, 100, 20, False)
            
            match = Match(pa, pb, game, winner=winner, reward_a=reward, reward_b=reward_b)
            matches.append(match)
            save_match(match)
            
            # Curriculum
            curriculum.record_result(pa, won_a)
            curriculum.record_result(pb, won_b)
            
            # Arena→PLATO feedback: auto-generate tile from match result
            try:
                import urllib.request as _ur
                _tile = json.dumps({
                    "domain": "arena",
                    "question": f"Arena match: {pa} vs {pb} in {game}",
                    "answer": f"Match {match.match_id}: {winner} won. {pa} ELO now {elo.get_or_create(pa).mu:.0f}±{elo.get_or_create(pa).sigma:.0f}. {pb} ELO now {elo.get_or_create(pb).mu:.0f}±{elo.get_or_create(pb).sigma:.0f}. Game: {game}. Reward: {reward:.3f}/{reward_b:.3f}.",
                    "confidence": 0.7,
                    "source": "arena-auto"
                }).encode()
                _ur.urlopen(
                    _ur.Request(
                        "http://localhost:8847/submit",
                        data=_tile,
                        headers={"Content-Type": "application/json", "User-Agent": "arena/1.0"},
                        method="POST"
                    ), timeout=2
                )
            except Exception:
                pass
            
            self._json({
                "match_id": match.match_id, "winner": winner,
                "elo_a": elo.get_or_create(pa).to_dict(),
                "elo_b": elo.get_or_create(pb).to_dict(),
                "reward_a": reward, "reward_b": reward_b,
                "curriculum_a": curriculum.get_stage(pa),
                "curriculum_b": curriculum.get_stage(pb),
            })
        
        elif path == "/register":
            name = self._sanitize(body.get("agent", "anonymous"))
            if not name:
                self._json({"error": "Invalid agent name"}, 403)
                return
            player = elo.get_or_create(name)
            league.add_snapshot(name, f"Registration for {name}")
            self._json({
                "status": "registered", "agent": name,
                "elo": player.to_dict(),
                "curriculum": curriculum.get_stage(name),
            })
        
        else:
            # Fallback: treat as GET equivalent
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
    
    server = HTTPServer(("0.0.0.0", PORT), ArenaHandler)
    print(f"⚔️ Self-Play Arena v1 on port {PORT}")
    print(f"   5 games. ELO ratings. League snapshots. Behavioral archetypes.")
    print(f"   The fleet's engine of autonomous skill acquisition.")
    server.serve_forever()
