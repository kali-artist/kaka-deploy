---
name: personal-work-portfolio
description: "Use when the user shares work content, asks for work summaries, resume generation, performance reviews, project retrospectives, or any career-related output. Automatically collects work records from fact_store and session history, stores them locally as structured JSON archives, and generates multi-scenario outputs (summaries, resumes, performance reports)."
version: 1.1.0
author: kaka
license: MIT
metadata:
  hermes:
    tags: [personal, portfolio, career, work-summary, resume, performance]
    related_skills: []
---

# 个人职业档案引擎

## Overview

{{MASTER_NAME}} 主人的个人工作内容采集、存储与多场景输出系统。从 fact_store 和 session 中自动采集散落的工作内容，也支持主人主动录入。所有记录结构化存储在本地 JSON 文件中，不写入长期记忆。需要时按场景（工作总结、简历、绩效等）灵活输出。

不预设固定分类，类型标签随内容自然生长。

## When to Use

- 主人分享工作内容、飞书记录、工作数据时 → 录入模式
- 主人说"采集一下""跑一轮自动采集"时 → 采集模式
- 主人问"我6月做了什么""影刀相关的有哪些"时 → 查询模式
- 主人要工作总结/简历/绩效/项目复盘时 → 输出模式
- 定期 cron 自动采集时 → 采集模式

**Don't use for:**
- 纯技术配置/环境搭建记录（不属于工作内容）
- 日常对话/非工作类内容
- 需要写入长期记忆的规则和偏好

---

## 🧭 执行导航层（模型入口，线性决策树）

### 核心执行铁律（违反即出错）
- 🔴 只存储在本地文件（~/kaka-portfolio/），绝不写入长期记忆（MEMORY.md/USER.md）
- 🔴 自动采集必须去重，不重复录入已有记录
- 🔴 输出内容基于真实记录，不编造未记录的内容
- 🔴 涉及日期必须准确，不确定时用 `date` 命令查证
- 🔴 每次新增/修改记录后必须同步更新 index.json

### 线性执行流程（按顺序执行，一步一判断）

1. **判断模式** → 用户分享内容？→ 执行【录入】；用户要求采集？→ 执行【采集】；用户提问查询？→ 执行【查询】；用户要输出文档？→ 执行【输出】
2. **执行对应模式** → 按下方操作流程逐步执行
3. **验证** → 运行验证清单，确认索引同步、无重复、输出正确

### 标准快速查表
| 维度 | 标准 | 对应动作 |
|------|------|----------|
| 去重判断 | 同日期+相似标题 | 跳过，不重复录入 |
| 日期不确定 | 无法确认具体日期 | 用 `date` 命令查证，或标注为月初 |
| 存储位置 | ~/kaka-portfolio/records/ | 按月归档 YYYY-MM.json |
| 输出位置 | ~/kaka-portfolio/exports/ | Markdown 格式 |
| 长期记忆 | 禁止写入 | 工作内容只在本地文件 |
| 采集来源 | fact_store + session_search | 双源扫描，去重后存储 |

---

## 数据存储

### 目录结构
```
~/kaka-portfolio/
  index.json              # 主索引（轻量，所有记录的摘要列表）
  records/
    2026-01.json          # 按月归档
    2026-06.json
    ...
  exports/                # 生成的输出文档
    work-summary-2026h1.md
    resume-202607.md
    ...
```

### 记录结构
```json
{
  "id": "20260605-001",
  "date": "2026-06-05",
  "month": "2026-06",
  "type": "ai-project",
  "tags": ["Hermes", "权限管控", "飞书网关"],
  "title": "Hermes飞书网关权限管控体系搭建",
  "summary": "搭建3层权限架构，实现跨平台admin白名单分离、身份映射机制",
  "details": "",
  "source": "session:20260605_101435",
  "outputs": [],
  "created_at": "2026-07-02T10:30:00Z",
  "updated_at": "2026-07-02T10:30:00Z"
}
```

### 字段说明
| 字段 | 必填 | 说明 |
|------|------|------|
| id | ✅ | 日期+序号，如 20260605-001 |
| date | ✅ | ISO日期 |
| month | ✅ | YYYY-MM，用于按月归档和检索 |
| type | ✅ | 类型标签，自由填写（见常见类型参考） |
| tags | ✅ | 自由标签数组，随内容自然生长 |
| title | ✅ | 简短标题 |
| summary | ✅ | 一句话摘要 |
| details | ❌ | 详细描述（如有） |
| source | ✅ | 来源：manual / session:xxx / fact:xxx |
| outputs | ❌ | 产出物引用（文档链接、文件路径等） |

### 常见类型参考（非穷举，可自由扩展）
| 类型 | 说明 |
|------|------|
| client-project | 客户项目跟进 |
| training | 实战营/培训 |
| ai-project | AI专项 |
| internal-management | 内部管理 |
| document | 文档产出 |
| business-trip | 出差 |
| skill-development | 技能开发 |
| other | 其他 |

---

## 操作流程

### 1. 录入模式

当用户主动提供工作内容时：

1. **解析内容**：识别时间、类型、关键信息
2. **结构化**：按记录结构组织字段，不确定的字段留空或询问
3. **去重检查**：读取 index.json，检查同日期+相似标题是否已存在
4. **存储**：追加到对应月份的 JSON 文件（不存在则创建）
5. **更新索引**：在 index.json 中添加摘要条目
6. **确认**：向用户展示录入结果

### 2. 采集模式

定期从 fact_store 和 session 中自动采集散落的工作内容：

1. **扫描 fact_store**：
   - `fact_store search` 用关键词：客户、项目、培训、AI、RPA、影刀、出差、文档、绩效、简历、实战营、直播等
   - 过滤出工作相关事实（排除纯技术配置/规则类）

2. **扫描 session**：
   - `session_search` 用相同关键词
   - 从会话摘要中提取工作内容

3. **去重**：
   - 读取 index.json，对比已有记录的日期+标题相似度
   - 跳过已存在的记录

4. **结构化存储**：
   - 将采集内容转为标准记录格式
   - source 标注为 session:xxx 或 fact:xxx
   - 存入对应月份文件，更新索引

5. **输出采集报告**：本次新增N条，按类型/月份统计

### 3. 查询模式

支持多维度查询：
- **按时间**："6月做了什么" → 筛选 month
- **按类型**："所有客户项目" → 筛选 type
- **按标签**："影刀相关的" → 筛选 tags
- **按关键词**：搜索 title + summary + details
- **组合查询**："6月的AI专项" → type + month

查询时读取 index.json 做初步筛选，需要详情时读取对应月份的 JSON 文件。

### 4. 输出模式

#### 工作总结
- 输入：时间范围（月/季/年/自定义）
- 输出：按类型分组的结构化总结，含量化统计
- 格式：Markdown，保存到 ~/kaka-portfolio/exports/

#### 简历生成
- 输入：目标岗位/方向（可选）
- 输出：能力模块化简历
- 从记录中提取：项目经验、技能、成果、培训经历

#### 绩效总结
- 输入：考核周期，或具体的绩效问题
- 数据来源：portfolio记录为主；涉及失误/教训类问题需额外用 session_search 补充（portfolio不存失误记录）
- 输出风格：**粗略口语化草稿**，用户会自己改，禁用"解决了什么/带来什么变化/具体价值"等结构化模板
- 常见绩效问题类型与应对：
  - "最有价值的N件事"：从记录中按战略价值筛选，提供备选项供用户挑选组合
  - "AI改变工作方式"：找前后对比最明显的场景，从记录中提炼before/after
  - "能力/认知突破"：按时间线看工作模式变化，提炼认知转变
  - "最大失误/遗憾"：用 session_search 搜"失误/失败/问题/教训"等关键词，提供多个方向供用户选
  - "需要什么支持"：分析当前瓶颈（人力/预算/机会），给2-3个不同角度的备选
- 从记录中提取：客户数量、培训场次、文档产出、AI专项等量化数据
- 跨类别整合：用户可能要求把不同类别的记录合并到一件事里（如把技能开发项并入流程标准化），灵活组合

#### 自定义输出
- 用户描述需求，基于记录灵活组织输出

---

## 自动采集 Cron 建议

建议配置定期采集 cron job：
- 频率：每周一次（如每周日晚）
- 动作：执行采集模式
- 交付：local（存档不打扰用户）

---

## Common Pitfalls

1. **重复录入**：自动采集时必须做去重，避免同一条工作内容多次记录。每次采集前先读取 index.json 对比。
2. **日期不准**：不确定日期时用 `date` 命令查证，不猜测。session 中提取的记录以会话时间为准。
3. **类型混乱**：类型标签自由但不随意，参考常见类型列表保持一致性。新类型可自由添加但需在第一次使用时说明。
4. **存储位置错误**：只在 ~/kaka-portfolio/ 存储，不写入长期记忆（MEMORY.md/USER.md/fact_store）。
5. **编造内容**：输出只能基于已存储的真实记录，不能为凑内容而编造。记录不足时如实说明。
6. **索引不同步**：每次新增/修改记录后必须同步更新 index.json，否则查询和采集会遗漏记录。

---

## Verification Checklist

- [ ] 录入后 index.json 已同步更新
- [ ] 采集后已去重，无重复记录
- [ ] 查询结果来自实际存储的记录，未编造
- [ ] 输出文档保存在 ~/kaka-portfolio/exports/
- [ ] 长期记忆未写入任何工作记录内容
- [ ] 日期字段准确，无猜测
- [ ] 记录类型使用常见类型参考中的标签，或合理的新类型
