# 🧩 Related Skills Matrix - 关联技能调用矩阵

> tutorial-generator 是**指挥官**，此矩阵告诉你什么场景下调用哪个成熟技能。

## 图表生成

| 需要的图类型 | 首选技能 | 何时用 | 命令示例 |
|-------------|---------|--------|---------|
| **技术架构图/云架构/系统组件图** | `architecture-diagram` | 有明确技术组件与连线 | 参考该技能 SKILL.md |
| **流程图/时序图/状态机（手绘感）** | `excalidraw` | 需要"轻松、白板感" | 参考该技能 SKILL.md |
| **信息图/概念对比/知识可视化** | `baoyu-infographic` | 概念入门/横向对比 | 参考该技能 SKILL.md |
| **数学动画/算法可视化** | `manim-video` | 数学/算法类深度讲解 | 参考该技能 SKILL.md |
| **代码运行截图/终端截图** | 直接 markdown 代码块 | 无需图形化 | — |
| **极简示意图（<3 个元素）** | 手写内联 SVG | 图工具太重时 | 直接嵌入 markdown |
| **生动插画/隐喻场景图** | `minimax-image-generation`（mmx） | 开篇/结尾章配插画、概念隐喻 | `mmx image generate --prompt "flat cartoon, ..." --aspect-ratio 16:9 --out-dir ./images --out-prefix chXX_illu_xxx` |

**兜底方案**：外部图 API 挂了 → 手写 SVG → 用 `rsvg-convert` 或 headless 浏览器截图转 PNG。

## 发布通道

| 目标 | 技能 | 说明 |
|------|------|------|
| **飞书文档** | `feishu-doc-automation` | 用 Lark CLI `docs +create --doc-format markdown` |
| **飞书图片插入** | `feishu-doc-automation` | 用 `docs +media-insert` 一条命令，不再用 3 步 API |
| **飞书文档归档** | `feishu-doc-auto-archiving` | 发完自动登记到多维表 |
| **本地 Markdown** | 本技能 `scripts/save_markdown.sh` | 存 `~/tutorials/` + 图片 |

## 需求对齐

| 场景 | 技能 |
|------|------|
| 教程主题模糊、需澄清 | `product-brainstorming` |

## 迭代优化

| 场景 | 技能 |
|------|------|
| 教程质量校验/回归测试 | `skillopt` |

## 判断树（速用）

```
用户要教程
  ├─ 主题清楚吗？
  │   ├─ 否 → 先跑 product-brainstorming
  │   └─ 是 → 进 Step 1 对齐
  ├─ 要架构图？→ architecture-diagram
  ├─ 要手绘流程？→ excalidraw
  ├─ 要概念对比信息图？→ baoyu-infographic
  ├─ 要生动插画/场景隐喻？→ minimax-image-generation (mmx) → generate_illustrations.sh
  ├─ 发飞书？→ feishu-doc-automation + feishu-doc-auto-archiving
  └─ 存本地？→ scripts/save_markdown.sh
```
