#!/bin/bash
# Fork gold repos from SuperInstance to cocapn
# Run this as CoCapn-claw (with cocapn's GitHub token)

REPOS=(
  # Tier 1: Core PLATO
  "plato-torch"
  "plato-tile-spec"
  "plato-ensign"
  "plato-kernel"
  "plato-lab-guard"
  "plato-afterlife"
  "plato-relay"
  "plato-instinct"
  "plato-demo"
  "plato-ml"
  
  # Tier 2: Runtime + Environments
  "flux-runtime"
  "flux-runtime-c"
  "holodeck-rust"
  
  # Tier 3: Agents + Orchestration
  "git-agent"
  "fleet-orchestrator"
  "DeckBoss"
  
  # Tier 4: Research + Specialized
  "constraint-theory-core"
)

echo "=== Forking ${#REPOS[@]} repos to cocapn ==="

for repo in "${REPOS[@]}"; do
  echo -n "  Forking $repo... "
  result=$(curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.github.com/repos/SuperInstance/$repo/forks" \
    -d '{"organization":"cocapn"}')
  
  full_name=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('full_name','FAILED'))" 2>/dev/null)
  echo "$full_name"
  sleep 2  # Rate limit
done

echo ""
echo "=== Creating profile repo ==="
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/user/repos \
  -d '{"name":"cocapn","description":"⚓ Agent Infrastructure — The Shell for Intelligence","public":true}' | python3 -c "import json,sys; print(json.load(sys.stdin).get('html_url','FAILED'))"

echo ""
echo "Done! Now push the README to cocapn/cocapn"
