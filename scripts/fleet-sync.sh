#!/bin/bash
# Fleet Sync Cron — merge Lucineer upstream into SuperInstance forks
# Run every 2 hours via cron or heartbeat
set -e
source ~/.bashrc
export GITHUB_TOKEN=$(grep GITHUB_TOKEN ~/.bashrc | head -1 | sed 's/.*=//' | tr -d "'" | tr -d '"')

LOG="/tmp/fleet-sync.log"
echo "$(date -u +%Y-%m-%dT%H:%M) Fleet sync starting" >> "$LOG"

# Known shared repos that need regular sync
SYNC_REPOS="holodeck-c holodeck-cuda capitaine flux-conformance-runner holodeck-studio cartridge-mcp flux-runtime-c flux-isa-v3"

cd /tmp/sync-workspace 2>/dev/null || mkdir -p /tmp/sync-workspace
cd /tmp/sync-workspace

for repo in $SYNC_REPOS; do
  # Clone or update
  if [ -d "$repo" ]; then
    cd "$repo"
    git fetch origin 2>/dev/null
    git reset --hard origin/main 2>/dev/null
  else
    git clone "https://SuperInstance:${GITHUB_TOKEN}@github.com/SuperInstance/${repo}.git" 2>/dev/null
    cd "$repo"
  fi

  # Add upstream
  git remote add upstream "https://SuperInstance:${GITHUB_TOKEN}@github.com/Lucineer/${repo}.git" 2>/dev/null || true
  git fetch upstream 2>/dev/null || true

  # Detect upstream default branch
  UPSTREAM_BRANCH=$(git remote show upstream 2>/dev/null | grep "HEAD branch" | sed 's/.*: //' | tr -d '[:space:]')
  
  if [ -n "$UPSTREAM_BRANCH" ] && [ "$UPSTREAM_BRANCH" != "(unknown)" ]; then
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse "upstream/$UPSTREAM_BRANCH" 2>/dev/null || echo "")
    
    if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
      echo "  Merging $repo from upstream/$UPSTREAM_BRANCH" >> "$LOG"
      git merge "upstream/$UPSTREAM_BRANCH" --allow-unrelated-histories --no-edit 2>/dev/null && \
      git push 2>/dev/null && \
      echo "  Synced $repo" >> "$LOG" || \
      echo "  CONFLICT in $repo" >> "$LOG"
    fi
  fi
  
  cd /tmp/sync-workspace
done

echo "$(date -u +%Y-%m-%dT%H:%M) Fleet sync complete" >> "$LOG"
