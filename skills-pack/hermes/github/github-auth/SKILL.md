---
name: github-auth
description: "GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Authentication, Git, gh-cli, SSH, Setup]
    related_skills: [github-pr-workflow, github-code-review, github-issues, github-repo-management]
---

# GitHub Authentication Setup

This skill sets up authentication so the agent can work with GitHub repositories, PRs, issues, and CI. It covers two paths:

- **`git` (always available)** — uses HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with a simpler auth flow

## Detection Flow

When a user asks you to work with GitHub, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"

# Always inspect existing SSH configuration before concluding SSH is unavailable.
# Users may have a GitHub Host alias (for example github.com-work or github.com-main)
# rather than the default git@github.com identity.
ls -la ~/.ssh/id_*.pub ~/.ssh/config 2>/dev/null || echo "no obvious SSH keys/config"
awk '/^Host /{print $0}' ~/.ssh/config 2>/dev/null || true
```

**Important:** If a GitHub SSH key was configured previously, do not tell the user SSH is unavailable until you have checked `~/.ssh/config`, key files, and tested the relevant Host alias with `ssh -T <host-alias>`. A successful GitHub SSH auth often returns exit code `1` with text like `Hi <user>! You've successfully authenticated, but GitHub does not provide shell access.` — treat that text as success.

**Critical: Do NOT use proxy for GitHub operations.** When `gh` CLI is available and authenticated (or when a token file exists), use `gh` directly — it handles authentication internally. Do not add `--proxy socks5://127.0.0.1:10808` to curl commands for GitHub API calls. If `.gitconfig` contains a leftover `http.proxy` setting, remove it with `git config --global --unset http.proxy`.

**Token persistence:** If a GitHub PAT is stored at `/home/ubuntu/.github-token`, ensure it is exported in `~/.bashrc` so all future sessions have it:

```bash
# Add to ~/.bashrc if not already present
grep -q 'GH_TOKEN' ~/.bashrc || {
  echo 'export GH_TOKEN=$(cat /home/ubuntu/.github-token)' >> ~/.bashrc
  echo 'export GITHUB_TOKEN=$(cat /home/ubuntu/.github-token)' >> ~/.bashrc
}
```

This makes `gh auth status` pass automatically in every new shell without needing `gh auth login`.

**Decision tree:**
1. If `gh auth status` shows authenticated → you're good, use `gh` for everything
2. If `gh` is installed but not authenticated → use "gh auth" method below
3. If `gh` is not installed → use "git-only" method below (no sudo needed)

---

## Method 1: Git-Only Authentication (No gh, No sudo)

This works on any machine with `git` installed. No root access needed.

### Option A: HTTPS with Personal Access Token (Recommended)

This is the most portable method — works everywhere, no SSH config needed.

#### Credential safety when a token is pasted in chat

If the user pastes a real GitHub token into the conversation:

- Treat it as exposed secret material: **never echo it back**, never include it in summaries, memory, skills, plans, logs, or final responses.
- Redact it as `[REDACTED]` whenever referring to it.
- If you must validate it, use the shortest possible GitHub API check (e.g. `/user`) and report only non-secret metadata such as the login name.
- Prefer not to persist exposed tokens. For durable access, recommend SSH keys or ask the user to create a fresh token after the exposed one is revoked.
- If the user explicitly accepts the risk and asks to proceed with the pasted token, use it only for the requested operation and remind them to revoke/rotate it afterward.
- Avoid placing tokens in shell commands, command arguments, remote URLs, screenshots, or files that may be logged. If persistence is necessary, use the platform's credential helper or `.env` storage with restrictive permissions and never print the value.
- If a freshly pasted token returns `401 Bad credentials`, do not retry noisily or ask the user to paste it repeatedly. Explain that the token may be expired/revoked, copied incompletely, missing authorization, or auto-revoked after exposure; recommend SSH keys for durable access.

**Safe temporary git push pattern with a pasted token (no persistence, no token in remote URL):**

```bash
# Token must come from the environment; do not put the token literal in the command.
export GITHUB_TOKEN="<token>"
ASKPASS=$(mktemp)
cat > "$ASKPASS" <<'SH'
#!/bin/sh
case "$1" in
  *Username*) echo x-access-token ;;
  *Password*) echo "$GITHUB_TOKEN" ;;
  *) echo ;;
esac
SH
chmod 700 "$ASKPASS"
GIT_ASKPASS="$ASKPASS" GIT_TERMINAL_PROMPT=0 git push -u origin main
rm -f "$ASKPASS"
unset GITHUB_TOKEN
```

This keeps the repository remote as `https://github.com/<owner>/<repo>.git`, avoids embedding secrets in `git remote -v`, shell history, process arguments, or command output, and fails non-interactively if credentials are invalid.

**Step 1: Create a personal access token**

Tell the user to go to: **https://github.com/settings/tokens**

- Click "Generate new token (classic)"
- Give it a name like "hermes-agent"
- Select scopes:
  - `repo` (full repository access — read, write, push, PRs)
  - `workflow` (trigger and manage GitHub Actions)
  - `read:org` (if working with organization repos)
- Set expiration (90 days is a good default)
- Copy the token — it won't be shown again

**Step 2: Configure git to store the token**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

After entering credentials once, they're saved and reused for all future operations.

**Alternative: cache helper (credentials expire from memory)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Alternative: set the token directly in the remote URL (per-repo)**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Step 3: Configure git identity**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Step 4: Verify**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### Option B: SSH Key Authentication

Good for users who prefer SSH or already have keys set up.

**Step 1: Check for existing SSH keys**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Step 2: Generate a key if needed**

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

Tell the user to add the public key at: **https://github.com/settings/keys**
- Click "New SSH key"
- Paste the public key content
- Give it a title like "hermes-agent-<machine-name>"

**Step 3: Test the connection**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Step 4: Configure git to use SSH for GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Step 5: Configure git identity**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## Method 2: gh CLI Authentication

If `gh` is installed, it handles both API access and git credentials in one step.

### Interactive Browser Login (Desktop)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### Token-Based Login (Headless / SSH Servers)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

### Verify

```bash
gh auth status
```

---

## Using the GitHub API Without gh

When `gh` is not available, you can still access the full GitHub API using `curl` with a personal access token. This is how the other GitHub skills implement their fallbacks.

### Setting the Token for API Calls

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### Extracting the Token from Git Credentials

If git credentials are already configured (via credential.helper store), the token can be extracted:

```bash
# Read from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### Helper: Detect Auth Method

Use this pattern at the start of any GitHub workflow:

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use a personal access token as the password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope — regenerate with correct scopes |
| `fatal: Authentication failed` | Cached credentials may be stale — run `git credential reject` then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` — must be `store` or `cache` |
| Multiple GitHub accounts | Use SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above — no installation needed |
| `gh` installation fails due to network/proxy issues | 1. Check proxy status: `systemctl status clash.service` / `echo $http_proxy $https_proxy`
2. If proxy is down, use domestic mirror: `wget https://mirrors.huaweicloud.com/gh-cli/releases/download/v2.94.0/gh_2.94.0_linux_amd64.deb -O /tmp/gh.deb && sudo dpkg -i /tmp/gh.deb`
3. Alternatively use pre-installed git-only method without gh |
| GitHub connection fails (SSH/HTTPS timeout) | 1. Check if proxy is working: `curl -m 10 https://github.com`
2. If proxy is faulty, temporarily unset proxy: `unset http_proxy https_proxy`
3. For SSH timeouts, try SSH over HTTPS port: add `Host github.com\n  Port 443\n  Hostname ssh.github.com` to `~/.ssh/config`
4. Verify network connectivity first before troubleshooting auth |
