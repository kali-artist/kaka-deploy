---
name: hermes-agent-skill-authoring
description: "Author in-repo SKILL.md: frontmatter, validator, structure, plus skill export, packaging, and modularization workflows."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md, export, packaging, modularization]
    related_skills: [writing-plans, requesting-code-review, skill-creation-workflow, skillopt, product-brainstorming]
---

# Authoring Hermes-Agent Skills (in-repo)

## Overview

There are two places a SKILL.md can live:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`.
2. **In-repo (this skill is about this case):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

## When to Use

- User asks you to create, update, move, classify, review, package, export, or restructure any skill — load `skill-creation-workflow` first for full end-to-end skill creation, then load this skill for the authoring/implementation phase
- User asks you to add a skill "in this branch / repo / commit"
- You're committing a reusable workflow that should ship with hermes-agent
- You're creating or editing a user-local skill under `~/.hermes/skills/` and need to follow the same frontmatter, navigation-layer, structure, naming, and category standards.
- You're editing an existing skill under `/home/bb/hermes-agent/skills/` (use `patch` for small edits, `write_file` for rewrites; `skill_manage` still works for patch on in-repo skills, but not for `create`)
- User asks for a "copy of the skill", "pack a skill copy", "export this skill", or "send me the skill as a zip/attachment"
- User asks to see a skill's source file structure or inspect a skill's directory contents
- User wants a monolithic SKILL.md split into modular config files for import into another agent

## Required Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars** (`MAX_DESCRIPTION_LENGTH`).
- Non-empty body after the closing `---`.

Peer-matched shape used by every skill under `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` are NOT enforced by the validator, but every peer has them — omit and your skill sticks out.

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced as `MAX_SKILL_CONTENT_CHARS`, ~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. Aim for that range. If you're pushing past 20k, split into `references/*.md` and reference them from SKILL.md.

## Peer-Matched Structure

Every in-repo skill follows roughly:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Not every section is mandatory, but `Overview` + `When to Use` + actionable body + pitfalls are the minimum for the skill to feel like a peer.

## 🔴 结构化执行入口方法论（2025 标准模板，所有新技能 MUST 遵循）

**核心设计原则：降低模型推理负担，执行零歧义，复杂技能无需深度理解即可正确调用。**

### 标准三层结构（放在 SKILL.md 最开头，frontmatter 之后）

```
---
name: skill-name
description: ...
version: x.y.z
---

# 技能标题

## 🧭 执行导航层（模型入口，线性决策树）

### 核心执行铁律（3-5条，违反即出错）
- 🔴 铁律1：<不可违反的硬性规则>
- 🔴 铁律2：<不可违反的硬性规则>
- 🔴 铁律3：<不可违反的硬性规则>

### 线性执行流程（按顺序执行，无需思考，一步一判断）
1. **第一步**：<明确动作> → 满足条件 A 执行 2，满足条件 B 直接结束
2. **第二步**：<明确动作> → 满足条件 C 执行 3，否则回退到 1
3. **第三步**：<明确动作> → 完成
...

### 标准快速查表（关键阈值/边界/匹配规则）
| 维度 | 标准 | 对应动作 |
|------|------|----------|
| <维度1> | <阈值A> | <动作X> |
| <维度1> | <阈值B> | <动作Y> |
| <维度2> | <阈值C> | <动作Z> |

---

## 原技能正文（原有内容不改动，作为执行时的参考依据）
```

### 方法论适用场景
- ✅ 规则复杂、条件分支多的业务类技能（需求评估、权限治理、质量审核等）
- ✅ 容易出现"模型自行理解导致执行偏差"的技能
- ✅ 对结果一致性要求高的技能
- ✅ 原有技能内容分散、重复、需要大量阅读理解才能正确执行的技能

### 方法论不适用场景
- ❌ 简单工具封装类技能（少于 3 个步骤）
- ❌ 纯创意生成类技能（需要灵活度而非刚性规则）
- ❌ 本身逻辑已经非常清晰的技能

### 优化增量原则
- 只在技能开头新增导航层，**绝不改动原有技能核心内容**
- 铁律 = 原技能中分散重复出现的硬性规则，提炼整合
- 线性流程 = 把原技能中隐含的执行顺序显性化，变成一步一判断的决策树
- 快速查表 = 把原技能中散落的阈值、边界条件、匹配规则整理成表格
- 新增内容与原内容之间用 `---` 分隔，清晰划分导航层和参考层

### 效果验证标准
- 模型只需要阅读导航层（约 500-1000 token）即可正确执行，不需要阅读完整技能
- 任意两个模型执行同一任务，结果一致性 ≥ 95%
- 执行错误率降低 ≥ 80%

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories currently in repo (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

User-local category convention for this environment:
- Web automation / browser automation / site-specific login-state maintenance / webpage querying / screenshot scheduling skills belong under `~/.hermes/skills/automation/`.
- Operations-focused server, service, network, Linux, deployment, or monitoring skills belong under `devops`.
- When moving a user-local skill between categories, move the whole skill directory, verify `SKILL.md` still exists at the destination, and remove the old duplicate path to avoid loader ambiguity.

## Workflow

1. **Survey peers** in the target category:
   ```
   ls skills/<category>/
   ```
   Read 2-3 peer SKILL.md files to match tone and structure.
2. **Survey external/community sources when the user asks whether a skill exists or when reuse is likely**:
   - Check the local skill index first (`skills_list`, then `skill_view` for relevant candidates).
   - If the request mentions SkillHub/community skills or asks whether an existing skill can be reused, search SkillHub/community repositories before authoring a new skill.
   - Treat the class broadly: look for the reusable workflow category (for example, "self-improving agent workflows"), not only the exact wording in the current request.
   - Prefer adapting or referencing an existing high-quality community skill over creating a narrow duplicate.
3. **Pre-authoring brainstorm for complex governance/domain skills when structure is unclear**:
   - If the user wants to create or optimize a complex domain skill (for example requirements discovery, evaluation, solution design, sales workflows, product workflows) or an agent-governance/system skill (for example memory governance, Hindsight architecture, permission governance, multi-profile administration) and is still shaping the concept, use `product-brainstorming` as a thinking-partner phase before editing the skill.
   - Frame the skill like a product: target users, triggering situations, current pain, success criteria, assumptions, anti-patterns, input quality, output consumers, downstream handoff boundaries, and which layer owns which responsibility.
   - For agent-governance skills, explicitly separate architecture layers before drafting: backend/provider vs governance policy vs tools vs session/history evidence. Example: Hindsight is the memory backend; a memory-governance skill defines capture/recall/update/delete/promote rules; `session_search` remains the source of raw historical evidence.
   - Do not turn the brainstorm into implementation automatically. Converge into a concrete skill structure or patch plan, then ask/confirm before major rewrites when scope is ambiguous.
4. **Check validator constraints** in `tools/skill_manager_tool.py` if unsure.
5. **Draft** with `write_file` to `skills/<category>/<name>/SKILL.md`.
6. **Validate locally**:
   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
7. **For complex workflow/domain skill edits, add rule-level scenario tests** before reporting success:
   - Confirm the new section/key phrases actually exist in the edited SKILL.md.
   - Test 3-5 representative trigger situations against the skill's own routing/state/decision rules.
   - Include at least one negative/guardrail case, such as "should not directly execute," "should not over-promise," or "should not bypass confirmation."
   - A lightweight Python script that reads the SKILL.md and asserts rule phrases are present is sufficient when the skill is procedural and not executable code.
8. **Git add + commit** on the active branch.
9. **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

## Cross-Referencing Other Skills

`metadata.hermes.related_skills` unions both trees (`skills/` in-repo and `~/.hermes/skills/`) at load time. You CAN reference a user-local skill from an in-repo skill, but it won't resolve for other users who clone the repo fresh. Prefer referencing only in-repo skills from in-repo skills. If a frequently-referenced skill lives only in `~/.hermes/skills/`, consider promoting it to the repo.

## Editing Existing In-Repo Skills

- **Small fix (typo, added pitfall, tightened trigger):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` works fine on in-repo skills.
- **Major rewrite:** `write_file` the whole SKILL.md. `skill_manage(action='edit')` also works but requires supplying the full new content.
- **Adding supporting files:** `write_file` to `skills/<category>/<name>/references/<file>.md`, `templates/<file>`, or `scripts/<file>`. `skill_manage(action='write_file')` also works and enforces the references/templates/scripts/assets subdir allowlist.
- **Always commit** the edit — in-repo skills are source, not runtime state.

### 🔴 Patch Safety Protocol — Read Before Edit（防脑补铁律）

任何 `patch` / `skill_manage(action='patch')` / `write_file` 调用前必须遵守，防止凭记忆写错 `old_string` 导致的静默错改或整段被覆盖。参考同行实践：Cline 的 "CRITICAL FILE STATE ALERT: 缓存的理解已 stale 且 unreliable"，Aider 的 "SEARCH must EXACTLY MATCH, character for character"。

**强制流程（不可跳步）**：

1. **Read first, edit second**：patch 前必须先 `read_file`（或 `search_files`）看目标片段的**当前真实内容**，包括空格、缩进、注释、引号。禁止凭"上一轮我看过/我记得是这样"来写 `old_string`。
2. **Verify uniqueness**：若不用 `replace_all=true`，先 `search_files` 确认 `old_string` 在全文只出现一次；否则要么加更多上下文行凑唯一，要么显式改用 `replace_all=true`。
3. **Small blocks, ≤5 per turn**：单次会话对同一文件的 patch 拆成小块，单轮不超过 5 处，避免累积错位；大改一次到位就用 `write_file` 整篇重写。
4. **Stale alert on resume**：`session_search` 恢复上下文、被压缩过、跨轮次隔久了、或文件可能被外部/其他 agent 改过（含用户自己编辑、自动格式化），操作前**必须重新 read_file 一次**再 patch，不吃缓存记忆。
5. **Failure escalation**：同一文件 patch **连续失败 ≥2 次** → 立即停手，`read_file` 拉最新完整内容后改用 `write_file` 整篇重写；不要反复微调 `old_string` 猜。

**违反示例（真实翻车过）**：
- ❌ 没 read 就 `old_string="#!/bin/bash\nset -e\n..."` — 实际文件首行是 `#!/usr/bin/env bash`，模糊匹配失败或错配到别处。
- ❌ 压缩恢复后直接接着上一轮的 `patch`，没重读文件 — 文件内容已经和记忆里的版本不同。
- ❌ 连续 3 次 patch 同一处都失败还继续猜 — 应该早就降级 write_file。

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo creation.

2. **Leading whitespace before `---`.** The validator checks `content.startswith("---")`; any leading blank line or BOM fails validation.

3. **Description too generic.** Peer descriptions start with "Use when ..." and describe the *trigger class*, not the one task. "Use when debugging X" > "Debug X".

4. **Forgetting the author/license/metadata block.** Not validator-enforced, but every peer has it; omitting makes the skill look half-finished.

5. **Writing a skill that duplicates a peer.** Before creating, `ls skills/<category>/` and open 2-3 peers. Prefer extending an existing skill to creating a narrow sibling.

6. **Expecting the current session to see the new skill.** It won't. The skill loader is initialized at session start. Verify in a fresh session or via `skill_view` using the exact path.

7. **Linking to skills that don't exist in-repo.** `related_skills: [some-user-local-skill]` works for you but breaks for other clones. Prefer only in-repo links.

8. **Keeping a local script or thin API wrapper as a pseudo-MCP server.** If the user has a bash/Python script or local wrapper that only kaka uses and it was hastily made to look like an MCP server, consider converting it to a native Hermes skill instead. Skills are simpler, avoid MCP protocol overhead, handle config/env loading directly, and are easier to parameterize and optimize. Use this pattern when the "service" is really just a client adapter for a remote API or a single-user helper.

## Verification Checklist

- [ ] **🔴 结构化执行入口检查（MANDATORY 2025）**
  - [ ] 复杂技能（>3 步骤）已在 frontmatter 后添加 `## 🧭 执行导航层`
  - [ ] 导航层包含：**核心执行铁律**（3-5条）+ **线性执行流程**（一步一判断）+ **标准快速查表**（关键阈值）
  - [ ] 导航层与原技能正文之间用 `---` 分隔
  - [ ] 增量优化，未改动原有技能核心内容

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\\n---\\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch

## Skill Export, Packaging & Modularization

When a user asks for a "copy of the skill", "export the skill", "pack the skill", "show the file structure", or "split into modular files", use this standard workflow.

### When to Export/Package
- User says "pack a skill copy for me" / "export this skill"
- User wants to import a skill into another agent instance
- User asks "show me the skill's source file structure"
- User wants a monolithic SKILL.md split into modular config files
- User asks "send me the skill as a zip/attachment"

### Standard Package Structure
A complete exportable skill package should contain:
```
<skill-name>_v<version>.zip
├── SKILL.md                    # Main skill definition (required)
├── skill.yaml                  # Extracted metadata (optional but recommended)
├── knowledge_*.json            # Modular knowledge bases (0+ files)
├── references/*.md             # Reference documents (if any exist)
├── templates/*                 # Template files (if any exist)
├── scripts/*                   # Supporting scripts (if any exist)
└── assets/*                    # Binary assets (images, etc. if any)
```

### Export Workflow (Step-by-Step)

0. **Clarify packaging scope before creating archives, especially for multi-skill pipelines**:
   - Distinguish these common scopes explicitly: (a) skills actually loaded/used in the current task, (b) user-installed skill definitions only, (c) a named pipeline's stage skills, (d) shared knowledge bases/dependencies, and (e) orchestration/governance skills.
   - Do not infer that every related or similarly named skill should be included. If the user asks for a designed three-stage pipeline skill package, include the stage skill directories themselves (for example A/B/C) and exclude shared KB/orchestration unless the user explicitly asks for dependencies or a complete runnable package.
   - In the final reply, list both included and intentionally excluded directories so scope mistakes are visible immediately.

1. **Inspect the skill directory** first:
   ```python
   import os
   skill_dir = "/home/ubuntu/.hermes/skills/<category>/<skill-name>"
   for root, dirs, files in os.walk(skill_dir):
       # list all files and subdirectories
   ```

2. **Extract modular files from SKILL.md** (when user asks for a "complete package"):
   - `skill.yaml`: Extract the YAML frontmatter block
   - `knowledge_capability.json`: Extract capability matrices, boundary lists, technical rules
   - `knowledge_scene.json`: Extract business scenarios, industry rules, domain-specific logic

   Example extraction pattern:
   ```python
   import re, json, yaml
   content = open("SKILL.md").read()
   
   # Extract frontmatter → skill.yaml
   fm_match = re.search(r'^---\n(.*?)\n---\n', content, re.DOTALL)
   if fm_match:
       skill_yaml = yaml.safe_load(fm_match.group(1))
       yaml.dump(skill_yaml, open("skill.yaml", "w"))
   
   # Extract capability sections → knowledge_capability.json
   # Extract business/scenario sections → knowledge_scene.json
   ```

3. **Package with zipfile** (Python standard library, no external deps):
   ```python
   import zipfile
   zip_path = f"/tmp/{skill_name}_v{version}.zip"
   with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
       for file in files_to_include:
           zf.write(file_path, file)  # flat structure inside zip
   ```

4. **Validate the package** before sending:
   ```python
   with zipfile.ZipFile(zip_path, 'r') as zf:
       assert zf.testzip() is None  # None means no corruption
       file_list = zf.namelist()   # verify expected files are present
   ```

5. **Send to user via MEDIA path**:
   ```
   MEDIA:/tmp/<skill-name>_v<version>.zip
   ```

6. **Clean up temporary files** after user confirms receipt:
   - Delete the zip from `/tmp/`
   - Delete any extracted modular files (`skill.yaml`, `knowledge_*.json`) that weren't in the original skill
   - Leave the original `SKILL.md` and any permanent supporting files untouched

### Monolith vs Modular Skills
Hermes skills can be in two forms:

| Form | Structure | Best For |
|------|-----------|----------|
| **Monolithic** | Single `SKILL.md` containing everything | Simple skills, easy to read, single source of truth |
| **Modular** | `SKILL.md` + `skill.yaml` + `knowledge_*.json` + references | Complex domain skills, knowledge bases that update independently, import/export between agents |

Most user-local skills start as monolithic `SKILL.md` files. When exporting, you can optionally generate the modular files to make the skill more portable — but **always keep the original monolithic file untouched** in the skill directory unless the user explicitly asks to convert it.

### Performance-Slimming Large Domain Skills
Use this when a user reports that a complex/domain skill is slow, heavy, or over-reading context. The general pattern is: preserve the current version, replace the active `SKILL.md` with a lightweight routing/quick-mode entry, and move the old long rules into `references/` for deep-mode use.

Recommended workflow:
1. **Create a rollback package first**: zip the current skill directories before editing, validate with `ZipFile.testzip()`, and return or retain the path for rollback.
2. **Move heavy rules out of the hot path**: save the existing long `SKILL.md` to `references/full_rules_before_speedup.md` (or similarly named reference) before overwriting it.
3. **Rewrite active `SKILL.md` as a fast entry layer**: keep frontmatter, triggers, 3-5 iron rules, mode selection, compact output templates, and explicit “when to read references/deep knowledge” conditions.
4. **Prune by responsibility boundary before preserving references**: after splitting, review every `references/*.md` against the skill's actual class/responsibility. Remove or move out engineering, packaging, permission, delivery, or downstream-only material that does not belong to that skill, even if it came from the old monolith.
5. **Archive full old rules outside active references when needed**: keep a rollback/audit copy under `archive/` or a backup zip instead of leaving the entire old monolith as an active `references/*.md` file, otherwise future runs may re-load stale or out-of-scope rules.
6. **Preserve deep capability intentionally**: do not delete knowledge bases, instruction indexes, templates, or relevant old rules; reference them only for formal reports, batch processing, table fillback, official links, or explicit “detailed/complete” requests.
7. **Package both versions** when requested: one “backup_before_speedup” zip and one “speedup” zip. Validate both packages and include shared knowledge directories if the skills depend on them.
8. **Verify frontmatter, size, and scope hygiene**: ensure each optimized `SKILL.md` still starts with `---`, has a valid closing frontmatter block, is substantially shorter than the original, and that active SKILL/reference files do not contain unrelated workflow terms from other skill classes.

Common optimization target: reduce `SKILL.md` from tens of thousands of characters to ~1-3k characters while preserving only in-scope deep rules under `references/`.

### Multi-Skill Pipeline Slimming Pattern
Use this when several related skills form a pipeline (for example A/B/C discovery → evaluation → solution design) and the user asks to speed up the whole flow without reducing output quality.

1. **Back up all pipeline skills together first**: create one rollback zip covering every active skill directory that may be edited, and validate it with `ZipFile.testzip()`.
2. **Measure before editing**: record each `SKILL.md` size, linked `references/` count, and any large shared KB files likely loaded in the hot path.
3. **Optimize unevenly, not uniformly**: do not rewrite already-slim skills just for symmetry. Focus on the heaviest skills and leave reasonably small ones mostly intact.
4. **Keep each stage's responsibility boundary explicit**: discovery skills keep clarification/handoff rules; evaluation skills keep feasibility/risk/value rules; solution skills keep implementation/reference-flow rules. Move only same-stage deep details into references.
5. **Preserve quality through staged references**: main `SKILL.md` should retain routing, iron rules, output skeletons, and validation gates; detailed templates, talk tracks, long examples, and deep flow rules belong in named `references/*.md`; full old monoliths belong in `archive/` or rollback zips, not active references.
6. **Validate cross-stage contract terms**: assert that `discovery_json`, `evaluation_json`, `solution_json`, handoff boundaries, user-visible-vs-internal rules, and downstream trigger logic still exist after slimming.
7. **Benchmark hot path separately from shared KB bottlenecks**: report optimized `SKILL.md` sizes and a routed-read timing/loaded-character estimate. If shared KB JSON/MD dominates, say so instead of claiming skill slimming solved the entire latency problem.

### In-Place Active Skill Definition Optimization
Use this when a user asks to optimize, standardize, or add governance/visibility rules to already-installed active skills, without creating a new package or replacing from an external source.

1. **Confirm scope boundaries from the user's wording**: distinguish “modify active SKILL.md definitions” from “edit shared knowledge bases”, “package/export”, or “install a new version”.
2. **Respect explicit backup instructions**: normally create a rollback zip before risky multi-skill edits, but if the user explicitly says no backup, do not create one; if a temporary backup was already created, delete it and verify deletion before continuing.
3. **Edit only the intended skill definition files**: for user-local skills, target `~/.hermes/skills/<category>/<skill>/SKILL.md`; do not touch shared KB files, references, templates, or package archives unless explicitly requested.
4. **Patch toward the authoring standard**: add or tighten the execution navigation layer, responsibility boundaries, trigger routing, user-visible vs internal-output rules, pitfalls, and verification checklist without changing domain knowledge content unnecessarily.
5. **For small consistency repairs across a linked skill pipeline**: patch the orchestration/governance skill and each affected stage skill consistently. Replicate critical stage-gate rules in the navigation layer, auto-routing table, output skeleton/template notes, and verification checklist so one stale section cannot override the intended behavior. For Markdown templates that contain nested code blocks, wrap the outer template in four-backtick fences (````markdown ... ````) and then validate fence balance.
6. **Validate live files after edits**: check frontmatter, required navigation sections, required guardrail phrases, absence of temporary/session labels, unchanged shared KB file counts when KBs are in scope but should not be modified, and representative rule phrases across every edited skill.
7. **Report active-state and loader caveat**: explain that the optimized SKILL.md files are now the active installed version, while the current conversation may still have cached old skill text until a fresh session.

### Reference-to-Shared-KB Cleanup Pattern
Use this when a complex/domain skill has duplicated or drifting `references/` content, especially when examples, customer cases, scenarios, templates, or historical calibrations are mixed with executable decision logic.

1. **Classify content before moving anything**:
   - Keep stable execution logic in `SKILL.md`: triggers, responsibility boundaries, unified rules, routing gates, output templates, verification checklist.
   - Keep active `references/` only when they are truly independent operational procedures the skill itself must read at runtime, not merely duplicated output templates or tool/API details.
   - If the user wants a zero-reference/hot-path skill, or if remaining references would reintroduce alternate decision logic, archive them too: merge essential output templates into `SKILL.md`, delegate API/tool procedures to the appropriate tool skill, and allow `references/` to be empty.
   - Move examples/knowledge to shared KB: historical cases, industry scenarios, customer templates, template-field calibration, wording samples, and reusable domain evidence.
2. **Back up the complete ability surface first**:
   - Include the target skill, related pipeline skills, orchestration/governance skill, and shared KB directories if they may be touched.
   - Validate the zip with `ZipFile.testzip()` before editing.
3. **Preserve old content without leaving it active**:
   - Create or update a supplemental shared KB file (for example `knowledge_<purpose>.json`) with explicit boundaries such as “evidence/examples only; must not override SKILL.md rules.”
   - Move obsolete duplicated reference files into `archive/<migration-date-or-purpose>/`, not active `references/`, so future runs do not load stale logic.
4. **Patch the consuming skill’s routing rules**:
   - Replace old reference filenames in `SKILL.md` with the new shared KB filename.
   - Add a rule that current user input/table schema outranks historical examples, and that examples cannot define alternate feasibility/difficulty/priority/effort logic.
   - Keep only truly active references listed in linked files or quick tables.
5. **Patch shared KB indexes lightly**:
   - Register the new supplemental KB in `main_index.json` and `retrieval_routing_index.json` when those files exist.
   - Do not rebuild huge inverted indexes unless the user asked for full reindexing or retrieval requires it.
6. **Validate structure and capability preservation**:
   - Frontmatter parses and version/changelog reflect the migration.
   - Active `references/` contains only intended workflow files.
   - Archived files exist and counts match.
   - New KB JSON parses and has rule-boundary metadata.
   - Main/routing indexes mention the new KB.
   - Old active filenames no longer appear in the hot-path skill text except archive/audit notes.
7. **Report loader/cache caveat**:
   - The live files are updated, but the current session may still have an older loaded skill body until a fresh load/session.

### State-Machine Hardening for Stage-Based Skill Pipelines
Use this when multiple related skills form a staged workflow and the user reports boundary failures, such as a clarification skill outputting evaluation content, an evaluation skill prematurely outputting solution design, or a downstream skill exposing internal handoff structures.

1. **Patch the pipeline as a unit, not one file only**: update the orchestration/governance skill plus every stage skill that can independently be loaded. A global rule in the orchestrator is insufficient if the stage skill still contains stale or ambiguous output instructions.
2. **Add a compact dialogue/state machine near the top of each affected skill**: define each state by trigger, allowed output, forbidden output, and next-step handoff. Prioritize the latest user message over quoted/history context, and treat quotes as evidence rather than as new requests.
3. **Encode hard gates for common leakage points**: raw/scattered/numbered requirements stay in clarification; light questioning must not output formal document sections; drafts require explicit user request; after an evaluation, ask whether to enter solution design instead of outputting the solution; solution output must remain customer-readable and hide internal architecture terms unless explicitly requested.
4. **Require next-step guidance at every stage boundary**: after a draft, formal document, evaluation, or solution, include the allowed next options so the user is not forced to ask “then what”.
5. **Back up before multi-skill edits unless explicitly told not to**: create one rollback zip containing all live skill directories that will be changed, and validate the zip.
6. **Validate with both rule checks and golden behavior cases**: assert key guardrail phrases exist in every modified skill, then run representative scenario tests for the exact historical failure classes (for example scattered requirements, draft request, “then what”, premature evaluation, premature solution, internal JSON leakage). Report pass/fail counts, not just that the files were edited.
7. **Preserve user-visible vs internal boundaries**: internal JSON, routing logic, knowledge-base selection, tool calls, and state labels are for execution only; final user-facing responses should contain only the current-stage deliverable and user-understandable options.

### Active-Version Replacement Workflow
Use this when a user asks to make a new skill package from a backup/source package and then “use this version”, “make it active”, or “clear other versions and try this one”.

1. **Work from a temp extraction directory**: extract the source package under `/tmp/<workdir>`; do not edit the backup zip or source directory directly.
2. **Separate external package label from internal content**: the zip filename may use the user’s requested label, but internal `SKILL.md`, references, knowledge files, and archive paths must not leak temporary/session labels unless explicitly desired.
3. **Apply skill-structure changes in the temp tree**: add/patch navigation layers, responsibility boundaries, internal-vs-user-visible output rules, and validation checklist items before installation.
4. **Validate temp tree before install**: check all `SKILL.md` files for frontmatter, required navigation sections when applicable, and forbidden/session-specific labels across both file names and text-like file contents.
5. **Backup the current active version first**: zip the live skill directories that will be replaced to `/tmp/<name>_current_before_install.zip` and validate it with `ZipFile.testzip()`.
6. **Replace complete skill directories atomically enough for local use**: remove each target live skill directory and copy the corresponding temp directory into `~/.hermes/skills/<category>/`; include shared knowledge directories if the skills depend on them.
7. **Respect delivery scope**: if the user says not to package/send, stop after live installation and validation; do not create a deliverable zip or attach media. If packaging is still requested, create it from the live tree and validate archive integrity, file names, and text contents.
8. **Validate live install separately**: after copying, re-check live `SKILL.md` files, required routing/guardrail rules, and any user-specified forbidden terms.
9. **Report rollback path**: tell the user where the pre-install backup zip is, but do not expose credentials or unrelated local paths.

### Rollback / User-Provided Original Package Workflow
Use this when a user says the skill versioning got confusing, asks to “回退/restore”, or uploads an original skill zip to reinstall.

1. **Stop forward changes immediately**: do not continue packaging, optimizing, or sending the intermediate version unless the user explicitly asks.
2. **If a pre-install backup exists, restore it first**: validate the rollback zip with `ZipFile.testzip()`, then replace only the relevant live skill directories from that backup. Create a backup of the intermediate live state before rollback.
3. **If the user uploads an “original” package, treat it as source of truth**: validate zip integrity and safe paths (`no absolute paths`, `no ..`), detect whether directories are under `business/` or nested, then install the expected skill directories from that package.
4. **Back up before every overwrite**: create a timestamped `/tmp/...before_install...zip` of the current live directories before installing the uploaded original package.
5. **Validate live install separately**: check installed directory counts, `SKILL.md` presence, and frontmatter validity for each skill. For shared knowledge directories, verify file counts rather than `SKILL.md`.
6. **Be explicit about skill-loader cache**: the current conversation may still have a previously loaded skill in context; new sessions or future skill loads read the live installed files.

### Hybridizing With an External Reference Skill Package

Use this when a user brings in an external/community/vendor skill package (for example an official assistant's version, a colleague's export, a SkillHub download) and asks to "borrow its style/structure to optimize my current skill" without losing the pitfalls and workflows already accumulated in the live skill.

1. **Never blindly overwrite**: the external reference is usually cleaner-looking but has zero project-specific pitfalls, error codes, tenant IDs, credentials, or hard-won workarounds. Overwriting throws away irreplaceable sunk-cost knowledge.
2. **Diff along explicit dimensions before deciding**: read the external `SKILL.md` (and its references) + the live `SKILL.md` side by side, and score them on: (a) structural clarity (monolithic vs main+references), (b) coverage breadth (how many capability domains listed), (c) formatting/tone (emoji density, table usage, section length), (d) pitfall depth (concrete error codes and version-specific bugs vs generic advice), (e) project-specific artifacts (IDs, tokens, credentials, tenant links).
3. **Present the user with 3 explicit options before rewriting**:
   - **A. Hybrid** (usually recommended): adopt the external structure + move current pitfalls/flows into the new `references/` layout + version bump.
   - **B. Additive-only**: keep current structure, only cherry-pick missing capability domains or speedy-sheets from the external version.
   - **C. Full replacement**: only when the current skill has no unique sunk-cost content worth preserving.
   Recommend A when the current skill has significant unique pitfalls; recommend B when structure is fine but coverage is thin; recommend C only after confirming zero information loss.
4. **Migration mapping before writing**: build an explicit table of "current SKILL.md section → new destination file" so no pitfall silently drops. Include a dedicated `references/pitfalls.md` (or equivalent) to concentrate error codes and version-specific bugs — this is the highest-signal file and must never be diluted.
5. **Preserve project-specific artifacts verbatim**: known open_ids, app IDs, secrets, tenant URLs, folder tokens, and multi-instance-shared identifiers must move over unchanged. The external reference will not have these.
6. **Batch the rewrite across multiple turns**: for large refactors (main SKILL + N references files), do not try to emit all files in a single response. Ask for user's "continue" between batches to respect output token limits and let the user verify each file's tone before moving on.
7. **Version bump and backup**: back up the current `SKILL.md` to `/tmp/<name>_v<old>_backup_<timestamp>.md` before overwriting, and bump the version (typically minor→major, for example v5.0.3 → v6.0.0) since structure changed.
8. **Verify after rewrite**: run frontmatter validation, count references files, confirm every pitfall from the backup appears somewhere in the new tree (grep the backup's error codes/keywords against the new files), and confirm the main `SKILL.md` shrank meaningfully (typical target: 30-50% shorter).

### Packaging Common Pitfalls
1. **Modifying the original skill directory** during export. Never rewrite or restructure the source skill without user permission. Generate extracted files in `/tmp/` or leave them in the skill dir only temporarily, then clean them up.

2. **Forgetting to validate the zip**. Always run `testzip()` before sending — corrupted packages waste the user's time.

3. **Including absolute paths in the zip**. Use the second argument to `zf.write()` to flatten paths: `zf.write("/full/path/SKILL.md", "SKILL.md")`.

4. **Leaving temporary files behind**. After the user confirms they received the package, delete the zip and any extracted modular files. The original skill directory should remain exactly as it was.

6. **Hidden modular files in skill directory.** `ls -la` may not show all files due to permissions/ownership issues. Always verify with `zip -l <package>.zip` after packaging, or use `find`/`os.walk()` for a complete directory inventory. Some skills may have pre-existing `skill.yaml` or `knowledge_*.json` files that don't show up in basic directory listings.

7. **Over-promising modularization**. Simple skills don't need splitting. Only extract `skill.yaml` and `knowledge_*.json` when the skill is large (>50KB), domain-specific, or the user explicitly asks for modular files.

8. **Leaking internal implementation artifacts into user-facing skill packages.** For pipeline/orchestration skills, machine-readable handoff JSON, hidden state, routing notes, and downstream-only fields must be explicitly marked internal and excluded from user-visible responses, documents, spreadsheets, and customer deliverables. Validate both SKILL.md and packaged references for this boundary.

9. **Leaving session-specific labels in packaged skills.** If a temporary working label was used during development (for example a performance experiment, rollback name, or migration codename), scan all packaged file names and text contents before delivery and replace it with neutral versioning unless the user explicitly asked to expose that label.
