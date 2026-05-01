#!/bin/bash
# ccc-shell-maintainer.sh — Oracle1 keeps CCC's shell alive
# Runs every 5 minutes via cron
# Updates STATE.md, pushes scout reports, routes bottles

CCC_REPO="/tmp/ccc-shell"
CCC_REPO_URL="https://SuperInstance:[GITHUB_TOKEN_REVOKED]@github.com/cocapn/cocapn.git"
PLATO_STATUS=$(curl -s http://localhost:8847/status 2>/dev/null)

# Clone or pull CCC's repo
if [ ! -d "$CCC_REPO" ]; then
    git clone "$CCC_REPO_URL" "$CCC_REPO" 2>/dev/null
else
    cd "$CCC_REPO" && git pull 2>/dev/null
fi

cd "$CCC_REPO"

# 1. Update hooks/intel/fleet-snapshot.json
TILE_COUNT=$(echo "$PLATO_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_tiles',0))" 2>/dev/null || echo "unknown")
cat > hooks/intel/fleet-snapshot.json << SNAP
{
    "updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "tiles": $TILE_COUNT,
    "rooms": 14,
    "services": {
        "keeper": 8900,
        "holodeck": 7778,
        "plato": 8847,
        "dashboard": 8848
    },
    "fleet": {
        "oracle1": "UP",
        "fm": "SHIPPING",
        "jc1": "HEARTBEATING",
        "zeroclaws": "CYCLING"
    }
}
SNAP

# 2. Copy latest zeroclaw scout report
LATEST_SCOUT=$(ls -t /tmp/zeroclaw*.log 2>/dev/null | head -1)
if [ -n "$LATEST_SCOUT" ]; then
    tail -20 "$LATEST_SCOUT" > from-fleet/scouts/latest-scout.txt 2>/dev/null
fi

# 3. Copy new FM bottles
for f in /tmp/fm-bottles/bottle-*.md; do
    [ -f "$f" ] && cp "$f" from-fleet/builds/ 2>/dev/null
done

# 4. Check for CCC's output in for-fleet/outbox/
if [ -d "for-fleet/outbox" ] && [ "$(ls -A for-fleet/outbox/ 2>/dev/null | grep -v .gitkeep)" ]; then
    echo "CCC has output to route!"
    # Route bottles to appropriate fleet vessels
    for f in for-fleet/outbox/*.md; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        if echo "$fname" | grep -qi "fm\|forgemaster"; then
            cp "$f" /tmp/oracle1-vessel/for-fleet/ 2>/dev/null
        elif echo "$fname" | grep -qi "jc1\|jetson"; then
            cp "$f" /tmp/jc1-vessel/for-fleet/ 2>/dev/null 2>/dev/null
        fi
        # Archive
        mv "$f" for-fleet/work/ 2>/dev/null
    done
fi

# 5. Commit and push
git add -A
git diff --cached --quiet || git commit -m "shell-maintainer: $(date -u +%H:%M) fleet update" 2>/dev/null
git push 2>/dev/null

echo "CCC shell maintained at $(date -u +%H:%M)"
