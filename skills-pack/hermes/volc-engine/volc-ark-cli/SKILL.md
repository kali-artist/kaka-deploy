---
name: volc-ark-cli
version: 0.1.0
description: "Volcengine Ark CLI (arkcli) — 官方CLI工具，用于火山方舟平台操作：套餐查询、用量统计、模型列表查看、计费等。⚠️ 模型切换功能CLI和API均不支持，但可通过Playwright自动化切换（已验证）。"
author: kaka
---

# Volcengine Ark CLI (arkcli)

## 概述

火山方舟官方CLI工具，通过原生命令行操作Ark平台，替代之前的浏览器自动化（Playwright）方案。

**替代关系：**
- `volc-ark-quota-session` 技能 → `arkcli plans get` + `arkcli usage stats`
- ⚠️ `switch-coding-plan-model` 技能已被删除，但 arkcli **无法替代其模型切换功能**（详见下方坑#1）

## 安装

```bash
npm i @volcengine/ark-cli@latest -g
```

## ⚠️ PATH 问题

npm全局安装后 `arkcli` 不在系统PATH中。Hermes环境下安装位置为：

```
/home/ubuntu/.hermes/node/bin/arkcli
```

**已持久化方案（写入 ~/.bashrc）：**
```bash
export PATH="/home/ubuntu/.hermes/node/bin:$PATH"
export ARK_API_KEY="ark-xxxx"
```

新终端会话自动加载，无需每次手动 export。

## 配置文件

- 配置路径：`~/.arkcli/config.yaml`
- 运行状态检查：`arkcli doctor`

## 认证

CLI需要认证后才能使用。两种方式：

### 方式1：API Key（仅限身份认证，功能受限）

通过 `--api-key` 全局参数或 `ARK_API_KEY` 环境变量传入：

```bash
# 命令行临时使用
arkcli --api-key "ark-xxxx" auth whoami

# 环境变量持久化（写入 ~/.bashrc）
export ARK_API_KEY="ark-xxxx"
```

⚠️ **重要限制：** API Key 只能完成身份认证（`auth status` / `auth whoami` 返回 `logged_in: true`），但大部分核心操作（`plans get`、`models list`、`usage stats`、`plans model-list`）都需要 SSO STS 令牌，仅靠 API Key 会报错：
> `requires Volc SSO STS, please run arkcli auth login volc-sso`

`arkcli auth apikey` 子命令本身也需要先完成 SSO 登录才能使用，不能单独用来认证。

### 方式2：SSO登录（完整功能，必须完成）

```bash
# 有浏览器环境
arkcli auth login volc-sso

# 无浏览器环境（沙箱/服务器，推荐）
arkcli auth login --no-browser
# 输出一个授权URL（10分钟有效），用户在任意设备打开并授权后获得base64授权码
# 再用授权码完成登录：
arkcli auth login --no-browser --code <base64授权码>
```

⚠️ `--no-browser` 是 `auth login` 的参数，不是 `auth login volc-sso` 的参数。

### 检查认证状态
```bash
arkcli auth status    # 查看认证方式和登录状态
arkcli auth whoami    # 查看当前身份（返回 project_name, region 等）
arkcli doctor         # 检查CLI运行状态
```

### 当前环境配置状态（✅ 全部完成）
- ✅ arkcli 已安装（v1.0.1），PATH 和 ARK_API_KEY 已写入 ~/.bashrc
- ✅ API Key 认证可用（身份认证通过）
- ✅ SSO 无浏览器登录已完成（账号 kali1442，个人认证，root 用户）
- ✅ Profile 已创建：`platform_cn-beijing_default`（type=platform, region=cn-beijing, project=default）
- ✅ `plans get`、`models list`、`plans model-list`、`usage stats` 等命令全部可用

### 🔴 关键坑：SSO 登录后的非交互式 Profile 创建

SSO `--no-browser --code` 交换令牌成功后，CLI 会尝试拉取项目列表并让用户选择项目（Project），但在非交互式终端（agent/沙箱）中会报错：

> `激活火山身份失败: BuildFirstProfileSet: Step 3 (project) cancelled: 非交互式终端`

**解决方案：** SSO 令牌已存储到 `~/.arkcli/.env`，只需手动创建 profile 即可：

```bash
arkcli profile create \
  --type platform \
  --project default \
  --region cn-beijing \
  --default-api-key "ark-xxxx" \
  --set-default \
  --no-interactive
```

完成后所有命令均可正常使用，无需再传 `--project-name`。

### ⚠️ SSO 令牌过期

SSO 令牌有效期约 48 小时。过期后需重新执行 `arkcli auth login --no-browser` 流程。`arkcli auth status` 的 `volc_sso.remaining` 字段可查看剩余时间。

## 核心命令

### 套餐管理（替代 volc-ark-quota-session）
```bash
# 查看当前账号订阅信息
arkcli plans get

# 列出套餐支持的模型及当前ark-latest-model
arkcli plans model-list

# 购买套餐
arkcli plans buy

# 续费
arkcli plans renew
```

### 用量统计（替代 volc-ark-quota-session）
```bash
# 查询用量
arkcli usage stats --start 2026-04-01 --end 2026-04-14
```

### 模型管理（替代 switch-coding-plan-model）
```bash
# 搜索模型
arkcli models search seedream

# 获取模型详情
arkcli models get doubao-seed-2-0-pro-260215
```

### 资源查看
```bash
# 列出可用资源ID
arkcli resources list
```

### 计费与定价
```bash
arkcli billing       # 计费命令
arkcli pricing       # 定价命令
```

### 其他实用命令
```bash
# 多模态生成（图片/视频）
arkcli +gen --model doubao-seedream-5-0-260128 --size 1920x1920 "提示词"

# 聊天/推理
arkcli +chat

# 多模态理解（图片/文档/视频）
arkcli +understand

# 代码示例
arkcli +code-example --model doubao-seed-2-0-pro-260215

# 部署endpoint
arkcli +deploy --model doubao-seed-2-0-pro-260215 --name my-endpoint

# 原始API探索
arkcli api model.list_foundation_models --params '{"PageSize":1}'
```

## 全局参数

| 参数 | 说明 |
|------|------|
| `--profile` | 指定配置profile |
| `--api-key` | 覆盖API Key |
| `--region` | 覆盖区域 |
| `--format` | 输出格式（默认json） |
| `--debug` | 打印请求/响应详情到stderr |
| `--dry-run` | 预览不执行 |
| `--env` | 环境配置：prod/stg |
| `--transform` | GJSON路径转换输出 |
| `--page-all` | 自动获取所有分页 |

## 🔴 关键限制：Agent Plan 模型切换不可通过 CLI/API 完成（但可用 Playwright 自动化）

arkcli 和 Volcengine OpenAPI **均不支持**切换 Agent Plan 的 `ark-latest-model`（即套餐当前使用的模型）。但可通过 Playwright 自动化操作网页控制台完成切换（见下方"切换方式1"）。

### 已验证的事实（2026-07-01）

1. **arkcli 无切换命令**：`arkcli plans model-list` 只能列出可用模型，不能切换。arkcli 所有子命令中没有任何 model switch/set/change 相关操作。

2. **Volcengine OpenAPI 无对应 action**：使用 STS 凭证 + 签名调用 API version `2024-01-01`，测试了以下 8 个候选 action 名称，全部返回 404 `InvalidActionOrVersion`：
   - `SwitchAgentPlanLatestModel`
   - `EnableAgentPlanLatestModel`
   - `SetAgentPlanLatestModel`
   - `ModifyAgentPlanLatestModel`
   - `UpdateAgentPlanLatestModel`
   - `OpenAgentPlanLatestModel`
   - `ChooseAgentPlanLatestModel`
   - `SelectAgentPlanLatestModel`

3. **唯一方案：网页控制台手动切换**。需要登录火山引擎控制台（https://console.volcengine.com/ark），在 Agent Plan 页面手动切换模型。由于需要 SSO 登录，使用 `human-assisted-browser-login` 技能协助用户完成登录后操作。

### 切换方式1：Playwright 自动化切换（推荐，无需人工操作）

使用 Playwright + 已登录的浏览器持久化 profile 自动切换模型，无需用户手动点击。

**前提条件：** 浏览器 profile 已完成火山引擎 SSO 登录（首次需用 `human-assisted-browser-login` 技能协助登录）。

**关键实现细节（已验证 2026-07-01）：**

1. **浏览器配置：**
   - Chromium 路径：`/snap/bin/chromium`
   - Profile 目录：`/tmp/stagehand-volc-ark/browser-profile`（或 `~/snap/chromium/common/hermes-browser-profiles/volc-ark`）
   - 参数：`--disable-blink-features=AutomationControlled`
   - Headless 模式可用

2. **目标页面 URL：**
   ```
   https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&advancedActiveKey=subscribe&tab=codingPlan
   ```
   页面加载后需等待 10-12 秒（SPA 异步渲染）。

3. **定位模型 radio 按钮（Arco Design 组件库）：**
   - 模型名称（如 "GLM-5.2"）是纯文本节点
   - Radio 按钮在模型名称上方第 5 层父元素中（`label.arco-radio` + `input[type="radio"]`）
   - 需要用 TreeWalker 遍历文本节点找到目标模型，再向上遍历 DOM 找到 radio
   - **点击 `label.arco-radio` 元素**（不是直接点击 input），点击更可靠

4. **验证切换成功：**
   - 页面验证：检查 radio 的 `checked` 状态，模型卡片文本应从"未启用"变为"已启用"
   - **截图发给用户**（用户明确要求的工作流：切换 → 确认成功 → 截图发送，不做多余 API 测试）
   - API 验证（仅在用户明确要求时）：用 curl 调用 `https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions`，`model` 参数填目标模型名（如 `glm-5.2`），返回正常即切换成功

5. **注意事项：**
   - GLM-5.2 等推理模型会消耗大量 reasoning tokens（简单请求也可能用 600+ tokens）
   - API Key 从 `~/.arkcli/config.yaml` 的 `api_key` 字段获取
   - Coding Plan API BaseURL：`https://ark.cn-beijing.volces.com/api/coding/v3`

### 切换方式2：手动操作（备用）

1. 使用 `human-assisted-browser-login` 技能登录火山引擎控制台
2. 导航到方舟 → Agent Plan 管理页面
3. 找到目标模型，点击切换/启用
4. 确认切换成功

## 与旧技能的关系

| 旧技能 | 旧方式 | arkcli 替代 | 说明 |
|--------|--------|------------|------|
| `switch-coding-plan-model` | Playwright浏览器自动化点击radio按钮 | ⚠️ **无法替代** | arkcli 只能列出模型 (`plans model-list`)，不能切换。仍需浏览器自动化或手动操作 |
| `volc-ark-quota-session` | Playwright打开控制台页面解析文本 | ✅ `arkcli plans get` + `arkcli usage stats` | 套餐和用量查询已完全替代 |

## 旧技能已删除

`switch-coding-plan-model`（浏览器自动化切换模型）和 `volc-ark-quota-session`（浏览器自动化查套餐）已于 2026-06-30 删除，arkcli 为唯一方案。

## 完成状态

- [x] 安装 arkcli 并配置 PATH（写入 ~/.bashrc）
- [x] 配置 ARK_API_KEY 环境变量（写入 ~/.bashrc）
- [x] 验证 API Key 身份认证可用
- [x] 完成 SSO 无浏览器登录（`arkcli auth login --no-browser` + `--code`）
- [x] SSO 认证后创建 profile（`arkcli profile create --no-interactive`）
- [x] 验证 `arkcli plans get` → Coding Plan Pro, Running
- [x] 验证 `arkcli plans model-list` → 14个可用模型
- [x] 验证 `arkcli models list` → 90个基础模型
- [x] 旧技能 `switch-coding-plan-model` 和 `volc-ark-quota-session` 已删除
