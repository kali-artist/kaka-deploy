---
name: kaka-gateway-admin
description: "kaka多用户网关管理 - 权限架构审查、多Profile隔离机制、Soul配置、Skills/Hooks/MCP系统管理"
version: 1.0.0
author: 卡力
tags: [kaka, gateway, multi-profile, permissions, soul, skills, hooks, mcp, administration]
related_skills: ["hermes-agent", "native-mcp", "permission-governance"]
trigger: |
  当用户询问以下内容时自动加载此技能：
  - 权限管理、授权配置、permission management
  - 多profile架构、隔离机制、multi-tenant
  - Soul配置、人格设置、SOUL.md
  - Skills管理、Hook系统、MCP集成
  - 网关运行状态、进程架构、gateway architecture
  - 系统安全设置、命令白名单、command allowlist
  - 权限断层、工具级权限、pre_tool_call、MCP安全设计
  - 用户-工具绑定、MCP白名单、三层防护架构
  - 平台凭证配置、APP ID、APP Secret、飞书配置、微信配置
  - API密钥更换、环境变量修改、.env文件
  - MCP配置同步、把MCP同步给、给小猫同步、给tiao同步
  - 清理Profile技能目录、profile技能清理、小猫清理技能
  - 清理临时文件、整理用户目录文件、临时目录创建、临时文件存储规则
  - 给少佐小猫/其他profile创建专属目录
---

# 🔐 kaka 多用户网关管理技能

## 📋 适用场景

当需要审查、理解或管理kaka的多Profile网关架构时使用此技能，包括：
- 权限系统和授权配置审查
- 多Profile隔离机制理解
- Soul人格配置管理
- Skills/Hooks/MCP系统配置
- 网关运行架构检查

---

## 🔄 执行层级与权限控制架构

### 消息处理执行顺序（由外到内）
```
消息到达 → Gateway Hook → Tool Call Hook → Soul规则 → Skill/MCP加载 → Tool执行 → LLM推理
  ↓          ↓              ↓            ↓         ↓            ↓
 可以中断   可以中断      可以中断      软约束     工具注册      实际执行
```

> ⚠️ **关键安全漏洞注意**：原始设计缺少 Tool Call Hook 层，存在严重权限断层！只要消息通过了Gateway Hook，后面就能调用所有工具/MCP服务，完全不受控。

**执行层级说明（外层优先级最高）：**

| 层级 | 名称 | 能力 | 能否中断消息 | 权限级别 |
|------|------|------|-------------|----------|
| **第1层** | Gateway Hook | 消息拦截、内容过滤、路由分发 | ✅ 可以直接拦截 | 最强 |
| **第2层** | **Tool Call Hook ✅ 新增** | **工具级权限控制** - 检查用户能否调用特定工具/MCP | ✅ 可以拒绝调用 | 强 |
| **第3层** | Profile | 进程隔离、独立配置、独立账号 | ✅ 物理隔离 | 强 |
| **第4层** | Config | 启用/禁用模块、白名单配置 | ⚠️ 静态配置 | 中 |
| **第5层** | Soul | 人格规则、行为准则、软约束 | ⚠️ 依赖LLM遵守 | 弱 |

### 五层权限控制机制（由外到内，外层优先）

**第1层 - Gateway Hook层（最强控制）**
- 触发时机：`pre_gateway_dispatch` - 消息到达网关后，交给Agent前
- 能力：可以直接拦截、拒绝、修改消息
- 配置：Hook的 `allowed_skills`、`allowed_mcp_servers` 白名单
- 特点：不依赖LLM，硬控制，100%可靠

**第2层 - Tool Call Hook层（关键防护 ✅ 必须启用）**
- 触发时机：`pre_tool_call` - Agent调用任何工具前触发
- 能力：检查用户能否调用特定工具、MCP服务
- 配置：工具白名单、MCP服务白名单、用户-工具绑定
- 特点：填补权限断层，100%硬控制，**必须实现**

**核心实现代码：**
```python
# HOOK.yaml 同时监听两个事件
events:
  - pre_gateway_dispatch  # 第1层：消息入口检查
  - pre_tool_call         # 第2层：工具调用前检查

# handler.py 核心逻辑
async def handle_pre_tool_call(event_type: str, context: dict):
    tool_name = context.get('tool_name')  # terminal, mcp_xxx_yyy
    user_id = context.get('user_id')
    
    # 1. 管理员完全放行
    if user_id in ADMIN_USER_IDS:
        return {"action": "allow"}
    
    # 2. 非管理员禁止调用敏感工具
    SENSITIVE_TOOLS = ['terminal', 'write_file', 'patch']
    if tool_name in SENSITIVE_TOOLS:
        return {"action": "deny", "reason": "仅限管理员使用"}
    
    # 3. MCP服务白名单控制
    if tool_name.startswith('mcp_'):
        mcp_server = tool_name.split('_')[1]
        if mcp_server not in ALLOWED_MCP_FOR_NORMAL:
            return {"action": "deny", "reason": f"MCP {mcp_server} 未开放"}
    
    # 4. 用户-工具绑定检查
    user_allowed_tools = USER_TOOL_BINDINGS.get(user_id, [])
    if user_allowed_tools and tool_name not in user_allowed_tools:
        return {"action": "deny", "reason": f"您只能调用: {user_allowed_tools}"}
    
    return {"action": "allow"}
```

**第3层 - Profile层（强隔离）**
- 机制：独立Gateway进程 + 独立工作目录
- 能力：物理隔离配置、记忆、会话、平台账号
- 配置：`profiles/{name}/` 目录完全独立
- 特点：不同用户之间完全隔离，互不影响

**第3层 - Config层（中粒度）**
- 配置：`config.yaml` 中的各种开关和白名单
- 能力：运行时启用/禁用模块、设置权限边界
- 包括：`security`、`approvals`、`command_allowlist`、`allowed_skills`
- 特点：静态配置，Agent启动时生效

**第4层 - Soul层（软约束）**
- 配置：`SOUL.md` 中的规则和指令
- 能力：依赖LLM理解和遵守规则
- 包括：身份识别、输出过滤、行为准则
- 特点：灵活但不可靠，需要配合外层硬控制

### Skill vs MCP 权限控制对比

| 维度 | Skill权限控制 | MCP权限控制 |
|------|--------------|-------------|
| Hook层 | `allowed_skills` 白名单 | `allowed_mcp_servers` 白名单 |
| Profile层 | 独立 `skills/` 目录 | 独立 `mcp_servers` 配置 |
| Config层 | `skills` 配置节点 | - |
| Soul层 | 软约束规则 | 软约束规则 |

---

## 🏗️ 整体架构概览

kaka运行**3个完全独立的Hermes Gateway进程**，形成多租户隔离架构：

| Profile | 用途 | 微信账号 | 安全等级 | 工作目录 |
|---------|------|----------|----------|----------|
| **default** | 卡力专属助手kaka | `{{WECHAT_USER_ID}}` | 最高 - 完整访问 | `~/.hermes/` |
| **tiao** | 条条专属电子小猫 | `64f3eba0ddd7` | 中 - 目录隔离 | `~/.hermes/profiles/tiao/` |
| **hang** | 独立Profile | `258de6e447d6` | 最高 - 强输出过滤 | `~/.hermes/profiles/hang/` |

---

## 👻 Soul 人格系统

### 配置文件位置
```
~/.hermes/SOUL.md                    # default profile (kaka)
~/.hermes/profiles/tiao/SOUL.md     # tiao profile
~/.hermes/profiles/hang/SOUL.md     # hang profile
```

### 为其他实例/Profile创建 Soul 技能（SKILL.md）

当需要给其他 Hermes 实例（如远程服务器 {{INSTANCE_NAME}}）或 Profile 创建专属 soul 技能时，**严禁直接复制 kaka-soul 改个名字**。每个实例有自己的身份和连接配置，必须基于目标实例自身的 SOUL.md 创建。

**正确流程：**
1. 先读取目标实例的 SOUL.md，了解其实际身份配置（名字、平台连接、用户标识）
2. 通用规则可直接复用（铁律、消息优先级、记忆调用规则、行为准则）
3. 以下内容**必须基于目标实例自身配置**，不能照搬：
   - 实例名字（kaka vs {{INSTANCE_NAME}} vs tiao）
   - 平台用户标识（飞书 {{FEISHU_USER_ID}} 是 kaka 的，{{INSTANCE_NAME}} 可能用不同飞书账号或还没配微信）
   - 临时目录命名（`{{AGENT_TMP_DIR}}/` vs `~/lili-tmp/` vs `~/cat-tmp/`）
   - 末尾"记住"行的平台标识列表
4. 创建后验证：检查不含源实例独有标识，序号无重复

**常见错误：**
- ❌ 把 kaka 的飞书 {{FEISHU_USER_ID}} 标识直接复制给 {{INSTANCE_NAME}}（{{INSTANCE_NAME}} 有自己的飞书连接）
- ❌ 临时目录还写 `{{AGENT_TMP_DIR}}/` 而不是 `~/lili-tmp/`
- ❌ 末尾提醒还写 "我是 {{AGENT_NAME}}" 而不是目标实例的名字

### 配置格式
- **纯Markdown格式**，无需YAML frontmatter
- 自上而下按优先级执行，最前面的规则优先级最高
- 每个Profile独立配置，互不影响

### Soul配置最佳实践
```markdown
# 🔴 最高优先级安全规则（放在最前面！）

## 身份识别规则
1. 只对特定用户ID响应
2. 其他人保持静默

## 安全输出限制
1. 禁止输出的内容列表
2. 输出过滤规则

## 文件访问权限
1. 允许访问的目录
2. 禁止访问的敏感路径

---

# 💼 核心职责（业务规则）

# 🎯 行为准则和沟通风格
```

---

## 🔐 权限系统配置
---
### 全局安全配置 (`config.yaml`)

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| `security.allow_private_urls` | `false` | 禁止访问内网URL |
| `security.redact_secrets` | `true` | 自动脱敏敏感信息 |
| `security.tirith_enabled` | `true` | 启用安全策略引擎 |
| `security.tirith_fail_open` | `true` | 安全检查失败时开放 |
| `hooks_auto_accept` | `false` | 不自动接受Hook操作 |
| `approvals.mode` | `manual` | 危险操作需人工审批 |
| `approvals.cron_mode` | `deny` | 默认禁止Cron任务 |

### 命令白名单 (`command_allowlist`)
允许执行的危险操作：
- script execution via -e/-c flag
- script execution via heredoc
- recursive delete
- stop/restart system service
- force kill processes

---

### 🔄 权限系统完全重置/全开操作流程
当需要彻底清空旧权限配置、完全放开所有限制以便重建新的权限系统时，按以下步骤执行：

1. **删除旧权限相关文件**
   ```bash
   # 删除权限配置文件及所有历史备份
   rm -f ~/.hermes/permission-config.yaml*
   # 删除旧的permission-governance技能
   rm -rf ~/.hermes/skills/kaka-soul/permission-governance
   ```

2. **清空终端命令黑白名单**
   修改`config.yaml`：
   ```yaml
   # 清空命令黑名单，不再限制任何终端命令
   command_blacklist: []
   # 清空命令白名单，不再有执行限制
   command_allowlist: []
   ```

3. **关闭Tirith安全策略引擎**
   修改`config.yaml`：
   ```yaml
   security:
     tirith_enabled: false  # 关闭安全策略引擎
   ```

4. **禁用权限相关网关插件**
   修改`config.yaml`：
   ```yaml
   plugins:
     enabled: []  # 移除owner-only-gateway等权限限制插件
   ```

> ⚠️ **注意**：此操作会完全放开所有权限限制，没有任何命令/工具拦截，仅适用于重新构建权限系统前的清理场景！操作完成后请尽快配置新的权限规则。

---

## 📚 Skills 技能系统

### 配置位置
```yaml
# ~/.hermes/config.yaml
skills:
  external_dirs: []              # 外部Skill目录
  template_vars: true            # 启用模板变量
  inline_shell: false            # 禁止内嵌Shell脚本
  inline_shell_timeout: 10       # Shell超时(秒)
  guard_agent_created: false     # 不强制防护Agent创建
```

### Skill标准目录结构
```
~/.hermes/skills/                          # 全局Skills根目录
           /{category}/                    # 分类目录（如 kaka-soul, mcp, devops 等）
                     /{skill-name}/        # 具体Skill目录
                                /SKILL.md  # Skill主文件
                                /assets/   # 资源文件（可选）
                                /scripts/  # 脚本文件（可选）

~/.hermes/profiles/{name}/skills/          # Profile专属Skills（可选）
```

### 向指定 Profile 分发/复制 Skill

当用户要求“把某个技能也给少佐小猫/tiao/hang/某个 profile”时，属于 **Profile 专属 Skills 管理**，不要新建重复 Skill，也不要只在聊天里说明；应把现有 Skill 目录复制到目标 Profile 的 `skills/` 目录，按需替换实例特有信息，并验证目标 Profile 可正常调用。

**适用场景：**
- 将 default/global 的某个 Skill 授权给另一个 Profile 使用。
- 让 tiao（少佐小猫）、hang 等独立 Profile 拥有同一套写作/业务/自动化能力。
- 同步一个已验证的 Skill 到 Profile 专属目录，保持隔离同时复用能力。

**⚠️ 同步前先判断凭据来源类别（避免无谓复制）：**

Hermes 里\"联网/多媒体/AI辅助\"能力大致有三种凭据获取方式，同步策略不同：

| 类别 | 凭据来源 | 子Profile 是否自动可用 | 同步动作 |
|------|---------|----------------------|---------|
| A. Agent auxiliary 配置类 | `config.yaml:auxiliary.<name>` 里的 `api_key/base_url/model` | ❌ 每个 profile 独立读自己的 config，不会共享 | 必须把 auxiliary 节点复制到目标 profile |
| B. 平台 SDK / `.env` 变量类 | `~/.hermes/.env` 全局或 `profiles/<p>/.env` | 视变量而定：全局 `.env` 会被所有 profile 加载；profile `.env` 各自独立 | 全局变量无需同步；profile 变量按需复制 |
| C. 外部 CLI 二进制 + 自有 home config 类 | 工具用 `subprocess` 调用系统 CLI（如 `mmx`、`gh`、`aws`），CLI 自己从 `~/.xxx/config` 读 key | ✅ 子 profile 进程 `HOME=/home/ubuntu`，自动共享同一份 CLI 配置 | **不需要任何同步动作**，只要目标 profile 的 toolsets 开启对应工具即可 |

**判定方法：** 打开对应工具源码（`~/.hermes/hermes-agent/tools/<tool>_tool.py`），看它是读 `config.yaml:auxiliary` 还是 `subprocess.run([cli, ...])`。

**典型案例（C 类）：** `minimax_web_search` 走 `mmx` CLI，key 在 `~/.mmx/config.json`。看到目标 profile `auxiliary.minimax_web_search: {}` 是空的**不要**去复制主 profile 的 `MINIMAX_API_KEY`——那个 key 是给 SDK 用的，跟 mmx CLI 无关。只要 skill 目录和 toolsets 就位，条条已经能直接用。

**推荐流程：**
1. 先用 `skills_list` / `skill_view` 确认源 Skill 存在且内容是最新版。
2. 确认目标 Profile 目录：`~/.hermes/profiles/<profile>/skills/`。
3. 复制整个 Skill 目录（包含 `SKILL.md` 以及 `references/`、`templates/`、`scripts/`、`assets/` 等支持文件），而不是只复制单个文件：
   ```bash
   mkdir -p ~/.hermes/profiles/<profile>/skills/<category>/
   cp -a ~/.hermes/skills/<category>/<skill-name> ~/.hermes/profiles/<profile>/skills/<category>/
   ```
   如果源 Skill 是嵌套分类（如 `kaka-soul/permission-governance`），目标侧保持相同相对路径。
4. **替换实例特有信息（关键！）**
   复制后必须检查并替换源实例专属的字段，否则目标 Profile 会写错目录或身份混乱。常见需要替换的内容：
   | 类型 | 示例 | 替换目标 |
   |------|------|----------|
   | 临时目录 | `{{AGENT_TMP_DIR}}/` | Profile 专属目录，如 `~/cat-tmp/`（少佐小猫 tiao） |
   | 配置文件/凭证路径 | `/home/ubuntu/.hermes/config/agnes_config.sh` | `~/.hermes/profiles/<profile>/config/agnes_config.sh` |
   | 作者字段 | `author: kaka` | `author: <profile>` 或通用名 |
   | 实例自我引用 | "让 kaka 可以..." | "让 <profile> 可以..." |
   | 硬编码用户 ID | 源实例的微信/飞书 ID | 目标 Profile 实际服务的用户 ID（如不同） |

   **⚠️ 为什么这步经常导致“复制过去但用不了”：** 子 Profile 通常启用了路径隔离 Hook，只允许访问自己的 `~/.hermes/profiles/<profile>/`、`~/<nick>-tmp/` 和 `/tmp/`。如果 Skill 还硬编码指向主 Profile 的配置文件（如 `~/.hermes/config/agnes_config.sh`）或主 Profile 的临时目录（`{{AGENT_TMP_DIR}}/`），调用时会被 Hook 拦截——读不到 API key、写不了结果，表现就是“技能有了但用不了”。

   替换方式建议用 `patch` 或精确 `sed`，避免盲目 `sed -i` 批量替换导致非目标内容被改。
5. **同步/复制独立的配置文件到子 Profile 自己的 config 目录**
   如果 Skill 依赖 `~/.hermes/config/*.sh` 或 `~/.hermes/.env` 中的凭证，不能指望子 Profile 跨边界读取主 Profile 文件。正确做法：
   ```bash
   mkdir -p ~/.hermes/profiles/<profile>/config
   cp ~/.hermes/config/<skill>_config.sh ~/.hermes/profiles/<profile>/config/<skill>_config.sh
   ```
   然后修改 Skill 中的读取路径，使其指向子 Profile 自己的副本（见上表）。
6. 创建/确认输出目录：如果 Skill 会在 `~/[profile]-tmp/...` 下产生文件，先创建好目标目录，避免首次调用时报错。
7. 验证文件层：读取目标 `SKILL.md` 前几行，确认 `name:` 与源 Skill 一致；必要时检查文件大小或支持文件数量。注意 Hub/package 目录名可能不同于 frontmatter `name`，运行时 `--skills` 和技能加载使用的是 frontmatter `name`，不是目录名。
8. **验证目标 Profile 可正常调用（至少做最小功能测试）**
   - **路径/隔离检查：**搜索目标 Skill 目录，确认没有残留源 Profile 的硬编码路径（如 `~/.hermes/config/*.sh`、`{{AGENT_TMP_DIR}}/`、源 Profile 的微信/飞书 ID 等）。
   - **独立配置检查：**如果 Skill 需要凭证文件，确认 `~/.hermes/profiles/<profile>/config/` 下已有对应副本，且 Skill 中的读取路径指向该副本。
   - 文件校验：`python3 -m py_compile <skill>.py`、YAML frontmatter 校验。
   - 实际调用一次 Skill 的核心功能（如文本生成、文件保存），确认返回成功。
   - 示例（Agnes AI 技能同步后）：
     ```bash
     python3 ~/.hermes/profiles/<profile>/skills/media/agnes-ai/scripts/agnes-generate.py --mode text --prompt "你好" --max_tokens 20
     # 预期返回 {"status": "success", "type": "text", "content": "你好！"}
     ```
   - 如果用 `hermes chat --profile <profile>` 验证：
     ```bash
     hermes chat --profile <profile> --skills <frontmatter-name> -q '请只回复：技能可用'
     ```
   注意：Hermes 的技能列表可能按 frontmatter `name` 展示，但 `--skills` / slash 预加载在部分版本会按目录名解析；如果目录名/Hub包名与 frontmatter `name` 不一致，可能出现"列表里有但 `Unknown skill(s)` / `Skill '<name>' not found`。此时应复制或建立同名目录别名（保持 `SKILL.md` 内容不变），例如把 `skills/content/mimo-xiaohongshu-copywriter/` 同步为 `skills/content/xiaohongshu-copywriter/`，再复测 `--skills <frontmatter-name>` 和 `/<frontmatter-name>`。启动横幅中看到名称不等于加载成功，必须以实际预加载/斜杠调用无 error 为准。
   如果目标 Profile 的微信/飞书会话仍反馈“读不到技能”，按“真实运行时”继续排查，不要只相信当前 default 会话的 `skill_view`：
   - 查目标 profile 最新 `sessions/session_*.js

... [OUTPUT TRUNCATED - 48851 chars omitted out of 78851 total] ...

 扩展 WRITE_INDICATORS 列表 | ✅ 已修复 |

**架构限制（无法通过字符串匹配 hook 修复，需架构层面解决）：**

| 限制 | 原因 | 影响 | 缓解措施 |
|------|------|------|----------|
| base64 编码命令 | `echo config | base64; base64 -d | sh` 等编码后执行 | 可绕过所有字符串匹配 | 需要在 shell 层做命令审计，非 hook 能力范围 |
| eval + base64 | `python3 -c "exec(__import__('base64').b64decode('...'))"` | 动态生成代码无法静态匹配 | 同上，需 python 沙箱或命令审计 |
| 变量拼接路径 | `P=$HOME/.hermes; cat $P/config.yaml` | 变量展开在运行时，字符串匹配无法覆盖 | 需 shell 层路径解析，非 hook 能力范围 |

**验证方法论 — 独立验证集：**

自写 hook 代码时容易有盲区（自己写的测试往往只测自己想到的攻击向量）。推荐使用 skillopt 的独立验证集方法：
1. 先让 hook 作者写实现 + 自测
2. 再让独立角色（不同 agent session）仅根据管理目标设计测试用例，不看实现代码
3. 独立测试集通常能发现 12+ 个作者遗漏的攻击向量
4. 修复后跑全量验证集确认 0 失败

本次审计中，独立验证集发现了 12 个自测遗漏的攻击向量，修复后全部通过。

**不需要拦截的项目及理由：**
- curl/wget 外发：不需要拦截。上游路径黑名单已封死 config.yaml、.env、memories、sessions 等敏感文件，tiao 根本读不到这些文件，也就没有东西能通过 curl 外泄。封掉 curl/wget 会破坏正常的联网搜索和网页抓取功能。

**当前三层防护状态总结（external_dirs=[] 后）：**
| 途径 | 能修改主Profile技能？ | 保护机制 |
|------|---------------------|----------|
| skill_manage 工具 | ❌ 安全 | `_is_local_skill()` 拒绝修改外部/只读技能 |
| write_file / patch | ❌ 安全 | hook `READONLY_PREFIXES` 拦截写操作 |
| terminal / execute_code | ❌ 已修复 | `check_command()` 检查只读路径 + 写指示符组合 |

**⚠️ 符号链接绕过 — realpath 修复覆盖分析（重要）：**

已知漏洞：`is_path_allowed()` 未用 `realpath()`，符号链接可绕过只读保护。但仅加 realpath **不够**，三个攻击向量只覆盖一个半：

| 攻击向量 | 仅加realpath能否防护 | 原因 |
|----------|---------------------|------|
| skill_manage 通过符号链接篡改 | ❌ 不能 | `check_skill_manage()` 根本不调用 `is_path_allowed()`，只检查 file_path 是否绝对路径或含 `..` |
| terminal 通过符号链接写入 | ❌ 不能 | `check_command()` 是命令字符串匹配，无法从任意命令中提取文件路径做 realpath |
| write_file/patch 通过符号链接写入 | ✅ 能 | `is_path_allowed()` 加 realpath 后，符号链接路径会解析为真实目标，匹配 READONLY_PREFIXES |

**根本原因分析：**
1. **skill_manage 缺口**：`check_skill_manage()` 函数只做了 file_path 的绝对路径和 `..` 检查，完全没有走 `is_path_allowed()` 路径校验流程。即使加了 realpath，也不经过那条路径。
2. **terminal 缺口**：`check_command()` 基于命令字符串模式匹配（`has_readonly` 检查命令是否包含 `~/.hermes/skills/` 字符串），如果通过符号链接路径（如 `~/.hermes/profiles/tiao/skills/web-access/SKILL.md`）写入，命令字符串不含被保护路径，`has_readonly` 不触发。

**❌ external_dirs 方案的根本缺陷（2026-06-30 验证结论）：**

经过完整攻击向量测试（13项），发现即使实现上述三管齐下修复，仍有 2/13 场景无法防护：
- terminal 通过符号链接路径写入（命令字符串匹配无法做 realpath）
- terminal 通过 python 脚本间接创建符号链接再写入

**根本原因：** 只要子Profile能通过任何路径引用到主Profile的技能目录（无论是 external_dirs 还是符号链接），就一定存在 terminal 层面的逃逸攻击面。hook 是字符串匹配，无法对动态命令中的文件路径做 realpath 解析。

**✅ 最终推荐方案 — 移除 external_dirs + 选择性复制（非符号链接）：**

1. 子Profile config.yaml 中 `external_dirs: []`（清空，不引用主Profile技能目录）
2. 把需要给子Profile用的技能**直接复制**到 `~/.hermes/profiles/<profile>/skills/` 下
3. 不使用符号链接（符号链接本身就是逃逸入口）
4. builtin 技能用 `skills.disabled` 黑名单控制

**此方案优势：**
- 子Profile完全不需要碰 `~/.hermes/skills/`，不存在符号链接攻击前提
- skill_manage 只操作自己 profile 的技能，改不到主Profile
- 所有 13 项攻击向量测试全部通过（0 缺口）
- 唯一代价：主Profile技能更新后需要手动同步给子Profile（维护成本，非安全问题）

**已实施状态（tiao profile）：**
- `external_dirs` 已从 `~/.hermes/skills` 改为 `[]`
- tiao 只能用自己的 `~/.hermes/profiles/tiao/skills/` 下的技能
- 与主Profile完全隔离

**如果后续需要给子Profile新增技能：**
```bash
# 复制（不是符号链接！）技能目录到子Profile
cp -a ~/.hermes/skills/<category>/<skill-name> ~/.hermes/profiles/<profile>/skills/<category>/
```

---

## 🔄 kaka ↔ {{INSTANCE_NAME}} 跨实例同步

kaka（本地）和 {{INSTANCE_NAME}}（阿里云 {{SERVER_IP}}）是两个独立 Hermes 实例，共享同一套基础设施（GitHub: {{GITHUB_USERNAME}}、Cloudflare、飞书多维表）。跨实例同步时遵循以下原则。

### 同步决策框架

| 内容 | 是否同步 | 原因 |
|------|----------|------|
| 共享工作流技能（website-operations、cloudflare-pages-deployment） | ✅ 双向同步 | 两边都能部署网站 |
| 权限管理超级管理员列表 | ✅ 统一同步 | 同一用户的所有账号 |
| Soul/身份技能（kaka-soul、lili-soul） | ❌ 不同步 | 各自独立身份 |
| 记忆插件代码（holographic __init__.py） | ✅ 从 kaka → {{INSTANCE_NAME}} | kaka 是主开发节点 |
| 飞书多维表配置（base-token、table-id） | ✅ 共享 | 同一个归档位置 |
| 微信通道配置 | ❌ 不同步 | 各自独立平台连接 |
| 过时/废弃技能 | ❌ 不同步到对方 | 清理而非传播 |

### 数据同步链路架构

**原则：每个数据类型只 designate 一个 source of truth，其他实例从源头拉取，不搞双向互写。**

**网站登记表示例：**
```
飞书多维表（source of truth）
    ↓ 每周一 9:00 {{INSTANCE_NAME}} cron 拉取
{{INSTANCE_NAME}} 的 site-registry.md
    ↓ 每周一/四 9:00 kaka cron SSH 读取
kaka 的 site-registry.md
    → 执行健康检查 → 发微信报告
```

**关键教训 — 不要在两处写同步逻辑：**
- ❌ 技能 SKILL.md 里写"用 lark-cli 查飞书多维表同步" + cron prompt 里写"SSH 读文件对比" → 两套逻辑不一致
- ✅ 同步逻辑只写在 cron prompt 中，SKILL.md 只描述数据格式和存储位置
- ✅ 技能里的同步说明应该是"cron 负责同步，手动操作时直接读本地文件"这种声明性描述

### 跨实例 Cron 设置要点

1. **源端 cron**（如 {{INSTANCE_NAME}} 查飞书）：`deliver: local`，不需要通知用户
2. **消费端 cron**（如 kaka 健康检查）：`deliver: telegram/weixin`，结果通知用户
3. **SSH 失败兜底**：消费端 cron 应处理源端不可达的情况 — 同步失败时仍执行本地检查，报告中标注"未能从 {{INSTANCE_NAME}} 同步"
4. **时序协调**：源端 cron 应在消费端之前执行（如 {{INSTANCE_NAME}} 周一 9:00 拉，kaka 周一/四 9:00 读 {{INSTANCE_NAME}}）

### 远程操作 {{INSTANCE_NAME}} 的标准方式

```bash
# SSH 命令模板
sshpass -p '<password>' ssh -o StrictHostKeyChecking=no root@{{SERVER_IP}} '<command>'

# 查看 {{INSTANCE_NAME}} cron 列表
sshpass -p '<password>' ssh root@{{SERVER_IP}} 'cd /root/.hermes && /root/.hermes/venv/bin/python -m hermes_cli.main cron list'

# 创建 {{INSTANCE_NAME}} cron（注意 CLI 参数格式：schedule 和 prompt 是位置参数）
sshpass -p '<password>' ssh root@{{SERVER_IP}} 'cd /root/.hermes && /root/.hermes/venv/bin/python -m hermes_cli.main cron create \
  --name "<name>" \
  --deliver local \
  "0 9 * * 1" \
  "<prompt text>"'
```

### 为 {{INSTANCE_NAME}} 创建独立身份技能

{{INSTANCE_NAME}} 不能直接复用 kaka-soul，必须创建独立的 lili-soul：
1. 读取 {{INSTANCE_NAME}} 的 SOUL.md 和 config.yaml 确认实际平台连接
2. 通用规则可复用（铁律、记忆调用规则、行为准则）
3. 必须基于 {{INSTANCE_NAME}} 自身配置替换：实例名、平台用户标识、临时目录（`~/lili-tmp/`）、飞书/微信连接信息
4. 验证不含 kaka 独有标识（{{FEISHU_USER_ID}} 飞书DM、kaka-tmp 等）

---

### 子Profile技能依赖审计

复制技能到子Profile后，必须检查该技能是否引用了子Profile没有的其他技能。遗漏依赖会导致技能在运行时报错或功能不完整。

**适用场景：**
- 刚给子Profile复制了新技能
- 子Profile的 `external_dirs` 已清空，完全依赖本地副本
- 用户反馈"技能加载了但用不了某功能"

**审计流程：**

1. 扫描子Profile所有 SKILL.md 中的技能引用：
   ```python
   import re
   from pathlib import Path

   tiao_root = Path.home() / '.hermes/profiles/tiao/skills'
   references = set()
   for p in tiao_root.rglob('SKILL.md'):
       txt = p.read_text(errors='ignore')
       # 匹配 skill_view("name") 和 skill_view('name')
       references |= set(re.findall(r'skill_view\(["\']([^"\']+)["\']\)', txt))
       # 匹配自然语言引用：use the `xxx` skill / load the `xxx` skill
       references |= set(re.findall(r'(?:use|load|import)\s+(?:the\s+)?`([a-z][a-z0-9-]+)`\s+skill', txt, re.I))
       # 匹配中文引用：先加载/调用 xxx 技能
       references |= set(re.findall(r'(?:先加载|调用|使用)\s*[`「]([a-z][a-z0-9-]+)[`」]\s*(?:技能|skill)', txt, re.I))

   # 检查哪些引用的技能不存在于子Profile
   tiao_skill_names = set()
   for p in tiao_root.rglob('SKILL.md'):
       tiao_skill_names.add(p.parent.name)
   missing = references - tiao_skill_names
   ```

2. 对每个缺失依赖，检查主Profile是否有对应技能：
   ```bash
   find ~/.hermes/skills/ -name '<missing-skill-name>' -type d
   ```

3. 如果主Profile有，复制过去；如果没有（如需 `skill_manage install` 的社区技能），记录并跳过。

4. 复制后验证文件完整性：
   ```bash
   diff ~/.hermes/skills/<category>/<skill>/SKILL.md ~/.hermes/profiles/<profile>/skills/<category>/<skill>/SKILL.md
   ```

**常见依赖模式：**
- `research-paper-writing` → 引用 `arxiv`、`subagent-driven-development`、`plan`、`jupyter-live-kernel`、`diagramming`
- `apple-notes` → 引用 `obsidian`
- `systematic-debugging` → 引用 `test-driven-development`
- `xinchuan-kaoyan-wechat-article` → 引用 `minimax_web_search`（工具集，非技能，无需复制）

### skills.external_dirs 配置与限制

**用途：** 让子Profile引用主Profile的技能目录，无需本地副本。

**配置方式（子Profile config.yaml）：**
```yaml
skills:
  external_dirs:
    - ~/.hermes/skills
```

**关键特性：**
- **只读**：外部目录技能是只读的，agent 不能通过 skill_manage 修改/删除它们
- **本地优先**：同名技能子Profile本地版本覆盖外部版本
- **完整集成**：外部技能出现在系统提示词索引、skills_list、skill_view 中
- **不存在的路径静默跳过**：不报错
- **路径扩展**：支持 `~` 和 `${VAR}`

**限制 — 不支持按技能名单独授权：**
- `external_dirs` 只支持**目录级别**，扫描目录下所有 SKILL.md
- 没有内置的 allowlist 机制按技能名白名单
- 只有 `skills.disabled` 黑名单可以逐个禁用技能

**实际可选方案：**
- **方案A（全给+黑名单）**：`external_dirs: [~/.hermes/skills]` + `skills.disabled: [不想给的技能名]`
- **方案B（符号链接白名单）**：创建独立目录，只 `ln -s` 要给的技能，把该目录加入 `external_dirs`
  - ⚠️ 需注意：`credential_files.py` 提到 "Skips symlinks entirely"，需验证 skills_tool.py 是否也跳过符号链接

**注意：** `skills_tool.py` 源码中 `iter_skill_index_files()` 使用 `rglob("SKILL.md")` 扫描，不跳过符号链接（与 credential_files.py 不同），所以方案B技术上可行。

### 子Profile技能黑名单策划方法论

当使用方案A（全给+黑名单）时，按以下风险分类策划 `skills.disabled` 列表：

**必须禁用（高风险）— 涉及身份/权限/服务器/Hermes配置：**
- 身份与核心规则：`kaka-soul`、`kaka-gateway-admin`、`holographic-memory-governance`、`problem-diagnosis`
- 权限管理：`permission-management`
- 服务器专属：`server-39-97-248-219`
- Hermes配置：`hermes-agent`

**建议禁用（中高风险）— 可修改系统/访问敏感数据：**
- 部署/迁移类：`hermes-server-migration`、`cloudflare-pages-deployment`、`webhook-subscriptions`
- 系统管理类：`systemd-service-troubleshooting`、`server-health-monitoring`、`proxy-server-configuration`
- 凭证/配置类：`feishu-app-connection`、`minimax-hermes-fallback`
- 安全/审计类：`skill-ecosystem-audit`、`hermes-agent-self-evolution`、`hermes-session-context-debugging`
- 自动化代理类：`claude-code`、`codex`、`opencode`、`hermes-community-skill-installation`
- 网关管理类：`hermes-webui-agent`

**判定原则：**
1. 技能能直接修改 Hermes 运行时配置/系统服务 → 高风险，必须禁用
2. 技能能访问/修改服务器凭证/SSH/密钥 → 高风险，必须禁用
3. 技能能安装/删除软件包或部署代码 → 中高风险，建议禁用
4. 技能只做内容生成/检索/分析 → 低风险，不禁用
5. 技能只做代码编辑（在子Profile边界内）→ 低风险，不禁用

**区分技能来源的方法：**
- Hermes 自带技能：文件时间戳统一为初始安装日期（如 2026-04-27），批量同时间
- 社区/Hub 安装技能：SKILL.md 中含 `clawhub`/`skills.sh`/`hub` 等关键词，frontmatter 通常无 `source` 字段
- 用户创建技能：文件时间戳分散在近期日期，frontmatter `author` 字段为用户名

### 子Profile技能白名单机制选型与实现

当用户要求把子Profile的技能访问从黑名单改为白名单，或要求"更安全的技能管控"时，按以下决策框架选型并实施。

**核心问题：黑名单（默认允许+逐个禁止）vs 白名单（默认拒绝+逐个允许）**

黑名单的致命缺陷：主Profile每新增一个技能，子Profile自动获得，漏一个就出事。白名单从源头隔离，新增技能默认不可见。

**三种方案对比：**

| 方案 | 原理 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|--------|
| A. Config全量disable+白名单豁免 | 保持external_dirs，把非白名单技能全加入disabled | 改动小 | 维护成本极高（100+条），新增技能默认enabled仍需手动disable | ❌ |
| B. Hook白名单拦截 | 在pre_tool_call.py增加skill_view白名单检查 | 改动最小 | skills_list仍列出所有技能名，agent看得到用不了（信息泄露+混淆） | ❌ |
| C. 符号链接白名单 | 移除external_dirs，只创建白名单技能的symlink | 从源头隔离 | 符号链接本身是逃逸攻击入口，terminal无法防护 | ❌ 已弃用 |
| D. 选择性复制（非符号链接） | 移除external_dirs，直接复制需要的技能到子Profile | 0攻击面，完全隔离 | 主Profile更新后需手动同步 | ✅ 推荐 |

**❌ 方案C（符号链接白名单）— 已弃用：**

2026-06-30 验证结论：符号链接本身就是逃逸攻击入口。terminal 命令字符串匹配无法对符号链接路径做 realpath 解析，导致通过符号链接写入主Profile技能的攻击无法被 hook 拦截。

**✅ 方案D（选择性复制，非符号链接）— 推荐：**

移除 `external_dirs`，把需要的技能**直接复制**到子Profile自己的 `skills/` 目录。无符号链接 = 无逃逸入口 = 0 攻击面。

**关键验证点：**
- `skills_tool.py` 的 `iter_skill_index_files()` 使用 `rglob("SKILL.md")` 扫描，**不跳过符号链接**（与 credential_files.py 不同），所以方案C技术上可行
- 移除 `external_dirs` 后，子Profile的 `skills_list` 只显示本地技能+符号链接技能，非白名单技能完全不可见
- builtin技能不受 external_dirs 控制，仍需用 `skills.disabled` 禁用不需要的

**白名单技能选择参考（以tiao为例）：**
- ✅ 内容创作：xiaohongshu-copywriter、frontend-design、ui-ux-pro-max
- ✅ 搜索检索：minimax-web-search、web-access、enterprise-intelligence
- ✅ 文档处理：feishu-doc-automation、docx-openxml-generation、powerpoint
- ✅ 创意工具：architecture-diagram、excalidraw、ascii-art等
- ✅ 子Profile本地技能：tiao-important-dates等
- 🔒 禁用：所有kaka-soul类、permission-management、server类、hermes-agent类、系统管理类

### skill_manage 对外部技能的内置保护

Hermes 的 `skill_manage` 工具（`tools/skill_manager_tool.py`）对外部技能有内置保护：
- `_is_local_skill()` 检查技能路径是否在本地 `SKILLS_DIR` 内
- 对外部技能执行 edit/patch/delete/write_file/remove_file 时返回错误：`"Skill is in an external directory and cannot be modified"`
- `_find_skill()` 先搜索本地目录，再搜索 external_dirs
- 新技能创建（`_create_skill`）始终写入本地 `SKILLS_DIR`，不会写到外部目录

**这意味着：** 即使配置了 `external_dirs`，子Profile也无法通过 `skill_manage` 工具修改主Profile技能。保护是工具级别的，不依赖 hook。

**验证方法：** 用 subprocess 模拟 stdin 输入测试 hook，覆盖以下场景：
- 边界内操作放行（ls/chmod/rm within profile dir）
- 跨边界文件访问拦截（~ 和绝对路径两种形式）
- 系统命令拦截（ssh/systemctl/apt/crontab）
- 非terminal工具放行（web_search等）
- **读主Profile技能放行**（read_file ~/.hermes/skills/xxx/SKILL.md）
- **写主Profile技能拦截**（write_file/patch ~/.hermes/skills/xxx/SKILL.md）
- **skill_manage路径逃逸拦截**（file_path含绝对路径或..）
- **terminal写命令绕过只读路径**（echo > ~/.hermes/skills/xxx/SKILL.md）← 需修复后验证

### 清理子Profile旧权限配置

当从"旧的全量权限管理"切换到"轻量级边界隔离hook"时，需要清理以下旧配置：

**config.yaml 硬限制清理：**
| 旧配置 | 操作 |
|--------|------|
| `terminal.command_blacklist` | 整段删除（边界内不限制命令） |
| `approvals.cron_mode: deny` | 改为 `allow`（边界内允许cron） |
| `approvals.mode: manual` | 改为 `auto`（边界内无需审批） |
| `command_allowlist` | 整段删除 |
| 旧permission-management hook配置 | 整段删除，替换为新隔离hook |

**SOUL.md 软限制清理：**
- 删除"文件访问权限规则"段（hook已硬性拦截，不需要软规则）
- 删除"安全输出限制"段（如"禁止输出路径/目录结构"等，这些限制了子Profile用户的正常使用体验）

> ⚠️ 清理后必须重启子Profile gateway 使hook配置生效。

### 跨Profile代发消息 / Profile身份转发

当用户要求“让某个Profile/机器人以自己的身份给某人发消息”（例如“让少佐小猫发给条条”）时，不要直接用当前(default/kaka)网关发送；应通过目标Profile启动一次独立会话，让该Profile调用它自己的平台网关发送，这样收件人看到的发送者身份才正确。

**通用流程：**
1. 明确目标Profile、目标联系人ID、目标平台和消息内容。
2. 使用 `hermes chat --profile <profile_name> -q "..."` 调用目标Profile。
3. 在 prompt 中要求目标Profile“通过你的 <平台> 网关发送给 <目标ID>”，并要求发送完成后返回可验证短句（如“已发送”）。
4. 检查命令输出中是否出现实际工具调用（如 `send weixin:<id>`）以及目标Profile最终回复。
5. 如需进一步确认，可查看目标Profile日志：`~/.hermes/profiles/<profile_name>/logs/gateway.log`。

**示例：让 tiao profile（少佐小猫）通过微信发给条条：**
```bash
hermes chat --profile tiao -q "少佐小猫，请你现在通过你的微信网关，把下面这条消息发给条条（微信ID：o9cq806NdT1_o-LNN6NCF5_hhl-M@im.wechat）：

<要发送的消息内容>

请发送完成后，只回复我：已发送。"
```

**验证成功的典型输出：**
```text
📨 send weixin:o9cq806NdT1_o-LNN6NCF5_hhl-M@im.wechat: "..."
已发送。
```

**注意事项：**
- 目标Profile未配置对应平台通道时，不要冒充它发送；应如实说明未配置。
- 对飞书/微信等平台，不要凭昵称猜测目标ID；必须有明确 chat_id/open_id/wechat_id 或从日志中确认。
- 如果用户说“通过那种方式/之前那种方式”，优先理解为“通过目标Profile的 hermes chat 代发”，再结合记忆和日志确认具体Profile。

---

## 📁 临时文件管理规范与操作流程
### 适用场景
当用户要求清理用户目录下的零散临时文件、为指定Profile创建专属临时目录、设置临时文件存储规则时使用本流程。
### 操作规范
1. **禁止在用户根目录直接生成临时文件**：所有Agent生成的临时文件必须存放在专属临时目录下
2. **专属临时目录命名规则**：
   - 全局临时目录：`{{AGENT_TMP_DIR}}/`（存放kaka默认Profile生成的临时文件）
   - Profile专属临时目录：`~/[profile-nickname]-tmp/`（例如少佐小猫tiao的临时目录为`~/cat-tmp/`）
3. **零散临时文件整理流程**：
   1. 首先扫描用户根目录下的零散临时文件：`ls -la ~ | grep -E "\.(md|docx|png|jpg|html|pdf|js|zip|json)$" | grep -v "^\."`
   2. 创建对应临时目录（如不存在）：`mkdir -p {{AGENT_TMP_DIR}} ~/cat-tmp`
   3. 将零散文件移动到对应临时目录：`mv ~/*.md ~/*.docx ~/*.png ~/*.jpg ~/*.html ~/*.pdf ~/*.js ~/*.zip ~/*.json {{AGENT_TMP_DIR}}/ 2>/dev/null || true`
   4. 验证根目录已清理：`ls -la ~ | grep -E "\.(md|docx|png|jpg|html|pdf|js|zip|json)$" | grep -v "^\."`（应无输出）
4. **Profile专属临时目录创建流程**：
   1. 确认Profile昵称对应的临时目录命名（例如：少佐小猫tiao → `cat-tmp`）
   2. 创建目录：`mkdir -p ~/[dir-name]/`
   3. 更新对应Profile的SOUL配置或记忆，要求其后续所有临时文件都生成到该目录下
5. **临时文件清理规则**：
   - 临时文件默认保留30天，超过30天的自动清理
   - 可根据用户要求调整保留时间

---

## 🧹 能力目录整理与残留清理流程

当用户要求“整理所有技能/能力/功能”“整合同类能力”“清理项目残留垃圾”时，按下面流程处理。目标是**归类、明确主入口、标记重复/重叠边界、安全清理缓存**，不要把所有 Skill 机械合并成一个，也不要删除正式配置/记忆/会话。

### 1. 先盘点再判断

```bash
# Skills 总量与元信息
python3 - <<'PY'
import pathlib, yaml, json
root=pathlib.Path.home()/'.hermes'
items=[]
for p in (root/'skills').rglob('SKILL.md'):
    txt=p.read_text(errors='ignore')
    fm={}
    if txt.startswith('---'):
        try: fm=yaml.safe_load(txt.split('---',2)[1]) or {}
        except Exception: fm={}
    items.append({'name':fm.get('name') or p.parent.name,'rel':str(p.parent.relative_to(root/'skills')),'description':fm.get('description','')})
print(json.dumps({'count':len(items),'items':items},ensure_ascii=False,indent=2))
PY
```

同时检查：
- `~/.hermes/profiles/*/config.yaml` 的 `toolsets` 和 Profile 职责。
- `~/.hermes/hermes-agent/tools/*` 中是否有高层工具封装（例如 `enterprise_intelligence_tool.py`）。
- `~/.hermes/hermes-agent/toolsets.py` 中是否注册了对应工具集。

### 2. 按“能力类别”整理，不按文件名粗暴合并

常见判断规则：
- **企业查询/调研**：`business/enterprise-intelligence` 是业务 Skill；`tools/enterprise_intelligence_tool.py` 是普通用户安全调用的高层工具封装，二者不是重复项。
- **飞书文档**：`feishu-doc-automation` 是文档主入口；`feishu-app-config` / `feishu-app-connection` 是配置与连接排错专项，不要误删。
- **网页能力**：`web-access` 是联网搜索/网页访问主入口；`playwright-browser` 和 `headless-browser-cjk-fonts` 是真实浏览器与截图/CJK 字体专项。
- **权限/Gateway**：`permission-governance` 负责用户→Skill→Tool 白名单；`kaka-gateway-admin` 负责 Profile/Gateway/Soul/Hook 总体管理。

如果能力高度重叠但删除风险不低，先在汇报中标注“可后续合并”，不要当场删除。

### 3. 生成/更新能力总目录

推荐维护：`~/.hermes/CAPABILITIES.md`，记录：
- 主业务能力入口。
- 相近能力的边界说明。
- Profile 当前用途和工具集。
- 清理策略与不清理范围。
- 后续维护约定：同类业务能力只保留一个主 Skill；普通用户用高层工具封装，不开放底层危险工具。

### 4. 安全清理残留：只隔离可再生垃圾

优先使用“隔离区”而不是永久删除：

```bash
mkdir -p ~/.hermes/cleanup-quarantine/$(date +%Y%m%d_%H%M%S)
# 将明确可再生的 /tmp 临时安装目录、浏览器临时 profile、node 编译缓存、__pycache__ 等移动进去
```

允许清理/隔离：
- `/tmp` 下明显的临时安装目录、Chrome 临时 profile、Playwright 下载残留、node 编译缓存。
- 自定义 Skill / tools 下的 `__pycache__`。
- 旧截图/音频缓存目录。

禁止清理：
- `~/.hermes/sessions` 会话记录。
- 记忆、正式 Skill、Profile、`.env`、`config.yaml`、`SOUL.md`。
- 当前刚交付但可能还会用到的业务输出文件。
- `/tmp/systemd-private-*`、`.X11-unix`、`.ICE-unix`、`snap-private-tmp` 等系统/runtime 目录。
- 不使用 `rm -rf` 做批量删除；先移动到隔离区，确认无误后再由管理员决定是否彻底删除。

### 5. 验证

整理后至少验证：

```bash
python3 - <<'PY'
import yaml, pathlib
root=pathlib.Path.home()/'.hermes'
for p in [root/'permission-config.yaml', root/'config.yaml', root/'profiles/tiao/config.yaml', root/'profiles/hang/config.yaml']:
    if p.exists():
        yaml.safe_load(p.read_text(encoding='utf-8'))
        print('YAML OK', p)
PY
python3 -m py_compile ~/.hermes/skills/business/enterprise-intelligence/enterprise_query.py ~/.hermes/hermes-agent/tools/enterprise_intelligence_tool.py
```

最终汇报应包含：整理了哪些主入口、哪些不是重复项、清理了什么、隔离区位置、验证结果。

---

## 🛠️ 标准审查流程

当用户要求审查权限配置时，按以下顺序执行：

### 🚀 快速自动化审计（推荐首选）
使用 `permission-governance` Skill 提供的自动化审计脚本，一键完成所有检查：

```bash
python3 ~/.hermes/skills/kaka-soul/permission-governance/scripts/audit.py
```

或者直接对话：
```
运行权限规范检查
执行目录结构审计
检查MCP配置是否规范
```

---

### 📋 手动审查流程（如需深入）
1. **执行层级与架构理解**
   - 确认Hook → Soul → Skill → Tool的执行顺序
   - 确认四层权限控制机制的优先级

2. **全局安全配置检查**
   ```bash
   # 读取config.yaml的security, approvals, command_allowlist部分
   # 重点检查 mcp_servers 配置是否正确
   ```

3. **Profile架构检查**
   ```bash
   # 列出profiles目录内容，检查各profile配置
   # 确认每个Profile有独立的config.yaml和SOUL.md
   ```

4. **Soul配置审查**
   ```bash
   # 读取各Profile的SOUL.md，检查安全规则设置
   # 确认身份识别规则放在最前面
   ```

5. **Skills/Hooks/MCP状态检查**
   ```bash
   # 检查已安装的Skill、Hook、MCP服务器
   # 确认native-mcp Skill存在，且没有为每个MCP创建单独的Skill目录
   ```

6. **运行状态检查**
   ```bash
   # 查看Gateway进程列表和状态
   # 确认每个Profile有独立的Gateway进程
   ```

7. **整理成结构化报告**

---

## ⚠️ 关键安全注意事项

1. **Profile隔离是逻辑隔离不是物理隔离**
   - default profile可以访问所有profile的文件
   - 给他人使用必须新建独立profile并设置目录限制
   - 在profile的SOUL.md中明确设置文件访问规则

2. **输出过滤必须在Soul层面强制执行**
   - 禁止输出服务器目录结构
   - 禁止输出完整文件路径
   - 禁止输出IP地址和端口
   - 禁止输出进程列表和系统信息

3. **审批机制是最后一道防线**
   - 危险操作必须手动审批
   - 不要轻易启用auto_approve
   - Cron任务默认deny

---

## 📝 配置修改建议

| 场景 | 推荐操作 |
|------|----------|
| 给他人创建专属助手 | 新建独立Profile，设置Soul安全规则和目录限制 |
| 需要扩展功能 | 安装或开发对应Skill |
| 需要精细化权限控制 | 开发Hook进行pre_gateway_dispatch拦截 |
| 需要连接外部工具 | 通过MCP协议集成 |
| 需要修改安全规则 | 编辑对应Profile的SOUL.md（放在最前面！） |

---

> 💡 **记住**：kaka的多Profile架构通过独立Gateway进程 + Soul层面安全规则实现租户隔离，这是一个灵活但需要谨慎配置的系统。每次修改配置后都应该进行审查和验证！