#!/bin/bash
export GROQ_API_KEY="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"
export DEEPINFRA_API_KEY="RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ"
export SILICONFLOW_API_KEY="[SF_KEY_REDACTED]"
export DEEPSEEK_API_KEY="[DEEPSEEK_KEY_REDACTED]"
python3 /home/ubuntu/.openclaw/workspace/scripts/lock-multi-model-test.py \
  "What is the most effective way to train agent instincts from accumulated interaction data, and how do you prevent catastrophic forgetting while adding new skills?" \
  adversarial 5
