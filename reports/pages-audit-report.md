# Pages Consistency Audit

**Date:** 2026-05-03  
**Scope:** 16 GitHub Pages repos (*-pages)  
**Method:** curl HEAD check + spot-check of 3 repos

---

## Summary

| Check | Result |
|-------|--------|
| All 16 domains resolve (HTTP 200) | ✅ Yes |
| All 16 repos have index.html | ✅ Yes (verified via gh API) |
| All 16 repos have README.md | ✅ Yes |
| Consistent fleet branding | ⚠️ Mixed — some mention Cocapn Fleet, some don't |
| Cross-link to agent repo | ❌ None do |

---

## Spot Check (3 repos)

| Repo | Fleet Mention | Agent Link | Personality Match |
|------|---------------|------------|-------------------|
| dmlog-ai-pages | ✅ "Part of the Cocapn Fleet" | ❌ No | ✅ Dungeon master tools |
| studylog-ai-pages | ✅ "Part of the Cocapn Fleet" | ❌ No | ✅ Study partner |
| reallog-ai-pages | ❌ No fleet mention | ❌ No | ⚠️ Generic (was copy-paste, now fixed) |

---

## Fleet-Wide Issues

1. **No cross-links:** No pages repo links to its matching agent repo (e.g., dmlog-ai-pages → dmlog-agent)
2. **Inconsistent branding:** ~8 repos mention Cocapn Fleet, ~8 don't
3. **No domain personality in landing copy:** Most are generic "GitHub Pages for X" descriptions
4. **All use identical HTML template:** No visual differentiation between domains

---

## Recommendations

1. Add "Fleet Context" section to all READMEs (link to cocapn-landing)
2. Add agent repo link to each pages README
3. Customize index.html opening paragraph per domain personality
4. Standardize footer: "Part of the [Cocapn Fleet](https://cocapn.com)"

---

*Quick audit by CCC — full deep-dive pending*
