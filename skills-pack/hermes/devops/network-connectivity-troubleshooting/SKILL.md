---
name: network-connectivity-troubleshooting
trigger: When troubleshooting network connectivity issues, timeouts, or restricted access patterns
description: Systematic network troubleshooting to diagnose connectivity limitations and restrictions
version: 1.0.0
author: kaka (卡力的专属小机器人)
license: MIT
metadata:
  hermes:
    tags: [network, troubleshooting, connectivity, firewall, proxy, debugging]
    related_skills: [systematic-debugging, systemd-service-troubleshooting]
---

# Network Connectivity Troubleshooting

## Overview

Network issues can be tricky - timeouts, partial connectivity, or region-based restrictions. This skill provides a systematic approach to diagnose network problems quickly.

## When to Use

Use when you encounter:
- Website access timeouts
- git clone failures
- download timeouts
- Partial connectivity (some sites work, others don't)
- Browser tool timeouts
- Any network-related operation that fails mysteriously

**Use this BEFORE:**
- Assuming the problem is "just the network"
- Trying workarounds without diagnosis
- Asking the user to "check their internet"

## Troubleshooting Flow

### Phase 1: Establish Baseline Connectivity

**Start with the simplest tests first:**

```bash
# Test basic IP connectivity
ping -c 3 8.8.8.8

# Test DNS resolution
nslookup github.com
# OR
dig github.com
```

**What to check:**
- If ping fails → fundamental network issue
- If ping works but DNS fails → DNS configuration issue
- If both work → move to Phase 2

### Phase 2: Test HTTP/HTTPS Connectivity

**Test with curl (HEAD first, then full GET):**

```bash
# First test just headers (fast)
curl -I --connect-timeout 10 https://github.com

# If that works, try actual content
curl --max-time 30 -L https://github.com | head -50
```

**Key patterns to look for:**
- HEAD works but GET fails → QoS/rate limiting
- Some sites work, others don't → regional restrictions
- All HTTPS fails → SSL/proxy issue
- All HTTP fails but ping works → firewall issue

### Phase 3: Test Regional/Domestic vs International

**Test both domestic and international sites:**

```bash
# Test international sites
curl -I --connect-timeout 10 https://github.com
curl -I --connect-timeout 10 https://google.com

# Test domestic sites (China example)
curl -I --connect-timeout 10 https://gitee.com
curl -I --connect-timeout 10 https://baidu.com

# Try actual content download
curl --max-time 30 -L https://gitee.com/explore | head -100
```

**Common patterns:**
- Only domestic works → Great Firewall or corporate regional restriction
- Only international works → DNS or routing issue to domestic
- Some of each → CDN/geolocation issue

### Phase 4: Check Proxy/Environment Configuration

```bash
# Check proxy env vars
env | grep -i proxy

# Check git proxy
git config --global --get http.proxy
git config --global --get https.proxy

# Check system-wide config
cat /etc/environment | grep -i proxy
```

### Phase 5: Check System Network Config

```bash
# Check DNS config
cat /etc/resolv.conf

# Check hosts file
cat /etc/hosts

# Check network interfaces
ip addr show
# OR
ifconfig
```

## Common Scenarios & Solutions

### Scenario 1: Can't Access GitHub but Can Access Gitee

**Symptoms:**
- `ping 8.8.8.8` works
- `curl -I https://gitee.com` works and can download content
- `curl https://github.com` times out with 0 bytes received
- `git clone` from GitHub fails

**Diagnosis:** Regional network restriction (China environment)

**Solutions:**
1. Use Gitee mirrors if available
2. Configure proxy/VPN
3. Manual file uploads

### Scenario 2: Browser Tool Times Out But curl Works

**Symptoms:**
- `browser_navigate` times out
- `curl` commands work fine
- ping works

**Diagnosis:** Browser tool sandbox/network configuration issue

**Solutions:**
- Use curl/web_extract as alternative
- Check browser tool proxy settings

### Scenario 3: HEAD Works But GET Fails

**Symptoms:**
- `curl -I` succeeds
- `curl` (full GET) times out after 0 bytes

**Diagnosis:** QoS, rate limiting, or deep packet inspection

**Solutions:**
- Try with `--limit-rate` to slow down
- Try different User-Agent
- Use alternative endpoints

### Scenario 4: Clash Proxy Running but Proxy Node Unreachable

**Symptoms:**
- `systemctl status clash.service` shows active (running)
- Direct connection to target site times out
- Connection through proxy also times out with `SSL_ERROR_SYSCALL`
- Proxy node IP responds to ping (ICMP works)
- `nc -zv <ip> <port>` times out connecting to proxy port

**Diagnosis:** Clash service is running, but the configured proxy endpoint node has failed / is offline / port is closed. Proxy node is still in the config but is no longer functional.

**Solutions:**
1. Confirm the failure with ping + nc test:
   ```bash
   ping -c 2 <proxy-ip>          # IP is reachable (ICMP works)
   nc -zv <proxy-ip> <port>       # but port times out → node is dead
   ```
2. Notify the user that the configured proxy node has failed and needs to be updated
3. If urgent and other nodes available in config, switch to another working node

### Scenario 5: Ping/TLS Works but Login/CDN Site Behaves Differently by Method or User-Agent

**Symptoms:**
- `ping <host>` succeeds and DNS resolves normally.
- `openssl s_client -connect <host>:443 -servername <host> -brief` shows TLS handshake and certificate verification are OK.
- `curl -I https://<host>/...` or browser automation fails, times out, or returns `ERR_CONNECTION_CLOSED` / `SSL_ERROR_SYSCALL`.
- A full `GET` with a realistic browser User-Agent may return `200 OK`, while `HEAD` still hangs or receives no bytes.
- Response headers may expose CDN/WAF hints such as request source IP, trace IDs, `x-need-token`, anti-bot cookies, or CDN timing headers.

**Diagnosis:** This is not a basic network outage. It is usually application-layer/CDN/WAF behavior, method filtering, anti-bot handling, or source-IP reputation/rate limiting. HEAD requests can be misleading for login/CDN pages.

**Tests:**
```bash
HOST=example.com
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36'
openssl s_client -connect ${HOST}:443 -servername ${HOST} -brief </dev/null
curl -vI --connect-timeout 8 --max-time 15 https://${HOST}/
curl -vL --connect-timeout 8 --max-time 20 -A "$UA" https://${HOST}/ -o /tmp/site_get.html
getent ahosts ${HOST}
# If multiple CDN IPs exist, test carefully with --resolve and preserve SNI/Host.
```

**Solutions:**
1. Stop repeated login/OTP/browser attempts if WAF or source-IP reputation is suspected; repeated attempts can worsen throttling.
2. Prefer realistic browser `GET` checks over `HEAD` for login pages and SPAs.
3. Compare console/main domain vs signin/auth domain; one may work while the other is selectively filtered.
4. If the Linux/server IP appears rate-limited, switch to a trusted desktop/browser environment or a different approved network rather than brute-forcing retries.

### Scenario 6: Clash Proxy Works for Domestic, Fails for GitHub (SSL_ERROR_SYSCALL)

**Symptoms:**
- Clash is running, ports 10808/9090 are listening
- Domestic sites work through proxy (baidu, gitee, etc.)
- GitHub specifically fails with `SSL_ERROR_SYSCALL` during TLS handshake
- Proxy nodes show as "alive" in controller but actual connection fails

**Diagnosis:** Clash nodes are dead upstream or blocked. "Alive" status in controller is not reliable for actual connectivity. The proxy service is running but nodes cannot reach GitHub/upstream.

**Solutions:**
1. **Do NOT spend time debugging Clash internals** - switch to content CDN mirrors
2. For npm CLI binaries: use `https://registry.npmmirror.com/-/binary/<package>/...`
3. For GitHub content: try jsDelivr, npmmirror, or Gitee mirrors
4. Ask user to update subscription only if absolutely required for the task

**This is the #1 most common network scenario on this Hermes server. Prefer CDN workarounds over proxy fixes.**

**Symptoms:**
- `ping <host>` succeeds and DNS resolves normally.
- `openssl s_client -connect <host>:443 -servername <host> -brief` shows TLS handshake and certificate verification are OK.
- `curl -I https://<host>/...` or browser automation fails, times out, or returns `ERR_CONNECTION_CLOSED` / `SSL_ERROR_SYSCALL`.
- A full `GET` with a realistic browser User-Agent may return `200 OK`, while `HEAD` still hangs or receives no bytes.
- Response headers may expose CDN/WAF hints such as request source IP, trace IDs, `x-need-token`, anti-bot cookies, or CDN timing headers.

**Diagnosis:** This is not a basic network outage. It is usually application-layer/CDN/WAF behavior, method filtering, anti-bot handling, or source-IP reputation/rate limiting. HEAD requests can be misleading for login/CDN pages.

**Tests:**
```bash
HOST=example.com
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36'
openssl s_client -connect ${HOST}:443 -servername ${HOST} -brief </dev/null
curl -vI --connect-timeout 8 --max-time 15 https://${HOST}/
curl -vL --connect-timeout 8 --max-time 20 -A "$UA" https://${HOST}/ -o /tmp/site_get.html
getent ahosts ${HOST}
# If multiple CDN IPs exist, test carefully with --resolve and preserve SNI/Host.
```

**Solutions:**
1. Stop repeated login/OTP/browser attempts if WAF or source-IP reputation is suspected; repeated attempts can worsen throttling.
2. Prefer realistic browser `GET` checks over `HEAD` for login pages and SPAs.
3. Compare console/main domain vs signin/auth domain; one may work while the other is selectively filtered.
4. If the Linux/server IP appears rate-limited, switch to a trusted desktop/browser environment or a different approved network rather than brute-forcing retries.

## Verification Checklist

Before concluding diagnosis, verify:
- [ ] Baseline ping works
- [ ] DNS resolution works
- [ ] Tested both domestic AND international sites
- [ ] Tested both HEAD AND GET requests
- [ ] Checked proxy/environment configuration
- [ ] Checked system network files
- [ ] Can explain the pattern clearly

## Tools to Use

**Hermes tools:**
- `terminal` - for all network commands
- `read_file` - for checking config files
- `todo` - for organizing troubleshooting steps
- `memory` - for recording findings for future reference

## Pitfalls to Avoid

❌ Don't assume it's "just network" without diagnosis  
❌ Don't skip testing domestic vs international  
❌ Don't only test HEAD without trying GET  
❌ Don't forget to record findings in memory for future reference  
❌ Don't propose workarounds before completing diagnosis  

## Example Workflow Template

```python
todo([
    {"content": "Test baseline connectivity (ping, DNS)", "id": "1", "status": "in_progress"},
    {"content": "Test HTTP/HTTPS (HEAD then GET)", "id": "2", "status": "pending"},
    {"content": "Test domestic vs international sites", "id": "3", "status": "pending"},
    {"content": "Check proxy/environment config", "id": "4", "status": "pending"},
    {"content": "Analyze and document findings", "id": "5", "status": "pending"}
])
```

## Memory Recording Pattern

After completing diagnosis, ALWAYS record findings:

```
[DATE] Network troubleshooting result: [summary of findings]. [Implications for future work].
```

**Good example:**
> 2026-05-07 Network troubleshooting result: Current environment can only access domestic websites (Gitee works), cannot access international websites (GitHub, Google, etc. fail to transfer any data). This is network policy restriction, requires proxy/VPN for international access. Cannot install from GitHub, but can try Gitee mirrors.
