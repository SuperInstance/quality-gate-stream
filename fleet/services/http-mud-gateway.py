"""Migrated http-mud-gateway.py — four-layer architecture."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# TODO: Decompose inline logic into vessel/equipment/agent/skills layers
# For now, import and run the original service
exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts", "http-mud-gateway.py")).read())
