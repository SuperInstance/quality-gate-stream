"""
Equipment Layer — MUD State Engine.
Shared room/object/navigation logic for all MUD-based services.
Python 3.10, zero external dependencies.
"""
import json
import random


class Room:
    """A MUD room with exits, objects, and descriptions."""
    def __init__(self, name, description="", domain="general"):
        self.name = name
        self.description = description
        self.domain = domain
        self.exits = {}  # direction → room_name
        self.objects = {}  # object_name → description
        self.dynamic_objects = {}  # object_name → callable(server, agent) → response
        self.actions = {}  # action_name → callable(server, agent, **kwargs) → response
        self.visits = {}
    
    def add_exit(self, direction, room_name):
        self.exits[direction] = room_name
    
    def add_object(self, name, description, dynamic_fn=None):
        self.objects[name] = description
        if dynamic_fn:
            self.dynamic_objects[name] = dynamic_fn
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "exits": dict(self.exits),
            "objects": {k: v for k, v in self.objects.items() 
                       if k not in self.dynamic_objects},
            "dynamic_objects": list(self.dynamic_objects.keys()),
        }


class MudEngine:
    """MUD state engine — rooms, navigation, interaction."""
    
    def __init__(self):
        self.rooms = {}
        self.agents = {}  # agent_name → {room, history, ...}
    
    def add_room(self, room):
        self.rooms[room.name] = room
    
    def get_room(self, name):
        return self.rooms.get(name)
    
    def connect(self, agent_name, start_room="harbor", job="explorer"):
        """Agent enters the MUD."""
        self.agents[agent_name] = {
            "room": start_room,
            "job": job,
            "actions": 0,
            "history": [],
            "connected_at": __import__("time").time(),
        }
        room = self.rooms.get(start_room)
        return {
            "agent": agent_name,
            "room": start_room,
            "description": room.description if room else "Unknown room",
            "exits": list(room.exits.keys()) if room else [],
            "objects": list(room.objects.keys()) if room else [],
            "job": job,
        }
    
    def move(self, agent_name, direction):
        """Move agent in a direction."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not connected"}
        
        room = self.rooms.get(agent["room"])
        if not room:
            return {"error": "Current room not found"}
        
        target = room.exits.get(direction, direction)
        target_room = self.rooms.get(target)
        if not target_room:
            return {"error": f"Cannot go {direction}. No exit that way."}
        
        agent["room"] = target
        agent["actions"] += 1
        
        # Track visits
        target_room.visits[agent_name] = target_room.visits.get(agent_name, 0) + 1
        
        return {
            "agent": agent_name,
            "room": target,
            "description": target_room.description,
            "exits": list(target_room.exits.keys()),
            "objects": list(target_room.objects.keys()),
        }
    
    def look(self, agent_name):
        """Look around current room."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not connected"}
        
        room = self.rooms.get(agent["room"])
        if not room:
            return {"error": "Room not found"}
        
        return {
            "room": room.name,
            "description": room.description,
            "exits": dict(room.exits),
            "objects": [
                {
                    "name": name,
                    "description": desc,
                    "available_actions": ["examine", "think", "create"],
                    "dynamic": name in room.dynamic_objects,
                }
                for name, desc in room.objects.items()
            ],
            "agents_here": [a for a, d in self.agents.items() if d["room"] == room.name],
        }
    
    def examine(self, agent_name, target):
        """Examine an object or feature in current room."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not connected"}
        
        room = self.rooms.get(agent["room"])
        if not room:
            return {"error": "Room not found"}
        
        agent["actions"] += 1
        
        # Check dynamic objects first
        if target in room.dynamic_objects:
            try:
                result = room.dynamic_objects[target](self, agent_name)
                if isinstance(result, dict):
                    return result
                return {"target": target, "result": result}
            except Exception as e:
                return {"target": target, "error": str(e)}
        
        # Then static objects
        if target in room.objects:
            return {"target": target, "description": room.objects[target]}
        
        return {"error": f"You don't see '{target}' here.", "room": room.name}
    
    def interact(self, agent_name, action, target=None, **kwargs):
        """Perform an interaction."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not connected"}
        
        room = self.rooms.get(agent["room"])
        agent["actions"] += 1
        
        # Check room-level actions
        if action in room.actions:
            return room.actions[action](self, agent_name, target=target, **kwargs)
        
        return {"error": f"Unknown action: {action}"}
    
    def status(self):
        """Get MUD status."""
        return {
            "rooms": len(self.rooms),
            "agents": len(self.agents),
            "total_objects": sum(len(r.objects) for r in self.rooms.values()),
            "room_list": [r.to_dict() for r in self.rooms.values()],
        }
    
    def agent_status(self, agent_name):
        """Get agent status."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not connected"}
        return {
            "agent": agent_name,
            "room": agent["room"],
            "actions": agent["actions"],
            "job": agent["job"],
        }
