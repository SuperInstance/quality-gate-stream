#!/bin/bash
export GROQ_API_KEY="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"
python3 /home/ubuntu/.openclaw/workspace/scripts/purplepincher-bootstrap.py iterate \
  "crush-agent" \
  "Build a Cloudflare Worker that accepts HTTP requests and runs iterative reasoning enhancement using Workers AI. Include D1 session storage and Vectorize embeddings." \
  "iterative_design" 5
