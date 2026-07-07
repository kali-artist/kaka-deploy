---
name: feishu-doc-auto-archiving
version: 1.2.0
description: "飞书文档自动归档技能 - 所有新创建的飞书文档自动归档到指定多维表，标签智能匹配"
author: kaka
category: feishu
required_skills: [feishu-doc-automation, terminal]
---

# 🚀 飞书文档自动归档技能 v1.1.0

## ⚠️ 强制触发规则
**只有首次创建全新的飞书文档（docx/doc/base等）时，才调用本技能执行归档操作。**

🔴 **禁止重复归档**：归档前必须先查询多维表是否已存在相同文档URL的记录，若已存在则跳过。修改/更新已有文档时不触发归档。

### 去重检查（归档前必做）
```bash
# 用文档URL搜索是否已归档过
EXISTING=$(lark-cli base +record-search \
  --base-token {{FEISHU_BASE_TOKEN}} \
  --table-id {{FEISHU_TABLE_ID}} \
  --keyword "$DOC_URL" --page-size 1)

# 如果已有记录则跳过归档
echo "$EXISTING" | jq '.data.items | length' 
# > 0 表示已存在，跳过；= 0 才执行归档
```

---

## 🎯 配置说明
### 默认归档目标（永久生效，除非用户修改）
- 多维表地址：https://{{FEISHU_DOMAIN}}.feishu.cn/base/{{FEISHU_BASE_TOKEN}}
- 多维表Token：`{{FEISHU_BASE_TOKEN}}`
- 默认表ID：`{{FEISHU_TABLE_ID}}`（自动识别首个表格，若结构变化可修改）

---

## 🏷️ 标签智能匹配规则

**归档时根据文档标题/内容自动匹配标签，禁止一律用固定值。**

### 关键词 → 标签映射表
| 关键词（标题/内容中出现即匹配） | 标签 |
|------|------|
| 内网穿透、frp、隧道、反向代理、网络 | 网络穿透 |
| 网站部署、部署、nginx、docker、server | 运维自动化 |
| 影刀、RPA、流程自动化、需求评估 | RPA |
| 飞书、lark、多维表、云文档、知识库 | 飞书自动化 |
| MCP、模型上下文、工具集成 | AIGC |
| 权限、审计、安全、hook | 安全审计 |
| 教程、课程、学习、入门、指南 | 教程 |
| 大模型、LLM、GPT、Claude | 大模型 |
| 微调、fine-tuning、LoRA、训练 | 微调 |
| 爬虫、抓取、spider、scrape | 爬虫 |
| prompt、提示词 | prompt工程 |
| crewAI | crewAI |
| 多智能体、multi-agent、agent编排 | 多智能体 |
| Python | Python |

### 匹配规则
1. 扫描文档标题（优先）和摘要内容，命中关键词即打对应标签
2. **可匹配多个标签**（标签是多选字段），取所有命中的
3. 若无任何匹配，**不填标签字段**（留空优于填错）
4. 🔴 **禁止编造不在映射表里的标签值**——只能用上面列出的14个标签

---

## 🔧 自动归档字段映射
| 多维表字段名 | 取值来源 | 说明 |
|-------------|---------|------|
| 标题 | 文档标题 | 创建时指定的title |
| 来源 | 智能匹配 | 默认「飞书文档」，若明显来自GitHub/官方文档等则改 |
| 知识类型 | 智能匹配 | 默认「技能文档」，教程→「学习资料」，部署→「实践记录」，审计→「踩坑总结」等 |
| 完整笔记 | 文档链接 | 可直接点击访问 |
| 状态 | 固定值「已归档」 | 默认值 |
| 标签 | 智能匹配 | 根据上方映射表匹配，可多选 |
| 日期 | 当前系统日期 | 自动生成 |

---

## 📋 标准执行流程
### 步骤1：创建文档后提取元数据
```bash
# 创建文档时必须保存以下变量
DOC_ID="xxx"
DOC_TITLE="xxx"
DOC_URL="https://{{FEISHU_DOMAIN}}.feishu.cn/docx/$DOC_ID"
```

### 步骤2：智能匹配标签
根据文档标题 `$DOC_TITLE` 和内容摘要，按上方映射表确定标签列表。

示例：
```bash
# 假设标题是 "零基础搭建影刀MCP服务"
# 命中 "影刀" → RPA，命中 "MCP" → AIGC
TAGS='["RPA", "AIGC"]'

# 假设标题是 "内网穿透：概念+配置实战"
# 命中 "内网穿透" → 网络穿透
TAGS='["网络穿透"]'

# 假设标题是 "网站部署档案 - AI小说写作助手"
# 命中 "网站部署" → 运维自动化
TAGS='["运维自动化"]'

# 无匹配时留空
TAGS='[]'
```

### 步骤3：自动写入归档多维表
```bash
# 写入记录到多维表（标签用智能匹配结果，留空时从fields中删除标签列）
lark-cli base +record-batch-create \
  --base-token {{FEISHU_BASE_TOKEN}} \
  --table-id {{FEISHU_TABLE_ID}} \
  --json "{
    \"fields\": [\"标题\", \"来源\", \"知识类型\", \"完整笔记\", \"状态\", \"标签\", \"日期\"],
    \"rows\": [[\"$DOC_TITLE\", \"飞书文档\", \"技能文档\", \"$DOC_URL\", \"已归档\", $TAGS, \"$(date '+%Y-%m-%d')\"]]
  }"
```

⚠️ 若 `$TAGS` 为空数组 `[]`，则从 fields 和 rows 中删除标签列，避免写入空多选。

### 步骤4：验证归档结果
执行成功后返回归档记录ID，确保数据已正确写入。

---

## 🔄 与feishu-doc-automation集成方案
在创建文档的流程最后，追加本技能的归档步骤：
1. 完成文档创建、权限配置后
2. 根据文档标题智能匹配标签
3. 自动调用本技能执行归档
4. 返回文档链接+归档成功提示

---

## 🔍 已归档文档检索（查找之前的文档）

当用户说"之前做过的那个XX文档""你刚创建的那个文档"但当前上下文没有链接时，**直接查归档表，不要先搜 session_history**。

### 为什么不先搜 session_history
- `session_search` 的 FTS5 默认 AND 匹配，中文分词常导致漏结果
- `grep` 本地文件只能找到写在技能/记忆里的链接，遗漏大
- 归档表是所有已创建文档的权威索引，一次查询即命中

### 标准检索命令
```bash
# 方式1：关键词搜索（推荐，支持模糊匹配标题）
lark-cli base +record-search \
  --base-token {{FEISHU_BASE_TOKEN}} \
  --table-id {{FEISHU_TABLE_ID}} \
  --keyword "部署" --page-size 50 --as bot

# 方式2：列出全部记录（记录不多时直接扫一遍更快）
lark-cli base +record-list \
  --base-token {{FEISHU_BASE_TOKEN}} \
  --table-id {{FEISHU_TABLE_ID}} --page-size 100 --as bot
```

返回的表格中「完整笔记」列即为文档链接，「标题」列用于匹配用户描述。

### 检索优先级
1. **归档表查询**（最快，权威索引）← 先做这个
2. `session_search`（补充，找创建过程上下文）
3. `grep` 本地文件（兜底，找技能/配置中硬编码的链接）

---

## 🧹 归档记录审计与清理（定期执行）

当用户说"清理多维表""知识库有些文档废弃了""归档记录检查"时，执行以下审计流程。

### 背景
删除飞书文档时不会自动清理多维表中的归档记录，长期积累会产生失效记录（文档已删但记录还在）。

### 审计流程

#### 步骤1：拉取全部记录
```bash
lark-cli base +record-list --base-token {{FEISHU_BASE_TOKEN}} \
  --table-id {{FEISHU_TABLE_ID}} --as user --page-size 100
```
从表格输出中提取每条记录的 record_id 和文档 URL（在「完整笔记」字段中），解析出 doc_id。

#### 步骤2：逐条验证文档存活
对每条记录的 doc_id 执行轻量级存活检查：
```bash
lark-cli docs +fetch --doc <doc_id> --scope outline --detail simple
```
- `"ok": true` → 文档存活 ✅
- 否则 → 文档已删除 ❌

批量检查时每条间隔 0.3s 避免 rate limit。

#### 步骤3：分类处理失效记录（⚠️ 不能无脑删！）

🔴 **关键教训**：失效记录 ≠ 直接删除。必须先判断文档是「该删的」还是「该补的」：

| 情况 | 判断依据 | 处理方式 |
|------|---------|---------|
| 旧版本被新版替代 | 同标题有存活记录 | ✅ 删除失效记录 |
| 文档确实废弃不再需要 | 主人确认废弃 | ✅ 删除失效记录 |
| **文档本应存在但链接丢了** | 属于某个系列/专题（如6个技能专题），或主人未曾要求删除 | ⚠️ **重新发布文档**，用 `record-upsert` 更新链接，**不要删记录** |

**检查方法**：看失效记录的标题是否属于一个已知系列（如"XX专题"系列、"网站部署档案"系列）。如果同系列其他记录都存活，说明这个文档是意外丢失，应该补回而不是删掉。

#### 步骤4：删除确认废弃的失效记录
对确认废弃的 record_id 执行：
```bash
lark-cli base +record-delete --base-token {{FEISHU_BASE_TOKEN}} \
  --table-id {{FEISHU_TABLE_ID}} --record-id <rid> --yes
```

#### 步骤5：报告结果
输出：总数 / 存活数 / 失效已清理数 / 需重新发布的文档列表 / 剩余有效记录列表。
⚠️ 如果有"需重新发布"的文档，必须明确告知主人，不能静默跳过。

### 重复记录检测
同时检查是否有相同标题的记录（文档更新后重新发布，旧版未删）。若同一标题有多条记录，保留文档存活的那条，删除失效的。

---

## 📖 内容陈旧审计（系统变更后触发）

当系统发生重大变更（技能删除/创建、记忆系统重构、配置变更、框架清理等）后，知识库中的已有文档可能引用了已失效的内容。此审计流程用于快速定位哪些文档需要更新。

### 触发场景
- 主人说"你今天的XX有更新，飞书知识库里哪些要更新"
- 主人说"检查一下知识库文档还有没有旧的引用"
- 重大系统变更后主动检查（技能删除、MEMORY/SOUL 重构、框架清理等）

### 执行流程

#### 步骤1：识别变更关键词
从本次系统变更中提取需要检查的关键词，例如：
- 被删除的技能/框架名称（如 `kaka-soul`、`kaka-learnings`）
- 被重构的系统名称（如 `MEMORY.md`、`Core Memory`、`三层存储`）
- 被停用的工具/服务名称（如 `Hindsight`）

#### 步骤2：列出知识库全部记录
```bash
lark-cli base +record-list --base-token {{FEISHU_BASE_TOKEN}} \
  --table-id {{FEISHU_TABLE_ID}} --as user --limit 50
```
从返回的表格中提取每条记录的标题和文档 URL（在「完整笔记」字段中），解析出 doc_id。

#### 步骤3：批量fetch+关键词搜索
用 `execute_code` 批量获取每个文档内容并搜索变更关键词，避免逐个手动操作：
```python
from hermes_tools import terminal

docs = [("标题", "doc_id"), ...]  # 从步骤2提取
keywords = ["kaka-soul", "kaka-learnings", "MEMORY.md", ...]  # 从步骤1提取

for doc_name, doc_id in docs:
    result = terminal(f'lark-cli docs +fetch --doc {doc_id} --as user --format text 2>&1', timeout=30)
    text = result.get("output", "")
    found = [(kw, text.lower().find(kw.lower())) for kw in keywords if kw.lower() in text.lower()]
    if found:
        print(f"⚠️ {doc_name}: {len(found)} 个陈旧引用")
    else:
        print(f"✅ {doc_name}: 无需更新")
```

#### 步骤4：报告结果
按需更新的紧急程度分类报告：
- ⚠️ **需更新**：文档中有已失效的引用（如引用了已删除的技能路径）
- ✅ **无需更新**：文档内容未受本次变更影响
- 对于需更新的文档，列出具体哪些关键词命中、大致在哪个章节

### 关键注意
1. **只报告不擅自改** — 审计结果交给主人确认后再更新文档，不静默修改
2. **关键词要精准** — 太宽泛（如"技能"）会误报，太窄（如完整路径）会漏报
3. **fetch用text格式** — 比json快且足够做关键词搜索
4. **优先检查技能文档和学习资料类型** — 实践记录和踩坑总结通常不需要随系统变更更新

---

## ✅ 注意事项
1. 若多维表结构调整，需同步更新字段映射配置
2. 归档操作不影响原文档的正常使用和权限
3. 所有归档记录可在多维表中统一管理、检索
4. 若执行归档时出现800030104错误（表不存在）或800030201错误（字段不存在），需先查询当前多维表的实际表ID和字段名，更新本技能的对应配置后再重试
5. 🔴 **800030005 not_found（选项值不存在）**：单选/多选字段（如「标签」「来源」「知识类型」「状态」）的取值必须是**多维表里已配置的预设选项**，写入不存在的选项值会报此错。CLI hint 里会列出前 5 个可用选项。**修复优先级**：
   - ① 优先：改用列出的合法选项
   - ② 兜底：把该字段从 fields 数组里**整体删除**，让记录跳过此字段（其他字段照常写入）
   - ③ 不要盲目重试相同值——错误码明确说"选项不存在"，不是网络抖动
   - **禁止**：随手编造标签值

### 当前多维表可选标签（14个）
大模型 / 多智能体 / 飞书自动化 / Python / crewAI / AIGC / RPA / 爬虫 / 运维自动化 / 微调 / prompt工程 / 网络穿透 / 教程 / 安全审计

### 归档前推荐先探选项（可选保险步骤）
```bash
# 查字段选项定义（避免踩雷）
lark-cli base +field-list --base-token {{FEISHU_BASE_TOKEN}} --table-id {{FEISHU_TABLE_ID}} --format json 2>/dev/null \
  | grep -oE '"name":"[^"]+"|"options":\[[^]]*\]' | head -40
```
