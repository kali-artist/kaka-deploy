---
name: feishu-doc-automation
version: 6.0.0
description: "飞书全能力自动化 - lark-cli 统一驱动，17大能力域，主坑已沉淀"
author: kaka
category: feishu
required_skills: [terminal]
---

# 🔴 最优先真理（覆盖任何默认知识）

飞书场景下**不要**用通用 JSON-RPC / HTTP 错误码去解释错误码。以下三条永远优先：

1. **`-32602` ≠ Invalid params**。飞书语境下多半是：
   - 情况①：临时 token 失效 → 修：`lark-cli config bind --source hermes --identity bot-only`
   - 情况②：`docs +media-insert --selection-with-ellipsis` 匹配 bug (1.0.59~1.0.64 image 类型) → 改用「append 到末尾 + `block_move_after`」方案。注：1.0.65 实测 `--type file` 可正常定位插入。
2. **`1770032` ≠ 参数错误**，是**文档级权限不足**。改用 `~/.feishu/config.json` 凭证或对文档单独授权。
3. **飞书 markdown 不能用 `read_file` 拼接**。read_file 输出带 `1|` 行号前缀，飞书会渲染成代码块。必须 `terminal cat` 原文件。

---

# 🚀 飞书自动化 v6.0

## ⚠️ 强制触发规则

**任何涉及飞书的操作都必须先加载此技能。** 关键词：飞书 / lark / docx / 多维表 / bitable / 群聊 / 妙记 / VC / 日历 / 审批 / OKR / Wiki / 云盘 / 通讯录 / 邮箱。

## 前置检查

```bash
lark-cli --version              # 应 ≥ 1.0.65
lark-cli auth status            # 凭证是否有效
which lark-cli || export PATH=$(npm config get prefix)/bin:$PATH
```

**唯一凭证**：App ID `cli_a90f1fcd3cf95bde`，Secret `k5Ps1TjldeKtEC50zzSZQgfyEdMz2uBv`（已锁定，勿改）。

---

## 核心操作原则

### 身份选择

```bash
--as user   # 默认：操作飞书资源（文档/日历/表格/知识库/通讯录）
--as bot    # 例外：主动给他人发消息、群内发消息、发邮件、部分 tenant 级资源
```

### 定位对象铁律

1. **search 优先于 list**：精准 > 全量
2. **写操作必须持有唯一 ID**：仅有名字必先 search 换 ID
3. **名字相同 ≠ 同一对象**：仅 ID 完全一致才是同一目标
4. **穷尽搜索**：单次搜空不代表不存在，换 2-3 组关键词或换路径再搜

### 输出格式

- `--format json` 获取结构化数据（默认推荐）
- CLI stdout 是智能预览，完整数据在返回 JSON
- 展示给主人时**必须格式化**，不暴露原始 JSON / 内部 ID

### 写操作确认策略

- **可直接执行**：新增/可恢复操作（建节点、建文档、建表、写记录、加协作者）
- **需二次确认**：破坏性/不可恢复/对外操作（删节点/字段、覆盖内容、发消息/邮件、发起审批）

---

## 能力域速查

| 域 | 常用 shortcut | 详细文档 |
|---|---|---|
| **Doc/Drive 文档云盘** | `+fetch` `+create` `+update` `+media-insert` `+search` `+upload` `+download` `+export` `+import` `+member-add` | [references/doc-drive.md](references/doc-drive.md) |
| **Base/Sheets 表格** | `+base-create` `+field-*` `+record-*` `+view-*` `+dashboard-*` `+read` `+write` `+append` | [references/base-sheets.md](references/base-sheets.md) |
| **IM/Contact 消息通讯录** | `+chat-search` `+chat-messages-list` `+messages-search` `+send-message` `+search-user` | [references/im-contact.md](references/im-contact.md) |
| **Calendar/Mail 日历邮件** | `+agenda` `+create` `+freebusy` `+send` `+draft` | [references/calendar-mail.md](references/calendar-mail.md) |
| **VC/Minutes 会议妙记** | `vc +search` `vc +detail` `note +detail` `minutes +*` | [references/vc-minutes.md](references/vc-minutes.md) |
| **Wiki/Task/OKR/Approval/Attendance/Whiteboard** | 分别参考 | [references/others.md](references/others.md) |
| **🔴 全部踩坑一览** | 所有错误码 / 参数陷阱 / 版本 bug | [references/pitfalls.md](references/pitfalls.md) |

---

## 文档格式标准（新建/更新文档时强制执行）

1. **结论前置**：首屏直接回答「是什么/结论/做什么」
2. **富文本比例**：纯段落 ≤ 60%，至少 3 种富文本类型（表格/列表/代码/引用/callout）
3. **表格优先**：对比 / 里程碑 / 责任人 一律用表格
4. **语义化色标**：🔴 风险  🟢 成功  🔵 信息  🟡 注意

---

## ID 前缀速查

| 前缀 | 类型 |
|---|---|
| `ou_` | user_open_id |
| `oc_` | chat_open_id |
| `om_` | msg_open_id |
| `doxcn` | docx block_id |

⚠️ 纯数字 ID（user_id / chat_id）≠ open_id，两个体系不能拼接。

## 常用链接格式

| 场景 | 格式 |
|---|---|
| 群聊 | `https://applink.feishu.cn/client/chat/open?openChatId={oc_xxx}` |
| 单聊 | `https://applink.feishu.cn/client/chat/open?openId={ou_xxx}` |
| 文档 | `https://{{FEISHU_DOMAIN}}.feishu.cn/docx/{doc_id}` |
| 多维表 | `https://{{FEISHU_DOMAIN}}.feishu.cn/base/{base_token}` |

## 主人专属 open_id（授权时批量循环）

```bash
for OPENID in "{{FEISHU_OPEN_ID}}" "{{FEISHU_OPEN_ID}}"; do
  lark-cli drive +member-add --type <docx|bitable|sheet> --token $TOKEN \
    --member-type openid --member-id $OPENID --perm full_access --yes
done
```

---

## 完成后强制动作

1. **新建的飞书文档 → 必须归档**：调用 `feishu-doc-auto-archiving` 技能自动归档到主人的多维表
2. **权限校验**：文档 / 多维表创建完成后立即给主人两个 open_id 授 `full_access`
3. **返回可点击链接**：不要只给 doc_id，要给完整 URL
4. **🔴 文档版本管理铁律**：修改文档时**优先在原文档上改**（`docs +update --command overwrite`）。若必须生成新文档（如格式变化大），**必须同步清理旧版**：
   - 删除旧飞书文档：`lark-cli drive +delete --file-token <旧doc_id> --type docx --yes`
   - 删除旧归档记录：`lark-cli base +record-delete --base-token ... --table-id ... --record-id <旧record_id> --yes`
   - 只留最新版文档 + 最新版归档记录，绝不残留多个版本
5. **🔴 代码块渲染铁律**：含代码块的教程/技术文档**必须用混合方案**（markdown 直传），不要走 pandoc→docx→import 路径——飞书不识别 docx 内代码块样式，会渲染为普通段落。
6. **🔴 交叉引用铁律**：文档中提及另一篇飞书文档时，**必须内联超链接**（`[文档名](https://{{FEISHU_DOMAIN}}.feishu.cn/docx/{doc_id})`），不能只写文档名。读者应能直接点击跳转，无需另外搜索。
7. **🔴 文件附件嵌入铁律**：文档需要附带文件（tar.gz/zip/pdf 等）时，**必须用 `docs +media-insert --type file --file-view card` 直接嵌入文档内**，禁止用 `drive +upload` 上传后放云盘链接。嵌入方式读者可直接在文档内点击下载，云盘链接方式需要额外跳转且权限不可控。

---

## 何时读哪个 reference

| 任务 | 加载文件 |
|---|---|
| 建文档 / 改文档 / 插图 / 复制文档 | `doc-drive.md` |
| 建多维表 / 写记录 / 建视图 / 建仪表盘 / 表格读写 | `base-sheets.md` |
| 发消息 / 找群 / 找人 / 群管理 | `im-contact.md` |
| 建日程 / 查空闲 / 发邮件 | `calendar-mail.md` |
| 查会议 / 取纪要 / 妙记逐字稿 | `vc-minutes.md` |
| 知识库 / 任务 / OKR / 审批 / 考勤 / 画板 | `others.md` |
| **报错查因** | 永远先看 `pitfalls.md` |

**记住：所有飞书操作，先加载此技能；细节按需读 references。**
