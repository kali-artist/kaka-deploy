---
name: tutorial-generator
description: "Use when 主人要求生成教程/课程/学习文档。产出结构清晰、图文并茂的多章节教程，交付到飞书文档或本地 Markdown。四套模板可选，输出必须注明所用模板便于主人针对优化。"
version: 2.1.0
author: kaka
license: MIT
category: education
metadata:
  hermes:
    tags: [tutorial, learning, education, course, 教程, 学习, 图文并茂, 插画]
    related_skills:
      - feishu-doc-automation
      - feishu-doc-auto-archiving
      - architecture-diagram
      - excalidraw
      - baoyu-infographic
      - minimax-image-generation
      - product-brainstorming
---

# 📚 Tutorial Generator - 教程/课程生成器 v2.1

## 🧭 Execution Navigation Layer (最高优先级，模型入口)

### 🔴 Core Iron Rules (违反 = 失败)
- 🔴 **R1 触发即加载**：主人说"教程/课程/学习文档/tutorial"必先加载此技能
- 🔴 **R2 红线双守+**：任何输出必须满足 (a) 结构清晰 (b) 图文并茂 (c) **生动插画**——除技术图外，至少配 1~2 张 mmx 生成的场景/隐喻插画（详见 `references/illustration-playbook.md`）
- 🔴 **R3 模板可追溯**：交付时必须显式告知主人"本次使用的是 XX 模板"，方便主人针对性优化
- 🔴 **R4 步骤不合并**：4 步 SOP 逐步确认，不得跳步

### 🎯 4-Step Linear Flow
| Step | 动作 | 关键产出 | 主人确认信号 |
|------|------|---------|-------------|
| **1️⃣ Align** | 明确 主题/受众/深度/章数/目标平台/模板选型 | 一句话规格单 | "开始生成大纲" |
| **2️⃣ Outline** | 输出章节大纲 + 每章要点 + 图表清单 | 大纲 markdown | "大纲通过，开写正文" |
| **3️⃣ Author** | 按选定模板写正文 + 批量生成图表 | 完整 markdown + 图片目录 | (自动进入发布) |
| **4️⃣ Deliver** | 发布到目标平台 + 输出自检报告 + **注明所用模板** | 飞书 URL / MD 文件路径 + 8 项 checklist | 主人确认收货 |

### 📋 4 套模板速查（详见 `templates/`）
| 模板 | 适用场景 | 结构特征 |
|------|---------|---------|
| **T1 technical-programming** | 编程/框架/API 类 | 代码块密集，每章"讲解+可跑示例+练习" |
| **T2 tool-usage** | 工具安装/CLI 使用 | 安装配置 → 常用命令 → 实战演练 → 排障 |
| **T3 concept-intro** | 概念/原理/理论入门 | 类比 → 图解 → 分层拆解 → FAQ |
| **T4 project-hands-on** | 项目从 0 到 1 | 需求 → 拆解 → 逐 commit 推进 → 复盘 |

### 🎨 图表决策矩阵（详见 `references/related-skills-matrix.md`）
| 图类型 | 首选技能 | 兜底 |
|-------|---------|------|
| 技术架构图/云图 | `architecture-diagram` | 本地 SVG |
| 流程图/时序图（手绘感） | `excalidraw` | 本地 SVG |
| 概念对比/信息图 | `baoyu-infographic` | 本地 SVG |
| **生动插画/场景图/隐喻图** | `minimax-image-generation` (mmx) | `agnes-ai` |
| 简单示意（<3 元素） | 直接内联 SVG | — |
| **生动插画/隐喻场景图** | `mmx image generate`（minimax-image-generation） | image_gen 内置工具 |

### 🚚 交付通道（本版本聚焦）
- **飞书文档** → `scripts/publish_to_feishu.sh`（薄封装 `lark-cli`）
- **Markdown 文件** → `scripts/save_markdown.sh`（本地存档 + 图片路径校验）

---

## 🎯 Overview

生成高质量、结构化学习教程。**本技能只做"编排"**，实际能力全部外挂：
- 📝 结构生成：内置 4 套模板 + prompt 规范
- 🖼 图表出图：调用 `architecture-diagram` / `excalidraw` / `baoyu-infographic`
- 🚀 飞书发布：调用 `feishu-doc-automation`（Lark CLI v5.0+）
- 📦 归档：调用 `feishu-doc-auto-archiving`
- ✅ 迭代优化：配合 `skillopt`

## 📌 When to Use

**触发场景**：
- 主人说"生成教程/课程/学习文档/tutorial/教学材料"
- 需要将某个技术主题结构化输出给他人学习
- 需要多章节递进 + 图文配合的知识产品

**不适用**：
- 简短 FAQ / 单条命令说明（直接答即可）
- 纯代码 review / 项目文档（用其他专用技能）
- 会议纪要 / 需求文档（模板不对口）

---

## 🔧 Core Operation Flow

### Step 1️⃣ Align 需求对齐（**AI 先推断，主人一句话确认**）

**执行方式（v2.1 简化流程）**：
1. 我根据主人一句话需求，**先自动推断 6 项规格**（不要来回追问），打包给主人一眼确认
2. 主人若无异议只需回「开始生成大纲」即视为全部确认
3. 主人若要改，只需说「章节改成 8 章 / 用 T2 模板」等增量修改

**输出模板**（标题必须含"推断"二字）：
```
🤖 教程规格单（我已推断，请确认 or 改）
- 主题：______（从主人话里提取）
- 目标读者：初学者（默认）/ 进阶 / 专家
- 深度：入门（默认）/ 系统 / 深入
- 章节数：5（默认，范围3~8）
- 目标平台：飞书+MD（默认）/ 仅飞书 / 仅MD
- 模板选型：T_（自动推荐）
- 插画配置：每章1技术图 + 开篇/结尾各1插画（默认）
```

**模板推荐规则（含混合场景）**：
- 主题含"入门/原理/是什么" → T3 concept-intro
- 主题含"框架/API/编程" → T1 technical-programming
- 主题含"CLI/工具/软件使用" → T2 tool-usage
- 主题含"实战/项目/从零" → T4 project-hands-on
- **混合场景**：工具+实战 → T2 为主干，穿插 T4 的 commit 推进节奏（标注"T2+T4混合"）
- **混合场景**：概念+工具 → T3 开篇建认知，T2 主体教操作（标注"T3→T2递进"）
- 拿不准 → 直接问主人"偏概念理解还是偏动手操作？"
- **混合场景**（如「用某工具做某项目」）→ **主选 + 副选组合**：
  - 「用 X CLI 完成 Y 项目」→ 主 T4 + 副 T2（每章嵌入命令小节）
  - 「用 X 框架写 Y demo」→ 主 T1 + 副 T4（末章加完整项目）
  - 「X 原理与 Y 实操」→ 主 T3 + 副 T4（前概念后实战）
  - 交付时注明「本次采用 主T4 + 副T2 混合模板」

### Step 2️⃣ Outline 大纲生成
按选定模板生成：
1. 学习目标（3~5 条）
2. 前置知识清单
3. 章节列表（每章一句话说清教什么）
4. **图表清单**（哪一章要几张什么图 —— 提前规划避免临时加图）
5. 进阶资源方向

⚠️ **必须等主人确认大纲后**再进入 Step 3。

### Step 3️⃣ Author 正文 + 图表批量出图

**并行执行**（省时间）：
- 写正文：`templates/{选定模板}.md` 填充
- 出技术图：按大纲的图表清单一次性批量生成
- **出插画**（v2.1 新增）：`bash scripts/generate_illustrations.sh <manifest.json> <images_dir>` 批量走 mmx，每章 1~2 张

**图片路径约定**：
- 统一放 `/tmp/tutorial_<时间戳>/images/`
- 技术图命名 `chXX_tech_描述.png`（例：`ch02_tech_架构图.png`）
- 插画命名 `chXX_illu_描述.jpg`（例：`ch01_illu_快递员穿墙.jpg`）
- markdown 中用**相对路径**引用

**插画生成**（v2.1 新增）：
- Step 2 大纲阶段同步产出 `illustrations` 清单（id+prompt+chapter）
- Step 3 调 `scripts/generate_illustrations.sh <outline.json> <images_dir>` 批量生图
- 风格锁定 flat cartoon，详见 `references/illustration-playbook.md`
- markdown 中用**相对路径**引用

### Step 4️⃣ Deliver 发布 + 自检

**发布**：
```bash
# 飞书
bash scripts/publish_to_feishu.sh <markdown_path> <images_dir> "教程标题"

# Markdown 归档
bash scripts/save_markdown.sh <markdown_path> <images_dir> "教程标题"
```

**自检**（跑 `references/quality-checklist.md` 0~2 分打分制，共 8 项，满分 16 分，≥13 才可交付）：
- 结构、图文、代码、术语、链接、练习、平台、模板标注（详见 checklist）

---

## ⚠️ Common Pitfalls

1. **跳过大纲直接开写** → 主人吐槽章节不对，返工 → 必须 Step 2 确认
2. **图临时加** → 打断写作节奏，图风格不统一 → Step 2 必须列图表清单
3. **图片路径写死绝对路径** → 归档/迁移崩 → 必须相对路径
4. **飞书发布用旧的 3 步 API** → 现在已被 Lark CLI 替代 → 走 `feishu-doc-automation`
5. **不注明模板** → 主人无从优化 → 交付消息必须写"本次采用 T_ 模板"
6. **代码块不写语言** → markdown 渲染丢高亮 → 一律标 `python` / `bash` / `json`
7. **章节命名不带编号** → 目录乱 → 统一 `## 第 N 章：xxx`
8. **红线判断错**：概念入门里也至少要 1 张类比图或结构图，不能全是文字
9. 🔴 **教程场景是输出截断重灾区** —— 3 章以上正文必须走全局 MEMORY 的"输出控制铁律 + 三层防护"（execute_code 通道优先），本技能不重复展开，见全局记忆
10. 🔴 **lark-cli 长 markdown 渲染陷阱**：`lark-cli docs +create --content @file.md` 遇到 5000 字级别的多章教程会**整片误识别为代码块**（章节标题、列表、表格全被套进 `<pre><code>`，主人看到的是一整块灰底代码）。**必须用两步法**：先 `+create` 建**空文档**（`--content "# 标题"` 只填标题），再 `lark-cli docs +update --command overwrite --doc-format markdown --content @file.md` 灌正文，才能正确渲染。`publish_to_feishu.sh` 已按此修正。
11. 🔴 **代码块 + 图片位置两难已解决（v3）**：v2 时 pandoc→docx→import 图片位置准但代码块样式丢失，markdown 直传代码块✅但图片定位不准。v3 混合方案（markdown 直传 + 三步法 block_move_after 插图）**同时解决两个问题**：代码块原生渲染 ✅ + 图片精确定位 ✅。`publish_to_feishu.sh` v3 已将混合方案提为首选，pandoc 降为兜底。
15. 🔴 **v3 图片自动定位对中文标题+英文图名失效**：`publish_to_feishu.sh` 的 `try_hybrid()` 用 `grep -B1 "$ANCHOR"` 匹配图片文件名（如 `ch01_gongwang_vs_neiwang`）到文档大纲标题（如 `1.2 什么是内网穿透`），**英文图名永远匹配不到中文标题**，所有图片会堆在文档末尾。**手动修复流程**：(1) `lark-cli docs +get-blocks --doc-id <id>` 拿大纲结构 (2) 从文档 HTML 中提取每张图片的 block_id（搜 `<img>` 标签） (3) 找到该图片应跟在哪个标题 block 之后 (4) 逐张调 `lark-cli docs +block-move-after --doc-id <id> --block-id <img_blk> --target-id <heading_blk>`。建议后续改进脚本：从 markdown 源文件解析图片上方最近的 `##` 标题文本，用标题文本而非文件名去匹配大纲。
12. **lark-cli 返回体不能直接 jq**：CLI 会把 warning/提示打到 stdout 混入 JSON，导致 `jq -r ...` 报 `Invalid numeric literal`。解析 document_id 用 `grep -oE '"document_id":\s*"[^"]+"'` 更稳。
13. **media-insert 已在 lark-cli 1.0.65 修复**：图片走 pandoc 转 docx 或 media-insert 均可，`publish_to_feishu.sh` v3 已双方案自动降级（混合方案首选，pandoc 降级兜底），插画/技术图统一走同一通道。
14. 🔴 **分片写入后的合并陷阱（最容易踩）**：因为"输出控制铁律"要求 write_file 分批写 ch01/ch02/...，**合并环节必须走原始文件拼接**，绝对禁止用 `read_file` 读回来再拼 —— `read_file` 输出自带 `1|内容` 行号前缀（是给 LLM 调试用的），当正文合并会让飞书把每行都判成代码块，全文变一整片灰底 pre。正确做法只有两条：
    - ✅ shell：`cat ch01.md ch02.md ch03.md > tutorial.md`（推荐，最短路径）
    - ✅ execute_code 里用 Python `open(f).read()` 而非 `read_file()`
    - ❌ 禁：`hermes_tools.read_file()` 的返回值参与拼接
    - **合并后必须 sanity check**：`head -3 tutorial.md` 看首行有没有 `1|`/空格缩进；grep 查 `^\s+[0-9]+\|` 应该零匹配；否则重新合并。
14. **区分"我的输出 token"和"最终产物大小"**：write_file ≤4000 字节铁律管的是**我单条消息里塞多少 content**（防 LLM 输出截断），不是最终 md 文件长度上限。最终产物可以任意大 —— 让 shell/工具去拼装/生成，跟我的输出 token 完全解耦。

---

## ✅ Verification Checklist

主人验收前，我必须自查：
- [ ] Step 1 已获主人书面确认「开始生成大纲」
- [ ] Step 2 已获主人书面确认「大纲通过」
- [ ] Step 3 所有图已按大纲清单生成，路径正确
- [ ] **Step 3 正文批量落盘走的是 `execute_code` 层1 通道**（3 章以上强制）
- [ ] **对话消息里没有 inline 展开任何 > 500 字的正文/SVG/代码块**
- [ ] Step 4 8 项 quality-checklist 全过
- [ ] 交付消息**明确写出所用模板编号**（T1/T2/T3/T4）
- [ ] 若发飞书：URL 已授权给主人两个 openid，已归档到多维表
- [ ] 若发 MD：所有图片路径 `file` 命令验证可读，通过 `MEDIA:/绝对路径` 发给主人

---

## 📂 Skill Layout

```
education/tutorial-generator/
├── SKILL.md                              # 本文件
├── references/
├── references/
│   ├── related-skills-matrix.md          # 关联技能调用矩阵
│   ├── illustration-playbook.md          # 🎨 插画生成手册（v2.1新增）
│   ├── delivery-playbook.md              # 飞书 + MD 发布手册
│   └── quality-checklist.md              # 8 项打分制自检（v2.1升级）
├── templates/
│   ├── technical-programming.md          # T1
│   ├── tool-usage.md                     # T2
│   ├── concept-intro.md                  # T3
│   └── project-hands-on.md               # T4
└── scripts/
    ├── publish_to_feishu.sh              # 飞书一键发布（v3 混合方案首选+pandoc降级）
    ├── save_markdown.sh                  # MD 归档
    └── generate_illustrations.sh         # 🎨 批量生插画（v2.1新增）
    └── generate_illustrations.sh         # 🆕 mmx 批量生图
```

---

**记住主人的红线：结构清晰 + 图文并茂（技术图+插画）+ 注明所用模板** 🚨
