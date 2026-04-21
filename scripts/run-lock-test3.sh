#!/bin/bash
export GROQ_API_KEY="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"
export DEEPINFRA_API_KEY="RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ"
export SILICONFLOW_API_KEY="sk-xtcrixoswqhmsopntnkfapccswjywrlsdpbunqjukpileiqo"
export DEEPSEEK_API_KEY="sk-f742b70fc40849eda4181afcf3d68b0c"
python3 /home/ubuntu/.openclaw/workspace/scripts/lock-multi-model-test.py \
  "Design the architecture for a system where external AI agents voluntarily contribute to a shared knowledge base through gamified exploration" \
  perspective 5
