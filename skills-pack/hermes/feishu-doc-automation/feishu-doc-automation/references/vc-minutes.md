# VC / Minutes 视频会议与妙记

> 遇到报错先看 [pitfalls.md](pitfalls.md)。会议纪要产物（note）与妙记（minutes）是**两个不同资源**，别混。

## 术语澄清

| 资源 | 说明 | ID 特征 |
|---|---|---|
| **VC (Meeting)** | 已结束的视频会议实例 | `meeting_id` |
| **Note** | 会议纪要（VC 会议自动生成的产物） | `note_id`，可关联 docx |
| **Minutes** | 妙记（独立的会议录音/录像+逐字稿产品） | `minutes_token` / `object_token` |

---

## VC Shortcut 清单

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+search` | 搜历史会议 | `--query` `--start` `--end` |
| `+detail` | 会议详情（含 note_id / minute_token / 参会人快照） | `--meeting-ids` |
| `+recording` | 拿录像 minute_token（供后续下载） | `--meeting-ids` |
| `+meeting-events` | 会中事件（Bot 参会时） | `--meeting-id` |
| `+meeting-join` `+meeting-leave` | 加入/离开会议（Bot） | `--meeting-id` |
| `+meeting-message-send` | 会中发消息（Bot） | `--meeting-id` |
| `+meeting-list-active` | 列活跃会议 | — |

> ⚠️ CLI **不支持**：`+list` / `+participants` / `+notes` / `+recordings`（复数）。参会人已并入 `+detail`；下载录像先用 `+recording` 拿 minute_token，再走 `minutes +download`。

## Note Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+detail` | 纪要详情（总结/待办/章节/逐字稿一次拿全） | `--note-id` |
| `+transcript` | 逐字稿单独拉 | `--note-id` |

> ⚠️ CLI **不支持**：`+summary` / `+todos` / `+chapters`（均已合并进 `+detail`）。

## Minutes Shortcut

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+search` | 搜妙记 | `--query` |
| `+detail` | 妙记基础信息 + 产物（summary/chapter/keyword/transcript 用开关控制） | `--minute-tokens` `--summary` `--chapter` `--keyword` |
| `+download` | 下载音视频 | `--minute-tokens` `--output-dir` |
| `+upload` | 上传音视频建妙记 | `--file` |
| `+update` | 改标题 | `--minute-token` `--topic` |
| `+speaker-replace` | 替换说话人 | `--minute-token` `--from` `--to` |
| `+word-replace` | 批量替换关键词 | `--minute-token` `--replace-words` |

> ⚠️ CLI **不支持**：`+content-read` / `+content-edit` / `+title-update` / `+keyword-replace`。参数名统一是 `--minute-token`（单数，改元数据）或 `--minute-tokens`（复数，批量读/下载），别再写 `--minutes-token`。

---

## 流程 A：找会议 → 取纪要

```bash
# 1. 搜会议
lark-cli vc +search --query "周会" \
  --start 2026-07-01 --end 2026-07-31 --format json
MEETING_ID=<从结果提取>

# 2. 拿会议详情（含 note_id、参会人）
lark-cli vc +detail --meeting-ids $MEETING_ID --format json
NOTE_ID=$(... | jq -r '.data[0].note_id')

# 3. 读纪要（一次拿全）
lark-cli note +detail --note-id $NOTE_ID --format json

# 或只拉逐字稿
lark-cli note +transcript --note-id $NOTE_ID
```

**⚠️ 陷阱**：并非所有会议都有 note。若 `note_id` 为空，说明当时未开启纪要功能。

## 流程 B：拉参会人快照（已并入 detail）

```bash
lark-cli vc +detail --meeting-ids $MEETING_ID --format json \
  | jq '.data[0].participants'
```

## 流程 C：下载录像

```bash
# 拿 minute_token
MINUTE_TOKEN=$(lark-cli vc +recording --meeting-ids $MEETING_ID --format json \
  | jq -r '.data[0].minute_token')

# 再用 minutes 下载
lark-cli minutes +download --minute-tokens $MINUTE_TOKEN --output-dir .
```

---

## 流程 D：搜妙记 → 读产物

```bash
# 1. 搜妙记（按标题/说话人/内容关键词）
lark-cli minutes +search --query "关键词" --format json
MINUTE_TOKEN=<从结果提取>

# 2. 一次拿全（基础信息 + 摘要 + 章节 + 关键词）
lark-cli minutes +detail --minute-tokens $MINUTE_TOKEN \
  --summary --chapter --keyword --format json

# 3. 下载音视频
lark-cli minutes +download --minute-tokens $MINUTE_TOKEN --output-dir .
```

## 流程 E：改妙记（标题/说话人/关键词）

```bash
# 改标题
lark-cli minutes +update --minute-token $TOK --topic "新标题"

# 替换说话人（把「未知说话人 A」改成「张三」）
lark-cli minutes +speaker-replace --minute-token $TOK \
  --from "未知说话人 A" --to "张三"

# 批量替换关键词（JSON 数组，可 @file 或 stdin）
lark-cli minutes +word-replace --minute-token $TOK \
  --replace-words '[{"source_word":"旧词","target_word":"新词"}]'
```

## 流程 F：上传音视频建妙记

```bash
# 本地音视频文件转妙记（自动 ASR + 摘要）
MINUTE_TOKEN=$(lark-cli minutes +upload \
  --file ./meeting.mp4 --title "外部访谈-李总" \
  | jq -r '.data.minute_token')

# 稍等 ASR 完成后再拉产物
sleep 60
lark-cli minutes +detail --minute-tokens $MINUTE_TOKEN --summary
```

---

## 流程 G：会议纪要工作流（推荐直接调技能）

需要"汇总某时间范围的所有会议纪要，生成结构化报告"时，**直接调 `lark-workflow-meeting-summary` 技能**，别手写循环。

## 常见陷阱

| 症状 | 原因 | 修复 |
|---|---|---|
| `note_id` 为空 | 会议当时未开纪要功能 | 提示主人，不是 bug |
| 妙记内容为空 | ASR 未完成 | 等 30-60 秒重试 |
| 妙记搜不到但知道存在 | 搜索索引延迟 | 换更长关键词，或换 `+list` 全量拉 |
| 视频下不下来 | 飞书流媒体链接需临时 token | 用 `minutes +download` 而非直接 wget URL |
| 说话人替换后没生效 | 替换是异步的 | 隔几秒重新 `+content-read` 看 |
| 混淆 note vs minutes | 两个体系 | note 属于 VC 会议产物；minutes 是独立妙记，别用 note API 查 minutes |
