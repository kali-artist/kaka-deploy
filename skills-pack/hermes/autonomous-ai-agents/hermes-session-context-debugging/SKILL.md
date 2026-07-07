---
name: hermes-session-context-debugging
description: Debug Hermes Agent session/context contamination, especially old user requests, synthetic todo snapshots, or compaction summaries being treated as active context after session rollover.
version: 1.0.0
author: kaka
license: MIT
metadata:
  hermes:
    tags: [hermes, session, context-compression, compaction, debugging, gateway]
    related_skills: [hermes-agent, systematic-debugging, problem-diagnosis]
---

# Hermes Session Context Debugging

## When to use

Use this skill when Hermes Agent appears to:

- Answer an old user request instead of the latest message.
- Replay or react to `[Your active task list was preserved across context compression]`.
- Carry unrelated context across `/compress`, automatic context compression, session continuation, or gateway session rollover.
- Confuse quoted/transport context with the current user message.
- Confuse interruption-resume system notes or stale tool results with the user's current intent.
- Hallucinate that the current message contains a quote/history block when the user did not actually send one.
- Persist an internal state marker as a normal `role=user` message.

Class of task: **root-cause tracing for Hermes conversation-history contamination across session creation, restoration, and context compaction.**

## Core principle

Do not diagnose from the rendered chat alone. Inspect the raw session records and code paths that build the model message list.

## Investigation workflow

1. **Find raw evidence first**
   - Inspect `~/.hermes/sessions/session_*.json` or related JSONL/export files.
   - Search for the suspicious phrase across nearby sessions by timestamp.
   - Confirm the exact `role`, index, and content shape.

2. **Classify the suspicious content**
   - Real user-authored message: normal `role=user` from inbound platform.
   - Quoted/transport wrapper: user message includes quoted context from WeChat/Feishu/etc.
   - Compaction summary: contains `CONTEXT COMPACTION`, `REFERENCE ONLY`, or handoff-summary language.
   - Interruption/system-note wrapper: content begins with `[System note: Your previous turn was interrupted...]` or similar. This may be persisted as `role=user` and concatenated with the user's real new message; treat the bracketed note as internal orchestration context, not the user's intent.
   - Todo snapshot: contains `[Your active task list was preserved across context compression]`.
   - Tool/search echo: phrase appears inside tool output, file content, or diagnostic logs.

3. **Trace session lineage**
   - Compare sessions before and after compression rollover.
   - Look for the phrase at early message indexes, especially index `0` or around the protected head.
   - Check whether multiple continuation sessions retain the same old first user message.

4. **Inspect context compression boundaries**
   - In Hermes Agent, check `agent/context_compressor.py`.
   - The compressor protects a head region (`protect_first_n`) and a recent tail region.
   - An old first-turn user message can survive many compression rollovers as an ordinary history message if it is in the protected head.
   - This is distinct from quote pollution: the text is no longer merely quoted; it is in the model history as `role=user`.

5. **Inspect todo snapshot injection**
   - Check `tools/todo_tool.py` for `format_for_injection()`.
   - Check the compression rollover path in `run_agent.py`.
   - Active todo state may be appended after compression as a message like:
     ```python
     {"role": "user", "content": todo_snapshot}
     ```
   - Treat this as synthetic internal state, not as a user-authored request.

6. **Separate root causes**
   - Old ordinary user message in protected head → stale first-turn preservation / session lineage contamination.
   - `[Your active task list...]` marker → synthetic todo state injection persisted as `role=user`.
   - Quoted message in current inbound payload → transport quote parsing/context handling.
   - Phrase only in tool output → diagnostic self-contamination, usually not the original bug.

## Minimal fix directions

Do not patch blindly. After proving the source:

- Mark internal state injections with metadata or a non-user role so they are not treated as real user instructions.
- Avoid preserving stale first-turn user requests indefinitely across compression rollovers when they are no longer relevant.
- In `agent/context_compressor.py`, if the transcript does not begin with a real `system` message, do not blindly apply `protect_first_n` to ordinary leading `user` messages; protect the system/head only when there is an actual system-led head worth preserving.
- In `tools/todo_tool.py`, make `format_for_injection()` explicitly label restored todos as internal state, not a user request.
- In the compression rollover path (for example `run_agent.py`), do not append todo snapshots after the latest real user message; insert them before the most recent real `role=user` turn so “latest user message” still points at the human's current request.
- Ensure compaction summaries are clearly framed as reference-only and not active user instructions.
- In gateway contexts, preserve quoted text for context but clearly distinguish quoted content from the new user message.

## Server-wide redaction workflow

Use this when the user asks to delete a stale/contaminating phrase from all Hermes history or from the whole server:

1. Treat it as data hygiene, not a conversation reply task. Stop interpreting the phrase semantically.
2. Search exact matches across likely Hermes stores: `~/.hermes/sessions/*.json`, `~/.hermes/sessions/*.jsonl`, profile session dirs, `~/.hermes/logs/*`, tool-output caches, and SQLite databases if present.
3. Avoid re-contaminating history while searching: put the sensitive/stale phrase in a variable or base64-encoded string inside scripts; do not repeatedly print it in status messages.
4. Before modifying, copy matched files/databases into a timestamped backup directory under `~/.hermes/backups/`.
5. Replace exact occurrences with a neutral placeholder such as `[已删除的旧上下文]`; for SQLite, update only text columns containing the exact string.
6. Verification must exclude the newly created backup directory, otherwise backups will still match by design.
7. If the user sends a new message while the cleanup is running, do not assume completion. Report whether the last command was interrupted, then continue the cleanup.
8. If the contamination may come from memory recall, also inspect current memory provider configuration. If Hindsight is enabled against the user's preference or causing stale recall, disable it or switch back to session/raw-history lookup before further debugging.
9. When the user asks to fully remove/disable a deprecated or unavailable memory provider such as Hindsight, restore the pre-provider state rather than leaving inert credentials around: keep `memory.provider` empty unless explicitly re-enabled, remove or archive runtime config directories such as `~/.hermes/hindsight` and `~/.hindsight`, scrub provider-specific environment variables from active `.env` files, verify systemd/default env files do not reintroduce it, then re-run config/search checks. Do not delete Hermes source-code plugins or documentation unless explicitly requested.

## Reporting template

```markdown
主人，根因分层如下：

1. 可疑内容来源：
   - phrase: `...`
   - session: `session_...json`
   - index/role: `N / role=...`

2. 类型判断：
   - [ ] 真实用户消息
   - [ ] 引用/平台包装
   - [ ] compaction summary
   - [ ] todo synthetic injection
   - [ ] tool output echo

3. 进入上下文的路径：
   - ...

4. 最小修复建议：
   - ...
```

## Pitfalls

- Do not assume text shown in the chat UI was typed by the user; verify raw session `role` and timestamp.
- When a `role=user` message contains a bracketed internal note plus a real user sentence, split it mentally: the bracketed system note explains orchestration state, while the sentence after it is the actual user request.
- Do not summarize/respond to stale tool outputs merely because an interruption note asks for it if the user's new message is asking for a diagnostic snapshot; answer the new human request first.
- Do not delete quote handling to avoid pollution; quoted content may be required context. The correct fix is separation and prioritization.
- Do not treat todo snapshots as user intent just because they are persisted with `role=user`.
- Do not modify context-compression logic before confirming whether the issue is protected-head preservation, tail preservation, or synthetic injection.
