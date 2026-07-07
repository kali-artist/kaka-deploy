---
name: permission-management
description: "全自动化权限管理skill，三层Hook联动实现无死角权限管控，零配置开箱即用，支持自然语言调用。"
version: 1.4.0
author: kaka-deploy
metadata:
  hermes:
    tags: [权限管理, gateway-hook, skill-hook, tool-hook, 安全审计]
    required_commands: [python3]
    required_environment_variables: []
    auto_config_hooks: true
---

# 权限管理skill使用说明

## 🌟 核心特性
- 三层Hook联动防护：网关层+技能层+工具层，前置校验符合主人偏好
- 零学习成本：支持自然语言调用，不用记复杂指令
- 开箱即用：默认配置仅{{MASTER_NAME}} 主人拥有全部权限，其他用户默认最小权限
- 自动权限下放：给用户开放技能后自动放行该技能必需的工具，无需额外配置
- 完整审计日志：所有权限变更、拦截操作全记录，可溯源
- 自动定期报表：每3天自动生成权限审计报表，发送到主人微信，历史报表可回溯
- Profile 级审计：支持审计 secondary profile 的 toolset 白名单、路径隔离、命令拦截、技能目录隔离，输出结构化飞书审计报告

## 📖 使用方式（直接说人话就行）
```
# 查看当前权限配置
查看权限配置
权限管理 查看规则

# 权限配置
给用户xxx开放技能 小红书文案生成
禁止用户xxx调用工具 terminal write_file
允许管理员用户调用所有工具
仅主人可以修改权限配置

# 多平台身份管理
添加其他平台用户为超级管理员
添加超级管理员 <平台用户ID>
移除超级管理员 <平台用户ID>

# 防护控制
开启全局权限防护
关闭全局权限防护

# 日志查询
查看最近100条权限拦截日志
导出最近一周的权限审计记录

# 远程Hermes实例操作
清理远程实例旧权限系统残留
权限清理 远程 <SSH地址> <账号> <密码/密钥路径>
一键部署当前权限系统到远程实例
部署权限系统到远程 <SSH地址> <账号> <密码/密钥路径>
```

### 🔧 内置默认安全规则
1. 超级管理员（{{MASTER_NAME}} 主人：微信ID {{WECHAT_USER_ID}}@im.wechat、飞书ID {{FEISHU_OPEN_ID}}、飞书ID {{FEISHU_OPEN_ID}}）拥有所有权限，不受任何限制，天然支持跨网关身份识别
2. 其他用户默认仅可调用普通查询类技能，完全禁止所有写/执行类工具权限
3. 危险操作（删除文件、修改系统配置、高危命令）默认仅管理员可执行
4. 技能仅可调用自身预先声明的工具列表，越权调用自动拦截

### 🧹 旧权限系统清理检查清单（必做）
清理任何旧权限系统时必须逐一检查以下项目，确保无残留：
1. 权限相关技能目录完全删除
2. `~/.hermes/hooks/`下所有权限相关Hook目录删除
3. `~/.hermes/`下所有权限配置文件（含备份）删除
4. `~/.hermes/logs/`下所有权限相关日志删除
5. 全局`config.yaml`无任何权限Hook残留配置
6. 重启网关验证运行正常无报错

---

## 🔍 身份审计与权限配置同步

当用户要求“查看/清理/审计当前超级管理员名单”或询问“把机器人加入飞书群后别人@会不会回复”时，按以下流程处理。

### 1. 区分两层权限控制
- **网关层准入**（如飞书 `allowed_users`、微信 `WEIXIN_ALLOW_ALL_USERS`）：控制“谁能把消息发进来”。被拦截时对方完全无感知。
- **权限层授权**（本 skill 的 `super_admins`、`user_permissions`）：控制“进来的人能做什么”。
- 只有同时通过两层控制的用户才会得到回复；普通用户即使通过了网关层，也受权限层限制。

### 2. 识别身份 ID 类型
审计时必须确认每个 ID 的真实含义，不要把不同类型的标识混用：

| 类型 | 示例 | 能否用于权限匹配 | 说明 |
|------|------|-----------------|------|
| 平台用户 open_id | 飞书 `ou_xxxxxxxx` | ✅ 可以 | 个人用户唯一标识 |
| 平台会话/群聊 ID | 飞书 `oc_xxxxxxxx` | ❌ 不可以 | 群或单聊会话标识，不是个人用户 |
| 用户名/显示名 | 飞书 `{{FEISHU_USER_ID}}` | ❌ 不可以 | 仅用于展示，权限系统按 ID 匹配 |
| 微信用户 ID | `xxxx@im.wechat` | ✅ 可以 | 微信通道用户唯一标识 |

### 3. 审计来源与清理决策
对每个超级管理员 ID 执行：
1. 用 `fact_store` 或 `session_search` 追溯该 ID 的添加背景。
2. 只保留用户明确确认过的**个人用户 ID**。
3. 必须移除以下类型：
   - 用户名/显示名；
   - 会话/群聊 ID；
   - 来源不明、无用户明确确认的用户 ID。
4. 修改后**同步更新所有相关配置**，避免配置文件重置后回退到旧名单：
   - `config/permissions.yaml`
   - `scripts/permission_core.py` 中的 `DEFAULT_PERMISSIONS["super_admins"]`
   - `SKILL.md` 中的默认规则示例
   - 网关层的 `allowed_users`（如 `~/.hermes/config.yaml` 中飞书网关配置）

### 4. 群组 @ 行为说明
- 飞书应用被加入群聊后，只有 `allowed_users` 中的用户在群里 @ 机器人，消息才会进入 Hermes 处理。
- 不在 `allowed_users` 中的群成员 @ 机器人时，网关层静默丢弃，不会回复。
- 超级管理员在群里 @ 机器人时，权限层会按 `super_admins` 规则放行所有操作。

---

# 报表与通知
- 内置3天自动报表功能：默认每3天生成一次权限审计报表，包含Hook状态、权限策略、操作日志
- 报表默认发送到{{MASTER_NAME}} 主人微信，可在scripts/generate_report.py中配置微信网关地址
- 报表生成后默认保存到reports/目录下，历史报表可回溯

---

# 🔍 权限合规监控与故障排查

当用户要求“运行权限合规监控检查”“检查权限系统是否正常”“权限监控 --once”等时，按以下流程执行。

## 1. 定位监控脚本
用户/定时任务可能引用**已废弃的旧路径家族**（这些文件在当前部署中都不存在）：
```bash
# 旧路径示例（均已废弃 — 都映射到本节的处理流程）
python3 ~/.hermes/skills/devops/permission-management/scripts/monitor.py --once
python3 ~/.hermes/skills/devops/permission-management/scripts/audit.py --fix
python3 ~/.hermes/skills/devops/permission-management/scripts/*.py
```
**统一改为执行实际报表脚本**（无论旧路径叫 monitor/audit/report 哪个名字）：
```bash
python3 ~/.hermes/skills/devops/permission-management/scripts/generate_report.py
```

### 定期审计工作流（每周/每3天 cron 触发时）
除了跑 `generate_report.py` 之外，一次完整审计应该包含以下检查（顺序执行）：
1. `find ~/.hermes/hooks -name "audit.log" -o -name "permissions.yaml"` — 检查符号链接分散文件（见第 6 节，有则清理）
2. `grep -A3 'hooks:' ~/.hermes/config.yaml` — 验证 Hook 路径指向 `scripts/` 目录（非 `~/.hermes/hooks/` 符号链接）
3. `find ~/.hermes/skills -maxdepth 2 -type d -empty` — 检查技能目录是否有异常空目录（`.hub/quarantine` 和 `education/lathe-*` 是正常的）
4. 若发现引用旧路径的 cron job，用 `cronjob action=update` 将其 prompt 中的脚本路径修正到当前有效路径，避免下次运行再走一遍寻路弯路
5. **Profile 级权限审计**（见下方专节，审计所有 secondary profile 时必做）

## 2. 确定实际注册的 Hook 路径（关键！）

config.yaml 中注册的 Hook 路径才是实际生效的。必须先查 config.yaml：
```bash
grep -A3 'hooks:' ~/.hermes/config.yaml
```

常见两种情况：
- **路径指向 `scripts/` 目录**（推荐）：Hook 与 permission_core.py 同目录，路径解析正确，审计日志写入中心路径。
- **路径指向 `~/.hermes/hooks/` 目录**（旧部署）：Hook 通过符号链接加载 permission_core.py，存在路径解析问题（见下方第 6 节）。

## 3. 检查 Hook 是否真正可用（不要只看文件存在）
报表只会显示 Hook 文件是否存在，但 Hook 文件可能因缺少依赖而无法运行。必须实际调用 Hook 验证。

**测试 config.yaml 中注册的实际 Hook 路径**（以 scripts 目录为例）：
```python
import json, subprocess, sys, os

scripts_dir = os.path.expanduser("~/.hermes/skills/devops/permission-management/scripts")

hooks = [
    ("gateway", os.path.join(scripts_dir, "gateway_pre_hook.py"), {"user_id": "test_user", "content": "hello"}),
    ("skill", os.path.join(scripts_dir, "skill_pre_exec_hook.py"), {"user_id": "test_user", "skill_name": "test-skill"}),
    ("tool", os.path.join(scripts_dir, "tool_pre_call_hook.py"), {"user_id": "test_user", "tool_name": "terminal", "args": "ls -la"}),
]

for name, path, payload in hooks:
    proc = subprocess.run([sys.executable, path], input=json.dumps(payload), capture_output=True, text=True, timeout=10)
    print(f"{name}: exit={proc.returncode}, stdout={proc.stdout.strip()[:200]}, stderr={proc.stderr.strip()[:200]}")
```

测试后检查中心审计日志是否有写入：
```bash
cat ~/.hermes/skills/devops/permission-management/logs/audit.log
```
如果中心日志为空但 Hook 返回了正确结果，说明 Hook 可能加载了符号链接版本的 permission_core.py，审计日志写到了错误位置（见第 6 节）。

## 3. 常见异常：ModuleNotFoundError: No module named 'permission_core'
如果Hook报错：
```
ModuleNotFoundError: No module named 'permission_core'
```
说明Hook脚本通过 `from permission_core import permission_manager` 导入核心模块，但 `permission_core.py` 没有部署到Hook所在目录。

### 修复方法：创建符号链接
```bash
SKILL_CORE="/home/ubuntu/.hermes/skills/devops/permission-management/scripts/permission_core.py"
ln -s "$SKILL_CORE" /home/ubuntu/.hermes/hooks/gateway/pre/permission_core.py
ln -s "$SKILL_CORE" /home/ubuntu/.hermes/hooks/skill/pre_exec/permission_core.py
ln -s "$SKILL_CORE" /home/ubuntu/.hermes/hooks/tool/pre_call/permission_core.py
```
然后确保Hook目录权限为755：
```bash
chmod 755 /home/ubuntu/.hermes/hooks/gateway/pre
chmod 755 /home/ubuntu/.hermes/hooks/skill/pre_exec
chmod 755 /home/ubuntu/.hermes/hooks/tool/pre_call
```

## 4. 验证修复结果
分别用超级管理员ID和普通用户ID测试三条路径：
- 超级管理员：gateway/skill/tool 均应放行
- 普通用户：gateway 放行，skill/tool 应拒绝（除非在允许列表中）

如果普通用户测试返回 `{"allowed": false}` 且exit code为1，这是**预期行为**，不是故障。

## 5. 生成监控报告
修复后重新生成报表，并保存一份结构化合规报告到 `reports/` 目录，包含：
- 发现的异常
- 修复措施
- 验证结果
- 当前系统状态
- 后续建议

## 6. 已知问题：符号链接路径解析导致审计日志分散

### 症状
中心审计日志 `~/.hermes/skills/devops/permission-management/logs/audit.log` 为空，但 Hook 功能正常（返回正确的 allow/deny）。

### 根因
`permission_core.py` 使用 `os.path.dirname(os.path.abspath(__file__))` 计算 SKILL_DIR。当通过 `~/.hermes/hooks/` 下的符号链接加载时，`__file__` 是符号链接路径而非真实路径，导致：
- 审计日志写入 `~/.hermes/hooks/{gateway,skill,tool}/logs/audit.log`（分散）
- 配置文件读取/创建 `~/.hermes/hooks/{gateway,skill,tool}/config/permissions.yaml`（自动生成默认配置，与中心配置不同步）

### 检测方法
```bash
# 检查是否有分散的审计日志和配置
find ~/.hermes/hooks -name "audit.log" -o -name "permissions.yaml" 2>/dev/null
```
如果找到这些文件，说明存在符号链接路径问题。

### 配置漂移风险
分散的 `permissions.yaml` 是初始化时自动生成的 `DEFAULT_PERMISSIONS` 副本，不会随后续中心配置更新而同步。可能包含已从中心配置中清除的无效 super_admin 条目（如用户名、群聊 ID）。

### 修复方法
**方案 A（推荐）：确保 config.yaml 指向 scripts 目录**
```yaml
# config.yaml 中 Hook 路径指向 scripts 目录（与 permission_core.py 同目录）
hooks:
  gateway:
    pre_hook:
    - command: python3 /home/ubuntu/.hermes/skills/devops/permission-management/scripts/gateway_pre_hook.py
```
这样 `__file__` 就是真实路径，无需修改代码。

**方案 B：修改 permission_core.py 使用 realpath**
```python
# 将 abspath 改为 realpath，跟随符号链接
SKILL_DIR = os.path.dirname(os.path.realpath(__file__))
```

**清理分散文件**（无论选哪个方案）：
```bash
rm -rf ~/.hermes/hooks/gateway/{config,logs}
rm -rf ~/.hermes/hooks/skill/{config,logs}
rm -rf ~/.hermes/hooks/tool/{config,logs}
```

## 8. Profile 级权限审计（secondary profile 审计专节）

当用户要求"检查/审计所有 profile 的权限""输出权限审计报告""检查 tiao（或其他 profile）的权限策略"时，在主 profile 审计基础上，还需逐一审计每个 secondary profile。

### 审计维度与检查命令

| 维度 | 检查内容 | 命令 |
|------|---------|------|
| **网关准入** | DM/group 策略、allowed_users | `python3 -c "import yaml; c=yaml.safe_load(open('~/.hermes/profiles/XXX/config.yaml'.replace('~',os.path.expanduser('~')))); print(c.get('feishu',{}), c.get('weixin',{}))"` |
| **Toolset 白名单** | 该 profile 开放的工具集 | 同上，取 `c.get('toolsets')` |
| **路径隔离 Hook** | 独立隔离 Hook 及其路径规则 | `cat ~/.hermes/profiles/XXX/config.yaml` 中 `hooks` 段 → 找到 hook 脚本路径 → `cat` 该脚本，检查允许/禁止路径列表 |
| **命令拦截** | 危险命令黑名单 | 同上，从 hook 脚本中提取 blocked commands 列表 |
| **技能目录隔离** | 独立技能目录 vs 主 profile | `ls ~/.hermes/profiles/XXX/skills/` 对比 `ls ~/.hermes/skills/` |
| **专属技能** | profile 个人技能 | `find ~/.hermes/profiles/XXX/skills -name SKILL.md` |
| **跨平台风险** | 微信/其他网关是否配置 | 检查 config.yaml 中 weixin 段是否为空 |

### 审计报告标准结构（输出飞书文档时参考）

1. **总体架构**：三层防护 + Profile 隔离架构图
2. **超级管理员配置**：管理员名单 + 权限 + 同步要求
3. **三层 Hook 防护**：网关/技能/工具层各检查项矩阵
4. **网关层准入**：飞书/微信 allowed_users 配置
5. **各 Profile 权限体系**：每个 profile 的 toolset/路径/命令/技能隔离详情 + 安全评级表
6. **审计日志**：日志位置 + 最近记录 + 已知限制
7. **定期报表机制**：周期/发送目标/存档
8. **安全评估与建议**：整体评级 + 改进建议表（按优先级）
9. **配置文件索引**：所有相关文件路径速查表

### 安全评级标准

| 评级 | 含义 | 判定条件 |
|------|------|---------|
| 🟢 合理/良好 | 配置严密无风险 | 隔离完整、无异常配置 |
| 🟡 中等 | 有改进空间 | 功能可用但有可优化项 |
| 🔴 风险 | 存在安全隐患 | 配置缺失或有异常 ID |

---

## 7. 已知限制：超级管理员操作无审计日志

`permission_core.py` 中超级管理员直接返回放行结果，不调用 `_log_audit()`。这意味着：
- 审计日志为空不代表系统无人使用，可能仅超级管理员在操作
- 超级管理员的所有操作（包括危险操作）无审计追踪
- 如需完整合规审计，建议在超级管理员放行路径也增加 `_log_audit()` 调用