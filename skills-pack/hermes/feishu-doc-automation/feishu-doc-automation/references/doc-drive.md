# Doc / Drive 文档与云空间

> 遇到报错先看 [pitfalls.md](pitfalls.md)。

## Shortcut 清单

### Drive（云盘）

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+search` | 搜索文件（doc/wiki/sheet/base） | `--query` `--creator-ids` `--doc-types` `--space-ids` |
| `+inspect` | 解析 URL 类型 | `--url` |
| `+download` | 下载文件 | `--file-token` |
| `+upload` | 上传文件到文件夹 | `--file` `--folder-token` |
| `+export` | 导出为本地 docx/xlsx | `--token` `--doc-type` `--file-extension` `--output-dir` |
| `+import` | 从本地文件导入为云文档 | `--file` `--type` `--name` |
| `+member-add` | 添加协作者 | `--type` `--token` `--member-type` `--member-id` `--perm` |
| `+apply-permission` | 向文档所有者申请权限 | `--token` `--perm view\|edit` `--remark` |
| （原生）`drive permission.members create/auth/transfer_owner` | 权限成员/所有者操作 | 需查子命令 |

> ⚠️ CLI **不支持**：`+member-delete` / `+member-list`（查/删协作者 shortcut 未包装）。需要时用 `drive permission.members` 原生子命令，或走 `lark-openapi-explorer`。
| `+delete` | 删除文件 | `--file-token` `--type docx` `--yes` |
| `+comments` | 查看/管理评论 | `--file-token` |

### Doc（云文档）

| Shortcut | 用途 | 关键 flag |
|---|---|---|
| `+fetch` | 获取文档内容 | `--doc` `--scope`(outline\|range\|keyword) `--detail`(simple\|with-ids) |
| `+create` | 创建文档 | `--title` `--content` `--doc-format markdown` `--folder-token` |
| `+update` | 更新文档 | `--doc` `--command`(append\|overwrite\|str_replace\|block_insert_after\|block_move_after\|...) |
| `+media-insert` | 插入图片/视频/文件 | `--doc` `--file` `--type`(image\|file) `--file-view`(card\|preview\|inline) `--caption` `--align` `--width` |
| `+word-stat` | 字数统计 | `--doc` |

## URL 类型识别

wiki URL 类型未明示时（`feishu.cn/wiki/<token>`），必须先解析：

```bash
lark-cli drive +inspect --url 'https://xxx.feishu.cn/wiki/xxx' --format json
```

返回 `type` + `token` 后路由：
- `docx` → `docs +fetch`
- `sheet` → `sheets +read`
- `bitable` → `base +...`
- `file` → `drive +download`

## 搜索技巧

```bash
# 关键词
lark-cli drive +search --query "关键词" --format json

# 按创建者
lark-cli drive +search --creator-ids ou_xxx --format json

# 限定知识库
lark-cli drive +search --query "关键词" --space-ids <space_id> --format json

# 按类型过滤
lark-cli drive +search --query "关键词" --doc-types docx --format json
```

---

## 流程 A：创建新文档（推荐一步到位）

```bash
# 1. 一步创建（--content @ 只支持相对路径 ./）
CREATE_RESULT=$(lark-cli docs +create --title "标题" \
  --doc-format markdown --content @./local_file.md)
DOC_ID=$(echo $CREATE_RESULT | jq -r '.data.document.document_id')

# 2. 批量给主人授权
for OPENID in "{{FEISHU_OPEN_ID}}" "{{FEISHU_OPEN_ID}}"; do
  lark-cli drive +member-add --type docx --token $DOC_ID \
    --member-type openid --member-id $OPENID --perm full_access --yes
done

# 3. 返回链接
echo "https://{{FEISHU_DOMAIN}}.feishu.cn/docx/$DOC_ID"

# 4. 归档到主人多维表（调 feishu-doc-auto-archiving 技能）
```

**⚠️ 陷阱**：
- 不加 `--doc-format markdown` 默认走 XML，会导致 Markdown 内容错乱
- 拼接 md 别用 `read_file`（带 `1|` 行号），用 `terminal cat`
- 长 md 建议先落盘再 `+create --content @` 传入

## 流程 B：更新文档（8 种精确 command）

```bash
# 追加
lark-cli docs +update --doc $DOC --command append --content '追加内容'

# 全量覆盖（长 md 优先用这个）
lark-cli docs +update --doc $DOC --command overwrite --doc-format markdown --content @./new.md

# 字符串替换
lark-cli docs +update --doc $DOC --command str_replace --pattern '旧' --content '新'

# 块级操作
lark-cli docs +update --doc $DOC --command block_insert_after --block-id blk_xxx --content '内容'
lark-cli docs +update --doc $DOC --command block_move_after --block-id <target> --src-block-ids <src>
lark-cli docs +update --doc $DOC --command block_delete --block-ids <blk1>,<blk2>

# 块级替换（替换整个 block 内容，不改 block_id）
lark-cli docs +update --doc $DOC --command block_replace --block-id blk_xxx --content '<pre lang="YAML"><code>新内容</code></pre>'
# 支持替换代码块、表格、段落等任意 block 类型
# 表格替换示例：
lark-cli docs +update --doc $DOC --command block_replace --block-id tbl_xxx \
  --content '<table><tbody><tr><td><p>列1</p></td><td><p>列2</p></td></tr></tbody></table>'
```

**校验**：改完 `docs +fetch` 看结构，正常应有 h1/h2/p/table 混合；若几乎全是 `<pre><code>` 说明格式毁了。

## 🔴 流程 B2：批量定向更新（本地文件变更后同步飞书文档）

**触发**：本地配置/架构文件变更后，需将飞书上记录这些文件的文档同步更新（如 MEMORY.md 精简后同步到架构指南文档）。

### 步骤

```bash
DOC="<doc_id>"

# 1. 用 keyword scope 定位需更新的段落（带 block_id）
lark-cli docs +fetch --doc $DOC --as user --detail with-ids \
  --scope keyword --keyword "要找的内容" --format json

# 2. 批量 str_replace（简单文本替换，可一行多个）
lark-cli docs +update --doc $DOC --command str_replace --as user \
  --pattern "旧文本" --content "新文本"

# 3. block_replace（整个代码块/表格替换）
lark-cli docs +update --doc $DOC --command block_replace --as user \
  --block-id "doxcnXXX" --content '<pre lang="Markdown"><code>新内容</code></pre>'

# 4. 验证：用 text 格式搜索确认旧内容已清除、新内容已存在
lark-cli docs +fetch --doc $DOC --as user --format text | python3 -c "
import sys
text = sys.stdin.read()
checks = [
    ('旧文本', '应删除', False),
    ('新文本', '应存在', True),
]
for pattern, note, should_exist in checks:
    count = text.count(pattern)
    status = '✅' if (count > 0) == should_exist else '❌'
    print(f'  {status} \"{pattern}\" x{count} ({note})')
"
```

### 要点
- **str_replace** 适合简单文本替换（改几个词），**block_replace** 适合整个块替换（代码块、表格、段落）
- 批量 str_replace 可在单个 terminal 调用中串联多个（用 `&&` 或换行），减少往返
- `--format text` 比 `--format json` 更适合验证搜索（纯文本无 HTML 标签干扰）
- block_id 通过 `--detail with-ids` 获取，格式为 `doxcn` 前缀
- ⚠️ `block_replace` 的 `--content` 中换行用真实换行符 `\n`，不要用 `<br/>`（str_replace 则可以用）

## 🔴 流程 C：图片插入（稳妥方案）

```bash
# 1. 拿目标 heading 的 block_id
lark-cli docs +fetch --doc $DOC --scope outline --detail with-ids | jq -r '.data.document.content'
TARGET_BLK=doxcnXXX

# 2. 图片先追加末尾，返回 block_id
IMG_BLK=$(lark-cli docs +media-insert --doc $DOC --file ./image.png \
  --caption "图 1.1 xxx" --align center --width 600 \
  | grep -oE '"block_id":\s*"[^"]+"' | head -1 | grep -oE '"[^"]+"$' | tr -d '"')

# 3. 移动到目标 heading 之后
lark-cli docs +update --doc $DOC --command block_move_after \
  --block-id "$TARGET_BLK" --src-block-ids "$IMG_BLK"
```

**❌ 禁用**：`--selection-with-ellipsis "匹配文本"` 在 1.0.59~1.0.65 会报 -32602，rebind 无效。

**批量插图脚本模板**：见现有 `/tmp/insert_images_v2.sh`，循环 `insert_one` 调三步。

### 流程 C-alt：block_insert_after 直插图片（图片已在 Drive 时首选）

**适用**：图片已上传 Drive（有 file_token），或需批量插入多张图到不同位置（比三步法少一半 lark-cli 调用）。实测 7 张图全部可靠插入。

```bash
# 1. 图片已上传 Drive（drive +upload），拿到 file_token
IMG_TOKEN="boxcnXXXXX"

# 2. 拿目标 heading 的 block_id（同流程 C 步骤 1）
TARGET_BLK=doxcnXXX

# 3. 直接在 heading 后插入图片（无需先追加再移动）
lark-cli docs +update --doc $DOC --command block_insert_after \
  --block-id "$TARGET_BLK" --content "<img src=\"$IMG_TOKEN\"/>"
```

**vs 三步法**：三步法（media-insert → block_move_after）每张图 2 次 lark-cli 调用；此方案已有 token 时仅 1 次。但需先 `drive +upload` 上传图片获取 token。

**⚠️ 同三步法限制**：`--content @file` 传文件时必须用相对路径 `./xxx`（绝对路径报 `unsafe file path`）。

## 🔴 流程 C2：文件卡片插入（embed 附件文件到文档）

`+media-insert --type=file` 可将任意文件（tar.gz/zip/pdf 等）作为**可下载文件卡片**嵌入文档，而非仅放一个文本链接。

```bash
# 1. 先追加文件到文档末尾，返回 block_id
cd /tmp  # 先 cd 到文件所在目录
FILE_BLK=$(lark-cli docs +media-insert --doc $DOC \
  --file ./package.tar.gz \
  --type file \
  --file-view card \
  --caption "package.tar.gz (约15MB)" \
  | grep -oE '"block_id":\s*"[^"]+"' | head -1 | grep -oE '"[^"]+"$' | tr -d '"')

# 2. 拿目标 heading 的 block_id
TARGET_BLK=$(lark-cli docs +fetch --doc $DOC --scope outline --detail with-ids \
  | grep -oE '"block_id":\s*"doxcn[^"]+"' | head -1 | ...)

# 3. 移动到目标 heading 之后（同图片流程）
lark-cli docs +update --doc $DOC --command block_move_after \
  --block-id "$TARGET_BLK" --src-block-ids "$FILE_BLK"
```

**关键参数**：
- `--type file`：指定插入文件（默认 image）
- `--file-view card|preview|inline`：渲染方式（card=文件卡片最常用，preview=音视频内联播放器，inline=行内）
- `--caption`：文件说明文字
- `--file`：本地文件路径（必须相对路径，先 cd 到文件目录）

**⚠️ 同图片流程**：`--selection-with-ellipsis` 同样会报 -32602，必须用「追加末尾 + block_move_after」方案。

**⚠️ Drive 上传限制**：`drive +upload` 单文件限制 20MB（错误码 1061043 quota_exceeded）。大文件需先瘦身（去 node_modules/.git）+ `gzip -9` 压缩。

## 🔴 流程 D-本地：本地含图 markdown 完整发布（v3 首选路径）

**触发**：主人有本地 md + 图片目录，要发到飞书；`docs +create --content @xx.md` 不会自动上传本地图片。

**✅ 方案①（首选）混合方案**：markdown 直传 + 三步法插图
- 代码块原生渲染：` ```bash ` → 飞书 `<pre lang="bash"><code>`（pandoc→docx 路径会丢失此样式）
- 图片通过 append + `block_move_after` 精确定位

```bash
# 1. 创建空壳文档
lark-cli docs +create --title "$TITLE" --doc-format markdown --content "# $TITLE"
# 提取 DOC_ID ...

# 2. overwrite 灌入 markdown 正文（代码块标记完整保留）
lark-cli docs +update --doc $DOC_ID --command overwrite --doc-format markdown --content @./input.md

# 3. 三步法插图（每张图片循环）
#    a. lark-cli docs +media-insert --doc $DOC_ID --file ./img.png → 返回 IMG_BLK
#    b. lark-cli docs +fetch --doc $DOC_ID --scope outline --detail with-ids → 找 TARGET_BLK
#    c. lark-cli docs +update --doc $DOC_ID --command block_move_after --block-id $TARGET_BLK --src-block-ids $IMG_BLK
```

**⚠️ 方案②（降级兜底）pandoc → docx → import**：
- 图片/格式一次性带过去，但**代码块样式丢失**（飞书不识别 docx 内代码块，渲染为普通段落）
- 仅在方案①失败时使用

```bash
# -f gfm 关键：避免 md 开头的 > blockquote 被误当 YAML 头（见 pitfalls）
cd "$(dirname input.md)"
pandoc -f gfm+tex_math_dollars -t docx ./input.md -o ./output.docx \
  --resource-path=".:./images"

# token 字段被掩码为 "***"，必须从 url 字段提取 doc_id
IMPORT_JSON=$(lark-cli drive +import --file ./output.docx --type docx --name "$TITLE")
DOC_ID=$(echo "$IMPORT_JSON" | grep -oE '"url"\s*:\s*"https://[^"]+/docx/[A-Za-z0-9]+"' | grep -oE '/docx/[A-Za-z0-9]+$' | sed 's#/docx/##')

# 授权 + 归档（同流程 A）
```

**验证**：`docs +fetch` 看内容结构——混合方案应有 `<pre lang="xxx"><code>` 代码块；若全是普通 `<p>` 段落说明走了降级路径。参考脚本：`~/.hermes/skills/education/tutorial-generator/scripts/publish_to_feishu.sh`（v3 双方案自动降级）。

## 🔴 流程 D：跨租户/完整副本（保留全部图片和格式）

### D1. 从飞书文档到飞书文档

```bash
# 步骤1：导出为 docx
lark-cli drive +export --token <源文档ID> --doc-type docx \
  --file-extension docx --output-dir . --overwrite

# 若导出成功但路径报错，用 file_token 补救：
lark-cli drive +export-download --file-token "<file_token>" \
  --file-name "output.docx" --output-dir . --overwrite

# 步骤2：导入为新云文档（自动保留图片/视频/格式）
cd /tmp   # 必须先 cd 到 docx 所在目录
lark-cli drive +import --file ./output.docx --type docx --name "文档标题"

# 步骤3：授权（导入的文档默认只有 bot 权限）
# ⚠️ token 字段被掩码为 "***"，从 url 字段提取 doc_id
NEW_DOC_ID=$(lark-cli drive +import --file ./output.docx --type docx --name "文档标题" \
  | grep -oE '"url"\s*:\s*"https://[^"]+/docx/[A-Za-z0-9]+"' \
  | grep -oE '/docx/[A-Za-z0-9]+$' | sed 's#/docx/##')
for OPENID in "{{FEISHU_OPEN_ID}}" "{{FEISHU_OPEN_ID}}"; do
  lark-cli drive +member-add --type docx --token $NEW_DOC_ID \
    --member-type openid --member-id $OPENID --perm full_access --yes
done

# 步骤4：归档到主人多维表（调 feishu-doc-auto-archiving 技能，先做去重）
```

### D2. 从本地 Markdown（带图）到飞书文档 —— 降级方案（pandoc）

> ⚠️ v3 起此路径降为**降级兜底**。含代码块的文档应优先用**流程 D-本地 混合方案**（markdown 直传）。
> pandoc→docx→import 路径飞书不识别 docx 内代码块样式，代码会渲染为普通段落。

```bash
# 步骤1：pandoc 转 docx，图片会真的嵌入
# ⚠️ 必须 -f gfm，否则文档头的 > blockquote 会被误当 YAML front matter
pandoc -f gfm+tex_math_dollars -t docx ./tutorial.md -o ./out.docx \
  --resource-path="$(pwd):$(pwd)/images"

# 验证图片嵌入：
unzip -l out.docx | grep -E '\.(png|jpg)$'

# 步骤2：导入
lark-cli drive +import --file ./out.docx --type docx --name "标题"

# 步骤3-4：同 D1（授权 + 归档）
```

**注意**：
- `--output-dir` 必须相对路径
- docx 较大时导入 10~30 秒
- 飞书内部流媒体视频链接导入后可能失效（需手动重传）
- **不要用** `docs +fetch` + `docs +create` 走一遍——会丢图片和格式

## 流程 E：读取文档（按范围/大纲/关键词）

```bash
# 简单读取
lark-cli docs +fetch --doc $DOC

# 只要大纲（推荐用于定位 block_id）
lark-cli docs +fetch --doc $DOC --scope outline --detail with-ids

# 按关键词范围读取
lark-cli docs +fetch --doc $DOC --scope keyword --keyword "第二章"

# 按 block 范围
lark-cli docs +fetch --doc $DOC --scope range --start-block-id blk_a --end-block-id blk_b
```

## 流程 F：文件上传下载

```bash
# 上传到指定文件夹
lark-cli drive +upload --file ./local.pdf --folder-token <folder_token>

# 下载（先 search 拿 file_token）
lark-cli drive +download --file-token <file_token> --output-dir .
```

## 权限管理

```bash
# 添加成员
lark-cli drive +member-add --type <docx|bitable|sheet> --token <token> \
  --member-type openid --member-id ou_xxx --perm <view|edit|full_access> --yes

# 移除/查询成员：CLI shortcut 未包装
# 用原生子命令或 lark-openapi-explorer 技能

# 申请权限（bot 没权限访问某文档时，用 user 身份申请）
lark-cli drive +apply-permission --as user \
  --token <doc_token> --perm edit --remark "需要编辑权限"
```

**⚠️ 陷阱**：
- 没有 `+permission` 子命令；成员查/删 shortcut 未包装
- `+create` 时**不支持** `--public` 参数，创建后单独授权

## 7 点质量验证（新建文档后）

```bash
# 1. 有内容
lark-cli docs +fetch --doc $DOC --detail simple | jq -r '.data.document.content' | wc -c

# 2. 有标题（h1/h2）
lark-cli docs +fetch --doc $DOC --scope outline | grep -E '<h[12]'

# 3-4. 富文本 ≥ 3 种，段落 ≤ 60%（人工核对）

# 5. 权限已授（CLI 无 +member-list shortcut，用 apply-permission 或原生子命令验证）
# 或者：以主人 --as user 身份 +fetch，能读到即已授

# 6. 链接可访问
echo "https://{{FEISHU_DOMAIN}}.feishu.cn/docx/$DOC"

# 7. 归档标记（查主人多维表是否已登记）
```
