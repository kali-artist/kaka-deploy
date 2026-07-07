# 🚚 Delivery Playbook - 发布手册

## 通道 1：飞书文档

**核心命令**（详见 `feishu-doc-automation` 技能）：
```bash
# 1. 创建带 Markdown 内容的文档（必须加 --doc-format markdown）
# ⚠️ --content @后的路径必须是相对路径（./xxx.md）
cd $(dirname "$MD_FILE")
CREATE_RESULT=$(lark-cli docs +create \
  --title "$TITLE" \
  --doc-format markdown \
  --content @"./$(basename "$MD_FILE")")
DOC_ID=$(echo "$CREATE_RESULT" | jq -r '.data.document.document_id')

# 2. 逐图插入（每张图用一个锚点文本或 block-id 定位）
for IMG in "$IMG_DIR"/*.png; do
  ANCHOR="$(basename "$IMG" .png)"  # 例：ch02_架构图
  lark-cli docs +media-insert \
    --doc "$DOC_ID" \
    --file "./$(realpath --relative-to=. "$IMG")" \
    --selection-with-ellipsis "$ANCHOR" \
    --align center \
    --width 600
done

# 3. 授权给主人两个 openid
for OPENID in "{{FEISHU_OPEN_ID}}" "{{FEISHU_OPEN_ID}}"; do
  lark-cli drive +member-add \
    --type docx --token "$DOC_ID" \
    --member-type openid --member-id "$OPENID" \
    --perm full_access --yes
done

# 4. 归档（调 feishu-doc-auto-archiving）
# 5. 输出链接
echo "https://{{FEISHU_DOMAIN}}.feishu.cn/docx/$DOC_ID"
```

**图片锚点约定**：markdown 里图片用**唯一可搜索的中文标注**做锚点，例如：
```markdown
![架构图](ch02_架构图.png)

<!-- 上面这行 markdown 会渲染成图，但插入图片时用 "ch02_架构图" 做 selection-with-ellipsis 定位 -->
```

**排障**：
- `1770032` → 应用无文档权限，检查 `~/.feishu/config.json`
- `-32602` → token 失效 → `lark-cli config bind --source hermes --identity bot-only`
- `unsafe file path` → 必须用相对路径 `./xxx.png`
- 图匹配失败 → 用 `--block-id` 精确定位

---

## 通道 2：本地 Markdown

**存储约定**：
- 主目录：`~/tutorials/<日期>_<标题拼音短名>/`
- 结构：
  ```
  ~/tutorials/2026-07-06_docker-intro/
  ├── README.md            # 教程正文
  ├── meta.json            # 元数据（模板/受众/生成时间）
  └── images/              # 所有图片
      ├── ch01_flow.png
      └── ch02_arch.png
  ```
- markdown 内图片引用一律 `./images/chXX_xxx.png`

**meta.json 字段**：
```json
{
  "title": "Docker 入门教程",
  "template": "T2 tool-usage",
  "audience": "初学者",
  "depth": "入门",
  "chapters": 5,
  "created_at": "2026-07-06T15:30:00+08:00",
  "images_count": 6
}
```

---

## 两通道都发时

顺序：**先本地存档 → 再发飞书**
- 本地是"母版"，飞书是"分发"
- 若飞书失败，本地版可再次尝试或让主人手动上传
