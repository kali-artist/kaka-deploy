# Calendar / Mail 日历与邮件

> 遇到报错先看 [pitfalls.md](pitfalls.md)。发邮件、代人发日程用 `--as bot`；查自己日历/邮箱用 `--as user`。

## Calendar Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+agenda` | 查看某日/某周日程 | `--date` `--range` |
| `+search-event` | 搜日程 | `--query` |
| `+create` | 建日程 | `--title` `--start` `--end` `--attendee-ids` |
| `+update` | 改日程 & 增删参与人 | `--event-id` `--add-attendee-ids` `--remove-attendee-ids` |
| `+freebusy` | 查忙闲 | `--user-ids` `--start` `--end` |
| `+suggestion` | 推荐时段（智能建议） | `--attendee-ids` `--duration-minutes` `--start` `--end` |
| `+rsvp` | 接受/拒绝日程 | `--event-id` `--status` |
| `+room-find` | 找会议室候选 | `--start` `--end` |
| `+meeting` | 会议详情 | `--event-id` |

> ⚠️ CLI **不支持**：`+search` / `+list` / `+delete` / `+event-get` / `+meeting-room-search` / `+meeting-room-book` / `+attendee-add` / `+attendee-remove` / `+recommend-time`。删日程、独立会议室预定需走原生 API（`lark-openapi-explorer`）。参与人增删并入 `+update`。

## Mail Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+send` | 发邮件 | `--to` `--subject` `--body` |
| `+reply` `+reply-all` `+forward` | 回复/全部回复/转发 | `--message-id` |
| `+draft-create` `+draft-edit` `+draft-send` | 草稿管理 | `--to` `--subject` |
| `+message` | 单封邮件详情 | `--message-id` |
| `+messages` | 批量拉邮件详情 | `--message-ids` |
| `+thread` | 会话线程 | `--thread-id` |
| `+triage` | 邮件分类 | — |

> ⚠️ CLI **不支持**：`+search` / `+get` / `+download-attachment` / `+folder-list` / `+mailgroup-search`。搜邮件用 `himalaya` 技能或原生 API；附件下载/文件夹列表需 `lark-openapi-explorer`。

---

## 流程 A：查日程（今日/本周）

```bash
# 今日日程
lark-cli calendar +agenda --date today

# 指定日期
lark-cli calendar +agenda --date 2026-07-10 --format json

# 一周日程
lark-cli calendar +agenda --range week --format json

# 关键词搜
lark-cli calendar +search-event --query "周会" --format json
```

## 流程 B：建日程（含邀请人）

```bash
# 1. 找参与人 open_id
lark-cli contact +search-user --query "李四" --format json

# 2. 查空闲时段（可选）
lark-cli calendar +freebusy \
  --user-ids ou_a,ou_b \
  --start "2026-07-10T09:00:00+08:00" \
  --end   "2026-07-10T18:00:00+08:00"

# 3. 建日程
lark-cli calendar +create \
  --title "项目周会" \
  --description "本周进度对齐" \
  --start "2026-07-10T14:00:00+08:00" \
  --end   "2026-07-10T15:00:00+08:00" \
  --attendee-ids ou_a,ou_b \
  --reminder-minutes 15

# 4. （可选）找会议室候选
lark-cli calendar +room-find \
  --start "2026-07-10T14:00:00+08:00" \
  --end   "2026-07-10T15:00:00+08:00" --format json
# 具体预定会议室：CLI 未包装，需 lark-openapi-explorer
```

**⚠️ 时间格式**：**必须** ISO 8601 带时区（`+08:00`），不带时区会被当 UTC。

## 流程 C：改日程 / 增删参与人 / RSVP

```bash
# 改时间
lark-cli calendar +update --event-id <id> \
  --start "2026-07-11T10:00:00+08:00" \
  --end   "2026-07-11T11:00:00+08:00"

# 增删参与人（并入 +update）
lark-cli calendar +update --event-id <id> --add-attendee-ids ou_x
lark-cli calendar +update --event-id <id> --remove-attendee-ids ou_x

# RSVP（accept/decline/tentative）
lark-cli calendar +rsvp --event-id <id> --status accept

# 删日程：CLI 未包装，走 lark-openapi-explorer
```

## 流程 D：智能推荐时段

```bash
# 30 分钟会议，3 人找共同空闲
lark-cli calendar +suggestion \
  --attendee-ids ou_a,ou_b,ou_c \
  --duration-minutes 30 \
  --start "2026-07-10T09:00:00+08:00" \
  --end   "2026-07-10T18:00:00+08:00"
```

---

## 流程 E：发邮件（bot 身份）

```bash
# 简单文本
lark-cli mail +send --as bot \
  --to "someone@example.com" \
  --subject "会议纪要" \
  --body "详见附件"

# HTML + 抄送 + 附件
lark-cli mail +send --as bot \
  --to "a@example.com,b@example.com" \
  --cc "c@example.com" \
  --bcc "d@example.com" \
  --subject "月度汇报" \
  --body-html @./body.html \
  --attachment ./report.pdf,./chart.png
```

## 流程 F：回复/转发/草稿

```bash
# 回复
lark-cli mail +reply --as bot --message-id <mid> \
  --body "已收到，本周内处理"

# 转发
lark-cli mail +forward --as bot --message-id <mid> \
  --to "colleague@example.com" --body "请你跟进"

# 存草稿（不直接发）
DRAFT_ID=$(lark-cli mail +draft-create --as bot \
  --to "a@example.com" --subject "待发" --body "内容" \
  | jq -r '.data.draft.draft_id')

# 后续发送草稿
lark-cli mail +draft-send --as bot --draft-id $DRAFT_ID
```

## 流程 G：读邮件（单封/批量）

```bash
# 单封
lark-cli mail +message --message-id <mid> --format json

# 批量（>20 自动分批）
lark-cli mail +messages --message-ids <mid1>,<mid2>,<mid3> --format json

# 搜邮件：CLI 未包装，用 himalaya 技能或 lark-openapi-explorer
# 附件下载：走 lark-openapi-explorer
```

---

## 常见陷阱

| 症状 | 原因 | 修复 |
|---|---|---|
| 日程时间对不上 | 没带时区 | 时间**必须** `YYYY-MM-DDTHH:MM:SS+08:00` |
| freebusy 拿不到数据 | 用户未开放日历权限 | 提示主人：日历需被查询者授权 |
| 邮件发不出去 | 用了 `--as user` | 发邮件用 `--as bot` |
| 附件不生效 | 路径是绝对路径 | 用相对路径 `./file.pdf` |
| 会议室预定失败 | 已被占用或无权限 | 换会议室或先 `+freebusy` 查会议室占用 |
| `+create` 无返回 event_id | 未加 `--format json` | 加 `--format json` 再 `jq` 提取 |
