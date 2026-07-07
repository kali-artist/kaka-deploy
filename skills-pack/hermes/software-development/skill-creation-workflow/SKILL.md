---
name: skill-creation-workflow
description: "Use when creating any new skill. 3-step standard workflow: 1) brainstorm & align requirements, 2) create skill with authoring standards, 3) optimize with SkillOpt. Prevents skipping stages and delivers high-quality validated skills."
version: 1.0.0
author: kaka
license: MIT
metadata:
  hermes:
    tags: [skills, authoring, workflow, brainstorm, optimization]
    related_skills: [product-brainstorming, hermes-agent-skill-authoring, skillopt]
---

# 📦 Skill Creation Workflow - 技能创建工作流

## 🧭 Execution Navigation Layer (Model Entry Point, Linear Decision Tree)

### Core Execution Iron Rules (Violation = Failure)
- 🔴 Rule 1: Must load this skill FIRST before creating any new skill
- 🔴 Rule 2: Strictly follow 3 steps, NEVER skip any
- 🔴 Rule 3: Must get owner confirmation after each step before proceeding

### Linear Execution Flow (Execute in order, confirm step-by-step)
| Step | Action | Skill to Load | Acceptance Criteria |
|------|--------|---------------|---------------------|
| **1️⃣ Brainstorm & Align** | Align requirements with owner repeatedly | `product-brainstorming` | ✅ Owner explicitly says "Requirements aligned" |
| **2️⃣ Create Skill** | Create skill following standards | `hermes-agent-skill-authoring` | ✅ Owner explicitly says "Creation complete" |
| **3️⃣ Optimize & Iterate** | Run tests and optimize skill quality | `skillopt` | ✅ Owner explicitly says "Optimization complete" |

### Mandatory Deliverables per Step
| Step | Must Produce |
|------|-------------|
| 1️⃣ Brainstorm | Skill requirements doc: goal + mechanism + io + boundaries |
| 2️⃣ Create | Complete SKILL.md + supporting scripts/references + complete frontmatter |
| 3️⃣ Optimize | Validation report + best_skill.md + before/after comparison |

---

## Overview

This is the standard workflow for creating Hermes Agent skills. It solves the core problems:
- ❌ Skipping requirement alignment, writing skills based on own understanding
- ❌ Delivering unvalidated skills full of bugs
- ❌ Writing skills without standard format, chaotic structure

**Correct approach: Brainstorm align first → Create by standards → Validate and optimize**, all 3 steps are mandatory.

## When to Use

- User says "help me create a skill"
- User says "optimize this skill"
- Any scenario requiring new skill creation or major modification of existing skills
- **Do NOT use for**: Minor bug fixes, small typo corrections

---

## 📋 Step 1: Brainstorm & Align (Use `product-brainstorming`)

### Must clarify with owner:
1. **Skill goal**: What problem does this skill solve?
2. **Trigger scenarios**: When to use this skill?
3. **Mechanism**: What's the input? Step-by-step process? What's the output?
4. **Boundary conditions**: What scenarios should NOT use this skill?
5. **Acceptance criteria**: How to know this skill is correct?
6. **Forbidden actions**: Any hard red lines that must never be crossed?

### Brainstorm Phase Red Lines
- ❌ Never start writing SKILL.md before alignment
- ❌ Never change requirements while writing
- ❌ Never use "I think it should be like this" instead of owner's actual requirements

### Phase Completion Marker
✅ Owner explicitly says: "Requirements aligned, you can start writing"

---

## 📋 Step 2: Create Skill (Use `hermes-agent-skill-authoring`)

### Mandatory Standard Structure:
```yaml
---
name: skill-name               # lowercase, hyphens
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: kaka
license: MIT
metadata:
  hermes:
    tags: [tag1, tag2]
    related_skills: [other-skill]
---
```

### Mandatory Sections:
1. ✅ **🧭 Execution Navigation Layer** (2025 Standard Template): Core Iron Rules + Linear Flow + Quick Lookup Table
2. ✅ **Overview**: One sentence explaining what this skill does
3. ✅ **When to Use**: What scenarios to use + what scenarios NOT to use
4. ✅ **Core Operation Flow**: Step-by-step how to do it
5. ✅ **Common Pitfalls**: Common mistakes and how to avoid
6. ✅ **Verification Checklist**: Acceptance checklist (checkbox style)

### Mandatory Validations:
- Frontmatter starts with `---` at byte 0, no leading blank lines
- Description ≤ 1024 characters
- Total file size ≤ 100,000 characters (recommended 8-15k)
- Placed in correct category directory

### Phase Completion Marker
✅ Owner explicitly says: "Creation complete, can enter optimization phase"

---

## 📋 Step 3: Optimize & Iterate (Use `skillopt`)

### SkillOpt Standard 8-Step Optimization Flow:
1. **Define optimization contract**: Success metrics + acceptance threshold + allowed modification scope
2. **Build train/validation sets**: At least 3-5 test cases (JSONL format)
3. **Run baseline test**: Run original skill, record baseline score
4. **Analyze failure traces**: Identify common issues
5. **Propose small modification**: One change at a time for easy comparison
6. **Run validation gate**: Re-run validation set after modification
7. **Accept/reject modification**: Accept only if score improves AND no regressions
8. **Export final version**: Generate best_skill.md + optimization report

### Optimization Phase Acceptance Criteria:
- Validation set pass rate ≥ baseline + 0.02
- No critical task regression (pass→fail)
- No meaningless skill bloat

### Phase Completion Marker
✅ Owner explicitly says: "Optimization complete, this skill is ready for delivery"

---

## Common Pitfalls

1. **Skipping brainstorm and writing skill directly**: End result completely different from what owner wanted, wastes time
2. **Merging 3 steps into 1**: Brainstorm+create+optimize mixed together, chaotic and quality uncontrollable
3. **Delivering without validation**: Skill looks beautiful but full of bugs when actually used
4. **Too many changes per iteration**: SkillOpt requires one small change at a time for easy effect localization
5. **Not recording failed modifications**: Repeat same mistakes, fall into same pit repeatedly
6. **Forgetting linked supporting files**: When optimizing existing skills, always check for linked scripts, references, templates and update them too — most skills rely on external files, not just SKILL.md
7. **Only updating documentation**: When fixing bugs or adding features, always update the actual implementation code (scripts, helpers) AND update the documentation to match — out-of-sync docs are worse than no docs
8. **SkillOpt nested path issue**: Some Hermes skills use 2-level nesting (e.g., `category/skill-name/skill-name/SKILL.md`), always run `ls -la` first to verify the actual SKILL.md path before running `skillopt.py init` — wrong path causes immediate "skill not found" error

---

## Verification Checklist

- [ ] **Step 1 Complete**: Loaded `product-brainstorming`, aligned requirements with owner, got "Requirements aligned" confirmation
- [ ] **Step 2 Complete**: Loaded `hermes-agent-skill-authoring`, created complete SKILL.md following standards including 🔴 structured execution entry
- [ ] **Step 3 Complete**: Loaded `skillopt`, ran at least 1 round of validation testing, has baseline vs optimized comparison
- [ ] **Deliverables Complete**: Full skill files + validation report + usage instructions
- [ ] **Final Confirmation**: Owner explicitly says "Optimization complete, ready for delivery"
