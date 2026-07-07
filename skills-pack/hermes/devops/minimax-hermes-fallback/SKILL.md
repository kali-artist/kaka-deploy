---
name: minimax-hermes-fallback
description: Configure MiniMax CLI credentials as Hermes Agent fallback provider, especially mmx region=cn.
version: 1.0.0
author: kaka
category: devops
tags: [hermes, minimax, mmx, fallback, provider]
trigger: |
  Load when diagnosing or configuring MiniMax/mmx CLI with Hermes Agent, Hermes fallback providers, or errors involving kimi-coding/kimi-k2.5 fallback 404.
---

# MiniMax CLI → Hermes fallback configuration

## Known environment facts
- `mmx` CLI path: `~/.local/bin/mmx`.
- `mmx` stores auth at `~/.mmx/config.json`.
- If `~/.mmx/config.json` has `region: cn`, Hermes should use:
  - provider: `minimax-cn`
  - model: `MiniMax-M2.7`
  - env key: `MINIMAX_CN_API_KEY`
  - base URL: `https://api.minimaxi.com/anthropic`
- The old fallback `kimi-coding` + `kimi-k2.5` can return HTTP 404 in this setup and should not be used as the active fallback unless revalidated.

## Diagnose
```bash
~/.local/bin/mmx auth status --output json --non-interactive
~/.local/bin/mmx text chat --model MiniMax-M2.7 --message '只输出OK' --max-tokens 50 --output json --non-interactive --timeout 60
hermes fallback list
hermes auth status minimax-cn
```

## Low-risk fix workflow
1. Back up config files:
```bash
TS=$(date +%Y%m%d_%H%M%S)
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak_minimax_$TS
cp ~/.hermes/.env ~/.hermes/.env.bak_minimax_$TS
```
2. Read `~/.mmx/config.json`; copy its API key into the matching Hermes env var:
   - `region=cn` → `MINIMAX_CN_API_KEY` and `MINIMAX_CN_BASE_URL=https://api.minimaxi.com/anthropic`
   - otherwise → `MINIMAX_API_KEY` and `MINIMAX_BASE_URL=https://api.minimax.io/anthropic`
3. Set `~/.hermes/config.yaml` fallback chain to:
```yaml
fallback_providers:
- provider: minimax-cn
  model: MiniMax-M2.7
```
   Use `provider: minimax` instead only for non-CN region.
4. Verify:
```bash
hermes fallback list
hermes auth status minimax-cn
hermes -z '只输出 OK 两个字母，不要解释' --provider minimax-cn -m MiniMax-M2.7 --ignore-rules
python3 ~/.hermes/skills/devops/permission-management/scripts/audit.py --quiet
```

## API Key 审计与对比

MiniMax API Key 可能存在于三个不同位置，且可能来自不同账号：

| 位置 | 配置文件 | 环境变量/字段 |
|------|---------|-------------|
| MCP 服务 | `~/.hermes/config.yaml` → `mcp_servers.minimax_mcp.env.MINIMAX_API_KEY` | `MINIMAX_API_KEY` |
| mmx 联网搜索 | `~/.mmx/config.json` → `api_key` | — |
| 备用模型 | `~/.hermes/.env` | `MINIMAX_CN_API_KEY` |

**审计命令（脱敏比对）：**
```bash
python3 -c "
import yaml, json, os
# MCP key
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)
mcp_key = cfg['mcp_servers']['minimax_mcp']['env']['MINIMAX_API_KEY']
# mmx key
with open(os.path.expanduser('~/.mmx/config.json')) as f:
    mmx = json.load(f)
mmx_key = mmx['api_key']
# fallback key
from pathlib import Path
env = Path('~/.hermes/.env').expanduser().read_text()
import re
m = re.search(r'MINIMAX_CN_API_KEY=*** env)
cn_key = m.group(1).strip() if m else ''
print(f'MCP:   {mcp_key[:10]}...{mcp_key[-4:]}')
print(f'mmx:   {mmx_key[:10]}...{mmx_key[-4:]}')
print(f'fallback: {cn_key[:10]}...{cn_key[-4:]}')
print(f'MCP == mmx: {mcp_key == mmx_key}')
print(f'MCP == fallback: {mcp_key == cn_key}')
print(f'mmx == fallback: {mmx_key == cn_key}')
"
```

**替换备用模型 key 的方法：**
从 `~/.hermes/config.yaml` 读取 MCP 服务的完整 `MINIMAX_API_KEY`，写入 `~/.hermes/.env` 的 `MINIMAX_CN_API_KEY` 字段即可。

## Pitfalls
- Do not use `/v1` as MiniMax base URL for Hermes `minimax-cn`; Hermes uses Anthropic Messages transport, so endpoint must be `/anthropic`.
- Do not print API keys in chat or logs; mask secrets.
- Do not use recursive permission changes while fixing this.
- 三个位置的 key 可能来自不同账号，审计时注意区分所有权，避免误覆盖。