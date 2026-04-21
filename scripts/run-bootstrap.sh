#!/bin/bash
export GROQ_API_KEY="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"
python3 /home/ubuntu/.openclaw/workspace/scripts/purplepincher-bootstrap.py iterate \
  "claude-code-agent" \
  "Design the vectorization pipeline for PurplePincher — how do we turn agent reasoning iterations into searchable embeddings that future agents can learn from?" \
  "socratic" 3
