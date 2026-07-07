# Others 其他能力域

> Wiki / Task / OKR / Approval / Attendance / Whiteboard 六合一。遇到报错先看 [pitfalls.md](pitfalls.md)。

---

## 📚 Wiki 知识库

### Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+space-list` | 列知识空间 | — |
| `+space-create` | 创建知识空间 | `--name` `--description` |
| `+delete-space` | 删除知识空间（异步） | `--space-id` `--yes` |
| `+member-list` `+member-add` `+member-remove` | 空间成员 | `--space-id` `--member-id`（wiki 域**直接叫** `member-*`，不带 `space-` 前缀） |
| `+node-list` | 节点列表（子节点） | `--space-id` `--parent-node-token` |
| `+node-get` | 节点详情 | `--node-token` |
| `+node-create` | 建节点（docx/sheet/base） | `--space-id` `--parent-node-token` `--obj-type` `--title` |
| `+node-delete` | 删节点（异步） | `--node-token` `--yes` |
| `+move` | 移动节点（含从 Drive 移入 Wiki） | `--node-token` |
| `+node-copy` | 复制节点 | `--node-token` |

> ⚠️ CLI **不支持**：`+space-get` / `+search`（wiki 域没有独立搜索，用 `drive +search --space-ids <space_id>`）；成员命令是 `+member-*`，**不是** `+space-member-*`。

### 流程：在知识库里建文档

```bash
# 1. 找目标空间
SPACE_ID=$(lark-cli wiki +space-list | jq -r '.data.spaces[] | select(.name=="工程知识库") | .space_id')

# 2. 找父节点（可选，直接建到根）
PARENT=$(lark-cli wiki +node-list --space-id $SPACE_ID | jq -r '.data.nodes[0].node_token')

# 3. 建 docx 节点
lark-cli wiki +node-create --space-id $SPACE_ID \
  --parent-node-token $PARENT \
  --obj-type docx --title "新文档标题"

# 4. 知识库内搜文档：wiki 域无 +search，用 drive +search
lark-cli drive +search --query "关键词" --space-ids $SPACE_ID --format json
```

**⚠️ 陷阱**：wiki URL 类型未明示时（`feishu.cn/wiki/<token>`）必须先 `drive +inspect --url` 解析真实类型。

---

## ✅ Task 任务

### Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+create` | 建任务 | `--summary` `--due-time` `--assignees` |
| `+get` | 任务详情 | `--task-guid` |
| `+update` | 改任务 | `--task-guid` `--summary` `--due-time` |
| `+complete` `+uncomplete` | 完成/撤销 | `--task-guid` |
| `+delete` | 删任务 | `--task-guid` `--yes` |
| `+search` | 搜任务 | `--query` |
| `+get-my-tasks` | 我的任务 | `--status` |
| `+subtask-create` | 建子任务 | `--parent-guid` |
| `+collaborator-add` `+collaborator-remove` | 协作人 | `--task-guid` `--user-ids` |
| `+tasklist-*` | 清单管理 | — |

### 流程：建任务 + 分派协作者

```bash
lark-cli task +create \
  --summary "完成月报" \
  --description "包含 KPI 与风险项" \
  --due-time "2026-07-15T18:00:00+08:00" \
  --assignees ou_a,ou_b \
  --tasklist-guid <可选清单> \
  --format json
```

**关联能力**：
- **日报/周报**：直接调 `lark-workflow-standup-report` 技能
- **看我今天的日程+任务**：`lark-workflow-standup-report`

---

## 🎯 OKR

### Shortcut

| Shortcut | 用途 |
|---|---|
| `+cycle-list` | 列周期（`--user-id`） |
| `+cycle-detail` | 周期详情（含目标+KR） |
| `+patch` | 更新目标/KR |
| `+progress-list` `+progress-get` `+progress-create` `+progress-update` `+progress-delete` | 进展记录 |
| `+indicator-update` | 更新量化指标 |
| `+reorder` `+weight` | 排序/权重 |
| `+upload-image` | 上传图片 |
| `+batch-create` | 批量建目标/KR |

> ⚠️ CLI **不支持**：`+list-periods` / `+list-objectives` / `+list-krs`（旧文档命名）。查目标+KR 用 `+cycle-detail` 一次拿全。

### 流程：查主人的 OKR

```bash
# 1. 列周期，找当前季度
lark-cli okr +cycle-list \
  --user-id {{FEISHU_OPEN_ID}} --format json
PERIOD_ID=<当前季度 id>

# 2. 拿周期详情（目标 + KR 都在里面）
lark-cli okr +cycle-detail --cycle-id $PERIOD_ID \
  --user-id {{FEISHU_OPEN_ID}} --format json
```

---

## 📝 Approval 审批

> ⚠️ approval 域**没有 shortcut**，全部是 subcommand 结构。手写起来啰嗦且需要 `--yes` 二次确认，**优先直接调 `lark-approval` 技能**（已封装好、参数更友好）。

### 原生 subcommand 结构

| 命令 | 用途 |
|---|---|
| `approval approvals search` | 搜审批定义 |
| `approval approvals get` | 定义详情（表单字段） |
| `approval instances create` | 发起审批实例（**high-risk-write**，需 `--yes`） |
| `approval instances get` | 实例详情 |
| `approval instances initiated` / `cc` | 我发起/抄送我的 |
| `approval tasks query` / `approve` / `reject` / `transfer` / `add_sign` / `remind` / `rollback` | 待办任务操作 |
| `approval instances cancel` | 撤回 |

### 建议流程

```bash
# 首选：调 lark-approval 技能，已封装参数校验和错误码
# 手写场景：
lark-cli approval approvals search --approval-name "报销单" --format json
lark-cli approval approvals get --approval-code <code> --format json
# 发起（必须先让用户明确确认再加 --yes）
lark-cli approval instances create --approval-code <code> \
  --user-id ou_xxx --form '[{"id":"widget1","type":"input","value":"..."}]' --yes
```

---

## ⏰ Attendance 考勤

> ⚠️ attendance 域**没有 shortcut**，只有 `attendance user_tasks query` 一个 subcommand。

```bash
lark-cli attendance user_tasks query \
  --user-ids {{FEISHU_OPEN_ID}} \
  --check-date-from 20260701 \
  --check-date-to 20260731 \
  --format json
```

**日期格式**：`YYYYMMDD`（数字，非 ISO）。

---

## 🎨 Whiteboard 画板

### Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+query` | 查/导出画板（image/svg/code/raw） | `--whiteboard-token` `--output_as` `--output` |
| `+update` | 更新画板内容（mermaid/plantuml/DSL，见 `lark-whiteboard` 技能） | `--whiteboard-token` |

> ⚠️ CLI **不支持**：`+get` / `+export` / `+node-list`。导出图片用 `+query --output_as image --output <dir>`。

### 流程：导出画板为 PNG

```bash
lark-cli whiteboard +query \
  --whiteboard-token <token> \
  --output_as image \
  --output ./whiteboard-out
```

**能做的事**：架构图 / 流程图 / 思维导图，都在画板里；渲染质量 API 直出 PNG 比 SVG 稳。

---

## 🔗 与其他技能的联动

| 需求 | 推荐技能 |
|---|---|
| 会议纪要汇总报告 | `lark-workflow-meeting-summary` |
| 日程+任务日报/周报 | `lark-workflow-standup-report` |
| 审批完整流程 | `lark-approval` |
| 知识库标准化搭建 | `feishu-knowledge-base-manager` |
| 新建文档归档 | `feishu-doc-auto-archiving` |
| Markdown 落地飞书 | `lark-markdown` |
| 探索 CLI 未包装的 OpenAPI | `lark-openapi-explorer` |

**记住**：这些**领域技能**比手写 CLI 循环更稳、更快，遇到对应场景优先加载。
