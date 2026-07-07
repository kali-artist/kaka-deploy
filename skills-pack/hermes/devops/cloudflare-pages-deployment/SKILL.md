---
name: cloudflare-pages-deployment
description: "Use when deploying static or full-stack websites to Cloudflare Pages + Tunnel. Supports pure static sites (zero server cost) and front-end/back-end split apps (Pages + Tunnel + local backend)."
version: 2.0.0
author: kaka-deploy
license: MIT
metadata:
  hermes:
    tags: [cloudflare, pages, deployment, tunnel, static-site, fullstack]
---

# Cloudflare 网站部署

## 🧭 执行导航层（模型入口，线性决策树）

### 核心执行铁律
- 🔴 铁律1：绝不修改或影响已部署的现有项目，每次新建独立项目
- 🔴 铁律2：部署前必须确认网站类型（纯静态 vs 前后端分离），不同类型流程不同
- 🔴 铁律3：Cloudflare API Token 必须从独立文件读取，禁止明文写在脚本或代码中
- 🔴 铁律4：每个操作步骤完成后必须验证（进程/端口/URL可达性），不能假设成功
- 🔴 铁律5：部署完成后必须端到端验证（前端可访问 + API联通 + 数据正常返回）
- 🔴 铁律6：统一使用 GitHub 自动构建模式，push 即自动部署，不在服务器本地构建
- 🔴 铁律7：所有网站部署后必须绑定自定义域名（xxx.superkali.online），不能只用默认的 *.pages.dev 域名。自定义域名绑定是部署流程的必要步骤，不是可选步骤

### 线性执行流程

1. **判断网站类型** → 纯静态执行流程A，静态+Functions代理执行流程C，前后端分离执行流程B
2. **流程A（纯静态）**：准备代码 → push到GitHub → 通过API创建带GitHub source的Pages项目 → push触发自动构建 → **绑定自定义域名** → 验证URL → 结束
3. **流程C（静态+Pages Functions代理）**：前端代码 + `functions/`目录（serverless API代理）→ 同流程A创建项目 → push触发自动构建 → 用 `wrangler pages secret put` 设置API密钥 → **绑定自定义域名** → 验证URL + API → 结束
4. **流程B（前后端分离）**：
   - B1. 后端部署到服务器（选端口、启动服务、systemd守护）
   - B2. Tunnel添加ingress规则（新域名→新端口）
   - B3. 前端代码push到GitHub → 通过API创建带GitHub source的Pages项目（含环境变量） → push触发自动构建 → **绑定自定义域名到Pages项目**
   - B4. 端到端验证（自定义域名可访问 + API联通 + 数据返回）→ 结束

### 标准快速查表

| 维度 | 标准 | 对应动作 |
|------|------|----------|
| 网站类型 | 无后端逻辑、纯HTML/CSS/JS | 纯静态流程A |
| 网站类型 | 静态前端 + 需要服务端API代理（隐藏密钥/CORS） | 流程C（Pages Functions） |
| 网站类型 | 有Node/Python后端 + 前端 | 前后端分离流程B |
| 端口分配 | 查找未占用端口（从3001起递增） | `ss -tlnp \|\| grep :PORT` |
| Tunnel域名 | xxx.superkali.online 格式 | 添加到config.yml ingress |
| Pages项目名 | 与网站功能相关、唯一 | 通过API创建，见下方步骤 |
| API环境变量 | VITE_API_BASE_URL 或同等变量 | 创建项目时在deployment_configs中配置 |
| Functions密钥 | API_KEY等敏感变量 | 用 `wrangler pages secret put` 设置（见pitfall #16） |
| 部署后更新 | git push → Cloudflare自动构建 | 无需手动操作 |

---

## Overview

将网站部署到 Cloudflare 平台。统一使用 GitHub 自动构建模式：
- **纯静态网站**：代码push到GitHub，Cloudflare自动构建部署到Pages，零服务器开销，CDN全球加速
- **前后端分离网站**：前端同上，后端跑在服务器本地，通过 Cloudflare Tunnel 暴露API

## When to Use

- 用户说"部署新网站"、"上线网站"、"部署前端"
- 用户有静态文件或前端构建产物需要上线
- 用户有前后端分离项目需要完整部署
- **不要用于**：仅本地开发调试、非Cloudflare平台的部署

## 前置条件检查

### 1. Cloudflare 凭证
- Cloudflare API Token（存于 Pages token 文件，chmod 600）
  - kaka: `/home/ubuntu/.cloudflare-pages-token`
  - {{INSTANCE_NAME}}: `/root/.cloudflare-pages-token`
- Cloudflare Account ID（`{{CLOUDFLARE_ACCOUNT_ID}}`）
- cloudflared 已安装且 Tunnel 运行中（仅前后端分离需要）
- cert.pem（用于提取 tunnel token 绑定自定义域名）
  - kaka: `/home/ubuntu/.cloudflared/cert.pem`
  - {{INSTANCE_NAME}}: `/root/.cloudflared/cert.pem`
- Cloudflare GitHub App已安装在GitHub账号上（之前通过Dashboard连接过任意仓库即可，一次性操作）
- **服务器/非交互环境下不要使用 `wrangler login`**，会超时卡住。所有 Wrangler/API 操作都通过 `CF_API_TOKEN` 或 `CLOUDFLARE_API_TOKEN` 环境变量（指向 token 文件）完成。

### 2. GitHub 凭证
- GitHub Personal Access Token（存于 GitHub token 文件，chmod 600）
  - kaka: `/home/ubuntu/.github-token`
  - {{INSTANCE_NAME}}: `/root/.github-token`
- gh CLI 已安装（见下方安装方法）
- gh 认证方式：`GH_TOKEN=$(cat /home/ubuntu/.github-token) gh <command>`（不要用 `gh auth login` 交互式登录，在非交互环境会失败）
- SSH Key 已配置（`~/.ssh/id_ed25519`，已添加到 GitHub 账号）

### 3. gh CLI 安装方法
```bash
# GitHub直连可能超时，用国内镜像
curl -sL --max-time 30 https://gh-proxy.com/https://github.com/cli/cli/releases/download/v2.65.0/gh_2.65.0_linux_amd64.tar.gz -o /tmp/gh.tar.gz && \
tar -xzf /tmp/gh.tar.gz -C /tmp && \
cp /tmp/gh_2.65.0_linux_amd64/bin/gh /usr/local/bin/gh && \
gh --version
```

### 4. 服务器资源
- 前后端分离项目：服务器需有足够内存运行后端服务（建议 ≥2G，含Swap）

### 5. 新建 GitHub 仓库
```bash
# 用gh CLI创建新仓库（private或public）
GH_TOKEN=$(cat /root/.github-token) gh repo create <repo-name> --public --clone /root/<repo-name>
# 或在已有仓库基础上初始化
cd /root/<repo-name> && git init && git remote add origin git@github.com:{{GITHUB_USERNAME}}/<repo-name>.git
```

---

## 流程A：纯静态网站部署

### 核心步骤：通过API创建带GitHub自动构建的Pages项目

所有操作通过Cloudflare API完成，无需登录Dashboard。

```python
import json, urllib.request, urllib.error

# 读取token
with open("/root/.cloudflare-pages-token") as f:
    cf_token = f.read().strip()

account_id = "{{CLOUDFLARE_ACCOUNT_ID}}"

# 1. 如果项目已存在（如之前用Direct Upload创建），先删除
#    Direct Upload项目不能通过API修改source，必须删除重建
# DELETE https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}

# 2. 创建新项目，直接设置GitHub source
project_config = {
    "name": "<project-name>",
    "production_branch": "main",
    "source": {
        "type": "github",
        "config": {
            "owner": "{{GITHUB_USERNAME}}",
            "repo_name": "<repo-name>",
            "production_branch": "main",
            "pr_comments_enabled": True,
            "deployments_enabled": True,
            "production_deployments_enabled": True,
            "preview_deployment_setting": "all",
            "preview_branch_includes": ["*"],
            "preview_branch_excludes": [],
            "path_includes": ["*"],
            "path_excludes": []
        }
    },
    "build_config": {
        "build_command": "",        # 纯静态项目留空；Vite项目填 "npx vite build"
        "destination_dir": "",      # 纯静态项目留空；Vite项目填 "dist"
        "root_dir": ""              # 前端在子目录时填子目录路径，如 "client"
    }
}

url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects"
data = json.dumps(project_config).encode('utf-8')

req = urllib.request.Request(url, data=data, method='POST')
req.add_header('Authorization', f'Bearer {cf_token}')
req.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode())
    # 验证source已正确设置
    print(f"success={result['success']}")
    print(f"source type: {result['result']['source']['type']}")
```

### 触发首次部署

代码push到GitHub main分支后，Cloudflare自动检测并构建部署：

```bash
# 确保代码已push到main分支
cd /root/<repo-name>
git add -A
git commit -m "feat: initial deploy"
git push origin main

# 等待1-2分钟后检查部署状态
# 通过API查看部署历史
curl -s "https://api.cloudflare.com/client/v4/accounts/{{CLOUDFLARE_ACCOUNT_ID}}/pages/projects/<project-name>/deployments" \
  -H "Authorization: Bearer $(cat /root/.cloudflare-pages-token)" | python3 -m json.tool
```

### 验证
```bash
# 1. 检查HTTP状态
curl -s -o /dev/null -w '%{http_code}' https://<project-name>.pages.dev
# 期望: 200

# 2. 检查页面内容
curl -s https://<project-name>.pages.dev | head -20

# 3. 检查部署历史，确认触发方式为 github:push
curl -s "https://api.cloudflare.com/client/v4/accounts/{{CLOUDFLARE_ACCOUNT_ID}}/pages/projects/<project-name>/deployments" \
  -H "Authorization: Bearer $(cat /root/.cloudflare-pages-token)" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for d in data.get('result', []):
    trigger = d.get('deployment_trigger', {})
    stage = d.get('latest_stage', {})
    print(f'{d[\"short_id\"]} | {stage.get(\"name\")} → {stage.get(\"status\")} | trigger: {trigger.get(\"type\")} | {trigger.get(\"metadata\", {}).get(\"commit_message\", \"\")}')
"
```

### 后续更新
改完代码 → `git push` → Cloudflare自动构建部署，无需任何手动操作。

---

## 流程C：静态前端 + Pages Functions 代理

适用于：前端 + 轻量服务端逻辑（API密钥代理、CORS解决、请求转发），无需独立后端服务器。

项目结构：
```
├── index.html
├── css/
├── js/
└── functions/          ← Pages Functions（文件即路由）
    └── api/
        └── chat.js     ← → /api/chat
```

### C1. 编写 Functions 代理

`functions/api/chat.js` 示例（转发到外部AI API，隐藏密钥）：

```javascript
export async function onRequestPost({ request, env }) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }
  try {
    const body = await request.json();
    const apiResponse = await fetch(`${env.API_BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${env.API_KEY}`,
      },
      body: JSON.stringify({ model: body.model || 'gpt-4o-mini', messages: body.messages, stream: body.stream ?? true }),
    });
    if (!apiResponse.ok) {
      return new Response(JSON.stringify({ error: `API error: ${apiResponse.status}` }), { status: apiResponse.status, headers: { 'Content-Type': 'application/json', ...corsHeaders } });
    }
    // 流式响应直接透传
    if (body.stream && apiResponse.body) {
      return new Response(apiResponse.body, { headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', ...corsHeaders } });
    }
    const data = await apiResponse.json();
    return new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json', ...corsHeaders } });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders } });
  }
}
```

### C2. 部署（同流程A）

项目创建、push、自动构建 — 与流程A完全相同。`functions/` 目录会被 Cloudflare 自动识别。

### C3. 设置 Functions 密钥

⚠️ 通过 Cloudflare API 设置的环境变量在 Functions 运行时可能不生效（见 pitfall #16）。必须用 wrangler CLI：

```bash
CF_API_TOKEN=$(cat /home/ubuntu/.cloudflare-pages-token) npx wrangler pages secret put API_KEY --project-name <project-name>
CF_API_TOKEN=$(cat /home/ubuntu/.cloudflare-pages-token) npx wrangler pages secret put API_BASE_URL --project-name <project-name>
```

设置 secret 后必须重新 `git push` 触发新部署，变量才会在 Functions 运行时通过 `env.API_KEY` 读取到。

### C4. 验证

```bash
# 1. 前端可访问
curl -s -o /dev/null -w '%{http_code}' https://<project-name>.pages.dev
# 2. Functions 代理工作（不返回 "not configured" 错误）
curl -s -X POST https://<project-name>.pages.dev/api/chat -H 'Content-Type: application/json' -d '{"messages":[{"role":"user","content":"hi"}]}' | head -c 200
```

---

## 流程B：前后端分离网站部署

### B1. 后端部署

```bash
# 1. 查找可用端口
ss -tlnp | grep -E ':(3001|3002|3003)' # 从3001起递增

# 2. 确认后端启动方式（根据项目类型）
# Node项目: node dist/app.js / npm start
# Python项目: python main.py / uvicorn main:app

# 3. 启动后端（建议用systemd守护）
cat > /etc/systemd/system/<service-name>.service << 'EOF'
[Unit]
Description=<project-name> backend
After=network.target

[Service]
Type=simple
WorkingDirectory=<project-dir>
ExecStart=<start-command>
Restart=on-failure
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now <service-name>

# 4. 验证后端
curl -s http://localhost:<port>/health || curl -s http://localhost:<port>/
```

### B2. Cloudflare Tunnel 配置

cloudflared 已注册为 systemd 服务，配置文件在 `/etc/cloudflared/config.yml`（不是 `~/.cloudflared/config.yml`）。

```bash
# 1. 编辑 Tunnel 配置文件（systemd 服务路径）
vim /etc/cloudflared/config.yml

# 2. 在 ingress 部分添加新规则（在 - service: http_status:404 之前）
# 格式：
#   - hostname: <new-subdomain>.superkali.online
#     service: http://localhost:<port>

# 3. 重启 cloudflared（systemd 方式）
systemctl restart cloudflared

# 4. 添加DNS记录（如果用的是named tunnel）
cloudflared tunnel route dns <tunnel-name> <new-subdomain>.superkali.online

# 5. 验证Tunnel
curl -s -o /dev/null -w '%{http_code}' https://<new-subdomain>.superkali.online
```
### B3. 前端部署（GitHub自动构建）

通过API创建Pages项目，直接设置GitHub source和环境变量：

```python
import json, urllib.request

with open("/root/.cloudflare-pages-token") as f:
    cf_token = f.read().strip()

account_id = "{{CLOUDFLARE_ACCOUNT_ID}}"
api_url = "https://<api-subdomain>.superkali.online/api"

project_config = {
    "name": "<project-name>",
    "production_branch": "main",
    "source": {
        "type": "github",
        "config": {
            "owner": "{{GITHUB_USERNAME}}",
            "repo_name": "<repo-name>",
            "production_branch": "main",
            "pr_comments_enabled": True,
            "deployments_enabled": True,
            "production_deployments_enabled": True,
            "preview_deployment_setting": "all",
            "preview_branch_includes": ["*"],
            "preview_branch_excludes": [],
            "path_includes": ["*"],
            "path_excludes": []
        }
    },
    "build_config": {
        "build_command": "cd client && npx vite build",  # 根据项目结构调整
        "destination_dir": "client/dist",                  # 根据项目结构调整
        "root_dir": ""
    },
    "deployment_configs": {
        "preview": {
            "env_vars": {
                "VITE_API_BASE_URL": {"type": "plain_text", "value": api_url}
            }
        },
        "production": {
            "env_vars": {
                "VITE_API_BASE_URL": {"type": "plain_text", "value": api_url}
            }
        }
    }
}

url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects"
data = json.dumps(project_config).encode('utf-8')

req = urllib.request.Request(url, data=data, method='POST')
req.add_header('Authorization', f'Bearer {cf_token}')
req.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode())
    print(f"success={result['success']}")
```

**后续更新：** 改完代码 → `git push` → 自动构建部署。

### B4. 端到端验证

```bash
# 1. 前端可访问
curl -s -o /dev/null -w '%{http_code}' https://<project-name>.pages.dev

# 2. 前端JS中API地址正确（新构建会有新hash）
curl -s https://<project-name>.pages.dev | grep -oP '/assets/index-[^"]+\.js' | head -1
JS=$(curl -s https://<project-name>.pages.dev | grep -oP '/assets/index-[^"]+\.js' | head -1)
curl -s "https://<project-name>.pages.dev${JS}" | grep -oP 'https?://[^"]*<api-subdomain>[^"]*'

# 3. API可达且返回数据
curl -s https://<api-subdomain>.superkali.online/api/<endpoint> | head -c 500

# 4. 后端进程存活
systemctl is-active <service-name>
```

---

### 美中不足
- `cloudflared tunnel route dns <tunnel-name> <hostname>` 在存在默认 `~/.cloudflared/config.yml` 时，可能会使用 config.yml 中的 tunnel ID 而不是指定的 tunnel-name，导致 DNS 记录指向错误的 tunnel。
- **修复方法**：显式使用 tunnel ID 路由 DNS：`cloudflared tunnel route dns <tunnel-id> <hostname>.superkali.online`，然后用 `cloudflared tunnel info <tunnel-id>` 验证。
- 服务器/非交互环境下 `wrangler login` 会卡住或超时，不要使用。统一使用 API Token（`CF_API_TOKEN` 或存储在文件中读取）进行所有 Cloudflare API/Wrangler 操作。

### 后续更新网站

所有项目统一通过 git push 更新，无需手动操作：

```bash
cd /root/<project-dir>
# 修改代码...
git add -A
git commit -m "update: <描述改劸>"
git push origin main

# 等待1-2分钟，Cloudflare自动构建部署
# 验证新部署
curl -s "https://api.cloudflare.com/client/v4/accounts/{{CLOUDFLARE_ACCOUNT_ID}}/pages/projects/<project-name>/deployments" \
  -H "Authorization: Bearer $(cat /root/.cloudflare-pages-token)" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for d in data.get('result', [])[:3]:
    trigger = d.get('deployment_trigger', {})
    stage = d.get('latest_stage', {})
    print(f'{d[\"short_id\"]} | {stage.get(\"name\")} → {stage.get(\"status\")} | {trigger.get(\"metadata\", {}).get(\"commit_message\", \"\")}')
"
```

---

## 自定义域名绑定（必做，部署后立即执行）

所有网站部署完成后，必须绑定自定义域名（xxx.superkali.online），不能只用默认的 *.pages.dev 域名。

### 纯静态网站（流程A）

Pages 项目创建并首次部署成功后，需要两步完成自定义域名绑定：

**步骤1：通过 Pages API 注册域名**（用 Pages token `cfat_`）

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/{{CLOUDFLARE_ACCOUNT_ID}}/pages/projects/<project-name>/domains" \
  -H "Authorization: Bearer $(cat /root/.cloudflare-pages-token)" \
  -H "Content-Type: application/json" \
  -d '{"name":"<custom-domain>.superkali.online"}'
```

**步骤2：添加 CNAME DNS 记录**（Pages token 无 DNS 权限，必须用 tunnel token）

⚠️ Pages API token (`cfat_`) 只有 Pages 操作权限，无法写入 DNS 记录（返回 `code 10000: Authentication error`）。
必须从 cloudflared 的 `cert.pem` 中提取 tunnel token (`cfut_` 前缀)，该 token 有 DNS 写入权限。

**关键：kaka 和 {{INSTANCE_NAME}} 共享同一套 Cloudflare 凭证（Pages token + cert.pem），两台机器都有 cert.pem，直接在本机提取即可，无需 SSH 跨机器。**
- kaka: `/home/ubuntu/.cloudflared/cert.pem`
- {{INSTANCE_NAME}}: `/root/.cloudflared/cert.pem`

```bash
# 提取 tunnel token（本机直接执行，kaka 和 {{INSTANCE_NAME}} 都有 cert.pem）
# 注意路径差异：kaka 用 ~/，{{INSTANCE_NAME}} 用 /root/
TUNNEL_TOKEN=$(python3 -c "
import json, base64, os
cert_path = os.path.expanduser('~/.cloudflared/cert.pem')
with open(cert_path) as f:
    content = f.read()
lines = content.split('\n')
in_token = False
token_b64 = ''
for line in lines:
    if 'BEGIN ARGO TUNNEL TOKEN' in line:
        in_token = True
        continue
    if 'END ARGO TUNNEL TOKEN' in line:
        in_token = False
        continue
    if in_token:
        token_b64 += line.strip()
decoded = json.loads(base64.b64decode(token_b64))
print(decoded['apiToken'])
")

# 添加 CNAME 记录，proxied 必须为 true（橙色云朵）
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/b7c4b682eb2ce38c3f2d30c9a443a25e/dns_records" \
  -H "Authorization: Bearer $TUNNEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"<subdomain>","content":"<project-name>.pages.dev","proxied":true,"ttl":1}'
```

### 前后端分离网站（流程B）

后端通过 Tunnel ingress 绑定自定义域名（已在 B2 步骤完成）。
前端同纯静态流程，通过上述两步绑定自定义域名。

### 验证自定义域名

```bash
# 等待1-2分钟后验证（SSL证书签发需要时间）
curl -s -o /dev/null -w '%{http_code}' https://<custom-domain>.superkali.online
# 期望: 200
```

### 自定义域名命名规则

- 子域名由用户指定，未指定时用项目名作为子域名（如 project-name → project-name.superkali.online）
- 前后端分离时，前端用主域名，后端 API 用 api 前缀（如 novel.superkali.online + api.superkali.online）

---

## Common Pitfalls

1. **Direct Upload项目不能通过API修改source**：如果项目是通过 `wrangler pages deploy`（Direct Upload）创建的，API会返回 `code 8000069: You cannot update the source object in a Direct Uploads project`。解决方法：先通过API DELETE删除项目，再用POST重新创建并设置GitHub source。

2. **GitHub自动构建的构建命令路径错误**：如果前端代码在子目录（如 client/），构建命令必须写 `cd client && npx vite build`，输出目录写 `client/dist`。写错路径会导致构建失败。

3. **Tunnel配置改了忘重启**：修改 `/etc/cloudflared/config.yml` 后必须重启 cloudflared，否则新规则不生效。注意：cloudflared 注册为 systemd 服务后，配置文件在 `/etc/cloudflared/config.yml`（不是 `~/.cloudflared/config.yml`）。`cloudflared service install` 会自动复制配置到 /etc/cloudflared/。

4. **端口冲突**：新后端服务必须检查端口是否被占用。建议从3001开始递增分配。

5. **API地址写成了localhost**：前端构建时 API 地址必须用公网域名（如 api.xxx.superkali.online），不能用 localhost，否则用户浏览器会请求自己电脑的 localhost。

6. **Token明文写在脚本里**：Token 应存于 `/root/.cloudflare-pages-token`（chmod 600），脚本从中读取，不要提交到 Git。

7. **gh CLI交互式登录在非交互环境失败**：`gh auth login` 需要交互式终端，在服务器非交互环境会失败。正确方式是将 Token 存到文件，用 `GH_TOKEN=$(cat /root/.github-token) gh <command>` 调用。

8. **GitHub下载超时**：服务器直连 github.com 下载可能超时（如 gh CLI 安装）。使用国内镜像 `gh-proxy.com` 替代：`https://gh-proxy.com/https://github.com/...`。

9. **影响已有项目**：每次部署新网站必须新建独立的 Pages 项目和 Tunnel ingress 规则，绝不能修改已有项目的配置。

10. **Token verify 端点会产生假阴性 — 不要用它做部署前检查**：Cloudflare 的 `/user/tokens/verify` 端点需要用户级权限（User > API Tokens > Read），而仅含 `Account > Cloudflare Pages > Edit` 权限的令牌会返回 `code 1000: Invalid API Token`，**即使令牌完全有效**。这会导致误判令牌已失效、不必要地要求用户重新生成令牌。**正确做法：用 Pages projects 列表端点验证**：
    ```bash
    # ✅ 正确：用 Pages API 验证令牌（与部署用相同的权限）
    curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/pages/projects" \
      -H "Authorization: Bearer $(cat /root/.cloudflare-pages-token)"
    # 如果 success: true → 令牌对 Pages 部署有效，可以继续
    # 如果 success: false → 令牌确实失效，需要用户重新生成

    # ❌ 错误：不要用 /user/tokens/verify 验证 Pages-only 令牌
    # curl -s https://api.cloudflare.com/client/v4/user/tokens/verify -H "Authorization: Bearer ..."
    # ↑ Pages-only 令牌会返回 code 1000 假阴性
    ```
    令牌格式以 `cfat_` 开头，正常长度约 53 字符。常见错误码见 `references/cloudflare-api-errors.md`。

11. **terminal工具处理token时的转义问题**：在shell命令中使用 `$(cat /root/.cloudflare-pages-token)` 读取token时，如果token包含特殊字符可能导致shell解析错误。推荐使用 `execute_code` 工具通过Python读取token文件并调用API，避免shell转义问题。

12. **cloudflared service install 后配置文件路径变化**：执行 `cloudflared service install` 注册 systemd 服务后，配置文件从 `~/.cloudflared/config.yml` 复制到 `/etc/cloudflared/config.yml`。后续修改 ingress 规则必须编辑 `/etc/cloudflared/config.yml`（不是 `~/.cloudflared/config.yml`），否则修改不生效。修改后 `systemctl restart cloudflared` 即可。

13. **Pages API token 无法写入 DNS 记录**：`cfat_` 前缀的 Pages token 只有 Pages 操作权限（创建项目、绑定域名），调用 `POST /zones/{id}/dns_records` 会返回 `code 10000: Authentication error`。绑定自定义域名需要两步：先用 Pages token 通过 Pages API 注册域名，再用 tunnel token（从 `cert.pem` 提取的 `cfut_` 前缀 token）添加 CNAME DNS 记录。提取方法见"自定义域名绑定"章节。

14. **Pages 自定义域名的 CNAME 必须 proxied=true（橙色云朵）**：如果 CNAME 设为非代理模式（灰色云朵，`proxied: false`），访问会返回 HTTP 522（Connection timed out）。Pages 自定义域名必须通过 Cloudflare 代理才能正常工作。

15. **Pages Functions 的 wrangler.toml 不能同时包含 `main` 和 `pages_build_output_dir`**：当使用 `_worker.js` 作为 Pages Functions 入口时，wrangler.toml 中只能保留 `pages_build_output_dir = "static"`（指向 `_worker.js` 所在的输出目录），必须删除 `main = "static/_worker.js"`。两者并存会导致构建失败：`Configuration file cannot contain both "main" and "pages_build_output_dir" concurrently`。

16. **Pages Functions 环境变量建议用 `wrangler pages secret put` 设置**：通过 Cloudflare API 设置 `deployment_configs.production.env_vars` 后，虽然项目配置中能看到变量，但实际运行 Pages Functions 时可能无法注入到 `env` 对象中（仅出现 `CF_PAGES_*` 系统变量）。**可靠做法**是使用 wrangler CLI 设置加密变量：
    ```bash
    CF_API_TOKEN=$(cat /root/.cloudflare-pages-token) npx wrangler pages secret put API_URL --project-name <project-name>
    # 然后输入变量值，再 push 一次触发新部署
    ```
    设置 secret 后必须重新 push 触发部署，Variables 才会在 Functions 运行时通过 `env.API_URL` 读取到。

17. **Pages Functions 两种写法**：(a) `_worker.js` 单文件模式 — 需要 `wrangler.toml` 配合 `pages_build_output_dir`，注意 pitfall #15 的冲突问题；(b) `functions/` 目录模式（推荐）— 文件即路由（如 `functions/api/chat.js` → `/api/chat`），无需 `wrangler.toml`，无需任何构建配置，直接 push 即可被 Cloudflare 自动识别部署。目录模式更简单，新项目优先使用。

18. **Pages Functions CORS 预检：`onRequestPost` 不处理 OPTIONS → 手机端 405**：`onRequestPost` 只响应 POST 请求，浏览器（特别是手机端）发送的 CORS 预检请求（OPTIONS 方法）会直接返回 405 Method Not Allowed，导致前端 fetch 报 `HTTP 405` 错误。**修复**：将 `onRequestPost` 改为 `onRequest`，在函数开头显式处理 OPTIONS 和方法检查：
    ```javascript
    export async function onRequest({ request, env }) {
      const cors = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      };
      if (request.method === 'OPTIONS') return new Response(null, { headers: cors });
      if (request.method !== 'POST') return new Response('Method Not Allowed', { status: 405, headers: cors });
      // ... 正常逻辑
    }
    ```
    同理 GET 路由用 `onRequest` 替换 `onRequestGet`，方法检查改为 `!== 'GET'`。**服务端 curl 测试正常但浏览器报 405 时，优先排查此问题**。

19. **SSE 流式代理：Cloudflare Pages Functions 透传 SSE 需注意格式**：当 Pages Functions 代理第三方 API 的 SSE 流式响应时，`apiResponse.body` 可直接作为 `new Response(apiResponse.body, { headers: { 'Content-Type': 'text/event-stream', ... } })` 透传。但前端解析时需注意：(a) SSE 事件以**双换行 `\n\n`** 分隔，不是单换行；(b) `data:` 行可能跨多行需要拼接；(c) 某些 API（如影刀 Power API）使用**双层 JSON**——外层 SSE data 是 JSON，其 `data` 字段又是一个 JSON 字符串，需要二次 `JSON.parse`。

20. **Live2D / 大型前端资源 CDN 在国内不可靠**：jsdelivr 默认 CDN（`cdn.jsdelivr.net`）在中国大陆移动网络下可能加载失败。解决方案：(a) 添加多个 CDN 镜像（`fastly.jsdelivr.net`、`gcore.jsdelivr.net`）作为 fallback；(b) 对资源加载加 `Promise.race` 超时机制（如 8 秒），防止单个 CDN 卡住整个页面渲染；(c) 所有 CDN 都失败时显示降级提示，不阻塞核心功能（如聊天）。

21. **前端未校验第三方 API 错误信封 → 通用错误掩盖真实原因**：Pages Functions 代理第三方 API 时，第三方返回的错误响应（如限流 `{"code":429,"success":false,"msg":"每日创建会话数已达上限"}`）会被透传给前端。如果前端直接取 `data.data.xxx` 而不先检查 `data.success`/`data.code`，会得到 "未获取到字段" 的通用错误，掩盖真实原因（限流、鉴权失败、参数错误等）。**修复**：前端 fetch 后先校验响应信封，失败时直接展示第三方返回的 `msg`/`error` 字段：\n    ```javascript\n    const data = await response.json();\n    if (data.success === false || data.code !== 0) {\n      throw new Error(data.msg || data.error || `API错误: ${data.code}`);\n    }\n    // 安全提取字段\n    this.conversationUuid = data.data?.conversationUuid;\n    ```\n    **调试技巧**：前端报"创建失败"/"未获取到字段"类错误时，直接 `curl -s -X POST <域名>/api/<endpoint>` 看第三方真实返回，快速区分是代理层问题还是第三方 API 问题。

## Tunnel 部署架构选择

前后端分离项目有两种 Cloudflare Tunnel 架构，按项目隔离需求选择：

### 架构1：共享 Tunnel（适合同一台服务器上的多个小项目）

所有项目共用同一个 cloudflared tunnel，所有 ingress 规则写在同一个配置文件里。

- 配置文件：`/etc/cloudflared/config.yml`（systemd 注册后的路径）
- 优点：少开进程，管理集中
- 缺点：修改任一项目的 ingress 可能影响其他项目；重启 tunnel 会短暂影响所有项目

### 架构2：独立 Tunnel（推荐，项目完全隔离）

每个项目创建独立的 tunnel、独立的配置文件、独立的 systemd 服务。

- 配置文件：`~/.cloudflared/<project>.yml`
- 优点：项目之间零影响，重启/调整只影响当前项目
- 缺点：每个项目多一个 cloudflared 进程（内存占用约 15-20MB）

**独立 Tunnel 完整示例**：

```bash
# 1. 创建新 tunnel
cloudflared tunnel create <project-name>
# 记录输出的 tunnel ID，如 8d35f9bc-1d37-45e9-8c3f-a797a6f51e71

# 2. 编写项目专属配置
cat > ~/.cloudflared/<project-name>.yml << 'EOF'
tunnel: <tunnel-id>
credentials-file: /home/ubuntu/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: <api-subdomain>.superkali.online
    service: http://127.0.0.1:<backend-port>
  - service: http_status:404
EOF

# 3. 添加 DNS 记录（建议显式用 tunnel ID，避免默认 config.yml 干扰）
cloudflared tunnel route dns <tunnel-id> <api-subdomain>.superkali.online

# 4. 创建独立 systemd 服务
cat > /etc/systemd/system/cloudflared-<project-name>.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel for <project-name>
After=network.target

[Service]
Type=notify
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/ubuntu/.cloudflared/<project-name>.yml run
Restart=always
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now cloudflared-<project-name>
```

---

## Python/Flask 后端部署示例

```bash
# 1. 同步代码到 /opt/<project-name>
sudo mkdir -p /opt/<project-name>
sudo rsync -av --exclude=venv --exclude=.git /home/ubuntu/<project-dir>/ /opt/<project-name>/
sudo chown -R ubuntu:ubuntu /opt/<project-name>

# 2. 创建 venv 并安装依赖
cd /opt/<project-name>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 创建 systemd 服务
cat > /etc/systemd/system/<project-name>.service << 'EOF'
[Unit]
Description=<project-name> Flask backend
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/<project-name>
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/<project-name>/venv/bin/gunicorn -w 2 -b 127.0.0.1:<port> app:app
Restart=on-failure
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now <project-name>
```

## Tunnel 403 诊断指南

部署前后端分离网站时，通过 Cloudflare Tunnel 访问前端/后端可能出现 403 Forbidden。有两种不同原因，必须先区分再修：

### 原因1：Vite preview allowedHosts（最常见）

**症状**：HTTP 403，响应体约 163 字节，包含 "Blocked request" 和 "allowedHosts"。

Vite preview 默认只允许 localhost 的 Host 头。通过 Tunnel 自定义域名访问时 Host 不匹配，被 Vite 安全机制拦截。

**修复**：在 vite.config.ts 中添加：

```typescript
export default defineConfig({
  preview: {
    host: true,
    port: 5173,
    allowedHosts: ["<your-subdomain>.superkali.online"],
  },
});
```

或用 `allowedHosts: true` 允许所有（Cloudflare Tunnel 后端可接受）。修改后必须重启 vite preview。

### 原因2：SSL/TLS mode 不匹配

**症状**：HTTP 403 或 525 SSL handshake failed，响应体是 Cloudflare 错误页（大 HTML）。

Cloudflare edge 用 HTTPS 连 origin，但 origin 只服务 HTTP。

**修复**：在 Cloudflare Dashboard 把域名 SSL/TLS mode 从 Full (Strict) 改为 Full 或 Flexible。

### 诊断顺序

1. 先看响应体：含 "Blocked request" → 原因1（allowedHosts）
2. 响应体是大 HTML 错误页 → 原因2（SSL/TLS）
3. 检查本地服务是否运行：curl http://localhost:<port>
4. 检查 config.yml 路由到正确端口和 http 协议
5. 检查 cloudflared 日志

## References

- `references/cloudflare-api-errors.md` — Cloudflare API 常见错误码
- `references/low-memory-nodejs-deployment.md` — 低内存服务器 Node.js 全栈部署 playbook（Swap、内存限制构建、Prisma 同步）
- `references/cloudflare-pages-hybrid-deployment.md` — 前端 Pages + 后端 Tunnel 混合部署模式详解
- `templates/deploy-pages.sh` — 一键 Cloudflare Pages 部署脚本
- `templates/start-prod.sh` — 生产启动脚本模板（检查构建产物、杀旧进程、启动+健康检查）

## Verification Checklist

- [ ] 网站类型已确认（纯静态 / 静态+Functions代理 / 前后端分离）
- [ ] **Cloudflare API Token 已验证有效**（用 Pages projects 列表端点验证，不要用 `/user/tokens/verify`）
- [ ] GitHub仓库已创建，代码已push到main分支
- [ ] Pages项目已通过API创建，source已设置为github（验证result.source.type == "github"）
- [ ] 首次部署已触发（push后检查部署状态为 github:push → success）
- [ ] **Functions密钥已用 `wrangler pages secret put` 设置**（仅流程C）
- [ ] **设置secret后已重新push触发新部署**（仅流程C，否则env变量不生效）
- [ ] 端口已检查无冲突（仅前后端分离）
- [ ] 后端服务启动并守护（仅前后端分离）
- [ ] Tunnel ingress 规则已添加并重启
- [ ] 前端构建产物中 API 地址正确（仅前后端分离）
- [ ] 前端 URL 可访问（HTTP 200）
- [ ] **Functions代理正常工作**（仅流程C，curl /api/xxx 不返回配置错误）
- [ ] API URL 可达并返回数据（仅前后端分离）
- [ ] 没有修改任何已有项目的配置
- [ ] **自定义域名已绑定并验证可访问**（xxx.superkali.online，HTTP 200）
- [ ] 飞书部署档案已创建并归档（加载 website-operations 技能，按"部署后文档创建"步骤执行）
- [ ] 网站登记表已更新（更新 website-operations 技能的 references/site-registry.md）
