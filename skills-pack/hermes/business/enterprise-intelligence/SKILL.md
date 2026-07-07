---
name: enterprise-intelligence
description: 企业信息智能查询 - 根据公司名称查询企业工商、风险、知识产权等全方位信息，生成专业报告文档
version: "1.4.0"
author: kaka (卡力的专属小机器人)
category: business
tags: [enterprise, company, report, business-intelligence, research]
related_skills: [permission-governance]
trigger: |
  当用户发送以下内容时自动加载此技能：
  - 查询XX公司、企业信息查询、公司背景调查
  - 客户拜访、拜访准备、客户背景调查
  - 尽职调查、尽调、投资尽调报告
  - 找增购点、增购机会分析
  - 企业分析、公司调研、商业情报
metadata:
  role: normal
  users: [all]
  api_key_env: "MINIMAX_API_KEY"        # 不在Skill中保存真实密钥
  group_id_env: "MINIMAX_GROUP_ID"      # 如API要求Group ID，从环境变量读取
  api_endpoint: "https://api.minimax.chat/v1/text/chatcompletion_v2"
  web_search_param: "enable_web_search"  # MMX联网搜索开关
  model: "abab6.5s-chat"
---

# 🏢 Enterprise Intelligence - 企业信息智能查询

根据公司名称，通过**Minimax MMX联网搜索能力**自动查询企业全方位信息，根据特定需求生成专业报告文档。

---

## 🎯 功能概述

### 飞书云文档报告排版基准（统一规范）

当企业调研/客户拜访/尽调/增购分析报告需要生成飞书云文档时，必须加载并遵守 `feishu-doc-automation` 中的主人融合后的统一飞书文档规范：

- **基础质量**：XML/富 block 优先、标题层级清晰、表格/列表/Callout 正确使用、颜色语义一致、避免段落墙、富 block 自检、API 失败时不得擅自降级。
- **阅读体验**：首屏结论前置，顶部添加报告元信息区，使用 `【核心结论】`、`【关键发现】`、`【风险提示】`、`【行动建议】`、`【下一步】` 等全角方括号视觉锚点。
- **企业报告专属要求**：客户背景、工商信息、业务/产品、经营信号、风险、机会、建议必须按主题汇总整理；多维信息优先表格化，不做原始资料堆砌。
- **交付闭环**：结尾必须给可执行下一步，如拜访问题清单、销售切入点、风险核验项、跟进优先级。

### 核心能力
- ✅ **MMX联网搜索**：使用Minimax内置的联网搜索能力获取最新企业信息
- ✅ **工商信息查询**：基本信息、法定代表人、注册资本、成立日期等
- ✅ **股东与投资信息**：股权结构、实际控制人、对外投资
- ✅ **风险信息**：司法风险、经营风险、失信被执行人
- ✅ **知识产权**：专利、商标、著作权、软件著作权
- ✅ **经营信息**：招投标、招聘、产品、融资信息
- ✅ **高管信息、分支机构、变更记录**
- ✅ **行业分析、竞品信息、新闻舆情**

### 报告类型
| 报告类型 | 适用场景 | 重点关注维度
|----------|----------|----------
| 🤝 **客户拜访报告** | 首次拜访前准备 | 公司规模、主营业务、核心产品、最近动态、决策人信息
| 💰 **增购分析报告** | 寻找销售增购机会 | IT投入、系统现状、痛点分析、增购机会点
| 📊 **尽职调查报告** | 投资/合作尽调 | 全面风险评估、财务状况、法律风险、经营状况
| 📋 **通用调研报告** | 通用企业研究 | 全方位信息、行业地位、竞争力分析

---

## 🚀 触发方式

### 关键词触发（自动加载）
```
查询[公司名]
查询[公司名] 客户拜访
查询[公司名] 找增购点
查询[公司名] 尽职调查
企业信息 [公司名]
```

### 示例
```
用户：查询阿里巴巴 客户拜访
用户：查询字节跳动 找增购点
用户：查询腾讯 尽职调查
用户：查询华为 通用报告
```

---

## 📋 执行流程

### 步骤1：提取公司名称
从用户消息中提取**公司名称**（必填）。
- 如果用户没有提供公司名，询问：
  ```
  您好！请问您想查询哪家公司的信息呢？
  ```

### 步骤2：询问报告类型、用户目的与输出格式
获取公司名称后，确认用户需求；如用户已经在消息中说明了报告类型/目的/格式，可直接采用，不要重复询问。

```
好的！请问您需要什么类型的报告，以及最终输出什么格式？

报告类型：
1️⃣ 🤝 客户拜访报告 - 首次拜访前准备
2️⃣ 💰 增购分析报告 - 寻找销售增购机会
3️⃣ 📊 尽职调查报告 - 投资/合作尽调
4️⃣ 📋 通用调研报告 - 全方位企业研究

输出格式（三选一）：
A. 飞书文档（默认推荐，使用 feishu-doc-automation）
B. Markdown 文档（.md 文件）
C. 文本文档（.txt 文件）

也可以补充你的目的，例如“拜访前准备 / 找增购点 / 投资尽调 / 供应商评估”。
```

### 步骤3：用户身份确认
- 如果是已知用户（在feishu_user_map中有记录），直接开始查询
- 如果是未知用户，礼貌询问：
  ```
  请问您怎么称呼？我好为您生成报告~
  ```

### 步骤4：确认开始
告知用户：
```
好的[姓名]！我正在查询**[公司名]**的信息，大约需要3-5分钟，请稍候... 🕒
```

### 步骤5：数据收集与报告生成
根据可用数据源按优先级选择查询方式：

#### 🔵 首选：MMX 联网搜索
当Minimax MMX Web Search可用时：
```python
data = {
    "model": "abab6.5s-chat",
    "messages": [...],
    "enable_web_search": True
}
```

#### 🟡 备用：360搜索 + 水滴信用（curl直接提取）
当浏览器工具频繁超时或API不可用时，使用**零依赖、高成功率**的curl方案：

```bash
# 直接通过360搜索和水滴信用获取企业信息（无需浏览器）
# 已验证：无需验证码，访问稳定，信息完整

# 搜索并提取关键信息
curl -s "https://www.so.com/s?q=杭州绮辰纺织品有限公司" \
  | grep -E "法定代表人|注册资本|成立日期|经营状态|统一社会信用代码" \
  | head -30

# 或直接访问水滴信用详情页（从搜索结果中提取URL）
curl -s "https://shuidi.cn/company-[digest].html" \
  | grep -E "法定代表人|地址|经营范围|参保人数" \
  | head -50
```

**可提取的关键字段（已验证）**：
- 公司名称、成立日期、注册资本、经营状态
- 法定代表人、统一社会信用代码、企业地址
- 经营范围、行业分类、公司类型、登记机关
- 股东信息（部分可见）、分支机构、变更记录

**核心优势**：
- ✅ 无需浏览器，curl即可完成
- ✅ 无验证码，访问稳定可靠
- ✅ 信息足够生成基础企业报告
- ✅ 适合服务器环境无GUI场景

### 步骤6：按用户选择的格式交付报告
**【强制要求】必须生成文档/文件形式并尝试发送或返回链接**：
1. 如果用户选择 **飞书文档**：使用 `feishu-doc-automation` 的创建/写入规范生成飞书文档；同时保存本地 Markdown 备份。
2. 如果用户选择 **Markdown 文档**：生成 `.md` 文件并通过 `send_message` 发送 `MEDIA:/path/to/file`。
3. 如果用户选择 **文本文档**：生成 `.txt` 文件并通过 `send_message` 发送 `MEDIA:/path/to/file`。
4. 如果用户未选择格式：先询问“飞书文档 / md文档 / 文本文档”三选一；如用户要求直接处理且未指定，默认飞书文档。
5. 微信/飞书文件发送失败时，降级显示文件绝对路径或飞书链接，并说明本地文件已保存。

## 🔧 API调用规范
## 🔧 API调用规范

### 方式1：mmx-cli 命令行（推荐）
使用 `mmx search query` 命令进行联网搜索，这是Minimax官方推荐的方式。

**当前已验证语法（2026-06）**：本环境中的 `mmx search query --help` 显示需要用 `--q` 传入查询词；JSON 输出使用 `--output json`。不要默认使用旧写法 `mmx search query "关键词" --json --limit 10`，执行前先跑一次 `mmx search query --help` 确认当前版本参数。

```bash
# 安装mmx-cli
npm install -g mmx-cli

# 配置API密钥
mmx config set api_key sk-cp-xxxxxxxxxxxx

# 搜索企业信息（当前环境已验证）
mmx search query --q "阿里巴巴集团 工商信息" --output json
```

**批量搜索规范（强制）**：默认将 MMX 作为企业调研/联网搜索的首选能力。围绕公司主体生成约 20 轮多维关键词，且必须结合用户目的动态调整检索词：
- 基础维度：工商、法定代表人、统一社会信用代码、官网、主营业务、股东/实控人、高管、对外投资、融资、专利、商标、软著、诉讼、被执行、失信、行政处罚、经营异常、招聘、招投标、新闻、竞品、客户案例。
- 客户拜访：增加“组织架构、近期重点、业务痛点、合作切入点、决策人”。
- 增购分析：增加“IT系统、现有供应商、信息化建设、预算、招标、数字化需求”。
- 尽职调查：增加“关联方、重大诉讼、合规风险、财务风险、履约风险”。
- 每轮原始 JSON/文本保存到 `/tmp/enterprise-intelligence/{company}_{timestamp}/raw_mmx/`，同时保存 `research.json` 方便追溯。
- 报告必须是**高可读的主题化调研文档**，不能只是 MMX 搜索结果堆叠或原始数据罗列；应把证据按客户背景、客户基础信息、业务/产品、经营动态、风险合规、股权/关键人/知识产权、机会建议等章节综合整理。
- 结论前置：报告开头必须包含执行摘要、可信度/信息完整度判断、关键发现和下一步动作建议；每个章节优先给归纳结论，再列证据和来源。
- 主体事实要严格区分：只把精确匹配目标公司的信息写入主体事实；近似名称、同名/疑似关联或搜索误命中的公司必须单独放入“潜在混淆主体/近似名称”章节，不得混入目标公司结论。
- 报告必须包含检索覆盖表、核心结论、按目的组织的建议、重点信息源/线索、原始检索摘要节选。
- 正式交付前必须咨询或识别用户输出格式：飞书文档、Markdown 文档（.md）、文本文档（.txt）。用户未说明时优先询问；用户要求高效处理时默认飞书文档并保留 Markdown 备份。

**mmx-cli 参数注意：**
```bash
# 先确认真实可用参数
mmx search query --help

# 当前环境常用形式
mmx search query --q "关键词" --output json
```

**在脚本中使用mmx-cli：**
```python
from enterprise_query import search_via_mmx_cli

result = search_via_mmx_cli(
    query="阿里巴巴集团 股东信息",
    limit=10,
    json_output=True
)
```

---

### 方式2：ChatCompletion V2 API
通过 `enable_web_search` 参数启用联网搜索：

```python
API_KEY = "sk-cp-xxxxxxxxxx"  # 您的API密钥
GROUP_ID = "1234567890"       # 您的Group ID（必填！）
API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-Group-Id": GROUP_ID  # 必填！认证必须参数
}

data = {
    "model": "abab6.5s-chat",
    "messages": [
        {"role": "system", "content": "你是企业信息查询专家..."},
        {"role": "user", "content": "请搜索查询[公司名]的工商信息..."}
    ],
    "enable_web_search": True,  # 🔑 启用MMX联网搜索
    "temperature": 0.1,
    "max_tokens": 4000
}
```

---

### 关键参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `X-Group-Id` | Header | ✅ | Minimax账号Group ID，必须在请求头中传递 |
| `Authorization` | Header | ✅ | Bearer + API_KEY |
| `enable_web_search` | Body | ✅ | 设置为True启用联网搜索 |
| `model` | Body | ✅ | 建议使用 `abab6.5s-chat` 支持联网搜索 |

### 获取Group ID的方法
1. 登录 [Minimax开放平台](https://platform.minimaxi.com/)
2. 进入 **"账户设置"** 或 **"API管理"** 页面
3. 找到您的 Group ID（通常是一串数字）
4. 复制到脚本的 `GROUP_ID` 变量中

---

### 脚本调用方式
```bash
# 直接调用Python脚本查询（新版：默认约20轮MMX联网搜索）
python3 ~/.hermes/skills/business/enterprise-intelligence/enterprise_query.py "公司名称" [报告类型] [输出文件] [兼容旧参数] \
  --purpose "用户目的/业务场景" \
  --rounds 20 \
  --output-format feishu|md|txt \
  --user-name "用户称呼"

# 参数说明:
#   报告类型: 1/客户拜访, 2/增购分析, 3/尽职调查, 4/通用报告
#   --purpose: 用户目的，例如“拜访前准备”“找增购点”“投资尽调”“供应商评估”
#   --rounds: MMX联网搜索轮次，默认20
#   --output-format: feishu=飞书文档, md=Markdown文件, txt=文本文档
#   输出文件: 可选；仅 md/txt 直接使用该路径，feishu 会自动创建飞书文档并保留本地md备份

# 示例1: 生成飞书文档版客户拜访报告
python3 ~/.hermes/skills/business/enterprise-intelligence/enterprise_query.py "阿里巴巴集团" 客户拜访 \
  --purpose "拜访前准备，寻找数据智能切入点" --rounds 20 --output-format feishu --user-name "张三"

# 示例2: 生成Markdown版尽调报告
python3 ~/.hermes/skills/business/enterprise-intelligence/enterprise_query.py "腾讯控股" 尽职调查 \
  --purpose "投资尽调" --rounds 20 --output-format md

# 示例3: 生成文本文档版增购分析
python3 ~/.hermes/skills/business/enterprise-intelligence/enterprise_query.py "某某科技有限公司" 增购分析 \
  --purpose "寻找增购点" --rounds 20 --output-format txt
```

---

### 主要函数接口
```python
# 查询企业信息并生成报告
from enterprise_query import query_and_generate_report

report = query_and_generate_report(
    company_name="杭州绮辰纺织品有限公司",
    report_type="1",  # 客户拜访报告
    user_name="张三",
    output_file="/path/to/report.md",
    search_mode="auto"  # auto/cli/api
)

# 单独使用mmx-cli搜索
from enterprise_query import search_via_mmx_cli
result = search_via_mmx_cli("企业名称 工商信息")

# 检查mmx-cli是否可用
from enterprise_query import check_mmx_cli_available
if check_mmx_cli_available():
    print("mmx-cli已安装")
```
    report_type="1",  # 客户拜访报告
    user_name="张三",
    output_file="/path/to/report.md"  # 可选：保存到文件
)
```

---

## 📊 报告模板

### 客户拜访报告模板
```markdown
# 🤝 [公司名] 客户拜访报告

## 📋 一、公司概览
- 成立时间、注册资本、法定代表人
- 经营范围、主营业务
- 公司规模、人员规模

## 👥 二、核心决策人信息
- 法定代表人、高管背景
- 股东结构、实际控制人

## 💼 三、主营业务与产品
- 核心产品线
- 最近业务动态
- 客户案例

## 🎯 四、拜访建议
- 切入话题建议
- 可能的兴趣点
- 注意事项

## 📅 五、最新动态
- 最近6个月重大事件
```

---

## 📤 报告文件发送规范

### ⚠️ 【强制要求】用户偏好
根据用户明确要求：**报告必须以文件形式发送，不能只显示文本内容**。这是最高优先级的操作规范，必须遵守。

### 发送流程
```
报告生成后 → 保存为 .md 文件
       ↓
尝试 send_message 发送 MEDIA: 文件
       ↓ 成功 ✓
用户收到文件附件
       ↓ 失败（如WeChat超时）
🟡 降级方案：
   1. 显示完整文件路径
   2. 显示文件内容供用户复制保存
   3. 告知用户文件已保存在服务器
```

### WeChat发送失败处理
**现象**：`Weixin media send failed: Timeout context manager should be used inside a task`
**处理步骤**：
1. 确认文件已成功保存到磁盘
2. 显示文件的绝对路径
3. 显示报告完整内容
4. 提示用户可复制保存为.md文件

**标准回复模板**：
```
✅ 报告已成功生成并保存！
📄 文件路径: /home/ubuntu/公司名_报告类型.md

---
[完整报告内容]
---

微信发送文件暂时遇到问题，您可以直接复制上面的内容保存为 .md 文件使用~
```

---

## ⚠️ 常见问题与解决方案

### 1. Minimax / MMX 认证失败
**现象**：`mmx search query ...` 或API调用返回 `API error: login fail: Please carry the API secret key in the 'Authorization' field`。
**排查要点**：
1. 先确认 CLI 已安装且命令语法匹配当前版本：`mmx --version`、`mmx search query "测试" --json --limit 3`。
2. 不要把真实API Key写进Skill或脚本；从环境变量读取：`MINIMAX_API_KEY`，必要时读取 `MINIMAX_GROUP_ID`。
3. 检查CLI是否真正把密钥放进 HTTP `Authorization` 头，而不是只作为普通参数；若CLI版本过旧/认证方式不兼容，优先改为直接调用MiniMax HTTP API。
4. MiniMax API调用常见头：`Authorization: Bearer $MINIMAX_API_KEY`、`Content-Type: application/json`，如平台要求再加 `X-Group-Id: $MINIMAX_GROUP_ID`。
5. 若用户曾提供安装包和Key，先在会话历史/服务器文件中确认现有资源，不要重复让用户提供；但认证仍失败时，需要说明可能是Key类型、Group ID或CLI版本不匹配。
**处理策略**：认证未通过前不要宣称MMX联网搜索可用；自动降级到curl企业查询方案生成文件报告。

### 2. Minimax模型回复"无法联网搜索"
**现象**：API返回成功，但模型回复"我的知识截止到2023年4月，无法访问互联网"
**原因**：`enable_web_search` 参数可能在当前模型版本不生效
**解决方案**：自动降级到 **curl + 360搜索 + 水滴信用** 方案

### 3. 浏览器工具频繁超时
**现象**：`browser_navigate` 60秒超时，无法抓取爱企查/天眼查页面
**原因**：企业查询网站反爬机制严格
**解决方案**：优先使用 curl 方案，无需浏览器

### 3. 数据不完整
**现象**：某些字段无法查询到
**解决方案**：在报告中标注"未公开"或"暂无信息"，不要编造数据

---

## 📋 已验证工作流（生产环境）

```
用户发送"查询[公司名]"
       ↓
Hook匹配关键词 → 自动加载Skill
       ↓
询问报告类型（1-4）
       ↓
询问用户姓名（个性化报告）
       ↓
🔵 尝试 MMX 联网搜索（enable_web_search=True）
       ↓ 如失败
🟡 降级到 curl + 360搜索 + 水滴信用
       ↓
整理数据 → 生成Markdown报告
       ↓
💾 【强制】保存报告到 .md 文件
       ↓
📤 尝试发送文件附件
       ↓ 成功 ✓
返回文件给用户
       ↓ 失败 ✗
降级：显示文件路径 + 完整内容供复制
```

---

## 🔒 权限配置

### 适用用户：**所有私聊用户
### 需要关键词触发后自动加载
### 权限管控：通过permission-governance的keyword_skill_map配置

### 配置位置
```yaml
# ~/.hermes/permission-config.yaml

keyword_skill_map:
  (查询|企业信息|公司|客户拜访|尽职调查|背景调查|增购点):
    skill: enterprise-intelligence
    instruction: 激活企业信息查询功能...
```

---

## 🛠️ 调试与测试

### 专用工具封装与上线验证

当把企业查询能力封装成普通用户可用的 Hermes 高层工具，或用户询问“企业查询工具现在好了吗/上线了吗”时，按以下顺序验证，而不是只看最终回复：

```bash
# 1) 语法检查：业务脚本、工具注册、权限 hook
python3 -m py_compile \
  ~/.hermes/skills/business/enterprise-intelligence/enterprise_query.py \
  ~/.hermes/hermes-agent/tools/enterprise_intelligence_tool.py \
  ~/.hermes/hooks/permission-manager/handler.py \
  ~/.hermes/hooks/permission-manager/pre_tool_call_shell.py

# 2) YAML 检查：统一权限配置 + 目标 profile
python3 - <<'PY'
import yaml, os
for p in ['~/.hermes/permission-config.yaml','~/.hermes/profiles/tiao/config.yaml']:
    path=os.path.expanduser(p)
    yaml.safe_load(open(path, encoding='utf-8'))
    print('YAML OK', path)
PY

# 3) 工具注册与 toolset 暴露检查
python3 - <<'PY'
import sys, importlib.util
sys.path.insert(0, '/home/ubuntu/.hermes/hermes-agent')
spec = importlib.util.spec_from_file_location('enterprise_intelligence_tool', '/home/ubuntu/.hermes/hermes-agent/tools/enterprise_intelligence_tool.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
print('TOOL_SCHEMA', mod.ENTERPRISE_INTELLIGENCE_SCHEMA['name'], mod.ENTERPRISE_INTELLIGENCE_SCHEMA['parameters']['required'])
import toolsets
print('TOOLSET_HAS_ENTERPRISE', 'enterprise_intelligence' in toolsets.TOOLSETS)
print('TOOLSET_TOOLS', toolsets.TOOLSETS.get('enterprise_intelligence',{}).get('tools'))
PY

# 4) MMX CLI 可用性与查询词生成检查
python3 - <<'PY'
import importlib.util
spec = importlib.util.spec_from_file_location('enterprise_query', '/home/ubuntu/.hermes/skills/business/enterprise-intelligence/enterprise_query.py')
eq = importlib.util.module_from_spec(spec); spec.loader.exec_module(eq)
queries = eq.build_search_queries('测试公司', '客户拜访', '拜访前准备', 20)
print('QUERY_COUNT', len(queries))
print('FIRST_QUERY', queries[0])
print('MMX_AVAILABLE', eq.check_mmx_cli_available())
PY

# 5) 权限 allow/block 最小测试：高层工具放行，高危工具阻断
python3 - <<'PY'
import asyncio, importlib.util, pathlib
p = pathlib.Path('/home/ubuntu/.hermes/hooks/permission-manager/handler.py')
spec = importlib.util.spec_from_file_location('pm', p)
pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)
uid='{{FEISHU_OPEN_ID}}'
async def main():
    for tool in ['enterprise_intelligence','web_search','feishu_doc_create','terminal','write_file','execute_code','browser_navigate']:
        print(tool, await pm.handle('pre_tool_call', {'user_id':uid,'platform':'feishu','tool_name':tool}))
asyncio.run(main())
PY

# 6) 如果 profile toolsets 刚修改过，确认目标 gateway 已重启且 active
systemctl --user is-active hermes-gateway-tiao.service
systemctl --user show hermes-gateway-tiao.service -p ActiveState -p SubState -p ExecMainStartTimestamp --value
```

期望结果：
- `TOOL_SCHEMA enterprise_intelligence ['company_name', 'output_format']`
- `TOOLSET_HAS_ENTERPRISE True`
- `TOOLSET_TOOLS ['enterprise_intelligence']`
- `QUERY_COUNT 20`
- `MMX_AVAILABLE True`
- `enterprise_intelligence` 放行；`terminal` / `write_file` / `execute_code` / `browser_navigate` 阻断。

### 测试命令
```bash
# 查看当前 mmx search 参数，避免 CLI 版本差异导致误用旧参数
/home/ubuntu/.hermes/node/bin/node /home/ubuntu/.hermes/scripts/mmx.mjs search query --help

# 生成 Markdown 报告测试（会真实执行 MMX 联网搜索）
python3 ~/.hermes/skills/business/enterprise-intelligence/enterprise_query.py "阿里巴巴集团" 通用报告 \
  --purpose "企业调研测试" --rounds 3 --output-format md --user-name "测试用户"
```

### 日志位置
```
~/.hermes/logs/enterprise-query.log
```

---

## 📈 未来扩展

### 待实现功能
- [ ] 报告导出为PDF
- [ ] 多公司对比分析
- [ ] 行业分析报告
- [ ] 竞品分析报告
- [ ] 实时监控企业动态
