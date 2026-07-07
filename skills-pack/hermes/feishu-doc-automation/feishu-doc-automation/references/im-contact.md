# IM / Contact 即时通讯与通讯录

> 遇到报错先看 [pitfalls.md](pitfalls.md)。**发消息给他人/群内发消息必须用 `--as bot`**。

## IM Shortcut 清单

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+chat-search` | 搜索群聊 | `--query` |
| `+chat-list` | 列出群 | — |
| `+chat-get` | 群详情 | `--chat-id` |
| `+chat-create` | 建群 | `--name` `--user-ids` |
| `+chat-members-list` | 群成员管理（**仅列表**；加/删成员 CLI 未包装，走 `lark-openapi-explorer` 或 `chats.members` 原生子命令） | `--chat-id` |
| `+chat-messages-list` | 拉群历史 | `--chat-id` `--start` `--end` |
| `+messages-search` | 跨会话消息搜索（user-only） | `--query` |
| `+messages-mget` | 批量拉消息详情 | `--message-ids` |
| `+messages-send` | 发消息 | `--user-id` **或** `--chat-id`；`--text`/`--markdown`/`--image`/`--file`/`--video`/`--audio` 或 `--content`+`--msg-type` |
| `+messages-reply` | 回复消息（支持 thread） | `--message-id` `--text`/`--content` |
| `+messages-resources-download` | 下载消息附件 | `--message-id` `--file-key` |
| `+threads-messages-list` | 拉话题回复串 | `--message-id`（om_/omt_） |

## Contact Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+search-user` | 按姓名/邮箱搜人 | `--query` |
| `+get-user` | 用户详情 | `--user-id` `--user-id-type` |
| `+department-list` | 部门列表 | `--parent-id` |
| `+department-users` | 部门下用户 | `--department-id` |

---

## 流程 A：找群 → 拉消息 → 关键词过滤

```bash
# 1. 找群（拿 chat_id）
lark-cli im +chat-search --query "群名关键词" --format json
CHAT_ID=oc_xxx

# 2. 拉群消息（按时间段）
lark-cli im +chat-messages-list --chat-id $CHAT_ID \
  --start "2026-01-01" --end "2026-01-31" --format json

# 3. 或跨会话搜关键词
lark-cli im +messages-search --query "关键词" --format json
```

## 流程 B：发消息（bot 身份）

```bash
# 纯文本（推荐 --text，自动包装 JSON）
lark-cli im +messages-send --as bot \
  --user-id ou_xxx --text "消息内容"

# 群里发
lark-cli im +messages-send --as bot \
  --chat-id oc_xxx --text "群消息内容"

# markdown（自动转 post + 图片 URL 解析）
lark-cli im +messages-send --as bot --user-id ou_xxx \
  --markdown "# 标题\n**加粗** [链接](https://x)"

# 图片 / 文件 / 视频（直接给路径或 URL，CLI 自动上传）
lark-cli im +messages-send --as bot --user-id ou_xxx --image ./x.png
lark-cli im +messages-send --as bot --user-id ou_xxx --file  ./a.pdf
lark-cli im +messages-send --as bot --user-id ou_xxx \
  --video ./v.mp4 --video-cover ./cover.jpg   # video 必须搭配 cover

# 卡片（interactive）用 --content @file + --msg-type
lark-cli im +messages-send --as bot --chat-id oc_xxx \
  --msg-type interactive --content @./card.json
```

**目标选择**：`--user-id ou_xxx` 或 `--chat-id oc_xxx`（互斥，必须其一）。已废弃 `--receive-id-type` / `--receive-id`。

## 流程 C：找人 → 拿 open_id

```bash
# 按姓名搜
lark-cli contact +search-user --query "张三" --format json

# 按邮箱搜
lark-cli contact +search-user --query "zhang@example.com" --format json

# 主人的两个 open_id 已知（勿再搜）：
# {{FEISHU_OPEN_ID}}
# {{FEISHU_OPEN_ID}}
```

## 流程 D：建群 + 拉人 + 发首帖

```bash
# 建群
CHAT_ID=$(lark-cli im +chat-create --as bot \
  --name "项目群" --user-ids ou_a,ou_b --format json | jq -r '.data.chat_id')

# 加人：CLI shortcut 未包装 +chat-members-add
# 用原生子命令：
lark-cli im chats.members create --chat-id $CHAT_ID \
  --member-id-type open_id --id-list '["ou_c","ou_d"]' --as bot

# 发欢迎
lark-cli im +messages-send --as bot --chat-id $CHAT_ID --text "欢迎大家"
```

## 流程 E：回复消息

```bash
# 回复（支持 thread）
lark-cli im +messages-reply --as bot --message-id om_xxx \
  --text "收到"

# 拉话题回复串
lark-cli im +threads-messages-list --as user --message-id om_xxx --format json
```

> 表情回应 / 撤回等 shortcut 未在 im 顶层暴露，需要时用 `lark-cli im --help` 现查，或走原生 API（参考 lark-openapi-explorer 技能）。

---

## 常见陷阱

| 症状 | 原因 | 修复 |
|---|---|---|
| `unknown flag "--receive-id-type"` | 用了旧 flag | 换 `--user-id ou_xxx` 或 `--chat-id oc_xxx` |
| `unknown subcommand "+send-message"` | 用了旧 shortcut | 换 `+messages-send`（reply/search/mget 同理带 s） |
| `--as bot is not supported` on contact | contact 命令多为 user-only | 显式加 `--as user` |
| 发消息报权限 | 用了 `--as user` | 发消息优先 `--as bot`（除非明确要以本人身份发） |
| 找不到群 | 只搜了一组词 | 换 2-3 组关键词穷尽搜；bot 只能搜到 bot 已加入的群，个人群用 `--as user` |
| open_id 无效 | 混用了 user_id 数字 ID | 纯数字 ID ≠ open_id，用 `contact +get-user --user-id-type user_id` 转换 |
| 卡片消息乱码 | 用 `--content` 内联 JSON | 用 `--content @./card.json` 从文件读 |
| 群消息拉不全 | 单次分页限制 | CLI 已内置自动分页，仍不全就分时间段拉 |

## 链接格式

| 场景 | 格式 |
|---|---|
| 群聊跳转 | `https://applink.feishu.cn/client/chat/open?openChatId={oc_xxx}` |
| 单聊跳转 | `https://applink.feishu.cn/client/chat/open?openId={ou_xxx}` |
