#!/usr/bin/env bash
# save_markdown.sh - 教程本地归档到 ~/tutorials/
# 用法: bash save_markdown.sh <markdown_file> <images_dir> "标题" [模板标识]

set -uo pipefail

MD_FILE="${1:?缺少参数: markdown 文件路径}"
IMG_DIR="${2:-}"
TITLE="${3:?缺少参数: 教程标题}"
TEMPLATE="${4:-unknown}"

[ -f "$MD_FILE" ] || { echo "❌ markdown 文件不存在: $MD_FILE" >&2; exit 1; }

# 生成安全目录名：日期_标题拼音短名
DATE="$(date +%Y-%m-%d)"
# 简化：中文标题转下划线拼接（不做拼音转换，直接过滤特殊字符）
SAFE_NAME="$(echo "$TITLE" | tr -cd '[:alnum:]_\u4e00-\u9fa5' | cut -c1-40)"
[ -z "$SAFE_NAME" ] && SAFE_NAME="tutorial"

OUT_DIR="$HOME/tutorials/${DATE}_${SAFE_NAME}"
mkdir -p "$OUT_DIR/images"

# 复制 markdown
cp "$MD_FILE" "$OUT_DIR/README.md"
echo "📄 markdown → $OUT_DIR/README.md"

# 复制图片
if [ -n "$IMG_DIR" ] && [ -d "$IMG_DIR" ]; then
  IMG_COUNT=$(find "$IMG_DIR" -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.svg' \) | wc -l)
  if [ "$IMG_COUNT" -gt 0 ]; then
    cp "$IMG_DIR"/*.png "$IMG_DIR"/*.jpg "$IMG_DIR"/*.jpeg "$IMG_DIR"/*.svg "$OUT_DIR/images/" 2>/dev/null || true
    echo "🖼 图片 $IMG_COUNT 张 → $OUT_DIR/images/"
  fi
else
  IMG_COUNT=0
fi

# 写元数据
CHAPTERS=$(grep -c '^## 第 [0-9]' "$MD_FILE" || echo 0)
ILLU_COUNT=$(find "$IMG_DIR" -maxdepth 1 -name '*illu_*.jpg' 2>/dev/null | wc -l || echo 0)
cat > "$OUT_DIR/meta.json" <<EOF
{
  "title": "$TITLE",
  "template": "$TEMPLATE",
  "chapters": $CHAPTERS,
  "images_count": $IMG_COUNT,
  "illustrations_count": $ILLU_COUNT,
  "created_at": "$(date -Iseconds)",
  "source_md": "$MD_FILE"
}
EOF

# 校验图片路径
echo ""
echo "🔍 校验图片路径..."
MISSING=0
while IFS= read -r IMG_REF; do
  [ -z "$IMG_REF" ] && continue
  # 只检查相对路径的本地图
  case "$IMG_REF" in
    http*|/*) continue ;;
  esac
  if [ ! -f "$OUT_DIR/$IMG_REF" ]; then
    echo "  ❌ 缺失: $IMG_REF"
    MISSING=$((MISSING + 1))
  fi
done < <(grep -oP '!\[.*?\]\(\K[^)]+' "$OUT_DIR/README.md" 2>/dev/null || true)

if [ "$MISSING" -eq 0 ]; then
  echo "  ✅ 所有图片路径 OK"
else
  echo "  ⚠️ $MISSING 张图片缺失"
fi

echo ""
echo "🎉 本地归档完成"
echo "📂 $OUT_DIR"
echo "📊 模板=$TEMPLATE  章节=$CHAPTERS  图片=$IMG_COUNT  插画=$ILLU_COUNT"

echo "$OUT_DIR"
