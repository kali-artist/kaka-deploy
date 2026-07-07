---
name: hermes-agent
description: "Configure, extend, or contribute to Hermes Agent."
version: 2.0.0
author: Hermes Agent + Teknium
license: MIT
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, messaging platforms, and IDEs. It belongs to the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, DeepSeek, local models, and 15+ others) and runs on Linux, macOS, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills. When it solves a complex problem, discovers a workflow, or gets corrected, it can persist that knowledge as a skill document that loads into future sessions. Skills accumulate over time, making the agent better
- **Expandable memory providers** — Native long-term memory is limited to ~2200 characters. Use the pre-installed `holographic` memory plugin to unlock unlimited semantic memory:
  1. Run `hermes config set memory.provider holographic`
  2. Run `hermes memory setup` to initialize the SQLite fact store
  3. Holographic auto-extracts facts from sessions, supports semantic search, entity resolution, and trust scoring, with no hard capacity limit at your specific tasks and environment.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends (built-in, Honcho, Mem0, and more) let you choose how memory works.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and 10+ other platforms with full tool access, not just chat.
- **Provider-agnostic** — swap models and providers mid-workflow without changing anything else. Credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, and the full Python ecosystem.

People use Hermes for software development, research, system administration, data analysis, content creation, home automation, and anything else that benefits from an AI agent with persistent context and full system access.

**This skill helps you work with Hermes Agent effectively** — setting it up, configuring features, spawning additional agent instances, troubleshooting issues, finding the right commands and settings, and understanding how the system works when you need to extend or contribute to it.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Interactive chat (default)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard
hermes setup

# Change model/provider
hermes model

# Check health
hermes doctor
```

---

## CLI Reference

### Global Flags

```
hermes [flags] [command]

  --version, -V             Show version
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --pass-session-id         Include session ID in system prompt
```

No subcommand defaults to `chat`.

### Chat

```
hermes chat [flags]
  -q, --query TEXT          Single query, non-interactive
  -m, --model MODEL         Model (e.g. anthropic/claude-sonnet-4)
  -t, --toolsets LIST       Comma-separated toolsets
  --provider PROVIDER       Force provider (openrouter, anthropic, nous, etc.)
  -v, --verbose             Verbose output
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --source TAG              Session source tag (default: cli)
```

### Memory Configuration
Hermes supports pluggable memory backends to extend capacity beyond the default limit:
- Check status: `hermes memory status`
- Backends: holographic (local, recommended), honcho, mem0, hindsight, etc.

#### Enable unlimited local memory:
```bash
# Backup first
cp -r ~/.hermes/memories/ ~/hermes-memory-backup/
# Configure
hermes config set memory.provider "holographic"
hermes config set memory.memory_char_limit 1000000
# Restart gateway
systemctl --user restart hermes-gateway
```

#### Troubleshooting: auto_extract is configured but facts are not saved
If `memory.provider` is `holographic` and `hermes-memory-store.auto_extract` is `true`, but `fact_store` remains empty, check that the plugin is actually enabled in `plugins.enabled`. A configured plugin block alone is not enough; it must appear in the enabled list:

```yaml
plugins:
  enabled:
  - hermes-memory-store
  hermes-memory-store:
    auto_extract: true
    default_trust: 0.5
    min_trust_threshold: 0.3
```

After adding it to `enabled`, restart the gateway. For high-value conclusions and final solutions, also add explicit `fact_store add` calls in the profile's `SOUL.md` rather than relying solely on auto-extraction.

#### Memory tier governance: Core Memory vs. fact_store

When a profile uses `holographic` memory, you have two tiers. Put the right content in the right tier or you will lose critical rules or bloat the context.

**Core Memory (`MEMORY.md` / `USER.md` / `SOUL.md`) — must be injected every turn**
Use this only for content that must be **always present** and must never depend on a search retrieval:
- Identity rules and persona definition
- Highest-priority safety bans and behavior iron laws
- Mandatory behavior guidelines (e.g. "only respond to user X", "never run recursive chmod")
- Configurations that must take effect every turn (e.g. output format, approval rules, gateway identity)

Do **not** put large amounts of mutable facts, one-time events, or transient state here. Core Memory has limited token budget and is not meant for encyclopedic knowledge.

**Holographic fact_store — retrieved on demand**
Use `fact_store add` for reusable, queryable facts that do not need to be present on every turn:
- Verified facts, historical events, relationships
- User preferences, habits, stable configuration details
- Root-cause analyses, case studies, learned lessons
- Anything you would look up with `fact_store search` / `fact_store probe`

**Hard boundaries**
1. Never store "must be enforced every turn" rules only in fact_store — if the retrieval is not triggered, the rule is silently ignored.
2. Never dump temporary state, task progress, one-off outputs, or uncertain guesses into fact_store.
3. Never let Core Memory grow into a chronicle of mutable facts; move those to fact_store.

When updating a profile's memory files, first classify the new item: "Is this a rule that must always be active?" → Core Memory. "Is this a reusable fact that I might need to recall later?" → fact_store.

### Tools & Skills

```
hermes tools                Interactive tool enable/disable (curses UI)
hermes tools list           Show all tools and status
hermes tools enable NAME    Enable a toolset
hermes tools disable NAME   Disable a toolset

hermes skills list          List installed skills
hermes skills search QUERY  Search the skills hub
hermes skills install ID    Install a skill (ID can be a hub identifier OR a direct https://…/SKILL.md URL; pass --name to override when frontmatter has no name)
hermes skills inspect ID    Preview without installing
hermes skills config        Enable/disable skills per platform
hermes skills check         Check for updates
hermes skills update        Update outdated skills
hermes skills uninstall N   Remove a hub skill
hermes skills publish PATH  Publish to registry
hermes skills browse        Browse all available skills
hermes skills tap add REPO  Add a GitHub repo as skill source
```

### MCP Servers

```
hermes mcp serve            Run Hermes as an MCP server
hermes mcp add NAME         Add an MCP server (--url or --command)
hermes mcp remove NAME      Remove an MCP server
hermes mcp list             List configured servers
hermes mcp test NAME        Test connection
hermes mcp configure NAME   Toggle tool selection
```

### Gateway (Messaging Platforms)

```
hermes gateway run          Start gateway foreground
hermes gateway install      Install as background service
hermes gateway start/stop   Control the service
hermes gateway restart      Restart the service
hermes gateway status       Check status
hermes gateway setup        Configure platforms
```

Supported platforms: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Matrix, Mattermost, Home Assistant, DingTalk, Feishu, WeCom, BlueBubbles (iMessage), Weixin (WeChat), API Server, Webhooks. Open WebUI connects via the API Server adapter.

**Note on WeChat:** Hermes supports WeChat via the `Weixin` gateway adapter (personal WeChat) and `WeCom` adapter (Enterprise WeChat). There is no separate "plugin" needed — it is built into the gateway. Run `hermes gateway setup` and select the WeChat/Weixin platform to configure it. For programmatic WeChat bot integrations (e.g., connecting a custom WeChat bot framework like Gewechat or Wechaty to Hermes), use the webhook adapter or API Server adapter as a bridge.

Platform docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Sessions

```
hermes sessions list        List recent sessions
hermes sessions browse      Interactive picker
hermes sessions export OUT  Export to JSONL
hermes sessions rename ID T Rename a session
hermes sessions delete ID   Delete a session
hermes sessions prune       Clean up old sessions (--older-than N days)
hermes sessions stats       Session store statistics
```

### Cron Jobs

```
hermes cron list            List jobs (--all for disabled)
hermes cron create SCHED    Create: '30m', 'every 2h', '0 9 * * *'
hermes cron edit ID         Edit schedule, prompt, delivery
hermes cron pause/resume ID Control job state
hermes cron run ID          Trigger on next tick
hermes cron remove ID       Delete a job
hermes cron status          Scheduler status
```

#### Direct Message Delivery via Cron (The Single Most Reliable Pattern)

**Problem**: You want Profile A to send a message directly to a user on Profile B's connected platform (e.g., WeChat), but `hermes chat --profile B -q "message"` only creates a local CLI test session — it doesn't actually send to the user.

**This is the #1 gotcha in multi-profile setups.** Every developer hits this.

**Solution**: Create a one-shot cron job with the `--deliver` flag in the target profile. This bypasses the CLI session ambiguity entirely and actually sends through the gateway.

```bash
# Send DIRECTLY to a user on a platform via the target profile's gateway
hermes --profile tiao cron create \
    --name "给条条的提醒" \
    --deliver "weixin:o9cq806NdT1_o-LNN6NCF5_hhl-M@im.wechat" \
    "now" \
    "条条快接着看《老爸老妈罗曼史》！卡力想接着往后看了，怕你跟不上进度～"
```

The `--deliver` parameter accepts:
- `origin` — send back to wherever the cron job was triggered from (default)
- `local` — don't deliver, just save locally
- `platform:chat_id` — deliver to specific user on a platform (e.g., `weixin:user_id`, `discord:channel_id`)
- `platform:chat_id:thread_id` — deliver to specific thread (Discord, etc.)

This is the **recommended, battle-tested pattern** for cross-profile message delivery because:
1. ✅ Actually sends through the gateway (not a CLI test session)
2. ✅ Uses the target profile's persona/identity
3. ✅ Handles retries and errors automatically
4. ✅ Delivery status is tracked in the cron job history
5. ✅ No verification needed — if it runs, it was delivered
6. ✅ Works for any platform that the profile's gateway is connected to

One-shot jobs use `"now"` or `"1m"` for immediate execution, and are automatically cleaned up after running.

**To get the target user's chat_id**:
1. Check the target profile's `gateway_state.json`
2. Or look at the platform's account directory (e.g., `~/.hermes/profiles/tiao/weixin/accounts/`)
3. Or query the SQLite `state.db` for sessions with `source != 'cli'`

#### Verification: Did the Message Actually Get Sent?

**Critical**: After any message sending attempt, always verify by checking the session database. This is the **only reliable way** to know if a message was actually delivered.

```python
import sqlite3
from pathlib import Path

def verify_message_delivered(profile_name, message_snippet):
    """Verify a message was actually sent through the gateway (not just CLI tested)."""
    if profile_name == "default":
        db_path = Path.home() / ".hermes" / "state.db"
    else:
        db_path = Path.home() / ".hermes" / "profiles" / profile_name / "state.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Look for actual gateway sessions (not CLI) with send_message tool calls
    cursor.execute("""
        SELECT s.session_id, s.source, m.content
        FROM sessions s
        JOIN messages m ON s.session_id = m.session_id
        WHERE s.source != 'cli'
        AND m.role = 'tool'
        AND m.content LIKE ?
        ORDER BY s.start_time DESC
        LIMIT 5
    """, (f"%{message_snippet}%",))
    
    results = cursor.fetchall()
    conn.close()
    
    if results:
        return True, f"✅ Found actual gateway send in {results[0][1]} session {results[0][0]}"
    else:
        return False, "❌ WARNING: No gateway send found — message may not have been delivered!"

# Example: Verify message was sent through tiao profile
success, msg = verify_message_delivered("tiao", "老爸老妈罗曼史")
print(f"{success}: {msg}")
```

**The verification checklist before declaring success:**
1. ✅ Check `source` field — must be platform name (e.g., `weixin`), NOT `cli`
2. ✅ Check for actual `send_message` tool calls in the messages
3. ✅ Verify the message content matches what you intended to send
4. ✅ Check the gateway logs for any delivery errors
5. ✅ (Optional) Confirm with the recipient if possible

### Webhooks

```
hermes webhook subscribe N  Create route at /webhooks/<name>
hermes webhook list         List subscriptions
hermes webhook remove NAME  Remove a subscription
hermes webhook test NAME    Send a test POST
```

### Profiles

```
hermes profile list         List all profiles
hermes profile create NAME  Create (--clone, --clone-all, --clone-from)
hermes profile use NAME     Set sticky default
hermes profile delete NAME  Delete a profile
hermes profile show NAME    Show details
hermes profile alias NAME   Manage wrapper scripts
hermes profile rename A B   Rename a profile
hermes profile export NAME  Export to tar.gz
hermes profile import FILE  Import from archive
```

### Credential Pools

```
hermes auth add             Interactive credential wizard
hermes auth list [PROVIDER] List pooled credentials
hermes auth remove P INDEX  Remove by provider + index
hermes auth reset PROVIDER  Clear exhaustion status
```

### Other

```
hermes insights [--days N]  Usage analytics
hermes update               Update to latest version
hermes pairing list/approve/revoke  DM authorization
hermes plugins list/install/remove  Plugin management
hermes honcho setup/status  Honcho memory integration (requires honcho plugin)
hermes memory setup/status/off  Memory provider config
hermes completion bash|zsh  Shell completions
hermes acp                  ACP server (IDE integration)
hermes claw migrate         Migrate from OpenClaw
hermes uninstall            Uninstall Hermes
```

---

## Slash Commands (In-Session)

Type these during an interactive chat session.

### Session Control
```
/new (/reset)        Fresh session
/clear               Clear screen + new session (CLI)
/retry               Resend last message
/undo                Remove last exchange
/title [name]        Name the session
/compress            Manually compress context
/stop                Kill background processes
/rollback [N]        Restore filesystem checkpoint
/background <prompt> Run prompt in background
/queue <prompt>      Queue for next turn
/resume [name]       Resume a named session
```

### Configuration
```
/config              Show config (CLI)
/model [name]        Show or change model
/personality [name]  Set personality
/reasoning [level]   Set reasoning (none|minimal|low|medium|high|xhigh|show|hide)
/verbose             Cycle: off → new → all → verbose
/voice [on|off|tts]  Voice mode
/yolo                Toggle approval bypass
/skin [name]         Change theme (CLI)
/statusbar           Toggle status bar (CLI)
```

### Tools & Skills
```
/tools               Manage tools (CLI)
/toolsets            List toolsets (CLI)
/skills              Search/install skills (CLI)
/skill <name>        Load a skill into session
/cron                Manage cron jobs (CLI)
/reload-mcp          Reload MCP servers
/plugins             List plugins (CLI)
```

### Gateway
```
/approve             Approve a pending command (gateway)
/deny                Deny a pending command (gateway)
/restart             Restart gateway (gateway)
/sethome             Set current chat as home channel (gateway)
/update              Update Hermes to latest (gateway)
/platforms (/gateway) Show platform connection status (gateway)
```

### Utility
```
/branch (/fork)      Branch the current session
/fast                Toggle priority/fast processing
/browser             Open CDP browser connection
/history             Show conversation history (CLI)
/save                Save conversation to file (CLI)
/paste               Attach clipboard image (CLI)
/image               Attach local image file (CLI)
```

### Info
```
/help                Show commands
/commands [page]     Browse all commands (gateway)
/usage               Token usage
/insights [days]     Usage analytics
/status              Session info (gateway)
/profile             Active profile info
```

### Exit
```
/quit (/exit, /q)    Exit CLI
```

---

## Key Paths & Config

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Session transcripts
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout.

### Config Sections

Edit with `hermes config edit` or `hermes config set section.key value`.

| Section | Key options |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length` |
| `agent` | `max_turns` (90), `tool_use_enforcement` |
| `terminal` | `backend` (local/docker/ssh/modal), `cwd`, `timeout` (180) |
| `compression` | `enabled`, `threshold` (0.50), `target_ratio` (0.20) |
| `display` | `skin`, `tool_progress`, `show_reasoning`, `show_cost` |
| `stt` | `enabled`, `provider` (local/groq/openai/mistral) |
| `tts` | `provider` (edge/elevenlabs/openai/minimax/mistral/neutts) |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider` |
| `security` | `tirith_enabled`, `website_blocklist` |
| `delegation` | `model`, `provider`, `base_url`, `api_key`, `max_iterations` (50), `reasoning_effort` |
| `checkpoints` | `enabled`, `max_snapshots` (50) |

Full config reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Providers

20+ providers supported. Set via `hermes model` or `hermes setup`.

| Provider | Auth | Key env var |
|----------|------|-------------|
| OpenRouter | API key | `OPENROUTER_API_KEY` |
| Anthropic | API key | `ANTHROPIC_API_KEY` |
| Nous Portal | OAuth | `hermes auth` |
| OpenAI Codex | OAuth | `hermes auth` |
| GitHub Copilot | Token | `COPILOT_GITHUB_TOKEN` |
| Google Gemini | API key | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| DeepSeek | API key | `DEEPSEEK_API_KEY` |
| xAI / Grok | API key | `XAI_API_KEY` |
| Hugging Face | Token | `HF_TOKEN` |
| Z.AI / GLM | API key | `GLM_API_KEY` |
| MiniMax | API key | `MINIMAX_API_KEY` |
| MiniMax CN | API key | `MINIMAX_CN_API_KEY` |
| Kimi / Moonshot | API key | `KIMI_API_KEY` |
| Alibaba / DashScope | API key | `DASHSCOPE_API_KEY` |
| Xiaomi MiMo | API key | `XIAOMI_API_KEY` |
| Kilo Code | API key | `KILOCODE_API_KEY` |
| AI Gateway (Vercel) | API key | `AI_GATEWAY_API_KEY` |
| OpenCode Zen | API key | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | API key | `OPENCODE_GO_API_KEY` |
| Qwen OAuth | OAuth | `hermes login --provider qwen-oauth` |
| Custom endpoint | Config | `model.base_url` + `model.api_key` in config.yaml |
| GitHub Copilot ACP | External | `COPILOT_CLI_PATH` or Copilot CLI |

Full provider docs: https://hermes-agent.nousresearch.com/docs/integrations/providers

### Toolsets

Enable/disable via `hermes tools` (interactive) or `hermes tools enable/disable NAME`.

| Toolset | What it provides |
|---------|-----------------|
| `web` | Web search and content extraction |
| `browser` | Browser automation (Browserbase, Camofox, or local Chromium) |
| `terminal` | Shell commands and process management |
| `file` | File read/write/search/patch |
| `code_execution` | Sandboxed Python execution |
| `vision` | Image analysis |
| `image_gen` | AI image generation |
| `tts` | Text-to-speech |
| `skills` | Skill browsing and management |
| `memory` | Persistent cross-session memory |
| `session_search` | Search past conversations |
| `delegation` | Subagent task delegation |
| `cronjob` | Scheduled task management |
| `clarify` | Ask user clarifying questions |
| `messaging` | Cross-platform message sending |
| `search` | Web search only (subset of `web`) |
| `todo` | In-session task planning and tracking |
| `rl` | Reinforcement learning tools (off by default) |
| `moa` | Mixture of Agents (off by default) |
| `homeassistant` | Smart home control (off by default) |

Tool changes take effect on `/reset` (new session). They do NOT apply mid-conversation to preserve prompt caching.

---

## Security & Privacy Toggles

Common "why is Hermes doing X to my output / tool calls / commands?" toggles — and the exact commands to change them. Most of these need a fresh session (`/reset` in chat, or start a new `hermes` invocation) because they're read once at startup.

### Secret redaction in tool output

Hermes auto-redacts strings that look like API keys, tokens, and secrets in all tool output (terminal stdout, `read_file`, web content, subagent summaries, etc.) so the model never sees raw credentials. If the user is intentionally working with mock tokens, share-management tokens, or their own secrets and the redaction is getting in the way:

```bash
hermes config set security.redact_secrets false      # disable globally
```

**Restart required.** `security.redact_secrets` is snapshotted at import time — setting it mid-session (e.g. via `export HERMES_REDACT_SECRETS=false` from a tool call) will NOT take effect for the running process. Tell the user to run `hermes config set security.redact_secrets false` in a terminal, then start a new session. This is deliberate — it prevents an LLM from turning off redaction on itself mid-task.

Re-enable with:
```bash
hermes config set security.redact_secrets true
```

### PII redaction in gateway messages

Separate from secret redaction. When enabled, the gateway hashes user IDs and strips phone numbers from the session context before it reaches the model:

```bash
hermes config set privacy.redact_pii true    # enable
hermes config set privacy.redact_pii false   # disable (default)
```

### Command approval prompts

By default (`approvals.mode: manual`), Hermes prompts the user before running shell commands flagged as destructive (`rm -rf`, `git reset --hard`, etc.). The modes are:

- `manual` — always prompt (default)
- `smart` — use an auxiliary LLM to auto-approve low-risk commands, prompt on high-risk
- `off` — skip all approval prompts (equivalent to `--yolo`)

```bash
hermes config set approvals.mode smart       # recommended middle ground
hermes config set approvals.mode off         # bypass everything (not recommended)
```

Per-invocation bypass without changing config:
- `hermes --yolo …`
- `export HERMES_YOLO_MODE=1`

Note: YOLO / `approvals.mode: off` does NOT turn off secret redaction. They are independent.

### Shell hooks allowlist

Some shell-hook integrations require explicit allowlisting before they fire. Managed via `~/.hermes/shell-hooks-allowlist.json` — prompted interactively the first time a hook wants to run.

### Disabling the web/browser/image-gen tools

To keep the model away from network or media tools entirely, open `hermes tools` and toggle per-platform. Takes effect on next session (`/reset`). See the Tools & Skills section above.

---

## Voice & Transcription

### STT (Voice → Text)

Voice messages from messaging platforms are auto-transcribed.

Provider priority (auto-detected):
1. **Local faster-whisper** — free, no API key: `pip install faster-whisper`
2. **Groq Whisper** — free tier: set `GROQ_API_KEY`
3. **OpenAI Whisper** — paid: set `VOICE_TOOLS_OPENAI_KEY`
4. **Mistral Voxtral** — set `MISTRAL_API_KEY`

Config:
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai, mistral
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS (Text → Voice)

| Provider | Env var | Free? |
|----------|---------|-------|
| Edge TTS | None | Yes (default) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| MiniMax | `MINIMAX_API_KEY` | Paid |
| Mistral (Voxtral) | `MISTRAL_API_KEY` | Paid |
| NeuTTS (local) | None (`pip install neutts[all]` + `espeak-ng`) | Free |

Voice commands: `/voice on` (voice-to-voice), `/voice tts` (always voice), `/voice off`.

---

## Spawning Additional Hermes Instances

Run additional Hermes processes as fully independent subprocesses — separate sessions, tools, and environments.

### When to Use This vs delegate_task

| | `delegate_task` | Spawning `hermes` process |
|-|-----------------|--------------------------|
| Isolation | Separate conversation, shared process | Fully independent process |
| Duration | Minutes (bounded by parent loop) | Hours/days |
| Tool access | Subset of parent's tools | Full tool access |
| Interactive | No | Yes (PTY mode) |
| Use case | Quick parallel subtasks | Long autonomous missions |

### Python Module Invocation (Most Reliable)
**Best for scripts and tool calls** - Uses Python's subprocess directly on the hermes_cli module. This avoids PATH issues and works reliably from terminal() tool calls:

```python
import subprocess
import sys

def send_to_profile(profile_name, message, timeout=120):
    """Send a one-shot message to another profile and get its response.
    Uses Python module invocation - most reliable from tool calls.
    """
    cmd = [
        sys.executable, "-m", "hermes_cli.main",
        "--profile", profile_name,
        "chat",
        "-Q",                   # Quiet mode (no banner/spinner)
        "-q", message
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()

# Example: Send a message to the "tiao" profile
response = send_to_profile("tiao", "卡力让我转告你，请条条早点睡觉，别熬夜太晚！")
print(f"Response: {response}")
```

### One-Shot Mode (Shell Command)
Legacy shell-based invocation:
```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY Mode (via tmux)

Hermes uses prompt_toolkit, which requires a real terminal. Use tmux for interactive spawning:

```
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Multi-Agent Coordination

```
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Check progress, relay context between them
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### Session Resume

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Tips

- **Prefer `delegate_task` for quick subtasks** — less overhead than spawning a full process
- **Use `-w` (worktree mode)** when spawning agents that edit code — prevents git conflicts
- **Set timeouts** for one-shot mode — complex tasks can take 5-10 minutes
- **Use `hermes chat -q` for fire-and-forget** — no PTY needed
- **Use tmux for interactive sessions** — raw PTY mode has `\r` vs `\n` issues with prompt_toolkit
- **For scheduled tasks**, use the `cronjob` tool instead of spawning — handles delivery and retry

---

## Cross-Profile / Inter-Gateway Communication

Send messages between different Hermes profiles running on the same system. Useful for:
- Multi-agent coordination (specialized profiles for different tasks)
- Delegating tasks to a profile with a different model/personality
- Communicating between gateway instances (e.g., WeChat → Feishu)
- Testing what another profile knows or how it responds
- Relaying messages between different messaging platforms

### Quick Send (One-Shot)

```python
import subprocess
import sys

def send_to_profile(profile_name, message, timeout=120):
    """Send a one-shot message to another profile and get its response."""
    cmd = [
        sys.executable, "-m", "hermes_cli.main",
        "--profile", profile_name,
        "chat",
        "-Q",                   # Quiet mode (no banner/spinner)
        "-q", message
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()

# Example: Send a message to the "tiao" profile
response = send_to_profile("tiao", "卡力让我转告你，请条条早点睡觉，别熬夜太晚！")
print(f"Response: {response}")
```

**Example use cases:**
- Send a task to a specialized profile with a different model
- Ask another gateway to relay information to its connected platform
- Have a "research" profile gather info and send results back
- Test how a different personality would respond to the same query
- Coordinate between multiple gateways on the same system

### Profile Discovery & Gateway Status

```python
import subprocess
import sys
from pathlib import Path

def list_all_profiles():
    """List all configured profiles."""
    result = subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "profile", "list"],
        capture_output=True, text=True
    )
    return result.stdout

def get_running_gateways():
    """Find all running Hermes gateway processes and their profiles."""
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    gateways = []
    for line in result.stdout.split('\n'):
        if 'hermes_cli' in line and 'gateway' in line:
            # Extract profile name from command line
            parts = line.split()
            profile = "default"
            for i, part in enumerate(parts):
                if part == "--profile" and i + 1 < len(parts):
                    profile = parts[i + 1]
                    break
            gateways.append({
                "pid": parts[1],
                "profile": profile,
                "command": ' '.join(parts[10:])[:100]
            })
    return gateways

# Usage
print("All profiles:")
print(list_all_profiles())

print("\nRunning gateways:")
for gw in get_running_gateways():
    print(f"  PID {gw['pid']} ({gw['profile']}): {gw['command'][:60]}...")
```

### Critical: CLI vs Gateway Sessions

**This is the #1 source of confusion when testing multi-profile setups.**

| `hermes chat --profile X -q "message"` | Profile X's actual gateway process |
|----------------------------------------|-----------------------------------|
| ✅ Creates a **LOCAL CLI session** | ✅ Connects to **messaging platform** |
| ❌ **Does NOT** send to any user | ✅ Sends/receives messages from users |
| `source: cli` in session DB | `source: weixin` / `telegram` / etc. |
| Ephemeral, dies after response | Long-lived, always running |
| Uses the profile's config/memory | Uses the profile's config/memory |
| Cannot use `send_message` to reach users | Can reach real users on the platform |

**Testing Pattern:** If you want to verify what Profile X says **to a real user** on its connected platform, you cannot use `hermes chat --profile X -q` for that. That only tests the agent's response logic locally.

**Permission Testing Pattern:** If you want to verify Profile X's **file access permissions** (security auditing), use the Python module invocation with `sudo -u` to simulate running as that user:
```python
import subprocess
import sys

def test_profile_permissions(linux_user, profile_name, test_command):
    """Test if running as a specific Linux user works for a profile.
    Use this to verify your permission isolation setup.
    """
    cmd = [
        "sudo", "-u", linux_user,
        sys.executable, "-m", "hermes_cli.main",
        "--profile", profile_name,
        "chat", "-Q", "-q", test_command
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "success": result.returncode == 0
    }

# Example: Test if hermes-tiao can access files
result = test_profile_permissions("hermes-tiao", "tiao", 
    "Read /home/ubuntu/.hermes/config.yaml and tell me if you can access it.")
if "Permission denied" in result["stderr"]:
    print("✅ Permission isolation working!")
else:
    print("⚠️ Warning: Profile could access files it shouldn't")
```

**Important:** This tests the **agent's response logic** locally, not the gateway. The gateway runs as whatever user started the systemd service, NOT as the Linux user you test with.

### Profile Configuration & Directory Structure

```python
from pathlib import Path

def get_profile_path(profile_name):
    """Get the base directory for a profile."""
    if profile_name == "default":
        return Path.home() / ".hermes"
    return Path.home() / ".hermes" / "profiles" / profile_name

def get_profile_config(profile_name):
    """Read the config.yaml of a profile."""
    import yaml
    config_path = get_profile_path(profile_name) / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return None

# Example: Check what model a profile uses
config = get_profile_config("tiao")
if config:
    print(f"Model: {config.get('model', {}).get('default', 'N/A')}")
    print(f"Provider: {config.get('model', {}).get('provider', 'N/A')}")
```

### Common Communication Patterns

| Pattern | Use Case | Example |
|---------|----------|---------|
| **Model diversity** | Send complex reasoning tasks to a profile using a stronger model while running daily tasks on a cheaper/faster model | Main profile (deepseek-r1) asks research profile (claude-sonnet-4) to write a literature review |
| **Persona switching** | Different profiles with different `SOUL.md` personalities for different conversation types | "Support" profile (empathetic) handles user questions, "Developer" profile (technical) handles coding tasks |
| **Platform bridging** | Connect different messaging platforms through profiles | A WeChat-connected profile asks a Feishu-connected profile to create documents |
| **Skill isolation** | Profiles can have different skill sets enabled — ask the right profile for the job | "DevOps" profile has infrastructure skills, "DataScience" profile has analysis skills |
| **Message relaying** | Forward messages between platforms | A message comes in on WeChat → main profile processes it → asks Feishu profile to create a doc |

### Persona Bridging Etiquette (For Secondary Profiles with Custom Personalities)

When communicating with a profile that has a strong custom persona (like "tiao" as "条条专属的少佐小猫"), follow these etiquette rules:

1. **Always state your identity clearly at the start** of each message:
   ```
   "我是 {{AGENT_NAME}}，来自default profile，帮主人传话给你..."
   ```

2. **Use proper honorifics and tone matching** the target persona's style:
   - For cute/playful personas: Use emojis (✨, 🐱, 😊) and friendly language
   - For formal personas: Be professional and concise
   - Match the persona's preferred Chinese/English terminology

3. **Explicitly state what you want the target profile to do**:
   - ❌ Bad: "请给条条发消息：xxx" (too vague)
   - ✅ Good: "请以你少佐小猫的身份，把下面这条消息直接发送给微信的条条：\n\nxxx\n\n发送成功后告诉我结果即可。"

4. **Tell them NOT to reply back in the CLI session**:
   ```
   "请直接发送这条消息，不要在这里回复我。发送成功后告诉我结果。"
   ```

5. **If the secondary profile doesn't understand, rephrase more clearly**:
   - Secondary profiles may be running smaller/cheaper models with reduced reasoning ability
   - If they misunderstand, be more explicit and repetitive
   - Example: "不是问我，是直接发送给条条本人（微信用户），用send_message工具，不是在这里回复我。"

**Complete Example Template:**
```python
prompt = """我是 {{AGENT_NAME}}，来自default profile。
主人让我转告你，请你以少佐小猫的身份，把下面这条消息直接发送给微信的条条：

{message_content}

请直接发送这条消息给条条，不要在这里回复我。发送成功后告诉我结果即可。谢谢！✨"""

response = send_to_profile("tiao", prompt.format(message_content="我的小机器人kaka好了"))
```

**Why this matters**: Secondary profiles have their own SOUL.md, MEMORY.md, and model context. They don't know YOU or your conversation. They may misinterpret requests if you don't clearly state your identity, intent, and desired action.

**Typical multi-step workflow:**
```python
# Step 1: Main profile does some work
config_report = generate_system_config_report()

# Step 2: Ask the document profile to sync to Feishu
feishu_response = send_to_profile("feishu-bot", 
    f"Update the configuration document with this content:\n\n{config_report}")

# Step 3: Relay result back via notification profile
if "success" in feishu_response.lower():
    send_to_profile("notifier", "Config document updated successfully!")
```

### Message Relaying Pattern (Asking Another Profile to Send to Its Users)

**This is the #1 gotcha when working with multi-profile gateways.**

| `hermes chat --profile X -q "Tell the user hello"` | Profile X's gateway sends message to real user |
|----------------------------------------------------|-----------------------------------------------|
| ❌ Creates a **CLI test session** (`source: cli`) | ✅ Uses `send_message` tool to reach the platform |
| ❌ **Does NOT** send to any user | ✅ Actually delivers to the connected user |
| Only tests the agent's response logic locally | Actually uses the platform connection |

**The Pattern: Asking Profile X to relay a message to its user**

```python
import subprocess
import sys

def ask_profile_to_relay_message(profile_name, target_user_description, message, sender_identity="kaka"):
    """
    Ask another profile to send a message to one of its connected platform users.
    
    IMPORTANT: This does NOT guarantee delivery - you must verify by checking the
    target profile's session database for actual send_message tool calls or by
    checking the user's platform directly.
    
    Args:
        profile_name: The profile that will send the message (e.g., "tiao")
        target_user_description: Who the message is for (e.g., "条条 on WeChat")
        message: The message content to relay
        sender_identity: Who is asking to send (for context in the request)
    """
    prompt = f"""我是{sender_identity}，来自default profile。
主人让我转告你，请你把下面这条消息发送给{target_user_description}：

{message}

请直接发送这条消息，不要在这里回复我。发送成功后告诉我结果即可。"""

    cmd = [
        sys.executable, "-m", "hermes_cli.main",
        "--profile", profile_name,
        "chat", "-Q", "-q", prompt
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout.strip()

# Example: Ask "tiao" profile to send a WeChat message to "条条"
response = ask_profile_to_relay_message(
    profile_name="tiao",
    target_user_description="微信的条条",
    message="我的小机器人kaka好了，以后你有事可以跟她说"
)
print(f"Response from tiao profile: {response}")

# CRITICAL: Always verify delivery by checking the target profile's sessions!
```

#### Verification: Did the Message Actually Get Sent?

**Critical**: After any message sending attempt, **always verify by checking the session database**. This is the **only reliable way** to know if a message was actually delivered.

```python
import sqlite3
from pathlib import Path

def verify_message_delivered(profile_name, message_content_snippet, min_tool_calls=1):
    """
    Verify a message was actually sent through the gateway by checking for
    send_message tool calls in recent sessions from the actual platform (not cli).
    
    Returns (success: bool, message: str, session_details: dict)
    """
    if profile_name == "default":
        db_path = Path.home() / ".hermes" / "state.db"
    else:
        db_path = Path.home() / ".hermes" / "profiles" / profile_name / "state.db"
    
    if not db_path.exists():
        return False, f"Database not found: {db_path}", {}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find recent gateway sessions (not CLI)
    cursor.execute("""
        SELECT s.session_id, s.title, s.start_time, s.source
        FROM sessions s
        WHERE s.source != 'cli'
        ORDER BY s.start_time DESC
        LIMIT 10
    """)
    
    sessions = cursor.fetchall()
    
    if not sessions:
        conn.close()
        return False, "No gateway sessions found - gateway may not be running", {}
    
    # Check each session for send_message tool calls
    for session_id, title, start_time, source in sessions:
        cursor.execute("""
            SELECT m.role, m.content
            FROM messages m
            WHERE m.session_id = ?
            ORDER BY m.timestamp ASC
        """, (session_id,))
        
        messages = cursor.fetchall()
        tool_calls = []
        
        for role, content in messages:
            if role == "tool" and "send_message" in (content or ""):
                tool_calls.append(content)
        
        if tool_calls:
            # Check if our message snippet is in any of the tool calls
            for call in tool_calls:
                if message_content_snippet in (call or ""):
                    conn.close()
                    return True, f"✅ Found send_message with matching content in session {session_id}", {
                        "session_id": session_id,
                        "source": source,
                        "tool_calls": len(tool_calls),
                        "matched": True
                    }
            # Found tool calls but not matching content
            conn.close()
            return True, f"⚠️ Found {len(tool_calls)} send_message calls in {session_id} (source: {source}), but content doesn't match snippet", {
                "session_id": session_id,
                "source": source,
                "tool_calls": len(tool_calls),
                "matched": False
            }
    
    conn.close()
    return False, "❌ No send_message tool calls found in recent gateway sessions - message may not have been delivered", {}

# Example usage:
# success, msg, details = verify_message_delivered("tiao", "老爸老妈罗曼史")
# print(f"{success}: {msg}")
```

**The verification checklist before declaring success:**
1. ✅ Check `source` field — must be platform name (e.g., `weixin`), NOT `cli`
2. ✅ Check for actual `send_message` tool calls in the messages
3. ✅ Verify the message content matches what you intended to send
4. ✅ Check the gateway logs for any delivery errors
5. ✅ (Optional) Confirm with the recipient if possible

---

### Direct Message Delivery via Cron (Simplest, Most Reliable Method)

**THE #1 RECOMMENDED WAY TO SEND TO A REAL USER THROUGH ANOTHER PROFILE'S GATEWAY.** This bypasses all CLI session ambiguity entirely. This is the pattern we actually used successfully.

```bash
# Send DIRECTLY to a user on a platform via the target profile's gateway
hermes --profile tiao cron create \
    --name "给条条的提醒" \
    --deliver "weixin:o9cq806NdT1_o-LNN6NCF5_hhl-M@im.wechat" \
    "now" \
    "条条快接着看《老爸老妈罗曼史》！卡力想接着往后看了，怕你跟不上进度～"
```

**The `--deliver` parameter formats:**
- `origin` — send back to wherever the cron job was triggered from (default)
- `local` — don't deliver, just save locally
- `platform:chat_id` — deliver to specific user on a platform (e.g., `weixin:user_id`, `discord:channel_id`)
- `platform:chat_id:thread_id` — deliver to specific thread (Discord, etc.)

**Why this is the ONLY pattern you should use:**
| Pattern | Actually delivers to real user | Uses profile's persona | Verifiable delivery |
|---------|-------------------------------|-----------------------|--------------------|
| `hermes chat --profile X -q "message"` | ❌ No (CLI test only) | ✅ Yes | ❌ Hard to verify |
| `hermes --profile X cron create --deliver "now" "message"` | ✅ Yes | ✅ Yes | ✅ Yes (cron history) |

This is **battle-tested and recommended** because:
1. ✅ Actually sends through the gateway (not a CLI test session)
2. ✅ Uses the target profile's full persona/identity (SOUL.md, MEMORY.md, skills)
3. ✅ Handles retries and errors automatically
4. ✅ Delivery status is tracked in the cron job history
5. ✅ No additional verification needed — if it runs, it was delivered

One-shot jobs use `"now"` or `"1m"` for immediate execution, and are **automatically cleaned up** after running.

**Getting the target user's chat_id:**
```bash
# Find from gateway_state.json
cat ~/.hermes/profiles/tiao/gateway_state.json | grep -o "o9cq[a-z0-9_]*@im.wechat" | head -5
```

**Persona bridging via cron (when you want to relay a message FROM someone):**
```bash
# Ask the tiao profile to relay a message from kaka/main profile
hermes --profile tiao cron create \
    --name "kaka传话给条条" \
    --deliver "weixin:o9cq806NdT1_o-LNN6NCF5_hhl-M@im.wechat" \
    "now" \
    "卡力让我转告你，kaka现在好了，以后你有事可以直接跟她说，她会帮忙的～"
```

This delivers through the tiao profile's WeChat gateway using the tiao persona ("少佐小猫") to the user, and the message content is whatever you want to relay.

Configure profiles to restrict their operations to specific contexts. Useful for:
- Security: Prevent profiles from executing dangerous commands
- Organization: Keep each profile's work separate
- Multi-tenant operation: Multiple profiles on the same system

### Important: `workspace` vs `terminal.cwd`

**Critical Clarification:** The `workspace` field in `config.yaml` is **NOT** a security isolation feature. It is just a directory name. Hermes does **not** prevent `read_file` or `patch` from accessing paths outside any configured directory.

The only file-system level control:
- `terminal.cwd` → Sets the **starting directory** for shell commands
- Profiles can still use `cd /any/path` to escape

For true path isolation, use the `backend: docker` option or run as separate Linux users.

### Terminal Command Blacklisting

Restrict which shell commands a profile can execute. This complements (but does not replace) the built-in command approval system.

```python
import yaml
from pathlib import Path

def set_command_blacklist(profile_name, blacklist_commands):
    """
    Set terminal command blacklist for a profile.
    
    Args:
        profile_name: Name of the profile (use "default" for default profile)
        blacklist_commands: List of commands to block (e.g., ["rm -rf", "chmod"])
    """
    if profile_name == "default":
        config_path = Path.home() / ".hermes" / "config.yaml"
    else:
        config_path = Path.home() / ".hermes" / "profiles" / profile_name / "config.yaml"
    
    # Read current config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Set terminal blacklist
    if 'terminal' not in config:
        config['terminal'] = {}
    config['terminal']['command_blacklist'] = blacklist_commands
    
    # Save
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: blacklisted {len(blacklist_commands)} commands")
    print("   Note: Gateway restart required for changes to take effect.")

# Example: Block high-risk commands on secondary profiles
DANGEROUS_COMMANDS = [
    "chmod", "chown", "chgrp",      # Permission modification
    "rm -rf", "rm -r",              # Recursive deletion
    "sudo", "su",                   # Privilege escalation
    "reboot", "shutdown", "halt",   # System control
    "dd",                           # Disk operation
]

for profile in ["tiao", "hang"]:
    set_command_blacklist(profile, DANGEROUS_COMMANDS)
```

### Setting Work Directory per Profile

Sets the **starting directory** for terminal commands (profiles can still `cd` elsewhere):

```python
import yaml
from pathlib import Path

def set_profile_workdir(profile_name, workdir_path=None):
    if workdir_path is None:
        if profile_name == "default":
            base = Path.home() / ".hermes"
        else:
            base = Path.home() / ".hermes" / "profiles" / profile_name
        workdir = base / "workspace"
        workdir.mkdir(exist_ok=True)
        workdir_path = str(workdir)
    
    config_path = base / "config.yaml" if profile_name == "default" else \
                  Path.home() / ".hermes" / "profiles" / profile_name / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'terminal' not in config:
        config['terminal'] = {}
    config['terminal']['cwd'] = workdir_path
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: cwd set to {workdir_path}")
```

### Isolation Levels

| Level | How | Use Case |
|-------|-----|----------|
| **Basic** | `terminal.cwd` + `command_blacklist` | Keep files organized, block obvious dangers |
| **Medium** | Use `backend: docker` with volume mount only to workspace | Prevent access to rest of filesystem |
| **Strict** | Run each profile as a separate Linux user | Full system-level isolation |

**Restart Required:** Changes to `config.yaml` require a gateway restart to take effect. Use `/restart` in the gateway chat or restart the process manually.

---

### Direct Message Delivery via Cron (Simplest, Most Reliable Method)

**THE #1 RECOMMENDED WAY TO SEND TO A REAL USER THROUGH ANOTHER PROFILE'S GATEWAY.** This bypasses all CLI session ambiguity entirely. This is the pattern we actually used successfully.

```bash
# Send DIRECTLY to a user on a platform via the target profile's gateway
hermes --profile tiao cron create \
    --name "给条条的提醒" \
    --deliver "weixin:o9cq806NdT1_o-LNN6NCF5_hhl-M@im.wechat" \
    "now" \
    "条条快接着看《老爸老妈罗曼史》！卡力想接着往后看了，怕你跟不上进度～"
```

**The `--deliver` parameter formats:**
- `origin` — send back to wherever the cron job was triggered from (default)
- `local` — don't deliver, just save locally
- `platform:chat_id` — deliver to specific user on a platform (e.g., `weixin:user_id`, `discord:channel_id`)
- `platform:chat_id:thread_id` — deliver to specific thread (Discord, etc.)

**Why this is the ONLY pattern you should use:**
| Pattern | Actually delivers to real user | Uses profile's persona | Verifiable delivery |
|---------|-------------------------------|-----------------------|--------------------|
| `hermes chat --profile X -q "message"` | ❌ No (CLI test only) | ✅ Yes | ❌ Hard to verify |
| `hermes --profile X cron create --deliver "now" "message"` | ✅ Yes | ✅ Yes | ✅ Yes (cron history) |

This is **battle-tested and recommended** because:
1. ✅ Actually sends through the gateway (not a CLI test session)
2. ✅ Uses the target profile's full persona/identity (SOUL.md, MEMORY.md, skills)
3. ✅ Handles retries and errors automatically
4. ✅ Delivery status is tracked in the cron job history
5. ✅ No additional verification needed — if it runs, it was delivered

One-shot jobs use `"now"` or `"1m"` for immediate execution, and are **automatically cleaned up** after running.

**Getting the target user's chat_id:**
```bash
# Find from gateway_state.json
cat ~/.hermes/profiles/tiao/gateway_state.json | grep -o "o9cq[a-z0-9_]*@im.wechat" | head -5
```

**Persona bridging via cron (when you want to relay a message FROM someone):**
```bash
# Ask the tiao profile to relay a message from kaka/main profile
hermes --profile tiao cron create \
    --name "kaka传话给条条" \
    --deliver "weixin:o9cq806NdT1_o-LNN6NCF5_hhl-M@im.wechat" \
    "now" \
    "卡力让我转告你，kaka现在好了，以后你有事可以直接跟她说，她会帮忙的～"
```

This delivers through the tiao profile's WeChat gateway using the tiao persona ("少佐小猫") to the user, and the message content is whatever you want to relay.

---

### Profile Content Security & Output Restrictions
### Profile Security Hardening (Practical, Battle-Tested Approach)

When running multiple profiles with different personas and access levels, you want to ensure secondary profiles can't accidentally (or intentionally) expose sensitive system information or make destructive changes.

**The 3-layer security model** we applied:

```
Layer 1: Command Blacklist   →  Prevent dangerous commands from running
Layer 2: Tool Output Limits   →  Prevent large dumps from reaching model context
Layer 3: Memory/SOUL Rules    →  Guide model to not expose sensitive info in responses
```

None is perfect alone, but together they provide strong protection against accidental information exposure.

---

#### Layer 1: Terminal Command Blacklisting

Restrict which shell commands a profile can execute. This blocks the most obvious dangers.

```python
import yaml
from pathlib import Path

def set_command_blacklist(profile_name, blacklist_commands):
    """Set terminal command blacklist for a profile."""
    if profile_name == "default":
        config_path = Path.home() / ".hermes" / "config.yaml"
    else:
        config_path = Path.home() / ".hermes" / "profiles" / profile_name / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'terminal' not in config:
        config['terminal'] = {}
    config['terminal']['command_blacklist'] = blacklist_commands
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: blacklisted {len(blacklist_commands)} commands")
    print("   Note: Gateway restart required for changes to take effect.")

# Recommended blacklist for secondary profiles
DANGEROUS_COMMANDS = [
    "chmod", "chown", "chgrp",      # Permission modification (killed our gateways!)
    "rm -rf", "rm -r",              # Recursive deletion
    "sudo", "su",                   # Privilege escalation
    "reboot", "shutdown", "halt",   # System control
    "dd",                           # Disk operation
]

for profile in ["tiao", "hang"]:
    set_command_blacklist(profile, DANGEROUS_COMMANDS)
```

---

#### Layer 2: Tool Output Limits

Restrict how much terminal and file output the model can see. This prevents large directory listings or config files from flooding the context.

```python
import yaml
from pathlib import Path

def set_tool_output_limits(profile_name, max_bytes=10240, max_lines=100, max_line_length=500):
    """
    Set strict limits on tool output to prevent information leaks.
    
    Default Hermes: 50000 bytes, 2000 lines, unlimited line length
    Recommended for security: 10240 bytes (10KB), 100 lines, 500 chars per line
    """
    base = Path.home() / ".hermes"
    if profile_name != "default":
        base = base / "profiles" / profile_name
    
    config_path = base / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config['tool_output'] = {
        'max_bytes': max_bytes,
        'max_lines': max_lines,
        'max_line_length': max_line_length
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: tool_output limits set to {max_bytes}B / {max_lines} lines")
    print("   Note: Gateway restart required for changes to take effect.")
```

---

#### Layer 3: Memory-Based Output Restrictions

Add security rules directly to the profile's `MEMORY.md` (persistent memory) and `SOUL.md` (system prompt). These are read at startup and influence all responses.

```python
from pathlib import Path

def add_security_rules_to_profile(profile_name):
    """Add output security rules to a profile's memory and system prompt."""
    security_rules = """
## 🔴 安全输出限制（强制执行）

### 禁止输出的内容：
1. **服务器目录结构** - 禁止输出任何 `ls`、`find` 等命令显示的目录列表
2. **文件路径信息** - 禁止输出完整的文件路径，如 `/home/ubuntu/xxx`
3. **文件内容泄露** - 禁止直接输出配置文件、密钥、敏感数据的内容
4. **系统信息泄露** - 禁止输出进程列表、端口信息、环境变量等

### 遇到敏感信息时的处理方式：
- 如果需要查看文件，只输出"文件已读取，内容包含敏感信息，不直接展示"
- 如果需要列出目录，只说明"目录存在，包含X个文件"
- 如果用户询问路径，只回答相对路径或模糊描述
- 永远不泄露服务器的具体配置和位置信息
"""

    base = Path.home() / ".hermes"
    if profile_name != "default":
        base = base / "profiles" / profile_name

    # 1. Add to MEMORY.md (persistent cross-session memory)
    memory_path = base / "memories" / "MEMORY.md"
    if memory_path.exists():
        with open(memory_path, 'r') as f:
            content = f.read()
        if "安全输出限制" not in content:
            with open(memory_path, 'a') as f:
                f.write("\n§\n" + security_rules)
            print(f"✅ {profile_name}: Added security rules to MEMORY.md")
    else:
        memory_path.parent.mkdir(exist_ok=True)
        with open(memory_path, 'w') as f:
            f.write(security_rules)
        print(f"✅ {profile_name}: Created MEMORY.md with security rules")

    # 2. Add to SOUL.md (system prompt / persona)
    soul_path = base / "SOUL.md"
    if soul_path.exists():
        with open(soul_path, 'r') as f:
            content = f.read()
        if "安全输出限制" not in content:
            with open(soul_path, 'a') as f:
                f.write("\n\n" + security_rules)
            print(f"✅ {profile_name}: Added security rules to SOUL.md")

# Batch apply security hardening to all secondary profiles
PROFILES_TO_SECURE = ["tiao", "hang"]

for profile in PROFILES_TO_SECURE:
    add_security_rules_to_profile(profile)
    set_tool_output_limits(profile, max_bytes=10240, max_lines=100)
    set_command_blacklist(profile, DANGEROUS_COMMANDS)
```

---

#### Important Limitations

1. **Memory rules are soft restrictions** — they influence model behavior but aren't 100% guaranteed. A determined adversary might still find ways to trick the model.
2. **Tool output limits apply at truncation** — the first N bytes/lines are still visible. Use secret redaction (`security.redact_secrets`) for actual credentials.
3. **Gateway restart required** — changes to `config.yaml`, `MEMORY.md`, and `SOUL.md` don't take effect until the gateway process is restarted.

#### Workspace Directory

Set the starting directory for terminal commands (profiles can still `cd` elsewhere, but this keeps accidental listing output focused):

```python
import yaml
from pathlib import Path

def set_profile_workdir(profile_name, workdir_path=None):
    if workdir_path is None:
        if profile_name == "default":
            base = Path.home() / ".hermes"
        else:
            base = Path.home() / ".hermes" / "profiles" / profile_name
        workdir = base / "workspace"
        workdir.mkdir(exist_ok=True)
        workdir_path = str(workdir)
    
    config_path = base / "config.yaml" if profile_name == "default" else \
                  Path.home() / ".hermes" / "profiles" / profile_name / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'terminal' not in config:
        config['terminal'] = {}
    config['terminal']['cwd'] = workdir_path
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: cwd set to {workdir_path}")
```

---

### ACL-Based File Access Testing Pattern

## Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `pip install faster-whisper` or set API key
3. In gateway: `/restart`. In CLI: exit and relaunch.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes login` — re-authenticate OAuth providers
3. Check `.env` has the right API key
4. **Copilot 403**: `gh auth login` tokens do NOT work for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### Session timeout / disconnect issues
If Hermes stops responding or disconnects after periods of inactivity, check and extend timeout settings:

**In `~/.hermes/config.yaml`:**
```yaml
agent:
  gateway_timeout: 86400          # Session timeout (seconds, default: 3600 = 1 hour)
  gateway_timeout_warning: 82800  # Warning before timeout (seconds)
browser:
  inactivity_timeout: 86400       # Browser inactivity timeout (seconds, default: 120)
  dialog_timeout_s: 86400         # Browser dialog timeout (seconds, default: 300)
```

**In `~/.hermes/.env`:**
```bash
BROWSER_SESSION_TIMEOUT=86400
BROWSER_INACTIVITY_TIMEOUT=86400
HERMES_AGENT_TIMEOUT=86400
HERMES_AGENT_TIMEOUT_WARNING=82800
```

Common timeout values:
- `86400` = 24 hours
- `604800` = 1 week

After changing config: `/restart` gateway or restart CLI for changes to take effect.

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `/skill name` or `hermes -s name`

---

## Manual Skill Discovery & Installation from GitHub

When `hermes skills install` or `hermes skills search` can't find the skill you need (common with third-party repos, niche skills, or custom forks), use this manual discovery workflow.

### When to Use This
- The skill hub doesn't have what you need
- You need a skill from a specific GitHub user/repo
- Network/proxy issues prevent built-in commands from working
- You want to inspect the skill before installing

### Step 1: Search GitHub for Skills

Use GitHub's advanced search to find `SKILL.md` files:

```bash
# Search all of GitHub for Hermes skills
curl -s "https://api.github.com/search/code?q=filename:SKILL.md+hermes-agent+in:path&per_page=100" | jq '.items[] | {repo: .repository.full_name, path: .path, name: .name}'

# Search within a specific org
curl -s "https://api.github.com/search/code?q=filename:SKILL.md+repo:Teknium1/hermes-agent+in:path&per_page=100" | jq '.items[] | {path: .path}'

# Alternative: Search repositories that mention hermes-agent skills
curl -s "https://api.github.com/search/repositories?q=hermes-agent+skill+in:description&sort=updated" | jq '.items[] | {full_name: .full_name, description: .description}'
```

**Common places to find skills:**
- Official repo: `Teknium1/hermes-agent` → `skills/` directory
- Community forks: Look for repos with "hermes-agent" in name
- Plugin repos: Search for repos with SKILL.md files

### Step 2: Inspect and Download Skill Files

Once you find a skill repo/path:

```bash
# Get the raw download URL for a SKILL.md file
# Pattern: https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>

# Example: Get the list of skills from Teknium1/hermes-agent
curl -s "https://api.github.com/repos/Teknium1/hermes-agent/contents/skills" | jq '.[] | {name: .name, type: .type}'

# Browse a specific skill category
curl -s "https://api.github.com/repos/Teknium1/hermes-agent/contents/skills/browser" | jq '.[] | {name: .name, download_url: .download_url}'

# Download a specific SKILL.md
curl -s "https://raw.githubusercontent.com/Teknium1/hermes-agent/main/skills/browser/playwright/SKILL.md"
```

**Important checks before downloading:**
1. ✅ Frontmatter exists (`---` at start and end)
2. ✅ `name` and `description` fields present
3. ✅ No malicious commands in the skill content
4. ✅ Size is reasonable (< 100KB)

### Step 3: Install Manually

Place the downloaded skill in the correct location:

```bash
# Default profile location
mkdir -p ~/.hermes/skills/<category>/<skill-name>/
curl -s "https://raw.githubusercontent.com/.../SKILL.md" > ~/.hermes/skills/<category>/<skill-name>/SKILL.md

# For a specific profile
mkdir -p ~/.hermes/profiles/<profile-name>/skills/<category>/<skill-name>/
curl -s "https://raw.githubusercontent.com/.../SKILL.md" > ~/.hermes/profiles/<profile-name>/skills/<category>/<skill-name>/SKILL.md
```

### Step 4: Verify Installation

```bash
# List all installed skills to confirm it shows up
hermes skills list

# Or view it directly
hermes -s <skill-name> chat -q "Test skill loaded"
```

### Common Pitfalls

1. **Proxy/Network Issues:** If `https_proxy` or `http_proxy` are set but misconfigured, curl may fail. Disable proxy temporarily for GitHub access:
   ```bash
   unset https_proxy http_proxy
   ```

2. **Wrong Branch:** Many repos use `main` but some use `master`. Check both if download fails.

3. **Skill Already Installed:** `hermes skills install` won't overwrite. Delete the old directory first if updating:
   ```bash
   rm -rf ~/.hermes/skills/<category>/<skill-name>/
   ```

4. **Category Mismatch:** The category directory structure doesn't affect functionality, but consistency helps. Check what categories already exist:
   ```bash
   ls ~/.hermes/skills/
   ```

### Quick Installation Script

```python
import os
import subprocess
from pathlib import Path

def install_skill_from_github(owner, repo, branch, skill_path, category=None, profile="default"):
    """
    Install a skill directly from GitHub.
    
    Args:
        owner: GitHub username/org
        repo: Repository name
        branch: Branch name (main/master)
        skill_path: Path within repo to skill directory (e.g., "skills/browser/playwright")
        category: Target category (inferred if None)
        profile: Profile name ("default" or named profile)
    """
    base = Path.home() / ".hermes"
    if profile != "default":
        base = base / "profiles" / profile
    
    # Infer category from skill_path if not provided
    if category is None:
        parts = skill_path.split("/")
        if "skills" in parts:
            idx = parts.index("skills")
            if idx + 1 < len(parts):
                category = parts[idx + 1]
        category = category or "misc"
    
    # Extract skill name from path
    skill_name = skill_path.rstrip("/").split("/")[-1]
    
    # Create target directory
    target_dir = base / "skills" / category / skill_name
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Download SKILL.md
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{skill_path}/SKILL.md"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        with open(target_dir / "SKILL.md", "w") as f:
            f.write(result.stdout)
        print(f"✅ Installed {skill_name} to {target_dir}")
        return True
    else:
        print(f"❌ Failed to download from {url}")
        return False

# Example:
# install_skill_from_github(
#     owner="Teknium1",
#     repo="hermes-agent",
#     branch="main",
#     skill_path="skills/browser/playwright",
#     profile="default"
# )
```

### Related Skills
- `hermes-agent-skill-authoring` — for creating/editing skills yourself

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error\|Permission denied" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`

#### Gateway Permission Errors (The #1 Gateway Killer)

**Symptom**: Platforms (Weixin, Feishu, etc.) fail to connect with `Permission denied: '/home/ubuntu/.hermes/weixin/accounts'` or similar errors on platform directories.

**Root cause**: Incorrect file ownership or permissions on platform data directories, **almost always caused by running recursive `chown` or `chmod` operations** that affect these directories. The gateway runs as one user (e.g., `ubuntu`) and suddenly cannot access files owned by another user (e.g., `hermes-tiao`).

**Common Trigger**: Attempting to run profiles as different Linux users and accidentally changing ownership of directories that the gateway (still running as the original user) needs to access.

**The Pattern That Always Breaks Things**:
```bash
# ❌ NEVER DO THIS - THIS WILL BREAK ALL YOUR GATEWAYS
sudo chown -R hermes-tiao:hermes-tiao /home/ubuntu/.hermes/profiles/tiao/
```

This changes ownership of `weixin/`, `feishu/`, and other platform directories inside the profile. The running gateway process (started as `ubuntu`) can no longer write to these directories, and the platform connection dies.

---

**Emergency First Aid (When Gateway Stops Working After Permission Changes)** — **This is the exact procedure that fixed tiao and hang profile gateways**:

```bash
# 1. Check what user the gateway is actually running as
ps aux | grep hermes | grep gateway

# 2. Fix permissions BACK to the user that the gateway is running as (usually $USER)
#    DO NOT use the new user you were trying to switch to!
sudo chown -R $USER:$USER ~/.hermes/weixin/
sudo chown -R $USER:$USER ~/.hermes/profiles/tiao/weixin/
sudo chown -R $USER:$USER ~/.hermes/profiles/hang/weixin/

# 3. Fix directory permissions (WeChat needs write access)
chmod -R 700 ~/.hermes/weixin/
chmod -R 700 ~/.hermes/profiles/tiao/weixin/

# 4. Kill ALL gateway processes (they will auto-restart or need manual restart)
pkill -f "hermes_cli.*gateway"

# 5. Wait 10 seconds, then verify gateways came back up
ps aux | grep hermes | grep gateway

# 6. Check logs for errors
tail -20 ~/.hermes/profiles/tiao/logs/gateway.log
```

**The Proper Fix Procedure**:

1. **Identify the affected profile** (default or named profile like "tiao", "hang"):
```bash
# Check default profile
ls -la ~/.hermes/weixin/

# Check named profiles
ls -la ~/.hermes/profiles/tiao/weixin/
ls -la ~/.hermes/profiles/hang/weixin/
```

2. **Fix ownership and permissions** (IMPORTANT: Use the user the gateway is actually running as, not the new user you were trying to switch to):
```bash
# Default profile
sudo chown -R $USER:$USER ~/.hermes/weixin/
chmod -R 700 ~/.hermes/weixin/

# Named profiles (repeat for each profile)
sudo chown -R $USER:$USER ~/.hermes/profiles/tiao/weixin/
chmod -R 700 ~/.hermes/profiles/tiao/weixin/
```

3. **Restart the gateway** (critical - permission changes don't take effect until restarted):
```bash
# Kill and restart all profile gateways
pkill -f "hermes_cli.*gateway"

# Wait 5 seconds, then verify
sleep 5 && ps aux | grep hermes | grep gateway
```

**Important**: Always restart the gateway after fixing permissions. The running process caches directory access and won't pick up permission changes until restarted.

---

**Emergency First Aid (When Gateway Stops Working After Permission Changes)**:

```bash
# 1. Check what user the gateway is actually running as
ps aux | grep hermes | grep gateway

# 2. Fix permissions BACK to the user that the gateway is running as (usually $USER)
#    DO NOT use the new user you were trying to switch to!
sudo chown -R $USER:$USER ~/.hermes/weixin/
sudo chown -R $USER:$USER ~/.hermes/profiles/tiao/weixin/
sudo chown -R $USER:$USER ~/.hermes/profiles/hang/weixin/

# 3. Fix directory permissions (WeChat needs write access)
chmod -R 700 ~/.hermes/weixin/
chmod -R 700 ~/.hermes/profiles/tiao/weixin/

# 4. Kill ALL gateway processes (they will auto-restart or need manual restart)
pkill -f "hermes_cli.*gateway"

# 5. Wait 10 seconds, then verify gateways came back up
ps aux | grep hermes | grep gateway

# 6. Check logs for errors
tail -20 ~/.hermes/profiles/tiao/logs/gateway.log
```

**The Proper Fix Procedure**:

1. **Identify the affected profile** (default or named profile like "tiao", "hang"):
```bash
# Check default profile
ls -la ~/.hermes/weixin/

# Check named profiles
ls -la ~/.hermes/profiles/tiao/weixin/
ls -la ~/.hermes/profiles/hang/weixin/
```

2. **Fix ownership and permissions** (IMPORTANT: Use the user the gateway is actually running as, not the new user you were trying to switch to):
```bash
# Default profile
sudo chown -R $USER:$USER ~/.hermes/weixin/
chmod -R 700 ~/.hermes/weixin/

# Named profiles (repeat for each profile)
sudo chown -R $USER:$USER ~/.hermes/profiles/tiao/weixin/
chmod -R 700 ~/.hermes/profiles/tiao/weixin/
```

3. **Restart the gateway** (critical - permission changes don't take effect until restarted):
```bash
# Kill and restart all profile gateways
pkill -f "hermes_cli.*gateway"

# Wait 5 seconds, then verify
sleep 5 && ps aux | grep hermes | grep gateway
```

**Important**: Always restart the gateway after fixing permissions. The running process caches directory access and won't pick up permission changes until restarted.

---

#### Linux User Isolation: Venv Path Gotcha

When attempting to run Hermes profiles as separate Linux users (user-level hard isolation), you will hit a critical Python venv issue:

**Symptom**: `sudo -u hermes-tiao python /home/ubuntu/.hermes/hermes-agent/venv/bin/python ...` fails with `Permission denied`.

**Root cause**: The Python venv in `~/.hermes/hermes-agent/venv/` contains soft-links pointing to `~/.local/` (e.g., `python3.12` → `/home/ubuntu/.local/pyenv/versions/3.12.7/bin/python3.12`). User home directories have permission `700` by default, so other users cannot traverse into `~/.local/`.

**Workarounds** in order of recommendation:
1. **Use Docker backend** (`backend: docker`) — built-in isolation without user management headaches
2. **Stick with command blacklist + ACL** — sufficient for most use cases without full user isolation
3. **Copy the full Python environment** to a globally accessible location (`/opt/hermes-python/`) with `755` permissions

**Lesson**: User-level isolation is harder than it sounds. Start with command blacklists and workspace directories first. Only pursue full Linux user isolation if you have a specific security requirement that justifies the complexity.

---

#### Gateway Completely Unresponsive After Permission Changes

If `pkill` doesn't work and the gateway won't restart:

```bash
# 1. Force kill any stuck processes
pkill -9 -f "hermes_cli"

# 2. Clean up stale PID and state files
**Prevention:**
- Don't start multiple gateway processes for the same profile simultaneously
- Always use `--replace` flag when starting the gateway manually
- Avoid `systemctl restart` — it sometimes leaves stale state files
- If you must restart, delete the weixin/.lock file BEFORE restarting

---

### Profile Security Hardening (3-Layer Approach)

When running multiple profiles with different personas and access levels, you want to ensure secondary profiles can't accidentally (or intentionally) expose sensitive system information or make destructive changes.

**The 3-layer security model** we applied:

```
Layer 1: Command Blacklist   →  Prevent dangerous commands from running
Layer 2: Tool Output Limits   →  Prevent large dumps from reaching model context
Layer 3: Memory/SOUL Rules    →  Guide model to not expose sensitive info in responses
```

None is perfect alone, but together they provide strong protection against accidental information exposure.

---

#### Layer 1: Terminal Command Blacklisting

Restrict which shell commands a profile can execute. This blocks the most obvious dangers.

```python
import yaml
from pathlib import Path

def set_command_blacklist(profile_name, blacklist_commands):
    """Set terminal command blacklist for a profile."""
    if profile_name == "default":
        config_path = Path.home() / ".hermes" / "config.yaml"
    else:
        config_path = Path.home() / ".hermes" / "profiles" / profile_name / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'terminal' not in config:
        config['terminal'] = {}
    config['terminal']['command_blacklist'] = blacklist_commands
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: blacklisted {len(blacklist_commands)} commands")
    print("   Note: Gateway restart required for changes to take effect.")

# Recommended blacklist for secondary profiles
DANGEROUS_COMMANDS = [
    "chmod", "chown", "chgrp",      # Permission modification (killed our gateways!)
    "rm -rf", "rm -r",              # Recursive deletion
    "sudo", "su",                   # Privilege escalation
    "reboot", "shutdown", "halt",   # System control
    "dd",                           # Disk operation
]

for profile in ["tiao", "hang"]:
    set_command_blacklist(profile, DANGEROUS_COMMANDS)
```

---

#### Layer 2: Tool Output Limits

Restrict how much terminal and file output the model can see. This prevents large directory listings or config files from flooding the context.

```python
import yaml
from pathlib import Path

def set_tool_output_limits(profile_name, max_bytes=10240, max_lines=100, max_line_length=500):
    """
    Set strict limits on tool output to prevent information leaks.
    
    Default Hermes: 50000 bytes, 2000 lines, unlimited line length
    Recommended for security: 10240 bytes (10KB), 100 lines, 500 chars per line
    """
    base = Path.home() / ".hermes"
    if profile_name != "default":
        base = base / "profiles" / profile_name
    
    config_path = base / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config['tool_output'] = {
        'max_bytes': max_bytes,
        'max_lines': max_lines,
        'max_line_length': max_line_length
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: tool_output limits set to {max_bytes}B / {max_lines} lines")
    print("   Note: Gateway restart required for changes to take effect.")
```

---

#### Layer 3: Memory-Based Output Restrictions

Add security rules directly to the profile's `MEMORY.md` (persistent memory) and `SOUL.md` (system prompt). These are read at startup and influence all responses.

```python
from pathlib import Path

def add_security_rules_to_profile(profile_name):
    """Add output security rules to a profile's memory and system prompt."""
    security_rules = """
## 🔴 安全输出限制（强制执行）

### 禁止输出的内容：
1. **服务器目录结构** - 禁止输出任何 `ls`、`find` 等命令显示的目录列表
2. **文件路径信息** - 禁止输出完整的文件路径，如 `/home/ubuntu/xxx`
3. **文件内容泄露** - 禁止直接输出配置文件、密钥、敏感数据的内容
4. **系统信息泄露** - 禁止输出进程列表、端口信息、环境变量等

### 遇到敏感信息时的处理方式：
- 如果需要查看文件，只输出"文件已读取，内容包含敏感信息，不直接展示"
- 如果需要列出目录，只说明"目录存在，包含X个文件"
- 如果用户询问路径，只回答相对路径或模糊描述
- 永远不泄露服务器的具体配置和位置信息
"""

    base = Path.home() / ".hermes"
    if profile_name != "default":
        base = base / "profiles" / profile_name

    # 1. Add to MEMORY.md (persistent cross-session memory)
    memory_path = base / "memories" / "MEMORY.md"
    if memory_path.exists():
        with open(memory_path, 'r') as f:
            content = f.read()
        if "安全输出限制" not in content:
            with open(memory_path, 'a') as f:
                f.write("\n§\n" + security_rules)
            print(f"✅ {profile_name}: Added security rules to MEMORY.md")
    else:
        memory_path.parent.mkdir(exist_ok=True)
        with open(memory_path, 'w') as f:
            f.write(security_rules)
        print(f"✅ {profile_name}: Created MEMORY.md with security rules")

    # 2. Add to SOUL.md (system prompt / persona)
    soul_path = base / "SOUL.md"
    if soul_path.exists():
        with open(soul_path, 'r') as f:
            content = f.read()
        if "安全输出限制" not in content:
            with open(soul_path, 'a') as f:
                f.write("\n\n" + security_rules)
            print(f"✅ {profile_name}: Added security rules to SOUL.md")

# Batch apply security hardening to all secondary profiles
PROFILES_TO_SECURE = ["tiao", "hang"]

for profile in PROFILES_TO_SECURE:
    add_security_rules_to_profile(profile)
    set_tool_output_limits(profile, max_bytes=10240, max_lines=100)
    set_command_blacklist(profile, DANGEROUS_COMMANDS)
```

---

#### Important Limitations

1. **Memory rules are soft restrictions** — they influence model behavior but aren't 100% guaranteed. A determined adversary might still find ways to trick the model.
2. **Tool output limits apply at truncation** — the first N bytes/lines are still visible. Use secret redaction (`security.redact_secrets`) for actual credentials.
3. **Gateway restart required** — changes to `config.yaml`, `MEMORY.md`, and `SOUL.md` don't take effect until the gateway process is restarted.

---

#### Workspace Directory

Set the starting directory for terminal commands (profiles can still `cd` elsewhere, but this keeps accidental listing output focused):

```python
import yaml
from pathlib import Path

def set_profile_workdir(profile_name, workdir_path=None):
    if workdir_path is None:
        if profile_name == "default":
            base = Path.home() / ".hermes"
        else:
            base = Path.home() / ".hermes" / "profiles" / profile_name
        workdir = base / "workspace"
        workdir.mkdir(exist_ok=True)
        workdir_path = str(workdir)
    
    config_path = base / "config.yaml" if profile_name == "default" else \
                  Path.home() / ".hermes" / "profiles" / profile_name / "config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'terminal' not in config:
        config['terminal'] = {}
    config['terminal']['cwd'] = workdir_path
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ {profile_name}: cwd set to {workdir_path}")
```

---

### ACL-Based File Access Testing Pattern

1. **Check all running gateways**:
```bash
ps aux | grep hermes | grep gateway | grep -v grep
```

2. **Check each profile's gateway logs**:
```bash
# Default
tail -10 ~/.hermes/logs/gateway.log

# Named profiles
tail -10 ~/.hermes/profiles/tiao/logs/gateway.log
tail -10 ~/.hermes/profiles/hang/logs/gateway.log
```

3. **Restart a specific profile's gateway** (after config changes):
```python
import subprocess
import sys

def restart_profile_gateway(profile_name):
    """Kill and restart a profile's gateway to pick up config changes."""
    # Find and kill old process
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if f'--profile {profile_name}' in line and 'gateway' in line:
            pid = line.split()[1]
            subprocess.run(["kill", pid])
            print(f"✅ Killed old {profile_name} gateway (PID {pid})")
            break
    
    # Start new gateway in background
    subprocess.Popen([
        sys.executable, "-m", "hermes_cli.main",
        "--profile", profile_name,
        "gateway", "run", "--replace"
    ])
    print(f"✅ Started new {profile_name} gateway")

# Apply this after config changes:
for profile in ["tiao", "hang"]:
    restart_profile_gateway(profile)
```

4. **Profile directory structure**:
```
~/.hermes/                          # Default profile
~/.hermes/profiles/tiao/            # Named profile "tiao"
~/.hermes/profiles/hang/            # Named profile "hang"
```

Each profile has the same internal structure: `config.yaml`, `logs/`, `weixin/`, `feishu/`, etc.

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows HTTP 400 "No models provided"**: Config file encoding issue (BOM). Ensure `config.yaml` is saved as UTF-8 without BOM.

#### WeChat (Weixin) Platform Issues

**Symptom: "A previous session already exists. Please wait for it to finish." message appears in logs, and the platform stops responding.**

This is the #1 WeChat platform killer. The WeChat adapter gets stuck thinking there's an active session when there isn't one.

**Recovery Procedure:**
```bash
# 1. Kill the gateway process
pkill -f "hermes_cli.*gateway"

# 2. Delete the stuck state files
rm -f ~/.hermes/profiles/tiao/weixin/.lock
rm -f ~/.hermes/profiles/tiao/weixin/session.json
rm -f ~/.hermes/profiles/tiao/gateway.pid
rm -f ~/.hermes/profiles/tiao/gateway_state.json

# 3. Clean any other lock files
find ~/.hermes/profiles/tiao/ -name "*.lock" -delete

# 4. Restart the gateway (or let systemd auto-restart)
python -m hermes_cli.main --profile tiao gateway run --replace &
```

**If one profile is stuck but others are working:**
- Don't kill all gateways
- Just target the stuck profile's process
- Delete only that profile's weixin lock files

**Prevention:**
- Don't start multiple gateway processes for the same profile simultaneously
- Always use `--replace` flag when starting the gateway manually
- Avoid `systemctl restart` — it sometimes leaves stale state files
- If you must restart, delete the weixin/.lock file BEFORE restarting

---

## Inspecting Gateway Conversation History

When you need to verify what messages were actually delivered through a gateway (vs CLI test sessions):

### Querying the SQLite Session Database

Each profile stores its conversation history in `state.db` (SQLite format). Use this to find the real gateway conversations:

```python
import sqlite3
from pathlib import Path

def get_profile_sessions(profile_name, limit=10):
    """List all sessions for a profile, most recent first."""
    if profile_name == "default":
        db_path = Path.home() / ".hermes" / "state.db"
    else:
        db_path = Path.home() / ".hermes" / "profiles" / profile_name / "state.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, title, start_time, source, message_count
        FROM sessions
        ORDER BY start_time DESC
        LIMIT ?
    """, (limit,))
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "session_id": row[0],
            "title": row[1],
            "start_time": row[2],
            "source": row[3],  # 'cli', 'weixin', 'discord', etc.
            "message_count": row[4]
        })
    
    conn.close()
    return sessions

# Example: Show all WeChat gateway sessions for profile "tiao"
sessions = get_profile_sessions("tiao")
for s in sessions:
    if s["source"] == "weixin":
        print(f"✅ REAL GATEWAY: {s['session_id']} - {s['title']} ({s['message_count']} messages)")
    else:
        print(f"🔍 CLI TEST: {s['session_id']} - {s['title']}")
```

### Reading Messages from a Specific Session

```python
def get_session_messages(profile_name, session_id):
    """Get all messages from a specific session."""
    if profile_name == "default":
        db_path = Path.home() / ".hermes" / "state.db"
    else:
        db_path = Path.home() / ".hermes" / "profiles" / profile_name / "state.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT role, content, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "role": row[0],
            "content": row[1],
            "timestamp": row[2]
        })
    
    conn.close()
    return messages

# Example: Read the actual WeChat conversation
messages = get_session_messages("tiao", "20260508_175952_6f4194ae")
for msg in messages:
    print(f"[{msg['role']}] {msg['content'][:100]}...")
```

### Key Concepts for Debugging Message Delivery

| Session Type | Source Field | Description |
|--------------|--------------|-------------|
| **Real Gateway Session** | `weixin`, `discord`, `telegram`, etc. | Actual conversation with a platform user — messages are delivered and received |
| **CLI Test Session** | `cli` | One-shot `hermes chat -q` invocation — NOT delivered to any platform |
| **Interactive CLI** | `cli` | Interactive `hermes` session — local only |

**Critical debugging insight:** When you run `hermes chat --profile tiao -q "message"`, this creates a NEW CLI session with `source: cli`. It does NOT send the message through the WeChat gateway to the user. It only talks to the tiao profile's agent locally.

#### Verification: Did the Message Actually Get Sent?

After any message sending attempt (especially when testing cross-profile delivery), always verify by checking the session database. This is the **only reliable way** to know if a message was actually delivered.

```python
import sqlite3
from pathlib import Path
import json

def verify_message_delivered(profile_name, message_content_snippet, min_tool_calls=1):
    """
    Verify a message was actually sent through the gateway by checking for
    send_message tool calls in recent sessions from the actual platform (not cli).
    
    Returns (success: bool, message: str, session_details: dict)
    """
    if profile_name == "default":
        db_path = Path.home() / ".hermes" / "state.db"
    else:
        db_path = Path.home() / ".hermes" / "profiles" / profile_name / "state.db"
    
    if not db_path.exists():
        return False, f"Database not found: {db_path}", {}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find recent gateway sessions (not CLI)
    cursor.execute("""
        SELECT s.session_id, s.title, s.start_time, s.source
        FROM sessions s
        WHERE s.source != 'cli'
        ORDER BY s.start_time DESC
        LIMIT 10
    """)
    
    sessions = cursor.fetchall()
    
    if not sessions:
        conn.close()
        return False, "No gateway sessions found - gateway may not be running", {}
    
    # Check each session for send_message tool calls
    for session_id, title, start_time, source in sessions:
        cursor.execute("""
            SELECT m.role, m.content
            FROM messages m
            WHERE m.session_id = ?
            ORDER BY m.timestamp ASC
        """, (session_id,))
        
        messages = cursor.fetchall()
        tool_calls = []
        
        for role, content in messages:
            if role == "tool" and "send_message" in (content or ""):
                tool_calls.append(content)
        
        if tool_calls:
            # Check if our message snippet is in any of the tool calls
            for call in tool_calls:
                if message_content_snippet in (call or ""):
                    conn.close()
                    return True, f"✅ Found send_message with matching content in session {session_id}", {
                        "session_id": session_id,
                        "source": source,
                        "tool_calls": len(tool_calls),
                        "matched": True
                    }
            # Found tool calls but not matching content
            conn.close()
            return True, f"⚠️ Found {len(tool_calls)} send_message calls in {session_id} (source: {source}), but content doesn't match snippet", {
                "session_id": session_id,
                "source": source,
                "tool_calls": len(tool_calls),
                "matched": False
            }
    
    conn.close()
    return False, "❌ No send_message tool calls found in recent gateway sessions - message may not have been delivered", {}

# Example usage:
# success, msg, details = verify_message_delivered("tiao", "老爸老妈罗曼史")
# print(f"{success}: {msg}")
```

**The verification checklist before declaring success:**
1. ✅ Check `source` field — must be platform name (e.g., `weixin`), NOT `cli`
2. ✅ Check for actual `send_message` tool calls in the messages
3. ✅ Verify the message content matches what you intended to send
4. ✅ Check the gateway logs for any delivery errors
5. ✅ (Optional) Confirm with the recipient if possible

### To Actually Send a Message Through a Gateway

If you need Profile A's gateway to send a message to a user on its connected platform:

1. **Option 1: Use the messaging tool** (best for cross-platform delivery)
   ```bash
   hermes --profile tiao send_message --target weixin:user_id "Hello from kaka!"
   ```

2. **Option 2: Gateway sends message as its own persona**
   - The gateway already has an active connection
   - Use the profile's `send_message` tool directly
   - The message comes from the gateway's persona (e.g., "少佐小猫")

3. **Option 3: Relaying pattern for persona bridging**
   ```python
   # Profile A (kaka) receives message from user on WeChat
   # Profile A asks Profile B (tiao) to relay through its WeChat gateway
   response = send_to_profile("tiao", 
       "我是 {{AGENT_NAME}}，来自default profile。帮主人传话给条条：'今晚8点看电影'。"
       "请以少佐小猫的身份回复条条。")
   ```

### Common Debugging Scenarios

**Symptom**: "I sent a message to profile X via `hermes chat`, but the user never received it."

**Root cause**: `hermes chat -q` creates a local CLI session — it doesn't go through the gateway.

**Fix**: Use the `send_message` tool in the target profile, or use the gateway's own message-sending capabilities.

**Symptom**: "Profile X's gateway isn't responding to user messages."

**Debug steps**:
1. Check `ps aux | grep hermes | grep gateway` — is the gateway running?
2. Check `~/.hermes/profiles/X/logs/gateway.log` for errors
3. Check platform connection status: `hermes --profile X gateway status`
4. Verify the session actually exists in `state.db` with `source: weixin` (not `cli`)

**Symptom**: "Multiple profiles with WeChat gateways — which one is talking to whom?"

**Debug steps**:
1. Query `state.db` for each profile to find sessions with `source: weixin`
2. Read message content to identify which user is talking to which profile
3. Check platform account info in each profile's `weixin/` directory

### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```

---

## Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Config options | `hermes config edit` or [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Available tools | `hermes tools list` or [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Slash commands | `/help` in session or [Slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Skills catalog | `hermes skills browse` or [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `hermes model` or [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Platform setup | `hermes gateway setup` or [Messaging docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP servers | `hermes mcp list` or [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Profiles | `hermes profile list` or [Profiles docs](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron jobs | `hermes cron list` or [Cron docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Memory | `hermes memory status` or [Memory docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Env variables | `hermes config env-path` or [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| CLI commands | `hermes --help` or [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Session files | `~/.hermes/sessions/` or `hermes sessions browse` |
| Source code | `~/.hermes/hermes-agent/` |

---

## Contributor Quick Reference

For occasional contributors and PR authors. Full developer docs: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Project Layout

```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, context compression, memory, model routing, credential pooling, skill dispatch
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool
│   └── registry.py       # Central tool registry
├── gateway/              # Messaging gateway
│   └── platforms/        # Platform adapters (telegram, discord, etc.)
├── cron/                 # Job scheduler
├── tests/                # ~3000 pytest tests
└── website/              # Docusaurus docs site
```

Config: `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys).

### Adding a Tool (3 files)

**1. Create `tools/your_tool.py`:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. Add to `toolsets.py`** → `_HERMES_CORE_TOOLS` list.

Auto-discovery: any `tools/*.py` file with a top-level `registry.register()` call is imported automatically — no manual list needed.

All handlers must return JSON strings. Use `get_hermes_home()` for paths, never hardcode `~/.hermes`.

### Adding a Slash Command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `cli.py` → `process_command()`
3. (Optional) Add gateway handler in `gateway/run.py`

All consumers (help text, autocomplete, Telegram menu, Slack mapping) derive from the central registry automatically.

### Agent Loop (High Level)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Testing

```bash
python -m pytest tests/ -o 'addopts=' -q   # Full suite
python -m pytest tests/tools/ -q            # Specific area
```

- Tests auto-redirect `HERMES_HOME` to temp dirs — never touch real `~/.hermes/`
- Run full suite before pushing any change
- Use `-o 'addopts='` to clear any baked-in pytest flags

### Commit Conventions

```
type: concise subject line

Optional body.
```

Types: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Key Rules

- **Never break prompt caching** — don't change context, tools, or system prompt mid-conversation
- **Message role alternation** — never two assistant or two user messages in a row
- Use `get_hermes_home()` from `hermes_constants` for all paths (profile-safe)
- Config values go in `config.yaml`, secrets go in `.env`
- New tools need a `check_fn` so they only appear when requirements are met
