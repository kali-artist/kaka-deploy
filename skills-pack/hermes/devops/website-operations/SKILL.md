---
name: website-operations
description: "已部署网站的运维管理：查看网站登记表、修改网站时获取部署信息、部署后创建飞书档案、健康检查。修改/更新已部署网站时使用。"
version: 1.0.0
author: 卡力
metadata:
  hermes:
    tags: [website, operations, maintenance, registry, cloudflare]
    related_skills: [cloudflare-pages-deployment]
---

# 网站运维管理

## When to Use

- 用户说"修改网站"、"更新网站"、"改下xxx网站"
- 用户说"查看已部署的网站"、"现在有哪些网站"
- 刚部署完新网站，需要创建飞书档案和登记
- 需要手动检查网站健康状态

## 默认规则

- 🔴 所有网站部署后必须绑定自定义域名（xxx.superkali.online），不能只用默认的 *.pages.dev 域名。自定义域名是网站交付的标准配置。

## 网站登记表

所有已部署网站的汇总在 `references/site-registry.md`。修改网站时先读取该文件获取部署信息和飞书文档链接。

每次部署新网站后，必须更新该文件（添加一行记录）。

---

## 修改网站流程

1. 读取 `references/site-registry.md` 获取目标网站的部署信息
2. 读取飞书部署档案获取详细配置（链接在登记表中）
3. 根据网站类型执行修改：
   - 纯静态：改代码 → **更新HTML中所有CSS/JS的缓存版本号** → git push → Cloudflare自动构建
   - 前后端分离前端：同上
   - 前后端分离后端：改代码 → 重新编译 → 重启服务 → 验证
4. 验证修改生效（curl检查URL，确认新版本号和新代码内容在线上）
5. 更新已有的飞书部署档案文档（追加修改记录 + 更新变化的配置项），**不要创建新文档、不要重新归档到多维表**
6. 更新本地 `references/site-registry.md`（如有配置变化）

🔴 **修改网站时禁止重复归档**：只更新已有飞书文档内容，不创建新文档，不往多维表插新记录。多维表归档仅在首次部署新网站时执行一次。

---

## 部署后文档创建（每次部署新网站必做）

每次完成新网站部署后，自动创建飞书文档记录项目背景和部署信息，归档到知识库，并更新登记表。

### 步骤

1. 用 lark-cli 创建飞书文档，标题格式：`网站部署档案 - <项目名>`
2. 写入以下信息（Markdown格式）：
   - 项目背景信息（部署前对齐内容）
     - 搭建目标/要解决什么问题
     - 目标用户与使用场景
     - 核心功能需求
     - 非功能需求（性能、安全、可扩展性等）
     - 技术栈与部署偏好
     - 域名偏好
     - 交付与维护计划
     - 外部依赖/对接系统
   - 项目概述（名称、路径、用途、状态、创建时间）
   - 部署结构（纯静态/前后端分离）
   - 前端详情（CF Pages项目名、GitHub仓库、构建命令、输出目录、环境变量、访问地址、自定义域名、DNS设置）
   - 后端详情（运行命令、工作目录、端口、进程管理、访问地址、环境变量、依赖版本）— 仅前后端分离
   - Tunnel配置（Tunnel名、ID、配置文件路径、Ingress规则）— 仅前后端分离
   - 本地端口占用
   - 后台登录信息（地址、账号、密码、修改建议）— 如有
   - 健康检查命令
   - 更新方式
   - 注意事项
3. 给两个管理员账号开通 full_access 权限：
   - {{FEISHU_OPEN_ID}}
   - {{FEISHU_OPEN_ID}}
4. 归档到知识库多维表（base-token: {{FEISHU_BASE_TOKEN}}, table-id: {{FEISHU_TABLE_ID}}）
   - 字段：标题, 知识类型(实践记录), 标签(运维自动化), 完整笔记(文档URL), 来源(自己实践), 状态(已归档), 日期(时间戳ms)
5. 更新 `references/site-registry.md` 添加一行记录

### 命令模板

```bash
# 1. 创建文档
DOC_ID=$(lark-cli docs +create --title "网站部署档案 - <项目名>" | jq '.data.document.document_id' -r)

# 2. 写入内容
lark-cli docs +update --doc $DOC_ID --command overwrite --doc-format markdown --content '<markdown内容>'

# 3. 开通权限
lark-cli drive +member-add --type docx --token $DOC_ID --member-type openid --member-id {{FEISHU_OPEN_ID}} --perm full_access --yes
lark-cli drive +member-add --type docx --token $DOC_ID --member-type openid --member-id {{FEISHU_OPEN_ID}} --perm full_access --yes

# 4. 归档到多维表（字段名：标题, 知识类型, 标签, 完整笔记, 来源, 状态, 日期）
lark-cli base +record-batch-create --base-token {{FEISHU_BASE_TOKEN}} --table-id {{FEISHU_TABLE_ID}} --json '{"fields":["标题","知识类型","标签","完整笔记","来源","状态","日期"],"rows":[["网站部署档案 - <项目名>","实践记录",["运维自动化"],"https://{{FEISHU_DOMAIN}}.feishu.cn/docx/'$DOC_ID'","自己实践","已归档",<timestamp_ms>]]}'
```

---

## 登记表同步说明

 site-registry.md，不互相传。

- 飞书多维表 → kaka：定时从飞书多维表拉最新数据，更新本地 site-registry.md
- 飞书多维表 → {{INSTANCE_NAME}}：定时从飞书多维表拉最新数据，更新本地 site-registry.md

两边独立从同一源头同步，不搞互相写。

---

## 修改网站代码时的陷阱与验证方法

### 陷阱1：多次 patch 调用导致大 HTML 文件截断

对同一个大 HTML 文件（>500行）连续多次调用 `patch` 工具，可能导致文件被截断——HTML body 内容和闭合标签全部丢失，只剩 CSS 部分被写入。文件从 1169 行变为 657 行，且无任何错误提示。

**安全做法**：用 Python 脚本通过 `terminal` 一次性完成所有修改：

```python
# 读取 → 内存替换 → 验证完整性 → 写回
with open('index.html', 'r') as f:
    content = f.read()
assert '</html>' in content, "File incomplete!"

# 批量替换
content = content.replace(old_css, new_css)
# ... 更多替换

assert '</html>' in content, "File incomplete after changes!"
with open('index.html', 'w') as f:
    f.write(content)
```

### 陷阱2：browser_vision 无法检测细微 CSS 效果

`browser_vision` 无法可靠检测 glassmorphism（backdrop-filter blur）、微妙 box-shadow、淡 background-gradient 等效果。Vision AI 会报告"无阴影/无毛玻璃"，即使 CSS 确实已生效。

**正确验证方式**：用 `browser_console` 执行 `getComputedStyle()` 程序化检查：

```javascript
const card = document.querySelector('.card');
const styles = getComputedStyle(card);
JSON.stringify({
  bg: styles.backgroundColor,
  backdropFilter: styles.backdropFilter,
  boxShadow: styles.boxShadow,
  borderColor: styles.borderColor
})
```

### 陷阱3：Cloudflare Pages 浏览器缓存（⚠️ 最易遗漏的部署步骤）

验证 CSS 变更时，浏览器可能加载旧缓存版本。加 URL 参数强制刷新：`https://example.com/?v=2`

**🔴 缓存版本号是 mandatory 步骤，不是 optional**：每次修改 CSS/JS 文件后，必须在 index.html 中更新所有引用的 `?v=` 参数，否则移动端浏览器（尤其是微信内置浏览器）会无限缓存旧版本，导致"代码已推送但用户看不到变化"。

**常见问题**：
- CSS 文件经常没有 `?v=` 参数（初始部署时遗漏）→ 需要主动添加
- 只更新了 JS 版本号但忘记 CSS → CSS 修改在移动端不生效
- 版本号格式不统一 → 建议用日期格式 `?v=YYYYMMDDx`（如 `?v=20260704a`），便于追溯部署时间

**验证方法**：
```bash
# 确认线上 HTML 包含新版本号
curl -s https://your-site.com/ | grep -E 'style\.css|chat\.js'
# 应输出带新版本号的引用，如：href="css/style.css?v=20260704a"

# 确认线上 CSS 内容已更新
curl -s "https://your-site.com/css/style.css?v=20260704a" | head -20
```

### 陷阱4：CSS 效果变化太微妙，用户看不到差异

AI 倾向于把 CSS 效果调得太"克制"（shadow 0.03、gradient 0.06、transparency 0.95），用户反馈"没啥变化"。当用户说看不到差异时，效果值需要 2-3 倍放大：

| 效果 | AI 觉得够了 | 用户能看到的 |
|------|-----------|-----------|
| box-shadow opacity | 0.03 | 0.06-0.08 |
| background gradient | 0.06 | 0.12-0.14 |
| 卡片透明度 | 0.90-0.95 | 0.60-0.70 |
| border-radius | 2px | 8px+ |
| hover translateY | -2px | -3px ~ -4px |
| font-weight 变化 | +50 | +100 (400→500→600) |

**策略**：一次性把多个效果值都调到位（shadow + gradient + transparency + radius + font-weight），不要逐个微调。用户看到变化后再根据反馈收窄。

### 陷阱5：用户要求改A，不要同时改B/C/D

用户说"改绿色光晕"时，只改背景渐变。不要同时调整卡片透明度、阴影深度、网格线、边框色等无关参数——即使用户之前夸过这些效果。

**错误模式**：用户要求改渐变 → 回退到旧commit再改 → 之前的阴影/毛玻璃/圆角全部丢失 → 用户不满。

**正确流程**：
1. 基于**当前最新commit**的文件修改（`git checkout HEAD -- index.html` 或直接编辑当前版本）
2. 只替换用户要求的那一处 CSS
3. 提交推送
4. 如果误改了不该改的，用 `git checkout <good-commit> -- index.html` 恢复完整版本，再只施加目标改动

```bash
# 恢复到有阴影效果的版本，再只改渐变
git checkout 0745283 -- index.html
python3 -c "
c = open('index.html').read()
c = c.replace(old_gradient, new_gradient)
open('index.html','w').write(c)
"
git add -A && git commit -m "style: 仅调整绿色光晕渐变" && git push
```

**铁律**：改啥就只改啥。其他效果保持不动。

---

## 手动健康检查

自动健康检查由 cron job 执行（每周一、四 9:00，先同步两边登记表再检查）。手动检查时执行以下命令：

```bash
# 1. Cloudflare Pages 项目状态
# 用 Python 读取 /root/.cloudflare-pages-token，调用 CF API 列出项目和部署状态

# 2. Tunnel 状态
systemctl is-active cloudflared
cloudflared tunnel info ai-novel

# 3. 本地后端端口
ss -tlnp | grep -E ':(3000|5173)'

# 4. 公网可达性
curl -s -o /dev/null -w '%{http_code}' https://api.superkali.online/api/health
curl -s -o /dev/null -w '%{http_code}' https://novel.superkali.online
curl -s -o /dev/null -w '%{http_code}' https://ai-novel-client.pages.dev
curl -s -o /dev/null -w '%{http_code}' https://kali-portfolio.pages.dev
```

## References

- `references/site-registry.md` — 网站登记表（所有已部署网站的汇总信息）
