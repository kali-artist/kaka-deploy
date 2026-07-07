# Cloudflare API Error Codes Reference

Common error codes encountered when using Cloudflare API for Pages deployment.

## Token Validation Errors

### ⚠️ 关键：不要用 `/user/tokens/verify` 验证 Pages-only 令牌

`/user/tokens/verify` 端点需要用户级权限（User > API Tokens > Read）。仅含 `Account > Cloudflare Pages > Edit` 权限的令牌会返回 `code 1000: Invalid API Token`，**即使令牌完全有效**。

**实际案例**：一个 `cfat_` 开头、53 字符的 Pages 令牌：
- `/user/tokens/verify` → `{"success": false, "code": 1000}` ← 假阴性！
- `GET /accounts/{id}/pages/projects` → `{"success": true}` ← 令牌实际有效
- `wrangler pages deploy` → 成功部署 ← 令牌确实有效

### ✅ 正确验证方法：用 Pages projects 列表端点
```bash
# 与部署使用相同的权限范围，结果可靠
ACCOUNT_ID="your-account-id"
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/pages/projects" \
  -H "Authorization: Bearer $(cat /root/.cloudflare-pages-token)"
# success: true → 令牌有效，可以继续部署
# success: false → 令牌确实失效，需要重新生成
```

## Error Codes

| Code | Message | Meaning | Action |
|------|---------|---------|--------|
| 1000 | Invalid API Token | **可能是假阴性**：令牌确实失效/过期/被撤销，**也可能**是令牌缺少 verify 端点所需的用户级权限但 Pages 权限正常 | 先用 Pages projects 列表端点二次确认；如果列表成功说明令牌有效可继续部署 |
| 9106 | Authentication failed (HTTP 400) | Token lacks required permissions or is invalid | Check token permissions: Account > Cloudflare Pages > Edit |
| 6003 | Invalid request headers | Authorization header format is wrong | Ensure `Bearer <token>` format, no extra whitespace |
| 6111 | Invalid format for Authorization header | Header value doesn't match expected format | Check for trailing newline in token file: `cat tokenfile \| xxd \| tail` |

## Debugging Token Issues

### 1. Check token file integrity
```bash
# Token should be single line, no trailing newline, ~53 chars, starts with cfat_
wc -c /root/.cloudflare-pages-token
head -c 10 /root/.cloudflare-pages-token
tail -c 10 /root/.cloudflare-pages-token
```

### 2. Check for trailing newline
```bash
# If wc shows 54 instead of 53, there's a trailing newline
# Fix: printf '%s' "$(cat /root/.cloudflare-pages-token)" > /root/.cloudflare-pages-token
```

### 3. Verify token via Pages API (not /user/tokens/verify)
```bash
# ✅ 正确：用 Pages API 验证（与部署使用相同权限）
ACCOUNT_ID="your-account-id"
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/pages/projects" \
  -H "Authorization: Bearer *** /root/.cloudflare-pages-token)"
# success: true → 令牌有效

# ❌ 错误：/user/tokens/verify 对 Pages-only 令牌会产生假阴性
# curl -s https://api.cloudflare.com/client/v4/user/tokens/verify ...
# ↑ 不要用这个端点验证 Pages-only 令牌
```

### 4. Check token permissions
Token needs at minimum:
- Account > Cloudflare Pages > Edit
- Account > Account Settings > Read (for project creation)

## Token Verify 端点的假阴性问题

### 根本原因

`/user/tokens/verify` 端点验证的是**用户级 API 令牌**，需要令牌包含 `User > API Tokens > Read`（或类似的用户级权限）。而用于 Pages 部署的令牌通常只包含 `Account > Cloudflare Pages > Edit` 权限，不含用户级权限，因此 verify 端点返回 `code 1000: Invalid API Token`。

### 判断令牌是否真正失效

1. 用 Pages projects 列表端点二次验证（见上方步骤3）
2. 如果列表端点也返回 `success: false`，令牌确实失效
3. 如果列表端点返回 `success: true`，令牌有效，可以继续部署
4. 如果 wrangler deploy 成功，令牌也有效

### 不要因为 verify 假阴性就要求用户重新生成令牌

这会浪费用户时间并造成困惑。先做二次验证。
