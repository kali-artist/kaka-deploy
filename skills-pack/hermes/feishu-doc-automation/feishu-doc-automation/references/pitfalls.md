# 🔴 飞书自动化踩坑总账

> 报错查因永远先看这份。凡是与"通用错误码含义"冲突时，飞书语境为准。

## 错误码速查

| 错误 | 飞书专属含义 | 修复方式 |
|------|------------|---------|
| **`-32602`** | 情况①：**临时 token 失效**（大多数命令报此码） | 先看 `~/.lark/config.json`，仍报错执行 `lark-cli config bind --source hermes --identity bot-only` |
| **`-32602`** | 情况②：`docs +media-insert --selection-with-ellipsis` 匹配 bug（1.0.59~1.0.65 复现，报 "invalid token"，其他命令正常） | **不用 selection 参数**，改「append 到末尾 → `block_move_after` 到目标 heading」方案（见 doc-drive.md） |
| `1770001` | 参数格式错 | CLI 自动处理，不需要手动构造 body |
| **`800010701`** | **`+record-upsert` 载荷不能包 `fields`**（"Record write payload must not be wrapped in fields"） | 直接 `{"字段名":值,...}`，不要外层 `{"fields":{...}}`。⚠️ `+record-batch-create` 反而用 `{"fields":[...],"rows":[...]}`，两种命令载荷格式不同 |
| **命令找不到 `+record-create` / `+record-query`** | 命令名过时（早期文档遗留） | 用 `+record-upsert`（单条写）/ `+record-list`（列出）/ `+record-search`（带过滤查）代替；批量走 `+record-batch-create` |
| **`+table-list` `--base` unknown flag** | 参数名错 | 用 `--base-token`（下同：`+field-*` `+record-*` 都用 `--base-token`） |
| **`1770032`** | **文档级权限不足（forbidden）** | API 应用已认证但无目标文档权限。优先用 `~/.feishu/config.json` 凭证，或在飞书文档中给应用授权 |
| `99991672` | 缺少 API scope 权限 | 开发者后台开通对应 scope |
| `800080207` | 主字段无法删除 | 主字段不能直接删除，将其重命名为需要的字段名即可 |
| `1254063` `MultiSelectFieldConvFail` | 多选字段格式错 | 写入多维表记录时，多选字段值必须传**数组**，不能传逗号分隔字符串 |

## CLI 参数陷阱

| 症状 | 根因 | 修复 |
|---|---|---|
| `lark-cli: command not found` | npm 全局 bin 未加入 PATH | `export PATH=$(npm config get prefix)/bin:$PATH` |
| `unsafe file path` | 传了绝对路径 | **必须用相对路径 `./xxx.png`** |
| `--content: invalid file path` | `--content @` 后传绝对路径 | `--content @` 后**只能**用当前目录下的 `./xxx.md`，先把文件复制到当前目录 |
| 创建 Markdown 文档内容错乱 | 未指定格式，默认 XML | 必须加 `--doc-format markdown` |
| `--format table 报错` | 该命令不支持 table 输出 | 去掉 `--format table`，用 `json` 或 `markdown` |
| 中文文本匹配失败 | 中文匹配不稳定 | 改用 `--block-id` 精确插入 |
| 字段删除报确认错 | 高危操作要求 | 删字段必须加 `--yes` |
| `unknown subcommand "permission"` | 一般不用裸子命令 | 加成员用 shortcut `+member-add`；查/删成员 CLI shortcut 未包装，用原生 `drive permission.members` 子命令或 `lark-openapi-explorer`；公共链接用 `drive permission.public get/patch` |
| `unknown flag "--public"` | `docs +create` 没有 public 参数 | 创建后调 `+member-add` 单独授权 |
| `unknown flag "--token"` on `drive +delete` | 参数名错 | `drive +delete` 用 `--file-token`，还需 `--type docx` 和 `--yes` |
| 添加多维表成员失败 | 类型参数错 | `--type bitable`，`--member-type openid`（不带下划线） |
| `--jq` 输出被 Warning 污染 | bot 身份创建资源时 `permission_grant` 提示写到了 stdout | 用 `--jq` 提取 ID 时**必须**加 `2>/dev/null` 屏蔽 stderr，或改用 `--json` 拿完整 JSON 后自行解析 |
| **`drive +import` 返回 `"token": "***"` 被掩码** | lark-cli 对敏感字段脱敏 | **不要从 `token` 字段提取**；改从 `"url"` 字段提取 doc_id：`grep -oE '"url"\s*:\s*"https://[^"]+/docx/([A-Za-z0-9]+)"' \| grep -oE '/docx/[A-Za-z0-9]+' \| tr -d '/docx/'`。⚠️ `--output json --quiet` 会**连同 JSON 一起屏蔽**，不能用于脚本提取 |
| link 类型字段创建失败 | 缺 link_table 参数 | link 类型必须指定 `link_table`；仅存链接文本用 `text` 类型 |
| 归档遗漏 | 流程遗漏 | 所有新建的飞书文档必须自动归档到主人多维表，调 `feishu-doc-auto-archiving` 技能 |
| **`base +record-search` 报缺参数** | `--keyword` 和 `--search-field` 必须同时提供 | `--keyword "关键词" --search-field "标题"`；`--json` 模式则需要 `{keyword, search_fields: [...]}` |
| **重新发布后找不到旧文档/重复文档** | import 会创建新文档，旧文档需手动搜索清理 | `lark-cli drive +search --query "关键词" --as user --format json` 搜索全部版本，从 URL 提取 token，bot 身份 `drive +delete` 逐个删除 |

## 🔴 图片插入的两种方案（重点）

### ❌ 不推荐：`--selection-with-ellipsis`

```bash
# lark-cli 1.0.59~1.0.65 会报 -32602 "invalid token"，rebind 修不好
lark-cli docs +media-insert --doc $DOC --file ./x.png --selection-with-ellipsis "标题文字"
```

### ✅ 稳妥方案：append → block_move_after

```bash
# 1. 拿目标 heading 的 block_id
lark-cli docs +fetch --doc $DOC --scope outline --detail with-ids | jq -r '.data.document.content'
TARGET_BLK=doxcnXXX

# 2. 图片先追加到文档末尾，返回 block_id
IMG_BLK=$(lark-cli docs +media-insert --doc $DOC --file ./image.png \
  --caption "图 1.1 xxx" --align center --width 600 \
  | grep -oE '"block_id":\s*"[^"]+"' | head -1 | grep -oE '"[^"]+"$' | tr -d '"')

# 3. 移动到目标 heading 之后
lark-cli docs +update --doc $DOC --command block_move_after \
  --block-id "$TARGET_BLK" --src-block-ids "$IMG_BLK"
```

## 🔴 pandoc md→docx YAML 前置块误判

**症状**：`pandoc x.md -o x.docx` 报 `YAML parse exception ... did not find expected comment or line break`。

**根因**：md 开头紧跟 `>` blockquote（尤其含 emoji/冒号）时，pandoc 默认按 CommonMark 会尝试把开头当 YAML front matter 解析。

**修复**：明确指定 GFM 输入格式，禁用 YAML 前置块。

```bash
# ❌ 会失败
pandoc input.md -o output.docx

# ✅ 稳妥（GitHub Flavored Markdown 不解析 YAML 头）
pandoc -f gfm+tex_math_dollars -t docx input.md -o output.docx \
  --resource-path="$(dirname input.md):$(dirname input.md)/images"
```

**顺带**：`--resource-path` 支持冒号分隔多个目录，让 pandoc 找到本地图片；md 里用 `![](/abs/path/xxx.png)` 或相对路径都能被内嵌进 docx。

## 🔴 SVG 转 PNG 中文/emoji 乱码

**症状**：SVG 里的中文/emoji 转 PNG 后变豆腐块。

**根因**：系统缺中文/emoji 字体 + SVG 未指定 fallback。

**修复**：

```bash
# 1. 装字体
apt-get install -y fonts-noto-cjk fonts-noto-color-emoji librsvg2-bin
fc-cache -f

# 2. SVG 里的 font-family 必须加 fallback
# 改前：font-family="sans-serif"
# 改后：font-family="'Noto Serif CJK SC','Noto Color Emoji',sans-serif"

# 3. 用 rsvg-convert（不是 imagemagick）
rsvg-convert -w 1200 input.svg -o output.png
```

## 🔴 飞书 Markdown 拼接陷阱

**❌ 绝对禁止**：用 `read_file` 输出去拼 md（会带 `1|` 行号前缀，飞书渲染成代码块）。

**✅ 正确做法**：`terminal cat` 原文件拼；多章合并的长 md 建议用 `+update --command overwrite` 传全量，而非 `+create`。

**改完必校验**：`docs +fetch` 后看正常应有 h1/h2/p/table 混合标签；若几乎全是 `<pre><code>` 说明格式毁了。

## 🔴 str_replace 无法修改链接 href 属性

**症状**：`docs +update --command str_replace --pattern "old_doc_id" --content "new_doc_id"` 返回 `"ok": true`，但文档中的 `<a href="...">` 链接 URL 没变。

**根因**：`str_replace` 在 XML 模式下只匹配**可见内联文本**（标签之间的文字），不匹配 HTML 属性值（`href`、`src` 等）。doc_id 在 `href="...docx/DOC_ID"` 中是属性值，不在可见文本范围。

**修复**：用 `block_replace` 替换包含链接的整个段落 block。

```bash
# 1. fetch section 拿到链接所在 <p> 的 block_id
lark-cli docs +fetch --doc $DOC --scope section --start-block-id $HEADING_ID \
  --detail with-ids --as user --format json
# → 从 XML 中找到 <p id="doxcnXXX"><a href="旧URL">文本</a></p>

# 2. block_replace 替换为新链接
lark-cli docs +update --doc $DOC --command block_replace \
  --block-id "doxcnXXX" \
  --content '<p><a href="https://xxx.feishu.cn/docx/NEW_DOC_ID">链接文本</a></p>' \
  --as bot
```

**典型场景**：重新发布技能专题文档后，需更新一键部署指南等引用文档中的链接。批量替换时遍历所有链接单元格的 block_id 逐个 `block_replace`。

## 🔴 跨租户/完整副本

**❌ 不要**用 `docs +fetch` + `docs +create`：只会复制纯文本，丢失所有图片、视频、富文本格式。

**✅ 正确**：`drive +export` (docx) → `drive +import` → 授权。详见 `doc-drive.md` 流程 H。

## 🔴 本地 Markdown（带图）发布到飞书

**❌ 不要**：`docs +create --content @xxx.md` 直接塞带 `![](./img.png)` 的 md
- 飞书只认 HTTP URL，本地图片路径全部丢失
- `+media-insert --selection-with-ellipsis` 在 lark-cli 1.0.59~1.0.65 报 -32602

**✅ 首选方案（v3）**：混合方案 — markdown 直传 + 三步法插图
- 代码块原生渲染（` ```语言 ` → 飞书 `<pre lang="xxx"><code>`）
- 图片通过 append + `block_move_after` 精确定位到对应标题后

```bash
# 1. 创建空壳 + overwrite 灌入 markdown（代码块标记完整保留）
lark-cli docs +create --title "标题" --doc-format markdown --content "# 标题"
lark-cli docs +update --doc $DOC_ID --command overwrite --doc-format markdown --content @./tutorial.md

# 2. 三步法插图（每张图片）
#    a. media-insert 追加到末尾，拿 block_id
#    b. fetch outline 找目标 heading 的 block_id
#    c. block_move_after 移动到标题后
```

**⚠️ 图片自动定位限制**：`publish_to_feishu.sh` v3 的 `try_hybrid()` 用图片文件名匹配大纲标题——**英文图名（如 `ch01_xxx`）匹配不到中文标题（如 `1.2 什么是内网穿透`）**，图片会全部堆在文档末尾。需手动 fetch outline + 逐张 `block_move_after` 修复。详见 tutorial-generator pitfall #15。

**⚠️ 降级方案**：`pandoc md → docx → drive +import`
- 图片/格式一次性带过去，但 **代码块样式丢失**（飞书不识别 docx 内代码块，渲染为普通段落）
- 仅在混合方案失败时使用

```bash
# ⚠️ 必须用 -f gfm，否则 md 开头的 > 引用会被 pandoc 误当 YAML front matter 头
pandoc -f gfm+tex_math_dollars -t docx ./tutorial.md -o ./out.docx \
  --resource-path="$(pwd):$(pwd)/images"
lark-cli drive +import --file ./out.docx --type docx --name "标题"
```

**参考实现**：`~/.hermes/skills/education/tutorial-generator/scripts/publish_to_feishu.sh`（v3 双方案自动降级，混合方案首选）。

## 归档流程遗漏

**触发**：主人说"新建的文档跑哪去了"或多维表里查不到。

**修复**：调 `feishu-doc-auto-archiving` 技能，把 doc_id 归档到主人的多维表 `{{FEISHU_BASE_TOKEN}}/{{FEISHU_TABLE_ID}}`。

## 路径 & 环境

- `~/.feishu/config.json` 是 CLI 主凭证，`~/.hermes/.env` 是 Hermes 凭证；**优先前者**
- `~/.lark/config.json` 是临时 token 缓存，`-32602` 情况①先看这
- CLI 默认 `--format json` 更利于脚本处理

---

**排障 5 步法**：①先看错误码 → ②对照本文档 → ③检查 `lark-cli auth status` → ④检查参数（相对路径/身份/JSON格式）→ ⑤仍不行才尝试 rebind。
