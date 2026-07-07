---
name: hermes-community-skill-installation
description: "Use when installing Hermes community skills from SkillHub/skills.sh, videos/posts, or GitHub repositories, especially when skill names are ambiguous, safety scanning blocks install, or GitHub API/HTTPS limits require SSH/manual fallback."
version: 1.0.0
author: kaka (卡力的专属小机器人)
license: MIT
metadata:
  hermes:
    tags: [hermes, skills, skillhub, installation, github, safety]
    related_skills: [hermes-agent, hermes-agent-skill-authoring, github-auth, network-connectivity-troubleshooting]
---

# Hermes Community Skill Installation

## Overview

This skill covers the reusable workflow for installing Hermes skills that come from SkillHub/skills.sh, social videos/posts, or community GitHub repositories. It focuses on resolving ambiguous skill names, installing safely, handling scanner warnings, working around GitHub API limits or TLS failures, and verifying that installed skills load in the current Hermes environment.

## When to Use

Use when:
- A user asks to install Hermes skills mentioned in a video, article, post, or screenshot.
- A user provides a skills.sh / SkillHub ID or community GitHub repository and wants it installed.
- `hermes skills install` or `inspect` fails due to GitHub API rate limits, HTTPS/TLS/network issues, or safety scanner blocks.
- You need to distinguish between installing a `SKILL.md` and executing setup commands described inside that skill.

Do not use for:
- Authoring a new skill from scratch; use `hermes-agent-skill-authoring`.
- General Hermes CLI/provider/gateway configuration; use `hermes-agent`.
- Pure network diagnosis without a skill-install context; use `network-connectivity-troubleshooting`.

## Standard Workflow

### 0. Check Whether the Skill Is Already Installed

Before searching SkillHub or running an install, check the local skill registry first, especially when the user gives an exact skill name.

```text
skills_list()
skill_view(name="<requested-skill-name>")
```

If `skill_view` loads successfully, the skill is already available to the current agent. Report that it is already installed/available and do not reinstall unless the user explicitly asks to update, reinstall, or replace it. If the requested label differs from the installed skill name, report the mapping clearly.

### 1. Resolve the Candidate Skills

Search broadly because video labels, repository names, and `SKILL.md` names may differ.

```bash
hermes skills search "<spoken-name-or-repo>" --limit 20
hermes skills search "<alternate-keywords>" --limit 20
```

For each candidate, inspect before installing:

```bash
hermes skills inspect "<hub-id>"
```

Confirm:
- The frontmatter `name` is the intended skill.
- The source repo/path matches the user's requested target as closely as possible.
- The skill is a real Hermes `SKILL.md`, not merely a project/repository with no installable manifest.
- If `hermes skills inspect "<hub-id>"` displays a short `Identifier` but `hermes skills install "<short-name>"` says "No exact match" or offers unrelated candidates, install with the full hub identifier you inspected (for example `skills-sh/obra/superpowers`) rather than the ambiguous short name.
- If the user's label is a project/marketing name rather than the exact skill name, build an explicit mapping table: `user label -> Hub identifier -> installed skill name`. Example patterns include `gbrain -> brain-ops`, `hermes-webui -> hermes-webui-agent`, `awesome-hermes-agent -> awesome-hermes-agent-ecosystem`, and `superpowers -> skills-sh/obra/superpowers -> superpowers`.
- For bundle-style skills such as `gstack`, installing the root skill may also expose child skills (for example `browse`, `qa`, `review`, `ship`, `plan-*`). Treat these as bundled extras, but still verify the requested root skill itself is present.

### 2. Prefer Normal Hub Install

```bash
hermes skills install "<hub-id>"
```

If install succeeds, continue to verification.

If the install pauses for an interactive confirmation prompt in a non-interactive/tool-run context, do not treat it as a network failure. After inspection and risk assessment, rerun with explicit confirmation:

```bash
printf 'y\n' | hermes skills install "<hub-id>"
```

Do not use `printf 'y\n'` to bypass safety scanner blocks; scanner blocks require the explicit `--force` workflow below.

### 3. Handle Safety Scanner Blocks

If the installer reports `DANGEROUS` or blocks installation:

1. Do not silently bypass.
2. Explain the scanner saw risky text or setup snippets, such as shell commands, git/npm/pip/docker, persistent config changes, credentials, proxy/password handling, or service changes.
3. Clarify that installing a skill stores `SKILL.md`; it does not execute the commands documented inside the skill.
4. Use `--force` only when the administrator/user explicitly requested installation and the risk is understood.

Example:

```bash
hermes skills install --force "<hub-id>"
```

Never run arbitrary setup commands from inside a community skill unless the user separately asks for setup and you have assessed the commands.

### 4. Work Around GitHub API Limits or HTTPS/TLS Failures

If SkillHub/GitHub API is rate-limited or direct HTTPS/git clone fails:

1. Check existing SSH configuration before giving up:
   ```bash
   test -f ~/.ssh/config && awk '/^Host /{print $0}' ~/.ssh/config
   ssh -T <github-host-alias>
   ```
   In this environment, a GitHub SSH alias may exist, e.g. `github.com-kali-sites`.
2. Clone by SSH using the configured alias:
   ```bash
   rm -rf /tmp/<repo-name>
   GIT_SSH_COMMAND='ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new' \
     git clone --depth 1 git@<github-host-alias>:<owner>/<repo>.git /tmp/<repo-name>
   ```
3. Locate target skill directories:
   ```bash
   python3 - <<'PY'
from pathlib import Path
root = Path('/tmp/<repo-name>')
for p in root.rglob('SKILL.md'):
    print(p)
PY
   ```
4. Copy only the intended skill directory into the user-local skills tree:
   ```bash
   mkdir -p ~/.hermes/skills/<skill-name>
   cp -a /tmp/<repo-name>/<path-to-skill>/. ~/.hermes/skills/<skill-name>/
   ```

Preserve the directory structure and confirm `SKILL.md` exists at the destination.

### 5. Verify Installation

Use both CLI and runtime loader checks:

```bash
hermes skills list | grep -i "<skill-name>" || true
```

Then call the tool-level loader for each skill:

```text
skill_view(name="<skill-name>")
```

If a Hub/package directory name differs from the `SKILL.md` frontmatter `name`, the frontmatter `name` is the runtime skill identifier used by `--skills` and by the loader. Treat the package directory as an install path only, and report the mapping clearly:

```text
Hub/package: <owner>/<package-or-directory>
Runtime skill: <frontmatter-name>
Path: ~/.hermes/skills/<package-or-directory>/SKILL.md
```

When installing for a non-default profile, verify inside that target profile rather than only in the current agent:

```bash
hermes chat --profile <profile> --skills <runtime-skill-name> -q '请只回复：技能可用'
```

For profile gateway/messaging use, also verify the skill can be loaded by an agent running under the target profile with an explicit `skill_view` request, not just by the startup banner or the current session:

```bash
hermes chat --profile <profile> -q '请调用 skill_view 读取 <runtime-skill-name>，然后只回复：读取成功 或 读取失败。'
```

If the target profile still reports `Skill '<name>' not found` or says it cannot read the skill while CLI checks seem successful:
- Inspect the target profile's latest raw sessions and logs (`~/.hermes/profiles/<profile>/sessions/`, `logs/gateway.log`, `logs/agent.log`) to confirm the actual tool error and latest user request.
- Check both loader contexts that may be involved: `HERMES_HOME=~/.hermes` plus `HERMES_PROFILE=<profile>`, and `HERMES_HOME=~/.hermes/profiles/<profile>` plus `HERMES_PROFILE=<profile>`.
- Ensure `SKILL.md` exists under stable root and category forms when directory/package names differ from frontmatter names, for example `~/.hermes/skills/<runtime-name>/`, `~/.hermes/skills/<category>/<runtime-name>/`, `~/.hermes/profiles/<profile>/skills/<runtime-name>/`, and `~/.hermes/profiles/<profile>/skills/<category>/<runtime-name>/` as appropriate.
- Restart the target gateway after filesystem changes and retest in a clean profile chat. Long-lived messaging sessions may preserve earlier failed conclusions even after the file layout is fixed; do not treat a model's old “read failed” statement as current evidence without checking raw session/tool results.

The startup banner should list the runtime skill name under Available Skills for that profile, and the query should complete without `Unknown skill(s)`.

For multi-skill/bundle installs, verify each requested mapping explicitly and include the filesystem path when useful:

```bash
python3 - <<'PY'
from pathlib import Path
root = Path.home() / '.hermes/skills'
for label, skill in [
    ('user-facing label', 'installed-skill-name'),
]:
    p = root / skill / 'SKILL.md'
    print(f'{label}\t{skill}\t{"OK" if p.exists() else "MISSING"}\t{p}')
PY
```

A skill is considered installed for the current agent if `skill_view` can load it successfully. Report aliases clearly so the user understands why the installed name may differ from the video/post label.

## Safety Rules

- Installing a `SKILL.md` is not the same as executing its documented commands; keep these separate in reports.
- Do not expose tokens, cookies, API keys, or private clone URLs in logs or final replies.
- Do not run `chmod -R`, `chown -R`, service restarts, docker commands, npm/pip install scripts, or shell setup snippets from community skills unless explicitly requested and separately assessed.
- If using `--force`, summarize why it was needed and what risk category the scanner flagged.

## Verification Checklist

- [ ] Candidate skill names were resolved with `hermes skills search` and/or source inspection.
- [ ] Each candidate was inspected before install when possible.
- [ ] Scanner warnings were not bypassed silently.
- [ ] GitHub/API/network fallback used SSH or a trusted mirror rather than exposing credentials.
- [ ] Manual copies included only the target skill directory and kept `SKILL.md` at the destination root.
- [ ] `skill_view` successfully loads every installed skill.
- [ ] Final report distinguishes installed skill text from any unexecuted setup commands.
