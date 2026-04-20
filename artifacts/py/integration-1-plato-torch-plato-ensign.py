"""
PLATO Room: integration
Tile: 1. **plato-torch** ↔ **plato-ensign** — **CONNECTED**
Domain: integration
"""

def export_ensign(self, adapter_path: str = "ensign_lora"):
      """Export room experience as LoRA adapter."""
      from plato_ensign import export_lora_from_tiles
      tiles = self.get_training_tiles()
      export_lora_from_tiles(tiles, adapter_path)

