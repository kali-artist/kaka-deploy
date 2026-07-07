# kaka-deploy

> AI 辅助 Hermes Agent 一键部署工具

从源实例打包技能/配置/Soul，到目标实例一键部署。支持占位符脱敏、联动组配置、AI 辅助填表。

## 快速开始

### 源实例打包

```bash
python3 kaka-deploy.py pack
```

扫描 `~/.hermes/skills/` 和 `~/.agents/skills/`，自动：
- 排除运行时文件（reports/logs/skillopt_runs）
- 替换个性化值为占位符（微信ID/飞书ID/IP/GitHub用户名等）
- 输出到 `skills-pack/` 目录

### 目标实例部署

```bash
# AI 辅助模式（推荐）
python3 kaka-deploy.py deploy --ai-assist

# 手动模式
python3 kaka-deploy.py deploy
```

部署步骤：
1. 安装 Hermes Agent
2. 写入 SOUL.md / MEMORY.md / USER.md / config.yaml
3. 复制技能包（hermes + lark）
4. 注册 Hooks
5. 启动 Gateway 服务

### 状态检查

```bash
python3 kaka-deploy.py status
```

### 查看技能包

```bash
python3 kaka-deploy.py list
```

## 目录结构

```
kaka-deploy/
├── kaka-deploy.py          # 主入口 CLI
├── scripts/
│   └── pack_skills.py      # 打包脚本
├── lib/
│   ├── ai.py               # AI 辅助模块
│   └── deploy.py           # 部署执行模块
├── config-templates/
│   ├── soul.template.md    # Soul 模板（占位符）
│   ├── memory.template.md  # 记忆模板
│   ├── env.template.yaml   # 环境变量模板
│   └── gateway.template.yaml
├── skills-pack/
│   ├── manifest.json       # 技能清单+联动组
│   ├── hermes/             # Hermes 技能包
│   └── lark/               # Lark 技能包
└── README.md
```

## 占位符列表

| 占位符 | 说明 | 来源 |
|--------|------|------|
| `{{AGENT_NAME}}` | 机器人名称 | identity.agent_name |
| `{{MASTER_NAME}}` | 主人名称 | identity.master_name |
| `{{WECHAT_USER_ID}}` | 微信用户ID | wechat.user_id |
| `{{FEISHU_USER_ID}}` | 飞书用户ID | feishu.user_id |
| `{{GITHUB_USERNAME}}` | GitHub用户名 | github.username |
| `{{SERVER_IP}}` | 服务器IP | server.ip |
| `{{CLOUDFLARE_ACCOUNT_ID}}` | CF账号ID | cloudflare.account_id |

## 联动组

某些技能需要配套配置才能工作：

| 组 | 技能 | 需要的配置 |
|----|------|-----------|
| ① 飞书 | feishu-doc-automation, lark-* | feishu.app_id, app_secret |
| ③ Cloudflare | cloudflare-pages-deployment | cloudflare.account_id, api_token |
| ⑤ GitHub | github-* | github.username, token |
| ⑦ 微信 | wechat-pc-robot-deployment | wechat.user_id |
