---
name: minimax-web-search
description: MiniMax MMX 联网搜索通用能力；当用户要求联网搜索、查一下、帮我搜、实时信息检索时使用 minimax_web_search 高层工具，不暴露终端等底层能力。
version: 1.0.0
author: kaka
category: web-access
tags: [minimax, mmx, web-search, safe-tool]
---

# MiniMax Web Search 通用联网搜索

## 适用场景

当用户要求：
- 联网搜索 / 网络搜索 / 网上搜索
- 搜索一下 / 查一下 / 帮我搜 / 搜一搜
- 查询实时信息、新闻、公开网页线索
- 使用 MiniMax / MMX 搜索能力

## 工具边界

使用 `minimax_web_search` 高层工具完成搜索。

普通用户侧不要使用：
- `terminal`
- `write_file`
- `execute_code`
- `browser_*`
- 其他底层执行/文件写入工具

## 输出规范

1. 不要把原始 JSON 直接展示给用户。
2. 将搜索结果整理为可读结论、要点和来源链接。
3. 如果信息不确定，要标注“需要进一步确认”。
4. 如果是企业调研等复杂报告，应交给对应业务能力（如 `enterprise_intelligence`），不要把本技能硬扩展成报告生成器。

## 推荐流程

1. 提炼用户问题为搜索关键词。
2. 优先调用 `minimax_web_search` 高层工具：
   - `query`: 搜索词
   - `max_results`: 默认 10，必要时 15-20
3. 如果当前环境没有暴露 `minimax_web_search` 高层工具、且任务执行者具备终端权限，可使用 MMX CLI 兜底；正确命令格式是：
   ```bash
   mmx search query --q "<搜索词>"
   ```
   不要使用旧/错误格式 `mmx web-search ...`。
4. 基于返回的 `markdown/results` 汇总答案。
5. 附上关键来源链接。

## 多轮产品/服务推荐搜索

当用户要求“搜 10~20 轮”“多搜几轮”“把推荐官网直接发我”“哪个更便宜/更稳定”这类产品或服务选型时：

1. 可用 `delegate_task` 并行拆成 2-3 个独立方向，每个方向使用 `minimax_web_search`：
   - 主流测评/榜单高频推荐
   - 隐私、安全、审计、退款政策等信任维度
   - 自建/企业级/替代方案等相邻类别
2. 汇总时优先保留“多个来源反复出现 + 可确认是官网”的候选项。
3. 用户明确要官网时，直接给官网 URL 列表，少解释；如用户追问价格，再按价格梯队/套餐类型总结。
4. 对 VPN、代理、爬虫、金融、医疗等敏感或受监管品类，只提供正规官网、合规用途、风险提醒和一般选购建议；不要提供规避监管、违法用途或滥用教程。
5. 避免把联盟返佣测评当成单一依据；能确认官网时优先官网，不能确认时标注“需进一步确认”。

## 验证

- `minimax_web_search` 对授权用户放行。
- `terminal` / `write_file` / `execute_code` 对普通用户仍阻断。
