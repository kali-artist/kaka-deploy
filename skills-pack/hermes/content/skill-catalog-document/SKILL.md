---
name: skill-catalog-document
description: 将多个技能按专题整理成精简版飞书文档，zip附件直接嵌入文档内，同步归档到多维表
version: 1.2.1
author: kaka
---

# 技能目录文档生成

## 触发条件
主人要求整理技能、生成技能目录文档、按专题归纳技能时使用。

## 全量技能扫描（🔴 必做第一步）

技能分布在**两个目录**，必须都扫描：
```bash
# 1. 主技能目录（~146个）
find ~/.hermes/skills -name "SKILL.md" -type f | sort
# 2. lark-* CLI技能目录（27个）
find ~/.agents/skills -name "SKILL.md" -type f | sort
```

## 已有专题交叉引用（🔴 创建新专题前必做）

查多维表确认哪些专题已发布，避免重复：
```bash
lark-cli base +record-list --base-token {base_token} --table-id {table_id} \
  --page-size 100 --as bot | grep "技能"
```
已有专题只需更新，未覆盖的技能才需要新建专题文档。

## 文档形式规范（核心）

每个专题文档的结构：

1. **标题 + 元信息**：`# 专题名` + 整理时间/整理人/技能数
2. **写在前面**：大白话解释专题，用生活化比喻让非技术人员也能懂，配 emoji
3. **配图**：每个专题1张 flat cartoon 风格 AI 生图（mmx generate），通过 block 操作插入（markdown 直传不支持本地图片引用）
4. **技能清单表**：序号/技能名/版本/用途，一行一个
5. **逐个技能介绍**（每个技能一个章节）：
   - 背景一句话
   - 核心能力表格（能力|说明）
   - 配置表格（配置项|值）
   - frontmatter 预览（仅 `head -15` 前15行，**不放全文**）
   - `> 📎 完整技能文件已打包：见文末附件下载`
6. **协作场景**（可选）：技能间如何配合
7. **附件下载区**：zip 附件通过 `docs +media-insert --type file` 直接嵌入文档

## 关键规则

### 篇幅控制
- **绝不在文档里放完整 SKILL.md 全文**，只放 frontmatter 前15行预览
- 技能文件打包成 zip，作为附件卡片直接嵌入文档内

### zip 打包
```bash
# 每个专题一个 zip，包含该专题所有技能目录
cd /tmp && zip -r skill-pack-{N}-{name}.zip <skill_dir1> <skill_dir2> ...
```

### 更新已有专题文档（🔴 首选方案 — 链接不变，直接 overwrite）

当专题已有文档时，**不要删除旧文档再新建**，直接在原文档上 overwrite：
- 飞书文档链接不变，用户收藏的链接仍然有效
- 省去授权、归档新记录等重复步骤

```bash
# 1. 生成新 markdown 内容
# 2. 直接 overwrite 原文档（doc_id 从多维表查得）
cd /tmp && lark-cli docs +update --doc {existing_doc_id} \
  --command overwrite --doc-format markdown \
  --content @skill-doc-{N}-{name}.md

# 3. 插入新 zip 附件（overwrite 会清空旧附件，需重新插入）
cd /tmp && lark-cli docs +media-insert --doc {existing_doc_id} \
  --file skill-pack-{N}-{name}.zip --type file --file-view card --as user

# 4. 如改了专题名，更新多维表记录标题
lark-cli base +record-upsert --base-token {base_token} --table-id {table_id} \
  --record-id {record_id} --json '{"标题":"{new_title}"}' --as bot
# 完事！不需要删除旧文档、不需要创建新文档、不需要重新授权
```

## 发布流程（v1.2 — markdown 直传为首选，pandoc 降级兜底）

🔴 **核心变更**：pandoc→docx→import 路径飞书不识别 docx 代码块样式，渲染为普通段落。
markdown 直传保留 ```语言 标记，飞书渲染为原生 `<pre lang="xxx"><code>` 代码块。

#### 方案①（首选）：markdown 直传 — 新建专题文档
```bash
# 1. 生成精简版 markdown（/tmp/skill-doc-{N}-{name}-v2.md）
# 2. AI 生图（可选）→ /tmp/theme-{name}_001.jpg
#    ⚠️ markdown 直传不支持本地图片引用，图片需单独用 block 操作插入或省略

# 3. 创建空壳文档
lark-cli docs +create --title "{专题名}" --doc-format markdown --content "# {专题名}"
# → 从返回的 "document_id" 字段提取 doc_id

# 4. overwrite 灌入正文（🔴 --content @file 必须用相对路径！先 cd /tmp）
cd /tmp && lark-cli docs +update --doc {doc_id} \
  --command overwrite --doc-format markdown \
  --content @skill-doc-{N}-{name}-v2.md

# 5. 授权主人
lark-cli drive +member-add --type file --token {doc_id} \
  --member-type openid --member-id {openid} --perm full_access --yes

# 6. 插入 zip 附件（🔴 必须用相对路径！先 cd /tmp）
cd /tmp && lark-cli docs +media-insert --doc {doc_id} \
  --file skill-pack-{N}-{name}.zip --type file --file-view card --as user

# 7. 验证代码块（fetch 后检查 <pre> 标签数和 lang 属性）
lark-cli docs +fetch --doc {doc_id} --scope full --as user --format json
# → 解析 content 字段，确认 <pre lang="yaml"> 等标记存在
# → 若 <pre>=0 则说明代码块未渲染，需排查

# 8. 删除旧文档（如有）
lark-cli drive +delete --type docx --file-token {old_token} --yes --as bot

# 9. 归档到多维表（带完整字段）
# 🔴 禁止只写标题和URL！必须带知识类型、来源、标签
lark-cli base +record-batch-create \
  --base-token {base_token} --table-id {table_id} \
  --json '{
    "fields": ["标题", "来源", "知识类型", "完整笔记", "状态", "标签", "日期"],
    "rows": [["{doc_title}", "飞书文档", "技能文档", "https://xxx.feishu.cn/docx/{new_token}", "已归档", ["{tag1}", "{tag2}"], "$(date +%Y-%m-%d)"]]
  }' --as bot
# 若是更新已有记录（删旧文档+新文档场景），用 record-upsert 替代：
lark-cli base +record-upsert --base-token {base_token} --table-id {table_id} \
  --record-id {record_id} --json '{"完整笔记":"https://xxx.feishu.cn/docx/{new_token}"}' --as bot
```

#### 方案②（降级兜底）：pandoc→docx→import
⚠️ 代码块样式会丢失（飞书不识别 docx 代码块），仅在前方案失败时使用。
```bash
cd /tmp && pandoc skill-doc-{N}-v2.md -o skill-doc-{N}-v2.docx --resource-path=/tmp
cd /tmp && lark-cli drive +import --file ./skill-doc-{N}-v2.docx --type docx --format json
# → 从返回的 url 字段提取 doc token（token 字段被掩码为 ***）
# 后续授权/插入zip/归档步骤同方案①
```

#### 批量重发（全部专题重新发布）
当需要批量重新发布多个专题文档时（如代码块修复后重发）：
1. 遍历所有专题，按方案①依次执行步骤 3-6（创建+灌入+授权+zip）
2. 批量验证代码块（步骤 7）
3. 批量删除旧文档（步骤 8）
4. 批量更新/创建多维表记录（步骤 9，已有记录用 upsert，新记录用 batch-create）

#### 批量重发后同步引用文档链接
重发专题文档后，其他引用了旧文档链接的文档（如一键部署指南）也需同步更新。

🔴 `str_replace` 无法修改 `<a href>` 属性，必须用 `block_replace`：
```bash
# 1. fetch section 定位引用文档中的专题链接表格
lark-cli docs +fetch --doc {ref_doc_id} --scope section \
  --start-block-id {heading_id} --detail with-ids --as user --format json
# → 从 XML 中提取每个 <p id="doxcnXXX"><a href="...旧doc_id...">文本</a></p>

# 2. 逐个 block_replace 替换为新链接
lark-cli docs +update --doc {ref_doc_id} --command block_replace \
  --block-id "doxcnXXX" \
  --content '<p><a href="https://xxx.feishu.cn/docx/{new_token}">专题名</a></p>' --as bot
```

### 归档标签智能匹配（专题文档专用）
| 专题关键词 | 标签 |
|---|---|
| 飞书、lark、多维表、云文档 | 飞书自动化 |
| 影刀、RPA、流程 | RPA |
| 搜索、抓取、爬虫、firecrawl | 爬虫 |
| 教程、课程、生成器 | 教程 |
| 系统、开发、技能管理、部署 | 运维自动化 |
| 信息检索 | 爬虫 |
| 浏览器自动化 | 教程 |
| 个人专属 | （留空，按实际内容匹配） |
🔴 无匹配时留空，禁止编造标签。可用标签见 feishu-doc-auto-archiving 技能的14个标签列表。

### 踩坑要点
| 问题 | 解决 |
|---|---|
| **pandoc→docx→import 代码块丢失样式** | 🔴 改用方案① markdown 直传，pandoc 方案仅作降级兜底 |
| **`docs +update --content @file` 报 invalid file path** | 🔴 必须用相对路径！先 `cd /tmp`，用 `@skill-doc-1-feishu-v2.md` 而非 `@/tmp/skill-doc-1-feishu-v2.md` |
| **markdown 直传后图片不显示** | markdown 直传不支持本地图片引用 `![](path)`，图片需单独用 block 操作插入或省略 |
| `drive +import` 返回 token 为 `***` | 从 `url` 字段提取真实 token（仅方案②） |
| `docs +media-insert --file` 报 unsafe file path | 必须用相对路径，`cd /tmp` 后执行 |
| `drive +delete` 报 no permission | 用 `--as bot` 身份删除 |
| `base +record-update` 不存在 | 用 `+record-upsert --record-id {id}` 更新 |
| 多维表搜索需要 `--search-field` | `--keyword "关键词" --search-field "标题"` |

## 归档多维表信息
- Base Token: `{{FEISHU_BASE_TOKEN}}`
- Table ID: `{{FEISHU_TABLE_ID}}`
- "完整笔记"字段: `fldujkMbvt`（URL类型，直接传文本URL）
- "关联资源"字段: `fldEkuS0W5`（附件类型）

## 主人 open_id（授权用）
- `{{FEISHU_OPEN_ID}}`
- `{{FEISHU_OPEN_ID}}`
