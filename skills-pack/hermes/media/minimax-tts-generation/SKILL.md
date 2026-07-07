---
name: minimax-tts-generation
description: "Generate speech/audio/TTS from text using the MiniMax mmx CLI, including voice selection, output file handling, and troubleshooting."
tags: [tts, speech, audio, voice, minimax, mmx, voice-generation, text-to-speech]
triggers:
  - generate speech
  - make audio
  - TTS
  - say this out loud
  - create mp3
  - speak this text
  - mmx speech
  - voice generation
  - text to speech
  - disable native tts
  - replace text_to_speech
  - 禁用原生语音
  - 永久替换TTS
---

# MiniMax TTS / Speech Generation

Use this skill when the user wants to generate speech/audio from text using the MiniMax mmx CLI, especially when the native text_to_speech tool fails, or when specific mmx voices are needed.

---

## 1. Core Workflow

### Step 1: List Available Voices
First, list all available voices to choose from:
```bash
mmx speech voices
```
Common voice examples:
- `zh_female_sweet: 甜美女声
- `zh_female_mature: 成熟女声
- `zh_male_warm: 温暖男声
- `zh_male_magnetic: 磁性男声
- `zh_cartoon_pig: 卡通小猪
- `zh_female_news: 新闻女声
- `zh_female_cute: 可爱女声

### Step 2: Generate Speech
Use the standard synthesis command:
```bash
mmx speech synthesize "你的文本内容" --voice <voice-name>
```

Example:
```bash
# 甜美女声唱歌
mmx speech synthesize "阳光彩虹小白马，滴滴哒滴滴哒" --voice zh_female_sweet

# 成熟女声深情表白
mmx speech synthesize "黑白，我爱你" --voice zh_female_mature

# 卡通小猪搞笑语音
mmx speech synthesize "黑白，我套你猴子" --voice zh_cartoon_pig
```

### Step 3: Handle Output Files
- Default output: `speech_<timestamp>.mp3` in the current working directory
- Move/rename to a specific path:
```bash
mv speech_*.mp3 /target/path/filename.mp3
```

---

## 2. Best Practices

### Voice Selection Guide
| Voice Name | Use Case |
|---|---|
| `zh_female_sweet` | Singing, cheerful content, children's content |
| `zh_female_mature` | Emotional, sincere, professional content |
| `zh_cartoon_pig` | Funny, playful, comedic content |
| `zh_male_warm` | Comforting, storytelling content |
| `zh_female_news` | Formal, informative content |

### Text Tips
- Keep text under 500 characters for best results
- For longer text, split into segments and generate separately
- Punctuation helps with natural pauses
- Avoid very short single words may produce unexpected results — add context if needed

---

## 3. Troubleshooting

### Common Errors
1. **Command not found**: Ensure mmx CLI is not installed or not in PATH
2. **Voice not found**: Check voice name spelling with `mmx speech voices`
3. **Empty output**: Verify text is not empty, check for special characters
4. **Audio quality issues**: Try a different voice, or adjust text punctuation

### Fallback
If mmx speech fails, try:
1. Check mmx CLI installation: `mmx --version`
2. Try a different voice
3. Simplify the text (remove special chars, shorten length
4. Use the native `text_to_speech` tool as backup

---

## 5. Permanently Disable Hermes Native TTS

When the native `text_to_speech` tool is unreliable, broken, or a better alternative exists (like mmx speech or MCP-based TTS), disable it permanently at FIVE levels to ensure only the replacement is used.

This pattern works for ANY built-in Hermes tool that needs to be permanently disabled and replaced with an external CLI/MCP alternative.

### Level 1: Config.yaml - Disable the Provider
**Goal**: Make the tool fail immediately even if someone tries to call it.

Use the `patch` tool to edit `~/.hermes/config.yaml`:
```yaml
tts:
  provider: disabled
```

**Actual workflow**:
```bash
# First verify current state
grep -A5 "^tts:" ~/.hermes/config.yaml
```
Then use patch to replace the tts section with `provider: disabled`.

### Level 2: Remove from Enabled Toolsets
**Goal**: Remove the toolset from profile-level tool exposure.

Use the `patch` tool to edit `~/.hermes/config.yaml`:
```yaml
enabled_toolsets:
  # ... existing toolsets ...
  # - "tts"  # REMOVE THIS LINE
  "memory",
  "todo",
  # ...
```

**Actual workflow**:
```bash
# First verify current enabled_toolsets
grep -A50 "enabled_toolsets" ~/.hermes/config.yaml | head -60
```
Then patch to remove the "tts" entry from the list.

### Level 3: Remove from Core Tools (Remove Tool from LLM Visibility)
**Goal**: Remove the tool from the LLM's tool schema entirely — the model won't even see it as an option.

Edit `~/.hermes/hermes-agent/toolsets.py` and remove `"text_to_speech"` from the `_HERMES_CORE_TOOLS` list:
```python
_HERMES_CORE_TOOLS = [
    # ... other tools
    "browser_vision", "browser_console", "browser_cdp", "browser_dialog",
    # REMOVE: # Text-to-speech
    # REMOVE: "text_to_speech",
    # Planning & memory
    "todo", "memory",
    # ...
]
```

**Actual verification**:
```bash
grep -n "text_to_speech" ~/.hermes/hermes-agent/toolsets.py
```
If any matches remain, patch them out.

### Level 4: Remove the TTS Toolset Definition
**Goal**: Clean up the unused toolset definition.

In the same `toolsets.py` file, delete the entire "tts" toolset entry:
```python
# DELETE THIS ENTIRE BLOCK:
# "tts": {
#     "description": "Text-to-speech: convert text to audio with Edge TTS (free), ElevenLabs, OpenAI, or xAI",
#     "tools": ["text_to_speech"],
#     "includes": []
# },
```

### Level 5: Update Memory - Document the Permanent Change
**Goal**: Ensure future sessions know about this change and don't try to use the disabled tool.

Use the `memory` tool to update `MEMORY.md`:
```python
memory(
    action="add",
    target="memory",
    content="TTS 配置已永久修改：Hermes原生 text_to_speech 已禁用，以后语音生成都直接用 mmx speech synthesize 命令。已完成的修改：1) tts.provider 设为 disabled；2) 从 enabled_toolsets 移除了 tts 工具集；3) 从 _HERMES_CORE_TOOLS 移除了 text_to_speech 工具。"
)
```

---

### Full Verification Checklist
After making ALL five changes, verify:

1. ✅ **Config level**: `grep -A2 "^tts:" ~/.hermes/config.yaml` should show `provider: disabled`
2. ✅ **Toolset level**: `grep "tts" ~/.hermes/config.yaml` should NOT show "tts" in enabled_toolsets
3. ✅ **Code level**: `grep -c "text_to_speech" ~/.hermes/hermes-agent/toolsets.py` should return 0 (or only in comments)
4. ✅ **Memory level**: Check `~/.hermes/memories/MEMORY.md` contains the TTS disablement note
5. ✅ **Gateway level**: Restart gateway and verify no errors

---

### Key Lessons
- **5 levels are needed**, not just 1 or 2: Config provider → enabled_toolsets → core tools list → toolset definition → memory
- The profile's `enabled_toolsets` is critical — even if the provider is disabled, if "tts" remains in enabled_toolsets, the tool may still be exposed
- Always update memory so future sessions don't waste time trying the disabled tool
- This pattern is generalizable: browser tools, terminal tools, any built-in tool can be permanently disabled this way

---

## 6. Lessons Learned
- The mmx CLI supports both speech synthesis is reliable for Chinese TTS
- Voice selection has a huge impact on tone and emotion
- Default output filenames are timestamped, so always move/rename after generation
- Cartoon/funny voices work best for short, punchy phrases
- Singing works surprisingly well with the sweet female voice
- Always verify the generated audio exists and plays correctly before delivering to user
