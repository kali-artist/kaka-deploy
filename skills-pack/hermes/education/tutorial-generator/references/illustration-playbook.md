# 🎨 Illustration Playbook - 教程插画生成手册

> 教程的图不能只有架构图/流程图这种"技术图"，要配**生动插画**才好看好懂。
> 本手册规定：**什么章节配什么风格、prompt 怎么写、走什么通道**。

## 🎯 两类图片的定位

| 类型 | 目的 | 通道 | 命名前缀 |
|---|---|---|---|
| **技术图**（架构/流程/对比表） | 传达结构和逻辑 | architecture-diagram / excalidraw / baoyu-infographic / 内联SVG | `chXX_tech_描述.png` |
| **插画**（隐喻/场景/角色） | 帮助记忆、活跃阅读 | **mmx image**（首选） / image_gen（兜底） | `chXX_illu_描述.png` |

## 📐 每章配图策略（v2 默认方案）

对于 5~8 章教程：
- **开篇章 + 结尾章** 各配 1 张插画
- **中间章节** 每章至少 1 张技术图 + 视情况配插画
- 目标：全篇插画占比 30~50%，避免全是干巴技术图

**极短教程（≤3 章）**：只在开篇配 1 张封面插画即可。

## 🎨 插画风格锁定

固定用 **扁平化卡通风** 保证全篇风格统一。核心 prompt 骨架：

```
flat cartoon illustration, {场景描述}, {角色/对象}, {动作/隐喻},
soft pastel colors, clean vector style, playful and educational tone,
white background, no text, no watermark
```

**⚠️ 关键要求**：
- `no text, no watermark` —— AI 生成的文字大概率是乱码，坚决不要
- `white background` —— 方便嵌入白色文档背景
- `flat cartoon illustration` —— 锁定风格避免每张画风都不一样
- 中文场景用中文描述 + 英文风格词组合最稳

## 📝 常见教程主题的插画 prompt 模板

| 教程主题类别 | 隐喻/场景 | Prompt 示例 |
|---|---|---|
| 网络/穿透 | 快递员穿墙送包裹 | `flat cartoon, cheerful delivery person carrying package through a wall tunnel between two buildings, one labeled "internal", one labeled "public", soft pastel, white bg, no text` |
| 数据库/存储 | 图书馆管理员整理书架 | `flat cartoon, friendly librarian sorting colorful books into labeled shelves, soft pastel colors, playful, white bg, no text` |
| API/接口 | 服务窗口递交表单 | `flat cartoon, character handing a form through a service window to a robot clerk, soft pastel, white bg, no text` |
| CI/CD/部署 | 传送带工厂 | `flat cartoon, cute conveyor belt factory processing code boxes into deployed apps, soft pastel, playful, white bg, no text` |
| 安全/加密 | 保险箱守卫 | `flat cartoon, cute guard with a shield protecting a safe box with a padlock, soft pastel, white bg, no text` |
| AI/LLM | 机器人思考灯泡 | `flat cartoon, friendly robot with a big glowing light bulb above head, thinking pose, soft pastel, white bg, no text` |
| 前端/UI | 画家在浏览器画布上作画 | `flat cartoon, character painting on a browser window canvas, soft pastel, playful, white bg, no text` |
| 版本控制/Git | 时间线上的分支列车 | `flat cartoon, train branching on parallel tracks representing git branches, cute conductor, soft pastel, white bg, no text` |

## 🛠 生成脚本用法

```bash
# 用法：从 outline JSON 批量生图
bash scripts/generate_illustrations.sh <outline.json> <output_dir>
```

`outline.json` 格式（Step 2 大纲阶段产出）：
```json
{
  "illustrations": [
    {
      "id": "ch01_illu_gongwang_neiwang",
      "prompt": "flat cartoon, ...",
      "chapter": 1
    },
    ...
  ]
}
```

## ⚠️ 已知坑

1. **mmx 输出在 `~/image_001.jpg`**——不是当前目录！生成后必须 `mv` 到目标 images 目录
2. **文件名会覆盖**——mmx 每次都存成 `image_001.jpg`，脚本里必须**串行**生成并每张立即重命名
3. **首次生成失败重试 1 次**——mmx 偶发抽风，脚本自带重试
4. **兜底**：mmx 失败时自动 fallback 到 `image_gen`（在生成脚本里实现）
5. **验证**：可选调 `vision_analyze` 检查是否真的是插画风格、有无乱码文字，节省 token 时也可跳过
