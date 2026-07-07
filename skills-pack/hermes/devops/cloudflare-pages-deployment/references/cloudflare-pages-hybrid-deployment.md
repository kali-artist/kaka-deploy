# Cloudflare Pages + Tunnel Hybrid Deployment

When a fullstack app (frontend + backend) needs to be deployed but the server has limited resources, split the deployment: frontend to Cloudflare Pages (free CDN hosting), backend stays on server via Cloudflare Tunnel.

## Architecture

```
User Browser
    │
    ├── novel.example.com (Cloudflare Pages)
    │       ↓ serves static frontend (client/dist)
    │
    └── api.example.com (Cloudflare Tunnel → server:3000)
            ↓ proxies to backend (node dist/app.js)
```

## When to Use This Pattern

- Server has ≤2GB RAM — frontend (vite preview) wastes 100-200MB that could be freed
- User wants free CDN-hosted frontend with auto-deploy from GitHub
- User already has a domain on Cloudflare (DNS managed there)
- Frontend is a static SPA (Vite build output) — no SSR needed
- Backend uses file-based DB (SQLite) or has local dependencies that prevent easy migration

## Prerequisites

- GitHub repository with the project code (can be a fork of upstream)
- SSH key configured for git push (see `github-auth` skill)
- Cloudflare account with domain already managed
- Backend already running on server (see `references/low-memory-nodejs-deployment.md`)

## Step 1: Prepare GitHub Repository

If the project's origin points to someone else's repo, fork it first:

```bash
# Check current remote
git remote -v
# If it's not your repo, either:
# A) Fork on GitHub web UI (simplest), then update remote:
git remote set-url origin git@github.com:YOUR_USERNAME/REPO.git
# B) Fork via GitHub API with a fine-grained PAT (Administration: Read and write):
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/ORIGINAL_OWNER/REPO/forks
# Then update remote to SSH:
git remote set-url origin git@github.com:YOUR_USERNAME/REPO.git
```

**CRITICAL — SSH key must be at account level, NOT repo Deploy Key**: When adding an SSH key to GitHub, add it at Settings → SSH and GPG keys (account level). If accidentally added as a repository Deploy Key, it will be read-only and `git push` will fail with `Permission denied to deploy key`. The SSH test response reveals this: `Hi username/Cloudflare!` (with app name) means deploy key; `Hi username!` means account-level key. See `github-auth` skill for details.

Ensure SSH key is set up and working:
```bash
ssh -T git@github.com
# Should say: "Hi YOUR_USERNAME! You've successfully authenticated..."
# If it says "Hi YOUR_USERNAME/Cloudflare!" — you added it as a Deploy Key (read-only), fix it.
```

## Step 2: Create wrangler.jsonc — for pnpm monorepo, put in CLIENT subdirectory

The new Cloudflare Pages (wrangler CLI mode) requires a `wrangler.jsonc` config file. For pnpm monorepo projects, DO NOT put it in the repo root — wrangler detects the workspace root and fails with `The Wrangler application detection logic has been run in the root of a workspace instead of targeting a specific project`. Instead, put it in the client subdirectory:

Create `client/wrangler.jsonc`:

```jsonc
{
  "name": "your-project-name",
  "compatibility_date": "2024-09-23",
  "pages_build_output_dir": "dist"
}
```

Key fields:
- `name`: Project identifier (arbitrary, should match the Pages project name)
- `compatibility_date`: Required by wrangler, use a recent date
- `pages_build_output_dir`: Path to Vite build output, relative to wrangler.jsonc location (e.g., `"dist"` when wrangler.jsonc is in client/ and build output is client/dist). **This field is REQUIRED by Cloudflare Pages** — if missing, you'll see: `We detected a configuration file at .../wrangler.jsonc but it is missing the "pages_build_output_dir" field, required by Pages.`

**CRITICAL**: Use `pages_build_output_dir`, NOT `assets.directory`. The `assets.directory` field is for Workers (not Pages) and will be ignored with a warning.

**IMPORTANT — shared workspace dependency**: If the client package imports from a `shared` workspace (e.g., `@ai-novel/shared`), you MUST build `shared` first in the build command: `pnpm --filter @scope/shared build && pnpm --filter @scope/client build`. Without this, the client build fails with module resolution errors.

Commit and push:
```bash
git add wrangler.jsonc
git commit -m "Add wrangler.jsonc for Cloudflare Pages deployment"
git push origin main
```

## Step 3: Commit Local Changes

Any local config changes (like vite.config.ts allowedHosts) need to be committed:

```bash
git add -A
git commit -m "feat: production deployment config"
git push origin main
```

If push is rejected (non-fast-forward), sync first:
```bash
git stash
git pull origin main --rebase
git stash pop
git push origin main
```

## Step 4: Create Cloudflare Pages Project

1. Go to dash.cloudflare.com → Workers & Pages → Create → Pages → Connect to Git
2. Authorize GitHub access and select the repository
3. Set the following in build settings:
   - **Root directory**: Leave empty (or `.`) — NOT `client/dist`
   - **Build command**: `corepack enable && pnpm install --frozen-lockfile && pnpm --filter @scope/shared build && pnpm --filter @scope/client build`
   - **Deploy command** (REQUIRED): `cd client && npx wrangler pages deploy dist --project-name=your-project-name`
4. **IMPORTANT — Create the Pages project BEFORE first deploy**: Go to Workers & Pages → Create → Pages → Direct Upload, create a project named `your-project-name`. Without this, the deploy fails with a misleading `Authentication error (code 10000)`.
5. **IMPORTANT — Build token permissions**: The Build token in Pages settings needs `Cloudflare Pages → Edit` (Account level). Without this, deploy fails with `Authentication error (code 10000)` (same error as missing project — confusing!).
6. Add environment variables:
   - `VITE_API_BASE_URL` = `https://api.example.com` (the backend tunnel URL)
7. Deploy

### CRITICAL — pnpm is pre-installed via asdf (do NOT npm install -g pnpm)

Cloudflare Pages build environment (as of mid-2026) has pnpm pre-installed via asdf at `/opt/buildhome/.asdf/installs/nodejs/20.19.0/bin/pnpm`. Running `npm install -g pnpm@10.6.0` FAILS with `EEXIST: file already exists`. Use `corepack enable` to activate the already-installed pnpm.

### CRITICAL — do NOT use `npm install` for pnpm workspaces

If you accidentally use `npm install` instead of `pnpm install`, npm will fail with `EUNSUPPORTEDPROTOCOL` error on `workspace:*` dependencies:
```
npm error code EUNSUPPORTEDPROTOCOL
npm error Unsupported URL Type "workspace:": workspace:*
```

### Build command for pnpm monorepos on Cloudflare Pages (tested, working pattern):

```
corepack enable && pnpm install --frozen-lockfile && pnpm --filter @ai-novel/shared build && pnpm --filter @ai-novel/client build
```
Replace `@ai-novel/shared` and `@ai-novel/client` with your actual package names from `pnpm-workspace.yaml`.

### CRITICAL — `wrangler deploy` vs `wrangler pages deploy`

When the deploy command is `npx wrangler deploy` (the default in new Cloudflare Pages UI), wrangler shows a warning: `It seems that you have run 'wrangler deploy' on a Pages project, 'wrangler pages deploy' should be used instead.` If you proceed, it fails with `Missing entry-point to Worker script or to assets directory`. 

**Fix**: Use `wrangler pages deploy` in the deploy command, and prefix with `cd client` so wrangler runs in the client directory where wrangler.jsonc lives:
```
cd client && npx wrangler pages deploy dist --project-name=your-project-name
```

The wrangler.jsonc in the client directory must have `pages_build_output_dir` set to `"dist"` (relative to the client dir).

**IMPORTANT — `--project-name` is needed**: If the Pages project name doesn't auto-resolve from wrangler.jsonc, you'll get `Must specify a project name`. Add `--project-name=<name>` to the deploy command. The project must also be created in the Cloudflare dashboard first (see Step 4 below).

**IMPORTANT — misleading "Authentication error (code 10000)"**: If the Pages project doesn't exist yet in the Cloudflare dashboard, the deploy command fails with `Authentication error (code 10000)`. This looks like a token permission issue but is actually caused by the project not existing. Create the project first: Workers & Pages → Create → Pages → Direct Upload → name it. Then re-run the deploy.

## Step 5: Configure Frontend API URL

The frontend needs to know where the backend is. Set `VITE_API_BASE_URL` in Cloudflare Pages project settings → Environment variables.

**IMPORTANT — value must include the API path prefix**: If the backend serves API routes under `/api` (e.g., `https://api.example.com/api/health`), the env var value must be `https://api.example.com/api` (NOT `https://api.example.com`). Without the `/api` suffix, the frontend will call `https://api.example.com/health` which returns 404.

```bash
# In Cloudflare Pages dashboard:
# Settings → Environment variables → Add
# Variable name: VITE_API_BASE_URL
# Value: https://api.example.com/api
```

**Note**: `VITE_`-prefixed env vars are embedded at build time, not runtime. After changing this value, you must trigger a rebuild (push to Git or manual rebuild in Pages dashboard).

### Alternative: `.env.production` file (more reliable than dashboard env vars)

Sometimes the Cloudflare Pages dashboard environment variables don't take effect on a specific build — the build runs but the env var isn't picked up, resulting in the default fallback (`/api` relative path) being baked into the JS bundle. A more reliable approach is to commit a `.env.production` file directly in the client directory:

```bash
# client/.env.production
VITE_API_BASE_URL=https://api.example.com/api
```

Since Vite automatically reads `.env.production` during production builds, this guarantees the env var is present every time a GitHub-triggered build runs — regardless of dashboard env var timing issues.

**Important**: Check `.gitignore` — the default Vite template ignores `.env` and `.env.local` but NOT `.env.production`. If `.gitignore` has a broad `.env*` pattern, add an exception:
```
!.env.production
```

Commit and push to trigger a rebuild:
```bash
git add client/.env.production
git commit -m "fix: set production API base URL"
git push origin main
```

### Diagnostic symptom: frontend loads but no data (empty lists, config errors)

When the frontend page loads successfully but shows empty data lists and configuration errors, the root cause is almost always a mismatched `VITE_API_BASE_URL`:

1. The browser loads the Pages domain (e.g., `ai-novel-client.pages.dev`) → frontend HTML/JS loads fine
2. The frontend tries to call the API at the wrong URL (either `localhost:3000` on the user's own machine, or `/api` relative path hitting `pages.dev/api` which doesn't exist)
3. API calls fail silently → empty lists, configuration page errors

**Diagnostic flow**:
1. Confirm frontend loads: `curl -s -o /dev/null -w '%{http_code}' https://novel.example.com` → 200
2. Confirm backend is running: `ss -tlnp | grep 3000` → port listening
3. Confirm tunnel is active: `ps aux | grep cloudflared | grep -v grep` → process running
4. **Inspect the deployed JS bundle** for the API URL (see "Debugging VITE_ Environment Variables" section below)
5. If the JS bundle shows `localhost:3000` or only `/api` (relative) → env var was not baked in → use `.env.production` approach above

In the frontend code, the API base URL is typically resolved like:
```typescript
// Production mode (no VITE_API_BASE_URL set): defaults to "/api" (relative path)
// With VITE_API_BASE_URL set: uses the configured value
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
```

## Step 6: Set Up Backend Tunnel (API subdomain)

Create or update Cloudflare Tunnel config to expose the backend on an API subdomain:

```yaml
# ~/.cloudflared/config.yml
tunnel: <tunnel-uuid>
credentials-file: /root/.cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: api.example.com
    service: http://localhost:3000
  - hostname: novel.example.com    # old direct frontend route (can remove)
    service: http://localhost:5173
  - service: http_status:404
```

Create DNS route for the API subdomain:
```bash
cloudflared tunnel route dns <tunnel-name> api.example.com
```

## Step 7: Configure CORS on Backend

The backend must allow requests from the Pages domain:

```bash
# In server/.env, update CORS_ORIGIN:
CORS_ORIGIN=https://novel.example.com,http://localhost:5173
```

Restart the backend after changing CORS settings.

## Step 8: Stop Local Frontend (Free Memory)

Once Cloudflare Pages is serving the frontend, stop the local vite preview to reclaim ~120-200MB:

```bash
pkill -f 'vite preview'
pkill -f 'esbuild'
```

Update the start-prod.sh script to only start the backend:

```bash
# Only start backend — frontend is now on Cloudflare Pages
cd "$PROJECT_DIR/server"
node dist/app.js &
```

## Step 9: Verify

### Quick Health Check

```bash
# Frontend (Cloudflare Pages) — should return 200
curl -s -o /dev/null -w "%{http_code}" https://novel.example.com

# Backend API (via tunnel) — should return health JSON
curl -s https://api.example.com/api/health

# DNS should show Cloudflare IPs, not server IP
dig +short novel.example.com  # Cloudflare Pages IPs
dig +short api.example.com    # Cloudflare Tunnel CNAME
```

### Full Multi-Layer Verification

When the quick check fails or you need to isolate which layer is broken, check each layer from the server:

```bash
# 1. Backend process running?
ps aux | grep -E 'node.*server|start-prod' | grep -v grep

# 2. Backend port responding? (404 on root / is NORMAL — backend only defines API routes)
curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/
# 404 = OK (root path undefined), 502/connection refused = backend down

# 3. Cloudflared process active?
ps aux | grep cloudflared | grep -v grep
# Or: systemctl is-active cloudflared

# 4. Tunnel domain reachable?
curl -s -o /dev/null -w '%{http_code}' https://api.example.com/
# 404 = OK (tunnel works, root path undefined), 502/timeout = tunnel or backend issue
```

**Key insight**: A 404 on the backend root path (`/`) is NOT an error — it means the tunnel is working and routing traffic to the backend, but the backend only defines routes under `/api/*`. If the frontend loads data correctly, the full chain (Pages → API → Tunnel → Backend) is working.

### Debugging VITE_ Environment Variables (JS Bundle Inspection)

`VITE_`-prefixed env vars are baked into the JS bundle at build time. If the frontend loads but API calls fail silently, verify the env var was correctly embedded by inspecting the deployed JS bundle:

```bash
# 1. Get the JS bundle filename from the deployed page
JS_FILE=$(curl -s https://novel.example.com | grep -oP '/assets/index-[^"]+\.js' | head -1)
echo "JS bundle: $JS_FILE"

# 2. Download the JS and search for the API domain
curl -s "https://novel.example.com${JS_FILE}" | grep -oP 'https?://[^"]*your-domain[^"]*' | head -5
# If output is empty → env var was NOT baked in → trigger a rebuild in Cloudflare Pages dashboard
# If output shows your API URL → env var is correctly embedded, issue is elsewhere (CORS, tunnel, etc.)
```

This technique works because Vite replaces `import.meta.env.VITE_*` references with literal strings during the build. If the env var wasn't set when the build ran, the string won't appear in the bundle.

## Memory Impact

| Component | Before (all on server) | After (Pages + Tunnel) |
|-----------|----------------------|----------------------|
| Frontend (vite preview) | 120-200MB | 0MB (on Cloudflare Pages) |
| Backend (node dist/app.js) | 150-350MB | 150-350MB (unchanged) |
| Cloudflared | 40MB | 40MB |
| **Total server memory** | **310-590MB** | **190-390MB** |
| **Savings** | — | **~120-200MB freed** |

## Multiple Sites on One Domain

One root domain can host unlimited subdomains on Cloudflare Pages:

- `novel.example.com` → AI Novel frontend
- `blog.example.com` → Blog frontend
- `tool.example.com` → Another tool
- `api.example.com` → Shared backend API (via Tunnel)

Each Pages project binds to one subdomain. Free tier allows unlimited projects.

### Diagnosing Direct Upload vs Git-connected mode via Cloudflare API

When GitHub auto-build doesn't trigger after push, the project may be in Direct Upload mode (no Git integration). Query the Cloudflare API to confirm:

```bash
# Requires a token with Pages:Read permission (cfat_ Edit-only tokens will get error 9106)
curl -s "https://api.cloudflare.com/client/v4/accounts/<account-id>/pages/projects/<project-name>" \
  -H "Authorization: Bearer <token>" | python3 -m json.tool
```

Key fields to check:

| Field | Git-connected (auto-build) | Direct Upload (manual) |
|-------|---------------------------|----------------------|
| `deployment_trigger.type` | `"push"` | `"ad_hoc"` |
| `build_config.build_command` | e.g. `"npx vite build"` | absent |
| `build_config.root_dir` | e.g. `"client"` | absent |
| `source.type` | `"github"` | absent |
| `source.repo_name` | e.g. `"your-repo"` | absent |

If `deployment_trigger.type` is `"ad_hoc"`, the project has NO Git integration — pushes won't auto-build. Two options:
1. **Reconnect Git** in Cloudflare Dashboard → Workers & Pages → project → Settings → Builds & deployments → connect GitHub repo and set build command.
2. **Use the deploy script** (`templates/deploy-pages.sh`) to build locally + deploy via wrangler. This is faster (no Cloudflare build environment) and works regardless of Git integration status.

### Pitfall: token with Pages:Edit but no Pages:Read cannot diagnose via API

A `cfat_`-prefixed token with only `Cloudflare Pages → Edit` permission can deploy successfully but CANNOT query project settings via the API (error 9106 "Authentication failed"). To use the API diagnostic above, the token needs `Cloudflare Pages → Read` as well (the "Edit Cloudflare Pages" template includes both). Alternatively, inspect project settings via the Cloudflare Dashboard.

## Updating Frontend After Changes

With Cloudflare Pages connected to GitHub, pushing to main branch auto-triggers rebuild:

```bash
# Make changes to frontend code
git add client/
git commit -m "fix: update frontend"
git push origin main
# Cloudflare Pages auto-rebuilds and deploys
```

### Pitfall: GitHub auto-build may NOT trigger after push

Sometimes the Cloudflare Pages GitHub integration silently fails or disconnects — you push to main, but no new build is triggered. The deployed JS hash stays the same. This is easy to miss because there's no error notification.

**Detection**: Compare the JS bundle filename before and after waiting ~2 minutes post-push:

```bash
# Before push
curl -s https://your-project.pages.dev | grep -oP '/assets/index-[^"]+\.js' | head -1
# Wait 2 min, then check again
sleep 120 && curl -s https://your-project.pages.dev | grep -oP '/assets/index-[^"]+\.js' | head -1
# If the hash is unchanged → auto-build did NOT trigger
```

**Fix 1**: Go to Cloudflare Dashboard → Workers & Pages → your project → Settings → Builds & deployments → disconnect and reconnect the GitHub integration. Then push again or click "Retry deployment".

**Fix 2 (faster, no dashboard needed)**: Build locally with the env var and deploy via wrangler:

```bash
# 1. Build locally with the correct env var
cd client
VITE_API_BASE_URL=https://api.example.com/api npx vite build

# 2. Verify the env var was baked into the JS bundle
grep -oP 'https?://[^"]*your-domain[^"]*' dist/assets/index-*.js | head -5
# Should output your API URL. If empty → env var wasn't set, rebuild.

# 3. Deploy via wrangler (requires CLOUDFLARE_API_TOKEN env var)
CLOUDFLARE_API_TOKEN=your_token npx wrangler pages deploy dist --project-name=your-project-name
```

**CRITICAL**: `wrangler` (the CLI tool for Pages deployment) requires a **separate** `CLOUDFLARE_API_TOKEN` environment variable. This is NOT the same as the cloudflared tunnel token in `cert.pem` or `~/.cloudflared/<UUID>.json`. Even if cloudflared is running successfully with a tunnel, `npx wrangler whoami` will show "not authenticated" without this env var.

To get a token: dash.cloudflare.com → Profile → API Tokens → Create Token → "Edit Cloudflare Pages" template (or custom token with `Cloudflare Pages → Edit` permission at Account level).

### Local build verification checklist

Before deploying a local build, verify:

```bash
# 1. Build output exists
ls -la client/dist/assets/index-*.js

# 2. API URL is baked into the bundle (NOT localhost or /api relative)
grep -oP 'https?://[^"]*superkali[^"]*' client/dist/assets/index-*.js | head -5
# Should show: https://api.your-domain.com/api

# 3. No stale localhost references in main bundle
grep -c 'localhost:3000' client/dist/assets/index-*.js
# Should be 0 (or only in fallback code paths, not the active config)
```

## Pitfalls

0. **pnpm activation in Cloudflare Pages build environment (MOST COMMON FIRST FAILURE)**: Cloudflare Pages build environment (as of mid-2026) has pnpm pre-installed via asdf. Running `npm install -g pnpm@10.6.0` FAILS with `EEXIST: file already exists` at `/opt/buildhome/.asdf/installs/nodejs/20.19.0/bin/pnpm`. Use `corepack enable` to activate the pre-installed pnpm. Do NOT use `npm install` as a substitute for `pnpm install` — npm fails with `EUNSUPPORTEDPROTOCOL` on `workspace:*` deps. Use: `corepack enable && pnpm install --frozen-lockfile && pnpm --filter @scope/shared build && pnpm --filter @scope/client build`.

0a. **wrangler.jsonc required for new Cloudflare Pages (wrangler CLI mode)**: The new Cloudflare Pages UI uses wrangler CLI mode and requires a `wrangler.jsonc` file. For pnpm monorepo projects, put it in the CLIENT subdirectory (NOT repo root — repo root causes workspace detection error). Without it, the build fails with `Failed: root directory not found`. Create the file with `pages_build_output_dir` (relative to the file's location, e.g. `"dist"` when in client/ and output is client/dist), `compatibility_date`, and `name` fields.

0b. **"Deploy command" is mandatory in new Cloudflare Pages UI**: The new Cloudflare Pages interface has a required "Deploy command" field. Fill it with `npx wrangler pages deploy <output_dir>`.

0c. **Shared workspace dependency must be built first**: If the client imports from a shared workspace package (e.g., `@ai-novel/shared`), the build command must build shared first: `pnpm --filter @scope/shared build && pnpm --filter @scope/client build`.

1. **CORS**: Backend must allow the Pages domain in `CORS_ORIGIN`. If frontend loads but API calls fail with CORS errors, check this first.

2. **Environment variables**: `VITE_` prefixed env vars are embedded at build time, not runtime. If you change `VITE_API_BASE_URL`, you must trigger a rebuild (push to Git or manual rebuild in Pages dashboard). If dashboard env vars don't take effect, use the `.env.production` file approach (see Step 5 above). Diagnostic symptom: frontend loads but shows empty data lists and config errors.

3. **Build command for pnpm monorepos**: Cloudflare Pages build environment has pnpm pre-installed via asdf (as of mid-2026). Use `corepack enable` to activate it — do NOT use `npm install -g pnpm` (fails with EEXIST). Do NOT use `npm install` instead of `pnpm install` — npm fails with `EUNSUPPORTEDPROTOCOL` on `workspace:*` dependencies.

4. **Don't forget to stop local frontend**: After Pages deployment is confirmed working, stop the local vite preview process to free memory. Update start-prod.sh accordingly.

5. **Public vs private repo**: Cloudflare Pages free tier works with both public and private GitHub repos. No need to make the repo public.

6. **Backend stays on server**: The backend uses SQLite (file-based DB) and has local API keys. Don't try to deploy backend to Pages — it won't work. Pages is static-only.

7. **SSH key vs Deploy Key**: When adding an SSH key to GitHub for push access, it must be added at account level (Settings → SSH and GPG keys), NOT as a repository Deploy Key. Deploy keys are read-only by default and `git push` will fail with `Permission to X denied to deploy key`. Test with `ssh -T git@github.com` — if the response includes an app name (e.g., `Hi username/Cloudflare!`), it's a deploy key; if it's just `Hi username!`, it's account-level and has push access.

8. **wrangler.jsonc `pages_build_output_dir` vs `assets.directory`**: Use `pages_build_output_dir` (string) in wrangler.jsonc for Cloudflare Pages. Do NOT use `assets.directory` (object) — that's for Cloudflare Workers, not Pages. The error when `pages_build_output_dir` is missing reads: `We detected a configuration file but it is missing the "pages_build_output_dir" field, required by Pages.`

9. **Misleading "Authentication error (code 10000)"**: This error has TWO possible causes: (a) the Pages project doesn't exist yet — create it first in the dashboard, or (b) the Build token lacks `Cloudflare Pages → Edit` permission. Check both before retrying.

10. **`--project-name` in deploy command**: If `npx wrangler pages deploy` complains `Must specify a project name`, add `--project-name=<name>` to the deploy command. This happens when the project name in wrangler.jsonc doesn't match an existing Pages project.

11. **cfat_ token scope — deploy works but project listing fails (error 9106)**: A `cfat_`-prefixed Cloudflare API Token with only `Cloudflare Pages → Edit` permission can run `wrangler pages deploy dist --project-name=xxx` successfully but FAILS on `wrangler pages project list` or any API call to `/accounts/{id}/pages/projects/...` with `Authentication failed (status: 400) [code: 9106]`. This is a permission scope issue, not an invalid token. When debugging, either upgrade the token to include `Cloudflare Pages → Read` (or use the "Edit Cloudflare Pages" template which includes both Read + Edit), or inspect project settings via the Cloudflare Dashboard instead of the API.
