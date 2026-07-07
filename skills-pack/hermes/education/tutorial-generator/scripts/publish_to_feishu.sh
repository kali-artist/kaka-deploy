#!/usr/bin/env bash
# publish_to_feishu.sh - 教程一键发布到飞书文档
# 用法: bash publish_to_feishu.sh <markdown_file> <images_dir_or_empty> "标题"
#
# 双方案策略（v3）：
#   方案①（首选）: 混合方案 — markdown 直传（代码块原生渲染）+ 三步法插图（block_move_after 精确定位）
#   方案②（降级）: pandoc md→docx → drive +import — 图片/格式一次性带过去，但代码块样式丢失
#
# v3 变更理由：pandoc→docx→import 路径飞书不识别 docx 代码块样式，渲染为普通段落；
#             混合方案 markdown 直传保留 ```语言 标记，飞书渲染为原生 <pre lang><code> 代码块。
#
# 依赖: lark-cli, jq（方案②额外需要 pandoc）
# 前置: 主人两个 openid 已在下方常量固化

set -uo pipefail

MD_FILE="${1:?缺少参数: markdown 文件路径}"
IMG_DIR="${2:-}"
TITLE="${3:?缺少参数: 教程标题}"

OWNER_OPENIDS=(
  "{{FEISHU_OPEN_ID}}"
  "{{FEISHU_OPEN_ID}}"
)

need() { command -v "$1" >/dev/null 2>&1 || { echo "❌ 缺少命令: $1" >&2; exit 1; }; }
need lark-cli; need jq

[ -f "$MD_FILE" ] || { echo "❌ markdown 文件不存在: $MD_FILE" >&2; exit 1; }

MD_DIR="$(cd "$(dirname "$MD_FILE")" && pwd)"
MD_NAME="$(basename "$MD_FILE")"
MD_STEM="${MD_NAME%.*}"

DOC_ID=""

# --------------------------------------------------------------------
# 方案①（首选）混合方案：markdown 直传 + 三步法插图
# 优势：代码块原生渲染（<pre lang="xxx"><code>），图片精确定位
# --------------------------------------------------------------------
try_hybrid() {
  cd "$MD_DIR" || return 1

  echo "  📄 创建空壳文档..."
  local CREATE_RESULT
  CREATE_RESULT=$(lark-cli docs +create --title "$TITLE" \
    --doc-format markdown --content "# ${TITLE}" 2>&1)
  local NEW_ID
  NEW_ID=$(echo "$CREATE_RESULT" | grep -oE '"document_id":\s*"[^"]+"' | head -1 | grep -oE '"[A-Za-z0-9]{15,}"' | tr -d '"')
  if [ -z "$NEW_ID" ]; then
    echo "  ❌ 创建失败:"; echo "$CREATE_RESULT"; return 2
  fi
  DOC_ID="$NEW_ID"
  echo "  ✅ 空壳 doc_id=$DOC_ID"

  echo "  📝 overwrite 灌入正文（markdown 直传，保留代码块标记）..."
  local UPDATE_RESULT
  UPDATE_RESULT=$(lark-cli docs +update --doc "$DOC_ID" \
    --command overwrite --doc-format markdown \
    --content @"./$MD_NAME" 2>&1)
  if ! echo "$UPDATE_RESULT" | grep -qE '"ok":\s*true'; then
    echo "  ❌ 正文写入失败:"; echo "$UPDATE_RESULT"; return 3
  fi
  echo "  ✅ 正文已写入"

  # 三步法插图（避开 --selection-with-ellipsis 的 1.0.59~1.0.65 bug）
  if [ -n "$IMG_DIR" ] && [ -d "$IMG_DIR" ]; then
    echo "  🖼 三步法插入图片..."
    local IMG_DIR_ABS OUTLINE
    IMG_DIR_ABS="$(cd "$IMG_DIR" && pwd)"
    OUTLINE=$(lark-cli docs +fetch --doc "$DOC_ID" \
      --scope outline --detail with-ids 2>/dev/null)

    shopt -s nullglob
    for IMG in "$IMG_DIR_ABS"/*.png "$IMG_DIR_ABS"/*.jpg "$IMG_DIR_ABS"/*.jpeg; do
      [ -f "$IMG" ] || continue
      local ANCHOR REL_IMG INSERT_RES IMG_BLK TARGET_BLK
      ANCHOR="$(basename "$IMG")"; ANCHOR="${ANCHOR%.*}"
      REL_IMG="$(realpath --relative-to="$MD_DIR" "$IMG" 2>/dev/null || echo "$IMG")"

      # Step1: 追加到末尾，拿 img block_id
      INSERT_RES=$(lark-cli docs +media-insert --doc "$DOC_ID" \
        --file "./$REL_IMG" --caption "$ANCHOR" \
        --align center --width 600 2>&1)
      IMG_BLK=$(echo "$INSERT_RES" | grep -oE '"block_id":\s*"[^"]+"' | head -1 | grep -oE '"[^"]+"$' | tr -d '"')
      if [ -z "$IMG_BLK" ]; then
        echo "    ⚠️ $ANCHOR 插入失败"; continue
      fi

      # Step2: 从 outline 里找匹配 anchor 的 heading block_id
      TARGET_BLK=$(echo "$OUTLINE" | grep -B1 "$ANCHOR" 2>/dev/null | grep -oE 'block_id["\s:]+[A-Za-z0-9]{10,}' | head -1 | grep -oE '[A-Za-z0-9]{10,}$')
      if [ -n "$TARGET_BLK" ]; then
        lark-cli docs +update --doc "$DOC_ID" \
          --command block_move_after \
          --block-id "$TARGET_BLK" --src-block-ids "$IMG_BLK" >/dev/null 2>&1 \
          && echo "    ✅ $ANCHOR → 已定位到锚点" \
          || echo "    ⚠️ $ANCHOR 移动失败，图片保留在末尾"
      else
        echo "    ℹ️ $ANCHOR 未找到锚点，图片保留在末尾"
      fi
    done
  fi
  return 0
}

# --------------------------------------------------------------------
# 方案②（降级兜底）pandoc → docx → drive +import
# 注意：此路径飞书不识别 docx 内代码块样式，代码会渲染为普通段落
# --------------------------------------------------------------------
try_pandoc_import() {
  command -v pandoc >/dev/null 2>&1 || { echo "  ⏭ 无 pandoc，跳过方案②"; return 1; }

  cd "$MD_DIR" || return 1
  local DOCX="./${MD_STEM}.docx"
  local RESOURCE_ARG=()
  if [ -n "$IMG_DIR" ] && [ -d "$IMG_DIR" ]; then
    RESOURCE_ARG=(--resource-path="$MD_DIR:$(cd "$IMG_DIR" && pwd)")
  else
    RESOURCE_ARG=(--resource-path="$MD_DIR")
  fi

  echo "  🔄 pandoc 转 docx..."
  # -f gfm 用 GitHub Flavored Markdown，不解析 YAML 前置块（避开 > blockquote 误伤）
  if ! pandoc -f gfm+tex_math_dollars -t docx "./$MD_NAME" -o "$DOCX" "${RESOURCE_ARG[@]}" 2>/tmp/pandoc.err; then
    echo "  ⚠️ pandoc 转换失败:"; cat /tmp/pandoc.err >&2
    return 1
  fi
  [ -s "$DOCX" ] || { echo "  ⚠️ 生成的 docx 为空"; return 1; }

  echo "  ⬆️  drive +import 上传..."
  local IMPORT_RESULT
  IMPORT_RESULT=$(lark-cli drive +import --file "$DOCX" --type docx --name "$TITLE" 2>&1)
  local NEW_ID
  NEW_ID=$(echo "$IMPORT_RESULT" | grep -oE '"token"\s*:\s*"[A-Za-z0-9]{15,}"' | head -1 | grep -oE '"[A-Za-z0-9]{15,}"' | tr -d '"')
  [ -z "$NEW_ID" ] && NEW_ID=$(echo "$IMPORT_RESULT" | grep -oE '"document_id"\s*:\s*"[A-Za-z0-9]{15,}"' | head -1 | grep -oE '"[A-Za-z0-9]{15,}"' | tr -d '"')

  if [ -z "$NEW_ID" ]; then
    echo "  ⚠️ 导入失败:"; echo "$IMPORT_RESULT" | tail -20
    return 1
  fi

  DOC_ID="$NEW_ID"
  echo "  ✅ 方案②成功 doc_id=$DOC_ID"
  return 0
}

# --------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------
echo "🚀 发布飞书文档: $TITLE"
echo "─── 方案① 混合方案（markdown直传+三步法插图）───"
if ! try_hybrid; then
  echo "─── 方案①失败，切换到方案② pandoc→docx→import ───"
  try_pandoc_import || { echo "❌ 两个方案都失败"; exit 4; }
fi

# 授权
echo "🔑 授权给主人..."
for OPENID in "${OWNER_OPENIDS[@]}"; do
  lark-cli drive +member-add --type docx --token "$DOC_ID" \
    --member-type openid --member-id "$OPENID" \
    --perm full_access --yes >/dev/null 2>&1 \
    && echo "  ✅ $OPENID" \
    || echo "  ⚠️ $OPENID 授权失败（可能已有权限）"
done

DOC_URL="https://{{FEISHU_DOMAIN}}.feishu.cn/docx/$DOC_ID"
echo ""
echo "🎉 发布完成"
echo "🔗 $DOC_URL"
echo ""
echo "📌 后续：调用 feishu-doc-auto-archiving 技能归档到多维表"

echo "$DOC_URL"
