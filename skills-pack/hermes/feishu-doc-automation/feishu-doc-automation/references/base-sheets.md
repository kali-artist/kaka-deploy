# Base / Sheets 多维表格与电子表格

> 遇到报错先看 [pitfalls.md](pitfalls.md)。多维表命令 50+，覆盖字段/记录/视图/仪表盘/工作流/角色权限/表单/附件全域。

## Base 核心 shortcut

| 分类 | Shortcut | 用途 |
|---|---|---|
| **建表** | `+base-create` | 建多维表本体 |
| | `+base-copy` | 复制多维表 |
| | `+table-list` `+table-create` `+table-delete` | 数据表管理 |
| **字段** | `+field-list` `+field-create` `+field-update` `+field-delete` | 字段 CRUD |
| **记录** | `+record-list` `+record-search` `+record-get` `+record-upsert` `+record-batch-create` `+record-batch-update` `+record-delete` | 记录 CRUD（⚠️ 没有 `+record-create` / `+record-query`，用 upsert / search 代替） |
| **视图** | `+view-list` `+view-create` `+view-update` `+view-delete` | 视图管理 |
| **仪表盘** | `+dashboard-list` `+dashboard-create` `+dashboard-copy` | 仪表盘 |
| **表单** | `+form-list` `+form-update` | 表单配置 |
| **角色** | `+role-list` `+role-create` `+role-update` `+role-delete` | 高级权限 |
| **附件** | `+attachment-upload` `+attachment-download` | 附件 |
| **工作流** | `+workflow-list` `+workflow-run` | 自动化 |

**核心原则**：**复杂参数统一用 `--json`**，不要用一堆 flag 拼。

---

## 流程 A：建多维表 + 配字段 + 建视图

```bash
# 1. 建多维表
BASE_TOKEN=$(lark-cli base +base-create --name "知识库" \
  | jq -r '.data.base.base_token')

# 2. 拿默认数据表 ID
TABLE_ID=$(lark-cli base +table-list --base-token $BASE_TOKEN \
  | jq -r '.data.tables[0].id')

# 3. 单选字段
lark-cli base +field-create --base-token $BASE_TOKEN --table-id $TABLE_ID \
  --json '{"name":"知识类型","type":"select","options":[
    {"name":"技能文档"},{"name":"脚本工具"},{"name":"技术调研"},
    {"name":"实践记录"},{"name":"踩坑总结"}
  ]}'

# 4. 多选字段（注意 multiple:true）
lark-cli base +field-create --base-token $BASE_TOKEN --table-id $TABLE_ID \
  --json '{"name":"标签","type":"select","multiple":true,"options":[
    {"name":"大模型"},{"name":"Python"},{"name":"飞书自动化"}
  ]}'

# 5. 建视图
lark-cli base +view-create --base-token $BASE_TOKEN --table-id $TABLE_ID \
  --json '{"name":"📥 收件箱","type":"grid"}'

lark-cli base +view-create --base-token $BASE_TOKEN --table-id $TABLE_ID \
  --json '{"name":"⏰ 看板","type":"kanban"}'

# ⚠️ API 不支持 calendar 视图（会报 99992402），改用 gallery
lark-cli base +view-create --base-token $BASE_TOKEN --table-id $TABLE_ID \
  --json '{"name":"📅 时间线","type":"gallery"}'

# 6. 建仪表盘（组件需在 UI 手动加，API 未开放）
lark-cli base +dashboard-create --base-token $BASE_TOKEN \
  --name "📊 统计仪表盘"

# 7. 授权
for OPENID in "{{FEISHU_OPEN_ID}}" "{{FEISHU_OPEN_ID}}"; do
  lark-cli drive +member-add --type bitable --token $BASE_TOKEN \
    --member-type openid --member-id $OPENID --perm full_access --yes
done

echo "https://{{FEISHU_DOMAIN}}.feishu.cn/base/$BASE_TOKEN"
```

## 字段类型速查

| type | 说明 | 关键参数 |
|---|---|---|
| `text` | 文本 | — |
| `number` | 数字 | `formatter` |
| `select` | 单/多选 | `options`；**多选必须** `multiple:true`（同一个 type=select） |
| `date` | 日期 | `date_formatter` `auto_fill` |
| `checkbox` | 复选框 | — |
| `user` | 人员 | `multiple` |
| `phone` | 电话 | — |
| `url` | 网址 | — |
| `attachment` | 附件 | — |
| `link` | 单向关联 | **必须** `link_table`；仅存文本改 `text` |
| `lookup` | 查找引用 | `link_field` `lookup_field` |
| `formula` | 公式 | `formula` |
| `auto_number` | 自动编号 | — |
| `created_time` / `modified_time` | 系统时间 | — |
| `created_user` / `modified_user` | 系统人员 | — |

---

## 流程 B：写记录（upsert / batch-create）

### 单条 upsert（⚠️ 载荷不能包 `fields`）

```bash
# ❌ 错：会报 800010701 "Record write payload must not be wrapped in `fields`"
# lark-cli base +record-upsert --base-token $BASE --table-id $TBL \
#   --json '{"fields":{"姓名":"张三","标签":["A","B"]}}'

# ✅ 对：直接给 field->value map，不要 fields 包裹
lark-cli base +record-upsert --base-token $BASE --table-id $TBL \
  --json '{"姓名":"张三","状态":"进行中","标签":["大模型","Python"]}'
```

### 批量 batch-create（fields + rows 结构）

```bash
lark-cli base +record-batch-create --base-token $BASE --table-id $TBL \
  --json '{
    "fields":["姓名","金额","标签"],
    "rows":[
      ["张三", 999, ["大模型"]],
      ["李四", 888, ["Python","飞书自动化"]]
    ]
  }'
```

**⚠️ 陷阱**：
- 多选字段值**必须传数组**（`["A","B"]`）。传字符串 `"A,B"` 在 `+record-upsert` 会被当成一个新选项自动创建（污染选项集），在 `+record-batch-create` 也可能默默通过——所以务必手动数组化。
- 人员字段传 `{"id":"ou_xxx"}` 结构，不是纯字符串
- 日期字段传 unix 毫秒时间戳（数字）
- 🔴 **`+record-upsert` 的 `--json` 载荷不能包 `fields`**，直接给 `{"字段名":值,...}`，否则报 `800010701 "Record write payload must not be wrapped in fields"`
- `+record-batch-create` 反过来使用 `{"fields":[...],"rows":[...]}` 结构（两种命令载荷格式不同）

## 流程 C：查询记录（含筛选）

⚠️ **命令名是 `+record-list` 和 `+record-search`**，没有 `+record-query`。

```bash
# 全量列出
lark-cli base +record-list --base-token $BASE --table-id $TBL

# 按视图列出
lark-cli base +record-list --base-token $BASE --table-id $TBL --view-id vew_xxx

# 带筛选（用 +record-search，filter 使用 FQL）
lark-cli base +record-search --base-token $BASE --table-id $TBL \
  --json '{"filter":{
    "conjunction":"and",
    "conditions":[{"field_name":"状态","operator":"is","value":["进行中"]}]
  }}'

# 只返回指定字段
lark-cli base +record-list --base-token $BASE --table-id $TBL \
  --field-names 姓名,状态,金额
```

## 流程 D：字段与记录的更新/删除

```bash
# 更新字段（改名/改选项）
lark-cli base +field-update --base-token $BASE --table-id $TBL \
  --field-id fld_xxx --json '{"name":"新名字"}'

# 删除字段（必须 --yes）
lark-cli base +field-delete --base-token $BASE --table-id $TBL \
  --field-id fld_xxx --yes

# 主字段不能删除，只能改名（否则 800080207）
lark-cli base +field-update --base-token $BASE --table-id $TBL \
  --field-id <主字段id> --json '{"name":"新主字段名"}'

# 批量更新记录
lark-cli base +record-batch-update --base-token $BASE --table-id $TBL \
  --json '{"records":[
    {"record_id":"rec_xxx","fields":{"状态":"完成"}}
  ]}'

# 删除记录（--record-ids 逗号分隔 + --yes）
lark-cli base +record-delete --base-token $BASE --table-id $TBL \
  --record-ids rec_a,rec_b,rec_c --yes
```

---

## Sheets 电子表格

| Shortcut | 用途 |
|---|---|
| `+read` | 读单元格/范围 |
| `+write` | 写单元格 |
| `+append` | 追加行 |
| `+search` `+replace` | 搜索替换 |
| `+merge` `+unmerge` | 合并/拆分 |
| `+sheet-add` `+sheet-delete` | 工作表管理 |
| `+row-insert` `+col-insert` | 行列增删 |

### 常用示例

```bash
# 读一段范围（A1 记法）
lark-cli sheets +read --sheet-token <token> --range "Sheet1!A1:C10"

# 写单元格
lark-cli sheets +write --sheet-token <token> --range "Sheet1!A1" \
  --values '[["姓名","金额"],["张三",999]]'

# 追加行
lark-cli sheets +append --sheet-token <token> --range "Sheet1!A1:C1" \
  --values '[["李四",888,"完成"]]'
```

---

## 流程 E：知识库标准化搭建（10 分钟从 0 到 1）

参考完整清单：6 大分类 × 23 项元数据 × 3 仪表盘 × 8 自动化 × 8 视图 × 多表关联，见 `feishu-knowledge-base-manager` 技能。核心步骤：

1. 建 base + 拿 table_id
2. 批量配字段（跑 for 循环调 `+field-create`）
3. 建视图（grid/kanban/gallery，避开 calendar）
4. 建仪表盘（本体建好即可，组件手动加）
5. 批量授权给主人 2 个 open_id
6. 输出链接 → 交付

## 流程 F：多维表复制/迁移

```bash
# 整个多维表复制（含所有 table）
lark-cli base +base-copy --base-token <源> --name "副本" --folder-token <目标文件夹>

# ⚠️ CLI 不支持 +table-copy（单表跨 base 复制）
# 变通方案：
#   1. +base-copy 整库复制后，删除不需要的 table
#   2. 或用 +record-search 从源表拉数据，+record-batch-create 写入目标表（结构需先手动对齐）
```

## 关键排障

| 症状 | 原因 | 修复 |
|---|---|---|
| `unknown subcommand "+record-create"` / `"+record-query"` | 命令名过时 | 用 `+record-upsert` / `+record-list` / `+record-search` |
| 报错 `800010701 payload must not be wrapped in fields` | `+record-upsert` 载荷格式错 | 去掉外层 `{"fields":...}`，直接 `{"字段":值}` |
| 主字段删除失败 (`800080207`) | 主字段不能删 | 改名即可 |
| 多选字段值异常 | 传了字符串被当作单选项 | 改成数组 `["A","B"]` |
| link 字段创建失败 (`Required. link_table`) | 缺 `link_table` | 加上或改 `text` |
| calendar 视图创建失败 (`99992402`) | API 不支持 | 改 `gallery` |
| `+member-add` 失败 | 类型参数错 | `--type bitable`，`--member-type openid` |
| 字段删除报确认错 | 高危操作 | 加 `--yes` |
