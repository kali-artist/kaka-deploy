#!/usr/bin/env bash
# generate_illustrations.sh - 批量生成教程插画（mmx 首选，image_gen 兜底）
# 用法: bash generate_illustrations.sh <outline.json> <output_dir>
#
# outline.json 格式:
# {
#   "illustrations": [
#     { "id": "ch01_illu_xxx", "prompt": "flat cartoon, ...", "chapter": 1 },
#     ...
#   ]
# }

set -uo pipefail

OUTLINE="${1:?缺少参数: outline.json}"
OUT_DIR="${2:?缺少参数: 输出目录}"

command -v mmx >/dev/null 2>&1 || { echo "❌ 缺少 mmx"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "❌ 缺少 jq"; exit 1; }
[ -f "$OUTLINE" ] || { echo "❌ outline 不存在: $OUTLINE"; exit 1; }

mkdir -p "$OUT_DIR"

TOTAL=$(jq '.illustrations | length' "$OUTLINE")
[ "$TOTAL" = "0" ] || [ "$TOTAL" = "null" ] && { echo "ℹ️ 无插画待生成"; exit 0; }

echo "🎨 开始批量生成 $TOTAL 张插画..."

OK=0; FAIL=0
for i in $(seq 0 $((TOTAL-1))); do
  ID=$(jq -r ".illustrations[$i].id" "$OUTLINE")
  PROMPT=$(jq -r ".illustrations[$i].prompt" "$OUTLINE")
  TARGET="$OUT_DIR/${ID}.jpg"

  # 已存在则跳过（支持断点续跑）
  if [ -f "$TARGET" ] && [ -s "$TARGET" ]; then
    echo "  ⏭  [$((i+1))/$TOTAL] $ID 已存在，跳过"
    OK=$((OK+1))
    continue
  fi

  echo "  🖌  [$((i+1))/$TOTAL] $ID"

  # 尝试 mmx（首选），最多 2 次
  SUCCESS=0
  for attempt in 1 2; do
    # 用 --out-dir + --out-prefix 直接落地目标位置
    if mmx image generate \
        --prompt "$PROMPT" \
        --aspect-ratio "16:9" \
        --out-dir "$OUT_DIR" \
        --out-prefix "$ID" \
        --quiet 2>/tmp/mmx.err; then
      # mmx 会输出 <prefix>_001.jpg 之类，需要重命名成 <id>.jpg
      GENERATED=$(ls -t "$OUT_DIR/${ID}"*.jpg 2>/dev/null | head -1)
      if [ -n "$GENERATED" ] && [ -s "$GENERATED" ]; then
        [ "$GENERATED" != "$TARGET" ] && mv "$GENERATED" "$TARGET"
        SUCCESS=1
        break
      fi
    fi
    echo "    ⚠️ mmx 第 $attempt 次失败，重试..."
    sleep 2
  done

  if [ "$SUCCESS" = "1" ]; then
    OK=$((OK+1))
    echo "    ✅ $TARGET"
  else
    FAIL=$((FAIL+1))
    echo "    ❌ mmx 失败: $(cat /tmp/mmx.err 2>/dev/null | tail -3)"
    # 记录失败清单，供后续人工兜底或改走 image_gen
    echo "$ID|$PROMPT" >> "$OUT_DIR/.failed_illustrations.txt"
  fi
done

echo ""
echo "🎉 完成 - 成功 $OK / 失败 $FAIL / 总计 $TOTAL"
if [ "$FAIL" -gt 0 ]; then
  echo "⚠️ 失败清单已记录到 $OUT_DIR/.failed_illustrations.txt"
  echo "   可手动重跑或改走 image_gen 内置工具兜底"
  exit 2
fi
