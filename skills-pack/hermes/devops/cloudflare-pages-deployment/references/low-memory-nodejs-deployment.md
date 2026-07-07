# Low-Memory Server Node.js Deployment

Real-world deployment of a Node.js fullstack app (Vite frontend + Express backend + Prisma + SQLite) on a 1.6GB RAM server.

## Server Specs

- RAM: 1.6GB total
- Swap: none initially
- OS: Ubuntu 26.04 LTS
- Node.js: v22

## The Problem

Running dev mode (`pnpm dev`) with concurrently launches:
- tsc --watch (shared layer) ~100-200MB
- ts-node-dev + Prisma (backend) ~200-400MB
- Vite dev server (frontend) ~300-500MB
- Peak: 600-1100MB → OOM crash on 688MB available

## Solution: Production Mode (方案A)

### Step 1: Create Swap

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Persist to fstab
grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Low swappiness — only use swap under pressure
sysctl vm.swappiness=10

# Verify
free -m
swapon --show
```

### Step 2: Build with memory limits

Build each package separately to avoid peak memory spikes:

```bash
# Start with conservative limit
export NODE_OPTIONS="--max-old-space-size=512"

# 2a: Build shared (small, usually fine)
pnpm --filter @scope/shared build

# 2b: Build server (heavy — 700+ TS files)
# If OOM at 512MB, increase to 2GB and let Swap absorb it:
export NODE_OPTIONS="--max-old-space-size=2048"
pnpm --filter @scope/server prisma:generate
pnpm --filter @scope/server build

# 2c: Build client (Vite — moderate)
export NODE_OPTIONS="--max-old-space-size=1024"
pnpm --filter @scope/client build
```

**Key insight**: TypeScript compiler (`tsc`) memory scales with number of source files. 773 TS files needed >800MB heap. With 2GB Swap available, setting `--max-old-space-size=2048` lets V8 overflow to Swap without crashing.

### Step 3: Sync database (CRITICAL — often missed)

```bash
# After building, the database tables don't exist yet
# Build only compiles TypeScript — it does NOT run migrations
cd server
pnpm prisma db push
# Or: pnpm prisma migrate deploy
```

**Without this step**, the server starts but crashes immediately with:
```
PrismaClientKnownRequestError: code: 'P2021'
The table `main.NovelSideEffectJob` does not exist in the current database.
```

### Step 4: Start in production mode

Use compiled output, not dev servers:

```bash
# Backend — node on compiled JS (no ts-node-dev overhead)
cd server
node dist/app.js &

# Frontend — vite preview on static build output (minimal memory)
cd client
npx vite preview --port 5173 --host 127.0.0.1 &
```

**Important**: Use `--host 127.0.0.1` (not `0.0.0.0`) to bind to localhost only. Public access should go through Cloudflare Tunnel or SSH tunnel only.

**CRITICAL — Vite preview allowedHosts**: When exposing vite preview through Cloudflare Tunnel (or any reverse proxy with a custom domain), you MUST add the domain to `preview.allowedHosts` in `vite.config.ts`:

```typescript
export default defineConfig({
  // ... existing config ...
  preview: {
    host: true,
    port: 5173,
    allowedHosts: ["your-domain.com"],  // or true to allow all
  },
});
```

Without this, Vite returns HTTP 403 with body: `Blocked request. This host ("your-domain.com") is not allowed.` This is the #1 most common issue when deploying Vite apps behind a tunnel/proxy. After changing vite.config.ts, restart vite preview — the config is only read at startup.

### Step 5: Verify

```bash
# Backend health
curl -s http://localhost:3000/api/health

# Frontend
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:5173

# Memory check
free -m
```

## Memory Comparison

| Mode | Peak Memory | Swap Usage | Stability |
|------|------------|------------|-----------|
| Dev mode (pnpm dev) | 600-1100MB | N/A (no swap) | ❌ OOM crash |
| Production mode | 400-500MB | 400-500MB | ✅ Stable |

## Production Startup Script Template

See `templates/start-prod.sh` for a ready-to-use startup script that:
- Checks for build artifacts and auto-builds if missing
- Kills old processes on ports 3000 and 5173
- Starts backend and waits for health check
- Starts frontend
- Reports access URLs and PIDs

## Runtime Memory Optimization: Vite Preview Direct Binary

When running `npx vite preview`, npm creates intermediate processes (npm exec + sh wrapper) that waste ~86MB. On low-memory servers, use the direct binary instead:

```bash
# ❌ Wasteful — creates 3 extra processes (~86MB overhead)
npx vite preview --port 5173 --host 127.0.0.1

# ✅ Direct binary — skips npm exec and sh wrapper
node ./node_modules/.bin/../vite/bin/vite.js preview --port 5173 --host 127.0.0.1
# Or if vite is in client/node_modules/.bin:
client/node_modules/.bin/vite preview --port 5173 --host 127.0.0.1
```

Process comparison:

| Method | Processes | Extra Memory |
|--------|-----------|-------------|
| npx vite preview | bash → npm exec → sh → vite | ~86MB |
| Direct binary | vite (single) | 0MB |

Also consider lowering the runtime NODE_OPTIONS for the backend. If the backend stabilizes at ~370MB with `--max-old-space-size=512`, lowering to `384` makes V8 more aggressive about garbage collection:

```bash
# Runtime (lower than build — backend doesn't need 512MB headroom)
export NODE_OPTIONS="--max-old-space-size=384"
```

## Pitfalls Summary

1. **Build ≠ DB sync**: `pnpm build` does not create/migrate database tables. Always run `prisma db push` or `prisma migrate deploy` after building.
2. **tsc OOM on large projects**: 700+ TS files needs >800MB heap. Set `--max-old-space-size=2048` with Swap available.
3. **Build packages separately**: Don't `pnpm build` all at once on low memory. Build shared → server → client in sequence.
4. **Drop caches between builds**: `sync && echo 3 > /proc/sys/vm/drop_caches` frees page cache between heavy build steps.
5. **vite preview host**: Default may bind 0.0.0.0. Always set `--host 127.0.0.1` for security.
6. **vite preview allowedHosts (CRITICAL)**: When behind a reverse proxy (Cloudflare Tunnel, nginx, etc.) with a custom domain, add the domain to `preview.allowedHosts` in vite.config.ts. Without it, Vite returns 403 "Blocked request. This host is not allowed." This is the #1 most common tunnel+Vite issue. Config is read at startup — restart vite after changing.
7. **Kill esbuild children too**: `pkill -f 'vite'` may leave stale esbuild child processes. Always `pkill -f 'esbuild'` as well when restarting vite.
