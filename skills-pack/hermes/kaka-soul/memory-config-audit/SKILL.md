---
name: memory-config-audit
description: "Audit and fix inconsistencies across the Hermes Agent memory system — Soul rules, MEMORY.md, USER.md, config.yaml, and related skills. Use when auditing memory configuration, resolving cross-file contradictions, or when utilization exceeds thresholds."
version: 1.0.0
author: kaka
metadata:
  hermes:
    tags: [memory, audit, config, consistency, kaka, soul]
    related_skills: [holographic-memory-plugin, task-state-persistence, hermes-agent]
---

# Memory Configuration Audit

Use when auditing the Hermes Agent memory system for consistency, fixing cross-file contradictions, or performing periodic memory cleanup beyond simple utilization checks.

## When to use

- User says "审核memory" / "检查记忆配置" / "memory有没有冲突"
- User says "你还记得什么" / "有没有丢内容" / "记忆是不是少了" — memory inventory and migration tracing
- MEMORY or USER utilization ≥80% (triggers Soul's audit flow → this skill adds consistency checks)
- After major Soul rule changes (new iron rules, adjusted storage boundaries, etc.)
- Suspected cross-file definition drift (e.g., Soul says "3个场景" but somewhere else says "4场景")

## Files to audit

| File | What's in it | What to check |
|------|-------------|---------------|
| `~/.hermes/SOUL.md` | Memory rules, storage boundaries, audit flow, recovery flow | Consistency of counts, targets, definitions |
| `~/.hermes/memories/MEMORY.md` | Red-line rules only | No non-red-line content (env facts, tool conventions, project facts) |
| `~/.hermes/memories/USER.md` | User identity + preferences only | No behavioral rules (those belong in SOUL), utilization ≤80% |
| `~/.hermes/config.yaml` | Memory provider, char limits, plugin config | Settings match what Soul claims |
| `~/.hermes/skills/kaka-soul/*/SKILL.md` | Skills with memory-related rules | Definitions match Soul (e.g., "triple guarantee" vs "四重保障") |

## 7 conflict patterns to check

### Pattern 1: Numeric inconsistency
Same concept, different numbers across files/sections.
- **Example**: Soul line A says "3个场景", Soul line B says "仅4场景"
- **Check**: `grep -n '场景' ~/.hermes/SOUL.md` — verify all counts match
- **Fix**: Unify to the correct number, verify the actual list length matches

### Pattern 2: Cross-file definition drift
Soul and a skill define the same concept differently.
- **Example**: Soul says "三重保障: summary + fact_store + session_search"; task-state-persistence skill says "triple guarantee: summary + fact_store + progress file"
- **Check**: `grep -rn '保障\|guarantee\|triple\|四重' ~/.hermes/SOUL.md ~/.hermes/skills/kaka-soul/`
- **Fix**: Pick one canonical definition, update all files to match

### Pattern 3: Missing steps in one file
Recovery/workflow flow in Soul doesn't mention a step that the skill includes.
- **Example**: Soul recovery flow omits "read progress file" step, but skill says it's the most reliable layer
- **Check**: Compare step-by-step flows between Soul and skills side by side
- **Fix**: Add missing steps to Soul, or reference the skill

### Pattern 4: Content placement violations
MEMORY.md contains non-red-line entries; USER.md contains behavioral rules.
- **Example**: "hermes CLI 调用..." (tool convention) in MEMORY.md; "测试模式" (behavioral rule) in USER.md
- **Check**: `grep -v '🔴' ~/.hermes/memories/MEMORY.md` — any line without 🔴 is suspect
- **Fix**: Migrate to correct location:
  - Red lines → MEMORY.md (only "违反=系统性伤害" items)
  - User identity/preferences → USER.md
  - Behavioral rules, env facts, tool conventions → SOUL.md
  - Case experiences, project facts → fact_store

### Pattern 5: Utilization target inconsistency
Different sections of Soul specify different thresholds for the same metric.
- **Example**: Line A says "MEMORY ≤30%", Line B says "MEMORY ≤50%"
- **Check**: `grep -n '≤30\|≤50\|≤80' ~/.hermes/SOUL.md`
- **Fix**: Use "日常目标 ≤X%, 审计后上限 ≤Y%" format to distinguish aspirational from hard limit

### Pattern 6: Allocation table vs audit rules contradiction
The Core Memory allocation table says behavioral rules → SOUL.md, but audit rules say → 留 USER.md.
- **Check**: Read allocation table and audit rules side by side
- **Fix**: Align both to the same destination. Behavioral rules → SOUL.md (both SOUL.md and USER.md are 常驻, so SOUL.md is the correct home for behavioral rules)

### Pattern 7: Utilization exceeding target
MEMORY or USER exceeds its target utilization.
- **Check**:
  ```bash
  python3 -c "import pathlib; c=pathlib.Path('/home/ubuntu/.hermes/memories/MEMORY.md').read_text(); print(f'{len(c)}/2200 = {len(c)*100//2200}%')"
  python3 -c "import pathlib; c=pathlib.Path('/home/ubuntu/.hermes/memories/USER.md').read_text(); print(f'{len(c)}/1375 = {len(c)*100//1375}%')"
  ```
  **⚠️ Must use `len()` not `wc -c`** — Chinese UTF-8 is 3 bytes per char but counts as 1 char.
- **Fix**: Move content to correct location (see Pattern 4 migration table)

## Memory inventory and migration tracing

When the user asks "what do you remember" or worries about lost content:

### Step 1: Full inventory across all layers
- **Core Memory**: Read MEMORY.md + USER.md (injected every turn, but explicitly state contents)
- **SOUL.md**: Note that it's also injected every turn and contains behavioral rules, env facts, tool conventions
- **fact_store**: `fact_store action=list limit=10` to see recent facts; `fact_store action=search` for specific topics
- **session_search**: Call with no args for recent sessions; use keyword queries for specific topics

### Step 2: Trace migration history (if content seems missing)
1. `session_search query="MEMORY.md OR 精简 OR 迁移 OR SOUL.md"` — find sessions where memory was reorganized
2. Compare past MEMORY.md utilization (from session summaries) vs current:
   ```bash
   python3 -c "import pathlib; c=pathlib.Path('/home/ubuntu/.hermes/memories/MEMORY.md').read_text(); print(f'{len(c)}/2200 = {len(c)*100//2200}%')"
   ```
3. If utilization dropped significantly (e.g., 87% → 8%), check SOUL.md for migrated content
4. Verify each previously-present rule now exists in SOUL.md or another location — content was *migrated*, not *lost*

**Key insight**: SOUL.md is injected every turn just like MEMORY.md/USER.md — content migrated to SOUL.md is NOT lost. The three-layer system (Core Memory + Holographic + session_search) ensures all content remains accessible.

## Audit methodology

### Step 1: Scan all files for key terms
```bash
grep -n '记忆\|fact_store\|memory\|MEMORY\|session_search\|holographic\|Core Memory\|压缩恢复\|场景\|保障' ~/.hermes/SOUL.md
grep -rn '保障\|guarantee\|triple\|四重\|progress.*file\|compaction.*recover' ~/.hermes/skills/kaka-soul/
```

### Step 2: Cross-reference definitions
For each concept that appears in multiple files, verify the definition matches:
- Guarantee layer count (三重 vs 四重)
- Scenario counts (3个 vs 4个)
- Utilization targets (≤30% vs ≤50%)
- Rule destinations (SOUL vs USER)

### Step 3: Check content placement
- MEMORY.md: only lines starting with 🔴
- USER.md: only user identity + preferences (no behavioral rules)
- SOUL.md: behavioral rules, env facts, tool conventions

### Step 4: Measure utilization
Use `len()` not `wc -c`. Check both MEMORY ≤30% (daily) / ≤50% (audit ceiling) and USER ≤80%.

### Step 5: Fix (bottom-to-top patching)
When patching SOUL.md, work from bottom to top to avoid line number shifts. Use `patch` tool, not `sed`.

### Step 6: Verify
After fixes, re-run Steps 1-4 to confirm all conflicts resolved.

## Migration destinations

When moving content out of MEMORY.md or USER.md:

| Content type | Destination | Tool |
|-------------|-------------|------|
| Case experiences, project facts | fact_store | `fact_store add` |
| Tool conventions, env facts | SOUL.md 环境硬事实 section | `patch` |
| Behavioral rules (cross-skill) | SOUL.md 其他执行规则 section | `patch` |
| Behavioral rules (skill-specific) | Skill SKILL.md | `skill_manage patch` |
| User identity, communication preferences | USER.md (keep) | — |

## Pitfalls

1. **`wc -c` overcounts Chinese** — Chinese chars are 3 bytes in UTF-8 but 1 char. Always use `len()` in Python.
2. **Bottom-to-top patching** — patching top-to-bottom shifts line numbers for subsequent patches.
3. **Forgetting to sync skills** — when Soul definitions change, check if any skill references the old definition.
4. **Audit rules self-contradiction** — the audit rules themselves can conflict with the allocation table. Check both.
5. **FTS5 Chinese tokenization** — fact_store search with short Chinese terms may return 0 results. Use English tags (`task_goal`, `task_milestone`) for reliable retrieval.
