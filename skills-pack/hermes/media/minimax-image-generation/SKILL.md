---
name: minimax-image-generation
description: "Generate images via MiniMax mmx CLI with vision verification and Python-based post-processing compositing. Handles common AI layout limitations, green screen/chroma key backgrounds, sprite sheets, animation frames, and sticker-style outputs."
tags: [image generation, minimax, mmx, ai image, sprite sheet, green screen, chroma key, pillow, PIL, vision analyze, sticker, chibi]
triggers:
  - generate image
  - make picture
  - create sprite
  - green screen
  - chroma key
  - mmx image
  - sprite sheet
  - animation frames
  - sticker style
  - chibi character
  - 生成图片
  - 绿幕背景
  - 精灵图
---

# MiniMax Image Generation via mmx CLI

Use this skill when the user wants to generate images using the MiniMax mmx CLI, especially for:
- Character sprites and sprite sheets
- Green screen / chroma key images for transparency
- Sticker-style Q版/chibi characters
- Animation frames and sequential images
- When the native image_gen tool fails or produces poor results

---

## 1. Core Workflow

### Step 1: Generate Image with mmx CLI

```bash
# ⚠️ 正确 flag 是 --aspect-ratio（不是 --size，--size 不存在）
mmx image generate --prompt "your detailed description" --aspect-ratio "16:9"
```

**Correct flags** (verified via `mmx image generate --help` on mmx 1.0.0):
- `--prompt <text>` — Image description
- `--aspect-ratio <ratio>` — e.g. "1:1", "16:9", "4:3", "3:2", "9:16"
- `--n <count>` — Number of images (default: 1)
- `--out-dir <dir>` — **Download images directly to target directory** (NOT always ~/)
- `--out-prefix <prefix>` — Filename prefix (default: "image")
- `--quiet` — Suppress verbose output (use in batch scripts)
- `--subject-ref <params>` — Subject reference for consistency

**Output location**: By default saves to `~/image_001.jpg`, BUT with `--out-dir <dir> --out-prefix <prefix>` you can save directly to any directory with custom naming. **Always use --out-dir + --out-prefix in batch workflows** to avoid manual mv/rename.

### Step 2: Verify with Vision Analysis

Always verify the generated image matches requirements:

```python
vision_analyze(
    image_url="/home/ubuntu/image_001.jpg",
    question="Verify: background color? layout grid pattern? character features matches description? any AI artifacts? sticker style? overall quality?"
)
```

### Step 3: Locate and Move Output File

```bash
# Find the generated image
find /home/ubuntu -name "image_001.jpg" -newermt "-1 min"

# Move to workspace
mv /home/ubuntu/image_001.jpg /home/ubuntu/.hermes/workspace/
```

---

## 2. Common Patterns and Solutions

### Pattern A: AI Won't Do Specific Layouts (MOST COMMON ISSUE)

**Problem**: AI image generators almost always produce 2x2 grids when asked for "4 frames horizontal" but they NEVER do true 1-frame-per-cell horizontal layouts.

**Solution**: The 2-Step Reliable Method:

1. **Generate ONE perfect single image** first
2. **Composite with Python/PIL** to create the exact layout needed

```python
from PIL import Image

# 1. Open the perfect single image
img = Image.open("/home/ubuntu/image_001.jpg")

# 2. Define cell dimensions
cell_width = 192
cell_height = 208

# 3. Resize to cell size
img_resized = img.resize((cell_width, cell_height), Image.Resampling.LANCZOS)

# 4. Create horizontal sprite sheet
total_width = cell_width * 4  # 4 frames
sprite = Image.new("RGB", (total_width, cell_height), "#00FF00")

# 5. Paste each frame
for i in range(4):
    frame = img_resized.copy()
    # Add animation variation here if needed
    sprite.paste(frame, (i * cell_width, 0))

# 6. Save
sprite.save("/home/ubuntu/output_sprite.png")
```

### Pattern B: Green Screen / Chroma Key Background

**Prompt pattern for pure green background:

```
纯 #00FF00 亮绿色背景，无阴影无发光无渐变，纯色背景
```

**Important**: Specify the EXACT hex color `#00FF00` and explicitly say "no shadows, no glow, no gradient, solid color background".

**Verification**: Always check with vision_analyze to confirm the background is actually pure and uniform green.

### Pattern C: Sticker Style Characters

**Prompt template for Q版/chibi stickers:**

```
Q版 chibi 女孩头像贴纸，深黑茶色齐肩直发，空气感碎齐刘海，圆润短圆脸，白皙肤色，圆杏仁眼，甜美微笑。戴着米妮发箍：黑色圆耳朵+大红色白色波点蝴蝶结。纯 #00FF00 亮绿色背景，无阴影无发光无渐变，纯色背景。贴纸风格，白色外描边，线条清晰，色彩饱满。
```

**Key elements to include:**
- Character specific features (hair color, style, face shape)
- Accessory details
- Background color specification
- "no shadows, no glow, solid color"
- "sticker style, white outline"
- "clean lines, vibrant colors"

---

## 3. Animation Frame Variations

When creating sprite sheets for animation, add subtle variations to each frame:

| Frame # | Variation | How to achieve |
|---|---|---|
| 1 | Normal, eyes open | Base image |
| 2 | Breathe in (slightly larger) | `resize(1.02x, center paste |
| 3 | Eyes closed/blink | Draw black ovals over eyes |
| 4 | Breathe out (slightly smaller) | `resize(0.98x), center paste |

```python
from PIL import Image, ImageDraw

# Example: Add blink effect to a frame
def add_blink(frame):
    draw = ImageDraw.Draw(frame)
    # Position eyes based on your character's eye location
    draw.ellipse((x1, y1, x2, y2), fill="black")
    return frame
```

---

## 4. Troubleshooting

### Common Issues

1. **File not found**: Without `--out-dir`, mmx saves to `~/image_001.jpg` by default. **Best practice: always pass `--out-dir <target_dir> --out-prefix <name>` to save directly where you need it.** Use `find /home/ubuntu -name "image_*.jpg"` if you forgot --out-dir.

2. **AI keeps making 2x2 grids**: Don't fight it - generate single, composite with Python. This is 100% reliable.

3. **Background not pure green**: Re-generate with more explicit prompt, specify hex code, add "uniform solid color" explicitly.

4. **Character features wrong**: Be MORE specific in prompt - describe every feature you want.

5. **AI artifacts**: Re-generate, or crop and composite the good parts with PIL.

### Fallback Strategies

1. If mmx image fails:
   - Check mmx is installed: `mmx --version`
   - Try a simpler prompt
   - Try a different size
   - Generate single images instead of complex layouts

2. If layout keeps failing:
   - ALWAYS fall back to Python compositing - it's the only reliable way

---

## 5. Best Practices

1. **Describe EVERYTHING**: Don't assume AI knows what you want. Describe:
   - Hair color, style, length
   - Face shape, eye color
   - Exact clothing/accessory details
   - Background color (with hex code!)
   - Style keywords (sticker, chibi, anime, realistic)

2. **Verify first, deliver second**: Always run vision_analyze before showing to user

3. **Single first, composite second**: For multi-frame layouts, always do perfect single + composite

4. **Green screen = #00FF00**: Always use this exact hex for chroma key compatibility

5. **Document the file path**: Tell user exactly where the file is located

---

## 6. Example Complete Workflow

```bash
# Step 1: Generate single perfect character — use --out-dir + --out-prefix for clean output
mmx image generate --prompt "Q版 chibi 女孩头像贴纸，深黑茶色齐肩直发，空气感碎齐刘海，圆润短圆脸，白皙肤色，圆杏仁眼，甜美微笑。纯 #00FF00 亮绿色背景，无阴影无发光无渐变，纯色背景。贴纸风格，白色外描边，线条清晰，色彩饱满。" --aspect-ratio "1:1" --out-dir ./output --out-prefix chibi_char --quiet
```

```python
# Step 2: Verify quality
vision_analyze(
    image_url="/home/ubuntu/image_001.jpg",
    question="Check: pure green background? chibi style? white sticker outline? character features correct? any artifacts?"
)
```

```python
# Step 3: Composite into 4-frame horizontal sprite sheet
from PIL import Image

img = Image.open("/home/ubuntu/image_001.jpg")
cell_w, cell_h = 192, 208
img = img.resize((cell_w, cell_h), Image.Resampling.LANCZOS)

sprite = Image.new("RGB", (cell_w * 4, cell_h), "#00FF00")

for i in range(4):
    frame = img.copy()
    if i == 1:  # breathe in
        small = img.resize((int(cell_w*1.02), int(cell_h*1.02))
        paste_x = (cell_w - small.width) // 2
        paste_y = (cell_h - small.height) // 2
        frame.paste("#00FF00", (0, 0, cell_w, cell_h))
        frame.paste(small, (paste_x, paste_y))
    sprite.paste(frame, (i * cell_w, 0))

sprite.save("/home/ubuntu/.hermes/workspace/sprite_sheet.png")
```

---

## 7. Key Lessons Learned

- **AI will NEVER do true horizontal multi-cell layouts reliably. Stop trying. Generate single + composite with Python.** This is the #1 lesson.

- **mmx saves images always saves to `/home/ubuntu/` NOT current directory.** → **CORRECTED (v1.1)**: Use `--out-dir <dir> --out-prefix <prefix>` to save directly to target. This is the reliable way for batch workflows.

- Pure green background needs EXPLICIT hex code `#00FF00` and explicitly say no shadows, no glow, solid

- vision_analyze is essential to catch AI won't tell you it messed up the layout until you check

- Python/PIL is faster than fighting AI 100x faster and 100% reliable for exact layouts

- **🚨 微信发图硬规则（跨技能通用）**：生成图片保存到本地后，发给主人必须用 `MEDIA:/absolute/path/to/image.jpg` 引用本地文件。**绝对禁止**直接发外部 URL（微信端 `MEDIA:<https://...>` 不会预览渲染）。用 `--out-dir` 指定输出目录后直接 `MEDIA:` 引用该路径即可。发完**不要立即 rm**（gateway 异步读文件会竞态丢图）。
