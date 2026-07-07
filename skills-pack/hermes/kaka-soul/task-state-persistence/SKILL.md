---
name: task-state-persistence
description: Persist multi-step task progress to a local file so it survives context compaction. Use when executing any complex task with 5+ steps or many tool calls — write a progress file, update after each step, read first when context seems lost.
version: 1.0.0
author: kaka
metadata:
  hermes:
    tags: [task-management, context-compaction, progress-tracking, persistence]
    related_skills: [hermes-session-context-debugging, problem-diagnosis]
---

# Task State Persistence

## When to use

Use this skill when executing any task that meets **any** of these criteria:
- 5+ discrete steps or subtasks
- Spans many tool calls (10+)
- Creates multiple artifacts (docs, files, records)
- Long-running — likely to trigger context compaction
- User explicitly asks "how to prevent task state loss during compaction"

Class of task: **preventing multi-step task progress loss when Hermes Agent context compaction occurs.**

## Why this exists

Context compaction can remove 100+ turns of conversation. If the compaction summary fails to generate (which happens), the agent completely loses task state — which steps are done, what artifacts were created, what remains. This leads to:
- Duplicating already-completed work (e.g., creating docs that already exist)
- Losing track of which subtasks remain
- Confusing the user by asking about things already decided
- Wasting tokens re-discovering state via session_search (which itself depends on summary generation)

**Two complementary persistence layers** (triple guarantee):
1. **Progress file on disk** — most reliable, doesn't depend on summary generation, session storage, or memory injection
2. **fact_store (holographic memory)** — stores task goals, milestones, and product IDs (doc_id/file paths) for semantic retrieval after compaction
3. **session_search** — final fallback for raw conversation evidence

**Hermes limitation (verified 2026-07-07):** Hermes currently has NO pre/post compaction hook events. Available hook events are `agent:start/end/step` and `session:start/end/reset` — none fire on compaction. This makes file-based + fact_store persistence not just the simplest approach but currently the ONLY viable approach. (GitHub research found 4 mainstream patterns: post-compact hooks, 3-phase compaction lifecycle, session handoff skills, and state-machine gates — all require hook support that Hermes lacks.)

## Core workflow

### Step 1: Create progress file at task start

Before executing the first step of a complex task, write a progress file:

```bash
# File path: {{AGENT_TMP_DIR}}/task-progress.md (or ~/cat-tmp/ for 少佐小猫)
```

The file must contain:

```markdown
# Task: {one-sentence task goal}
Created: {date/time}
Context: {any key context the user provided — categorization decisions, constraints, etc.}

## Steps
- [ ] Step 1: {description} → {expected artifact/path/id}
- [ ] Step 2: {description} → {expected artifact/path/id}
- [ ] Step 3: {description} → {expected artifact/path/id}
...

## Key Artifacts (fill as you go)
| Item | ID/Path | Status |
|------|---------|--------|
| Doc 1 | doc_id_here | pending |

## Current Position: Step 1
```

### Step 2: Also write task memory to fact_store

In addition to the progress file, write task goals and milestones to fact_store for semantic retrieval:

```
fact_store add — task goal:
  content: "任务目标：{one-sentence goal}. Context: {key constraints}"
  tags: "task_goal,{domain_tags}"
  entities: ["{task_name}", "{related_tools}"]

fact_store add — milestone (after each major step):
  content: "任务里程碑：{step}完成. 产物ID: {doc_id/path}. 状态: done"
  tags: "task_milestone,{domain_tags}"
  entities: ["{task_name}"]
```

**Granularity rules (from Soul):**
- ✅ Task goals, key milestones, product IDs (doc_id, file paths) — write to fact_store
- ✅ Goal corrections (user changes scope) — write to fact_store with "改了什么、为什么改、新目标"
- ❌ Temporary running state ("正在执行命令X"), debugging output, one-time results — do NOT write

**FTS5 search limitation (verified 2026-07-07):** fact_store's FTS5 tokenizer handles English tags well but struggles with short Chinese terms. When searching after compaction, use tag-based queries (`task_goal`, `task_milestone`) or entity-based probes for reliable retrieval. Searching with Chinese keywords like "专题" may return 0 results even when the fact exists.

### Step 3: Update after each completed step

After completing each step, update the file:
- Check off the completed step `[x]`
- Fill in the artifact ID/path in the Key Artifacts table
- Update "Current Position" to the next step
- Note any decisions made or issues encountered

Also update the file immediately when:
- **User changes task scope** (adds/removes steps, changes requirements mid-task)
- **User corrects a decision** (e.g., "actually use overwrite not create")
- **An error changes the plan** (e.g., a step fails and you pivot to a different approach)

Scope changes are the #1 cause of post-compaction confusion — the progress file says "Step 3: create doc X" but the user already said "skip X, do Y instead" and that correction was lost. Update the file on ANY goal/scope change, not just step completion.

Use `patch` or `write_file` to update — keep it concise.

### Step 4: Recovery protocol (when context seems lost)

If any of these signals appear, execute the **3-step recovery flow** before doing anything else:
- A `[CONTEXT COMPACTION]` or `[REFERENCE ONLY]` message in conversation
- You feel uncertain about what's already been done
- The user says "you seem confused" or "you're losing track"
- You're about to create something but aren't sure if it already exists

**Step 1: `fact_store search`** — search for task memory:
```
fact_store search "task_goal"       # find task goals
fact_store search "task_milestone"  # find completed milestones
fact_store probe "{task_name}"      # entity-based lookup
```

**Step 2: Read progress file** (if fact_store insufficient):
```bash
read_file {{AGENT_TMP_DIR}}/task-progress.md
```

**Step 3: `session_search`** (if both above insufficient):
```
session_search query="{task keywords}"
```

Then:
1. Read the task goal and steps
2. Check which steps are done vs. pending
3. Review Key Artifacts for existing doc_ids/paths
4. Resume from "Current Position"
5. **Do NOT re-create artifacts that already exist** — verify first

**Four-layer guarantee**: summary (if generated) + progress file (disk, most reliable) + fact_store (task memory) + session_search (raw records) — any one success is enough to recover.

### Step 5: Cleanup after task completion

Once the task is fully complete and the user confirms, delete or archive the progress file:
```bash
rm {{AGENT_TMP_DIR}}/task-progress.md
```

## What to put in the progress file

### Must include:
- **Task goal** (one sentence)
- **Step list** with checkboxes
- **Key artifacts** table (doc_id, file path, record_id, etc.)
- **Current position** marker

### Should include:
- Key user decisions/constraints discovered during the task
- Cross-references between steps and artifacts (e.g., "Step 3 output doc_id used in Step 5")
- Error/issue notes for steps that had problems

### Must NOT include:
- Full content of documents being created (use file paths instead)
- Detailed tool outputs (just note success/failure + key IDs)
- User personal information

## Recovery decision tree

```
Context lost? (detected [CONTEXT COMPACTION] or uncertainty)
├─ Step 1: fact_store search "task_goal" + "task_milestone"
│   ├─ Found task memory? → Read goal + milestones + artifact IDs → Resume
│   └─ Nothing found → Continue to Step 2
├─ Step 2: Read {{AGENT_TMP_DIR}}/task-progress.md
│   ├─ File exists? → Read steps + artifacts → Resume from Current Position
│   └─ No file → Continue to Step 3
├─ Step 3: session_search "{task keywords}"
│   ├─ Found sessions? → Extract task state from summaries
│   └─ Nothing → Ask user "I lost task context. What were we working on?"
├─ After recovery, verify artifacts before acting:
│   ├─ Doc already exists? → fetch content, don't recreate
│   ├─ Record already in base table? → upsert, don't create new
│   └─ File already on disk? → check before re-downloading
```

## Pitfalls

- **Don't forget to update the file** — a stale progress file is worse than none. Update after EVERY completed step, not just at the end.
- **Don't put too much detail** — the file should be scannable in 10 seconds. If it's longer than ~50 lines, you're writing too much.
- **Don't rely on session_search alone** — session_search depends on summary generation, which can fail. The progress file is the primary recovery mechanism; session_search is a supplement.
- **Don't rely on the todo tool alone** — todo state may or may not survive compaction depending on Hermes version. The file on disk always survives.
- **Read before acting** — after compaction, always read the progress file BEFORE making any tool calls. Acting without context leads to duplicate work.
- **Verify before creating** — even with the progress file, verify artifacts still exist (docs not deleted, records not removed) before assuming they're there.

## Future enhancement: 3-phase compaction model

The ideal long-term solution follows a 3-phase model (found in GitHub research):

1. **Capture** (before compaction) — save task state to file ← *this skill does this*
2. **Inject** (during compaction) — inject progress file content into the compaction summary so the agent sees it immediately after compaction ← *not currently possible, requires Hermes `session:compact` pre-hook*
3. **Restore** (after compaction) — agent reads progress file and resumes ← *this skill does this*

If Hermes adds `session:compact` pre/post hook events in the future, the inject phase can be automated via a hook that reads the progress file and appends it to the compaction summary. Until then, the file-based capture+restore approach in this skill is the workaround.
