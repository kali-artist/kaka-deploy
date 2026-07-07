---
name: feishu-app-connection
version: 1.0.0
category: integration
description: Connect to Feishu applications using App ID/Secret and verify API access
---

# 🔴 飞书通用坑预警（必看）
**⚠️ 所有飞书操作通用规则：**
- ❌ **-32602 错误码≠通用JSON-RPC参数错误**，在飞书场景下=临时token失效
- ✅ **-32602 唯一修复命令：`lark-cli config bind --source hermes --identity bot-only`**
- ❌ **追加文档内容不要把child_index放JSON payload里**
- ✅ **追加文档内容必须在URL加`?child_index=9999`参数，才能可靠追加到末尾**

# Feishu App Connection

## When to use
When connecting to a Feishu application with provided App ID and Secret to establish API access.

## Document style standard for Feishu output

When this connection work leads to creating, updating, importing, or rewriting Feishu cloud documents, load/reference `feishu-doc-automation` and follow the owner's **unified Feishu document standard**. The original reference documents are source materials only; do not split rules by version or keep their links in skills.

Minimum requirements for generated Feishu documents:
- XML/rich block first, clear hierarchy, tables/lists/callouts, semantic colors, rich-block self-check, and no unauthorized paragraph-wall fallback.
- First-screen conclusion, useful metadata area, full-width bracket anchors such as `【核心结论】` / `【风险提示】` / `【下一步】`, table-first compression, semantic callouts, and executable next steps.
- First line is `<title>...</title>` when using XML overwrite/import.
- If the actual writer is the docx native block API, convert these XML layout semantics into native Feishu blocks as closely as possible.

## Steps
1. Save app credentials to ~/.feishu/config.json
2. Request tenant access token via Feishu auth API
3. Verify permissions scope (doc/drive read/write)
4. Confirm connection with test API call

## Pitfalls
- Ensure App Secret is stored securely
- Handle token expiration (2-hour TTL)
- Validate required permissions are granted

## Verification
Check for successful token response and permissions confirmation.