#!/bin/bash
python3 /home/ubuntu/.openclaw/workspace/scripts/purplepincher-bootstrap.py stats

echo ""
echo "=== ML Tile Files ==="
ls -la /home/ubuntu/.openclaw/workspace/data/purplepincher-ml/tiles/
echo ""
echo "=== Embedding File ==="
wc -l /home/ubuntu/.openclaw/workspace/data/purplepincher-ml/embeddings/index.jsonl 2>/dev/null
echo ""
echo "=== Sample Embedding ==="
head -1 /home/ubuntu/.openclaw/workspace/data/purplepincher-ml/embeddings/index.jsonl | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'ID: {d[\"id\"]}')
print(f'Embedding dims: {len(d[\"embedding\"])}')
print(f'Metadata: {d[\"metadata\"]}')
"
