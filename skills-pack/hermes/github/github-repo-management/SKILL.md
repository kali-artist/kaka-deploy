---
name: github-repo-management
description: "Clone/create/fork repos; manage remotes, releases."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Repositories, Git, Releases, Secrets, Configuration]
    related_skills: [github-auth, github-pr-workflow, github-issues]
---

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Each section shows `gh` first, then the `git` + `curl` fallback.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)

### Setup

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

# Get your GitHub username (needed for several operations)
if [ "$AUTH" = "gh" ]; then
  GH_USER=$(gh api user --jq '.login')
else
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
fi
```

If you're inside a repo already:

```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Cloning Repositories

Cloning is pure `git` — works identically either way:

```bash
# Clone via HTTPS (works with credential helper or token-embedded URL)
git clone https://github.com/owner/repo-name.git

# Clone into a specific directory
git clone https://github.com/owner/repo-name.git ./my-local-dir

# Shallow clone (faster for large repos)
git clone --depth 1 https://github.com/owner/repo-name.git

# Clone a specific branch
git clone --branch develop https://github.com/owner/repo-name.git

# Clone via SSH (if SSH is configured)
git clone git@github.com:owner/repo-name.git

# Clone via a configured GitHub SSH Host alias from ~/.ssh/config
ssh -T github.com-work
git clone --depth 1 --single-branch git@github.com-work:owner/repo-name.git
```

**With gh (shorthand):**

```bash
gh repo clone owner/repo-name
gh repo clone owner/repo-name -- --depth 1
```

### Project discovery and unstable-network fallback

When the task is to find a suitable GitHub project/tool before downloading it, compare candidates by stars, recency of maintenance, README/API maturity, language/runtime fit, and whether it directly solves the user's current class of problem.

If `git clone` is slow or stalls on an unstable network, keep the clone running in the background and start a parallel ZIP download fallback. Use whichever completes first:

```bash
# Default-branch ZIP fallback; try main first, then master if needed
curl -L --retry 3 --connect-timeout 20 -o /tmp/repo-main.zip https://github.com/owner/repo-name/archive/refs/heads/main.zip
unzip -q /tmp/repo-main.zip -d /tmp
```

If direct GitHub HTTPS and the configured proxy/Clash route both fail, try public GitHub ZIP accelerator endpoints as a download-only fallback. Do not trust blindly: verify the archive before using it, and prefer official GitHub URLs whenever they work.

```bash
OWNER=owner
REPO=repo-name
BRANCH=main
mkdir -p /tmp/gh-download /tmp/gh-unzip
for base in \
  'https://gh.llkk.cc/https://github.com' \
  'https://gh-proxy.com/https://github.com' \
  'https://ghfast.top/https://github.com'
do
  url="$base/$OWNER/$REPO/archive/refs/heads/$BRANCH.zip"
  out="/tmp/gh-download/$REPO-$BRANCH.zip"
  if curl -L --retry 2 --connect-timeout 20 --max-time 180 -o "$out" "$url" \
     && python3 - <<PY
import zipfile, sys
p='$out'
with zipfile.ZipFile(p) as z:
    bad=z.testzip()
    print('zip_entries', len(z.namelist()), 'bad', bad)
    sys.exit(1 if bad else 0)
PY
  then
    unzip -q "$out" -d /tmp/gh-unzip
    echo "downloaded:$out"
    break
  fi
done
```

For repeated git operations in the same shell, export a key-specific SSH command if needed:

```bash
export GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_work"
git clone --depth 1 --single-branch git@github.com-work:owner/repo-name.git
```

Note: Inline `GIT_SSH_COMMAND="..." git clone ...` is also valid in POSIX shells; exporting first is useful when running multiple commands in the same session.

## 2. Creating Repositories

**With gh:**

```bash
# Create a public repo and clone it
gh repo create my-new-project --public --clone

# Private, with description and license
gh repo create my-new-project --private --description "A useful tool" --license MIT --clone

# Under an organization
gh repo create my-org/my-new-project --public --clone

# From existing local directory
cd /path/to/existing/project
gh repo create my-project --source . --public --push
```

**With git + curl:**

```bash
# Create the remote repo via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{
    "name": "my-new-project",
    "description": "A useful tool",
    "private": false,
    "auto_init": true,
    "license_template": "mit"
  }'

# Clone it
git clone https://github.com/$GH_USER/my-new-project.git
cd my-new-project

# -- OR -- push an existing local directory to the new repo
cd /path/to/existing/project
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/$GH_USER/my-new-project.git
git push -u origin main
```

To create under an organization:

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/my-org/repos \
  -d '{"name": "my-new-project", "private": false}'
```

### From a Template

**With gh:**

```bash
gh repo create my-new-app --template owner/template-repo --public --clone
```

**With curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/template-repo/generate \
  -d '{"owner": "'"$GH_USER"'", "name": "my-new-app", "private": false}'
```

## 3. Forking Repositories

**With gh:**

```bash
gh repo fork owner/repo-name --clone
```

**With git + curl:**

```bash
# Create the fork via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo-name/forks

# Wait a moment for GitHub to create it, then clone
sleep 3
git clone https://github.com/$GH_USER/repo-name.git
cd repo-name

# Add the original repo as "upstream" remote
git remote add upstream https://github.com/owner/repo-name.git
```

### Keeping a Fork in Sync

```bash
# Pure git — works everywhere
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

**With gh (shortcut):**

```bash
gh repo sync $GH_USER/repo-name
```

## 4. Repository Information

**With gh:**

```bash
gh repo view owner/repo-name
gh repo list --limit 20
gh search repos "machine learning" --language python --sort stars
```

**With curl:**

```bash
# View repo details
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f\"Name: {r['full_name']}\")
print(f\"Description: {r['description']}\")
print(f\"Stars: {r['stargazers_count']}  Forks: {r['forks_count']}\")
print(f\"Default branch: {r['default_branch']}\")
print(f\"Language: {r['language']}\")"

# List your repos
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/user/repos?per_page=20&sort=updated" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    vis = 'private' if r['private'] else 'public'
    print(f\"  {r['full_name']:40}  {vis:8}  {r.get('language', ''):10}  ★{r['stargazers_count']}\")"

# Search repos
curl -s \
  "https://api.github.com/search/repositories?q=machine+learning+language:python&sort=stars&per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['items']:
    print(f\"  {r['full_name']:40}  ★{r['stargazers_count']:6}  {r['description'][:60] if r['description'] else ''}\")"
```

## 5. Repository Settings

**With gh:**

```bash
gh repo edit --description "Updated description" --visibility public
gh repo edit --enable-wiki=false --enable-issues=true
gh repo edit --default-branch main
gh repo edit --add-topic "machine-learning,python"
gh repo edit --enable-auto-merge
```

**With curl:**

```bash
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  -d '{
    "description": "Updated description",
    "has_wiki": false,
    "has_issues": true,
    "allow_auto_merge": true
  }'

# Update topics
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  https://api.github.com/repos/$OWNER/$REPO/topics \
  -d '{"names": ["machine-learning", "python", "automation"]}'
```

## 6. GitHub Pages for Static Sites

Use this when publishing a simple static site (`index.html`, CSS, JS) from a repository to a public preview URL like `https://<owner>.github.io/<repo>/`.

### Fast path: push static files

```bash
cd /path/to/site
# If the remote already has commits (e.g. an auto-created README), fetch/merge before pushing.
git fetch origin main || true
if git show-ref --verify --quiet refs/remotes/origin/main; then
  git merge origin/main --allow-unrelated-histories --no-edit || {
    git status --short
    echo "Resolve conflicts, then git add/commit before pushing"
    exit 1
  }
fi

git add index.html styles.css script.js README.md
git commit -m "Add static demo site" || true
git push -u origin main
```

If `git push` is rejected with `fetch first`, the remote contains work not present locally. Fetch and merge `origin/main` (use `--allow-unrelated-histories` when local and remote were initialized separately), resolve conflicts such as `README.md`, commit, then push again.

### Pages deployment options

**Option A — Branch source (simplest):** enable Pages from `main` branch `/` root. With an API token/gh auth that has repository administration/pages permission:

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$OWNER/$REPO/pages \
  -d '{"source":{"branch":"main","path":"/"}}'

# If Pages already exists, update it instead:
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$OWNER/$REPO/pages \
  -d '{"source":{"branch":"main","path":"/"}}'
```

**Option B — GitHub Actions source:** add `.github/workflows/pages.yml` using `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages`. The repository still must have Pages source set to **GitHub Actions** in Settings → Pages, or via an authenticated API/gh operation with sufficient permission.

Important: SSH authentication only proves `git` push/pull access. It cannot call GitHub REST APIs or change repository settings such as Pages source. If only SSH is available, push the workflow/files and ask the user to manually open `https://github.com/<owner>/<repo>/settings/pages` and set **Build and deployment → Source: GitHub Actions** (or branch source as appropriate).

#### Vite/React project-site replacement pattern

Use this when replacing an existing static Pages demo with a built Vite/React app in a project repo (`https://<owner>.github.io/<repo>/`):

1. Configure Vite with the repository subpath, or assets will 404 on Pages:
   ```js
   // vite.config.js
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'

   export default defineConfig({
     plugins: [react()],
     base: '/<repo>/',
   })
   ```
2. Keep build outputs out of git for Actions deployments:
   ```gitignore
   node_modules/
   dist/
   .env
   .env.*
   ```
3. Put `.nojekyll` under `public/.nojekyll` so it is copied into `dist`.
4. Use an Actions workflow that installs dependencies, runs `npm run build`, then uploads `dist` rather than the repo root:
   ```yaml
   name: Deploy Vite React site to GitHub Pages

   on:
     push:
       branches: ["main"]
     workflow_dispatch:

   permissions:
     contents: read
     pages: write
     id-token: write

   concurrency:
     group: "pages"
     cancel-in-progress: false

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with:
             node-version: 22
             cache: npm
         - run: npm ci
         - run: npm run build
         - uses: actions/upload-pages-artifact@v3
           with:
             path: dist

     deploy:
       environment:
         name: github-pages
         url: ${{ steps.deployment.outputs.page_url }}
       runs-on: ubuntu-latest
       needs: build
       steps:
         - id: deployment
           uses: actions/deploy-pages@v4
   ```
5. Disable or remove older root-upload/Jekyll Pages workflows to avoid duplicate deployments overwriting the Vite `dist` artifact. If preserving the file, limit it to `workflow_dispatch` and make it a no-op. A common blank-page symptom is that the live `https://<owner>.github.io/<repo>/` HTML contains `<script type="module" src="/src/main.jsx">` instead of built `/repo/assets/...` files; this means a root/Jekyll workflow published source files after the Vite workflow and overwrote the correct deployment.
   - If the user is editing workflows in GitHub's web/mobile UI and sees `A file with same name already exists`, distinguish this from a deploy/runtime failure: it means they are trying to create a workflow file whose filename already exists. Inspect `.github/workflows/`, remove or rename stale duplicate workflow files (for example `static.yml`, `static2.yml`, `jekyll-gh-pages.yml`) only after confirming they are obsolete, and leave exactly one intended Pages deployment workflow when possible.
   - When a workflow run says `success` but `https://<owner>.github.io/<repo>/` returns 404, check both the published URL and repository Pages settings/source. The repository Pages REST endpoint can return 404 without sufficient auth or when Pages is not enabled/configured; do not assume the source code is broken solely from that API response.
6. Run `npm install && npm run build` locally and inspect `dist/index.html` for `/repo/assets/...` URLs before committing.
7. For GitHub Pages project sites that need SPA-style navigation, prefer hash routing (`/#/path`) unless a custom 404 fallback is configured. Hash routes avoid server-side 404s on direct refresh and work reliably under `https://<owner>.github.io/<repo>/`.
8. When verifying hash routes, remember that URL fragments are not sent to the server. `curl https://<owner>.github.io/<repo>/#/path` only validates the root HTML. To verify the actual route, load it in a browser and check the page title/DOM, or fetch the JS bundle and confirm route markers are present.
9. If `git push` is rejected with `fetch first` after committing, run `git fetch origin main`, inspect the graph, then `git rebase origin/main` when the remote change is non-conflicting (for example a workflow-only commit). Re-run `npm run build` after rebase before pushing again.

### Verification

```bash
# For public repos this returns repo metadata; private repos return 404 unless authenticated.
curl -I https://github.com/$OWNER/$REPO

# Pages may take 30-120 seconds to become available after enable/deploy.
curl -I -L --max-time 20 https://$OWNER.github.io/$REPO/
```

If `gh` is not installed or no `GITHUB_TOKEN`/`GH_TOKEN` is available, you can still confirm a public GitHub Pages deployment by checking the `github.io` URL directly. `HTTP/2 200` (or `HTTP/1.1 200`) from `https://$OWNER.github.io/$REPO/` is enough to report that the public preview is live, even if repository settings cannot be inspected via API.

A public unauthenticated `404` for the repo API or repo URL may mean the repository is private, not missing. Verify with authenticated API or SSH (`ssh -T git@github.com`). A `404` from the `github.io` URL usually means Pages is not enabled yet, deployment is still pending, the repository name/path is wrong, or the site has not propagated; wait 30-120 seconds and retry before escalating.

## 7. Branch Protection

```bash
# View current protection
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection

# Set up branch protection
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["ci/test", "ci/lint"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1
    },
    "restrictions": null
  }'
```

## 7. Secrets Management (GitHub Actions)

**With gh:**

```bash
gh secret set API_KEY --body "your-secret-value"
gh secret set SSH_KEY < ~/.ssh/id_rsa
gh secret list
gh secret delete API_KEY
```

**With curl:**

Secrets require encryption with the repo's public key — more involved via API:

```bash
# Get the repo's public key for encrypting secrets
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/public-key

# Encrypt and set (requires Python with PyNaCl)
python3 -c "
from base64 import b64encode
from nacl import encoding, public
import json, sys

# Get the public key
key_id = '<key_id_from_above>'
public_key = '<base64_key_from_above>'

# Encrypt
sealed = public.SealedBox(
    public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder)
).encrypt('your-secret-value'.encode('utf-8'))
print(json.dumps({
    'encrypted_value': b64encode(sealed).decode('utf-8'),
    'key_id': key_id
}))"

# Then PUT the encrypted secret
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/API_KEY \
  -d '<output from python script above>'

# List secrets (names only, values hidden)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets \
  | python3 -c "
import sys, json
for s in json.load(sys.stdin)['secrets']:
    print(f\"  {s['name']:30}  updated: {s['updated_at']}\")"
```

Note: For secrets, `gh secret set` is dramatically simpler. If setting secrets is needed and `gh` isn't available, recommend installing it for just that operation.

## 8. Releases

**With gh:**

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v2.0.0-rc1 --draft --prerelease --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0" --notes "Release notes"
gh release list
gh release download v1.0.0 --dir ./downloads
```

**With curl:**

```bash
# Create a release
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  -d '{
    "tag_name": "v1.0.0",
    "name": "v1.0.0",
    "body": "## Changelog\n- Feature A\n- Bug fix B",
    "draft": false,
    "prerelease": false,
    "generate_release_notes": true
  }'

# List releases
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    tag = r.get('tag_name', 'no tag')
    print(f\"  {tag:15}  {r['name']:30}  {'draft' if r['draft'] else 'published'}\")"

# Upload a release asset (binary file)
RELEASE_ID=<id_from_create_response>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  "https://uploads.github.com/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=binary-amd64" \
  --data-binary @./dist/binary-amd64
```

## 9. GitHub Actions Workflows

**With gh:**

```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID>
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID>
gh run rerun <RUN_ID> --failed
gh workflow run ci.yml --ref main
gh workflow run deploy.yml -f environment=staging
```

**With curl:**

```bash
# List workflows
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows \
  | python3 -c "
import sys, json
for w in json.load(sys.stdin)['workflows']:
    print(f\"  {w['id']:10}  {w['name']:30}  {w['state']}\")"

# List recent runs
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['workflow_runs']:
    print(f\"  Run {r['id']}  {r['name']:30}  {r['conclusion'] or r['status']}\")"

# Download failed run logs
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs

# Re-run a failed workflow
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun

# Re-run only failed jobs
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun-failed-jobs

# Trigger a workflow manually (workflow_dispatch)
WORKFLOW_ID=<workflow_id_or_filename>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows/$WORKFLOW_ID/dispatches \
  -d '{"ref": "main", "inputs": {"environment": "staging"}}'
```

## 10. Gists

**With gh:**

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list
```

**With curl:**

```bash
# Create a gist
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  -d '{
    "description": "Useful script",
    "public": true,
    "files": {
      "script.py": {"content": "print(\"hello\")"}
    }
  }'

# List your gists
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  | python3 -c "
import sys, json
for g in json.load(sys.stdin):
    files = ', '.join(g['files'].keys())
    print(f\"  {g['id']}  {g['description'] or '(no desc)':40}  {files}\")"
```

## Quick Reference Table

| Action | gh | git + curl |
|--------|-----|-----------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` + `git clone` |
| Repo info | `gh repo view o/r` | `curl GET /repos/o/r` |
| Edit settings | `gh repo edit --...` | `curl PATCH /repos/o/r` |
| Create release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
| List workflows | `gh workflow list` | `curl GET /repos/o/r/actions/workflows` |
| Rerun CI | `gh run rerun ID` | `curl POST /repos/o/r/actions/runs/ID/rerun` |
| Set secret | `gh secret set KEY` | `curl PUT /repos/o/r/actions/secrets/KEY` (+ encryption) |
