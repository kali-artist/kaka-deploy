---
name: holographic-memory-plugin
description: "Holographic memory plugin code customization — modifying auto-extraction patterns, context extraction logic, and testing end-to-end with MemoryStore."
version: 1.0.0
author: kaka for Kali
metadata:
  hermes:
    tags: [holographic, memory-plugin, auto-extract, regex, chinese, kaka]
    related_skills: [hermes-agent]
---

# Holographic Memory Plugin Customization

Use when modifying the holographic memory plugin's auto-extraction logic, adding regex patterns, debugging fact extraction, or testing the MemoryStore.

## Code Locations

- **Plugin entry**: `~/.hermes/hermes-agent/plugins/memory/holographic/__init__.py`
  - `HolographicMemoryProvider` class (line ~114)
  - `_load_plugin_config()` — reads `plugins.hermes-memory-store` from config.yaml
  - `_auto_extract_facts(self, messages)` — called on session_end
  - `_extract_context(content, match, window=150)` — static method, window-based snippet extraction
- **Store class**: `~/.hermes/hermes-agent/plugins/memory/holographic/store.py`
  - `MemoryStore` class (line ~98)
  - Methods: `add_fact`, `search_facts`, `list_facts`, `update_fact`, `remove_fact`, `record_feedback`, `rebuild_all_vectors`
- **Retriever**: `~/.hermes/hermes-agent/plugins/memory/holographic/retriever.py`
  - `FactRetriever` class — handles search with HRR vector similarity

## Config Structure

```yaml
# ~/.hermes/config.yaml
memory:
  provider: holographic        # activates the plugin
  memory_char_limit: 2200
  user_char_limit: 1375
  nudge_interval: 10
  flush_min_turns: 6

plugins:
  enabled:                      # plugin must be listed here to load
  - hermes-memory-store
  hermes-memory-store:          # plugin-specific config
    auto_extract: true          # enable auto-extraction on session_end
    default_trust: 0.5          # trust score for new facts
    min_trust_threshold: 0.3    # minimum trust for retrieval
    # db_path: $HERMES_HOME/memory_store.db  (optional, defaults to ~/.hermes/memory_store.db)
    # hrr_dim: 1024             (optional, HRR vector dimensions)
```

**⚠️ Common mistake 1**: `plugins.enabled` must include `hermes-memory-store`. If `plugins.enabled` is empty (`[]`) or omits the plugin, the plugin code is never loaded, so `auto_extract: true` has no effect and `fact_store` will stay empty even though the config looks correct.

**⚠️ Common mistake 2**: Config key is `plugins.hermes-memory-store.db_path`, NOT `memory.holographic_store_path`. The old governance skill had the wrong key name — it has been deleted.

## DB Location

- Default: `~/.hermes/memory_store.db` (SQLite, WAL mode)
- Tables: `facts`, `entities`, `fact_entities`, `facts_fts` (FTS5), `memory_banks`, `sqlite_sequence`
- `facts` columns: `fact_id`, `content`, `category`, `tags`, `trust_score`, `retrieval_count`, `helpful_count`, `created_at`, `updated_at`, `hrr_vector`

## Auto-Extract Patterns

The `_auto_extract_facts` method uses three pattern groups:

| Category | English Patterns | Chinese Patterns |
|---|---|---|
| `user_pref` | I prefer/like/love/use/want, my favorite/preferred/default is, I always/never/usually | 我喜欢/偏好/习惯/爱用, 我总是/从不/一般/通常, 我的偏好/默认, 记住/以后都, 我用/选了/装了 |
| `project` | we decided/agreed/chose, the project uses/needs | 我们决定/选了/敲定, 项目用/需要, 方案是/用, 部署在/运行在 |
| `general` | (none) | 服务器叫/是, 端口是/为, 账号是/为 |

### Adding New Patterns

1. Edit `__init__.py` → find `_auto_extract_facts` method
2. Add `re.compile(r'your_pattern')` to the appropriate pattern list
3. Use `re.search()` (not `re.match()`) for position-independent matching
4. Each message matches at most one pattern per category (break after first match)

### Context Extraction

`_extract_context(content, match, window=150)`:
- Extracts ±150 chars around the match position (not `content[:400]`)
- Adds `...` prefix/suffix if truncated
- Caps at 500 chars
- Ensures the matched fact has enough surrounding context to be meaningful

## Testing

### Quick Pattern Test (no DB)

```python
import re
# Copy patterns from __init__.py and test against sample text
patterns = [re.compile(r'your_pattern')]
text = '测试文本'
assert any(p.search(text) for p in patterns), "Should match"
```

### End-to-End Test (with DB)

```python
import sys, os, tempfile, re
sys.path.insert(0, os.path.expanduser('~/.hermes/hermes-agent'))
from plugins.memory.holographic.store import MemoryStore

# Create temp DB
tmpdir = tempfile.mkdtemp()
store = MemoryStore(os.path.join(tmpdir, 'test.db'))

# Test add_fact
store.add_fact('我喜欢用nginx', category='user_pref')
facts = store.list_facts()
assert len(facts) >= 1

# Test search
results = store.search_facts('nginx')
assert len(results) >= 1

store.close()
```

### Verify Production DB

```bash
# Check DB exists and has data
sqlite3 ~/.hermes/memory_store.db "SELECT count(*) FROM facts"
sqlite3 ~/.hermes/memory_store.db "SELECT fact_id, category, substr(content,1,60) FROM facts ORDER BY fact_id DESC LIMIT 5"
```

## After Code Changes

1. `python -m py_compile plugins/memory/holographic/__init__.py` — verify compilation
2. Run pattern tests (see above)
3. Restart gateway: `systemctl --user restart hermes-gateway`
4. Changes take effect on next `session_end` (auto_extract runs at session end)

## Cross-Instance Code Sync (Local → Remote)

When plugin code is modified and verified locally, push to remote instances (e.g. {{INSTANCE_NAME}}).

### Remote Plugin Path Discovery

The plugin code lives inside the venv site-packages, which varies by Python version:

```bash
# Find the remote plugin path (one-liner)
ssh root@REMOTE_IP 'find /root/.hermes/venv -path "*/plugins/memory/holographic/__init__.py" 2>/dev/null'
# Example {{INSTANCE_NAME}} path: /root/.hermes/venv/lib/python3.14/site-packages/plugins/memory/holographic/__init__.py
# Local path (for reference): ~/.hermes/hermes-agent/plugins/memory/holographic/__init__.py
```

### Sync + Verify (single SSH command)

```bash
# 1. Upload the modified file
sshpass -p 'REMOTE_PASS' scp -o StrictHostKeyChecking=no \
  ~/.hermes/hermes-agent/plugins/memory/holographic/__init__.py \
  root@REMOTE_IP:REMOTE_PLUGIN_PATH

# 2. One-shot verification (Chinese patterns + compile + config + DB)
sshpass -p 'REMOTE_PASS' ssh root@REMOTE_IP '
  grep -c "喜欢\|偏好\|习惯\|决定\|服务器叫\|端口是" REMOTE_PLUGIN_PATH
  cd $(dirname REMOTE_PLUGIN_PATH)/../../.. && python3 -m py_compile plugins/memory/holographic/__init__.py && echo "✅ compile OK"
  ls -la /root/.hermes/memory_store.db
  python3 -c "import yaml; c=yaml.safe_load(open(\"/root/.hermes/config.yaml\")); print(\"provider:\", c.get(\"memory\",{}).get(\"provider\")); print(\"auto_extract:\", c.get(\"plugins\",{}).get(\"hermes-memory-store\",{}).get(\"auto_extract\"))"
'
# 3. Restart gateway on remote to activate changes
sshpass -p 'REMOTE_PASS' ssh root@REMOTE_IP 'systemctl --user restart hermes-gateway 2>/dev/null || pkill -f "hermes.*gateway" && nohup /root/.hermes/venv/bin/python -m hermes_cli.main gateway run --replace > /root/.hermes/gateway.log 2>&1 &'
```

### Key Pitfalls

1. **Path differs per instance**: venv Python version (3.12/3.14/etc.) changes the site-packages path segment. Always discover with `find` first.
2. **Local vs remote path**: Local uses `~/.hermes/hermes-agent/plugins/...`, remote ({{INSTANCE_NAME}}) uses `~/.hermes/venv/lib/pythonX.Y/site-packages/plugins/...`.
3. **Gateway restart required**: Code changes don't take effect until the remote gateway process restarts.
4. **Config also needs syncing**: If config.yaml was modified locally (e.g. adding `plugins.hermes-memory-store` section), sync that too — the remote may be missing the plugin config block entirely.

## Common Pitfalls

1. **Plugin not enabled**: `plugins.enabled` must list `hermes-memory-store`. An empty `enabled` list means the plugin never loads, so no facts are extracted regardless of `auto_extract: true`. Quick check:
   ```bash
   python3 -c "import yaml; c=yaml.safe_load(open('~/.hermes/config.yaml')); print('enabled:', c.get('plugins',{}).get('enabled',[]))"
   ```
2. **Wrong config key**: `memory.holographic_store_path` does NOT exist. Use `plugins.hermes-memory-store.db_path`.
3. **Wrong class name**: Store class is `MemoryStore` (not `HolographicStore`).
4. **content[:400] bug**: Old code truncated to first 400 chars. Fixed with `_extract_context()` window-based extraction.
5. **No Chinese patterns**: Original code only had English regex. Chinese patterns added 2026-06-30.
6. **Restart required**: Code changes need gateway restart to take effect.
7. **Remote plugin path differs**: See "Cross-Instance Code Sync" above — always `find` the remote path first, don't assume the same venv structure.

## Quick Diagnosis: `fact_store` stays empty

If you expect facts to be auto-extracted but `fact_store search` returns nothing:

1. Confirm `memory.provider` is `holographic`.
2. Confirm `plugins.enabled` includes `hermes-memory-store`.
3. Confirm `plugins.hermes-memory-store.auto_extract` is `true`.
4. Confirm the plugin code exists and compiles: `python3 -m py_compile ~/.hermes/hermes-agent/plugins/memory/holographic/__init__.py`.
5. Confirm the DB file exists and is writable: `ls -la ~/.hermes/memory_store.db`.
6. Restart gateway after any config change.
7. Wait for a session to end (auto_extract runs on `session_end`), or manually call the store to test.