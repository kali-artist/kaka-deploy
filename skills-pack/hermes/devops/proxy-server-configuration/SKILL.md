---
name: proxy-server-configuration
trigger: When configuring proxy servers, setting up VPN clients, or working in network-restricted environments
description: Configure proxy servers, set up VPN clients (Clash, v2ray, etc.), and handle network-restricted environments
version: 1.0.0
author: kaka (卡力的专属小机器人)
license: MIT
metadata:
  hermes:
    tags: [proxy, vpn, clash, v2ray, network, firewall, gfw]
    related_skills: [network-connectivity-troubleshooting]
---

# Proxy Server Configuration

## Overview

When working in network-restricted environments (such as behind firewalls or regional restrictions), you need to configure proxies to access external resources. This skill provides a systematic approach to setting up proxy servers and clients.

## When to Use

Use when you encounter:
- Regional network restrictions (can't access GitHub, Google, etc.)
- Need to configure Clash/v2ray/xray or other proxy clients
- Have proxy subscription URLs but need to set up the client
- Network diagnosis confirms restrictions and you need to implement a solution
- Need to download tools but can't access GitHub directly

**Use this AFTER:**
- Using network-connectivity-troubleshooting to diagnose the issue
- Confirming it's a regional/restriction problem that needs a proxy solution

## Proxy Configuration Workflow

### Phase 1: Gather Proxy Information

First, collect all necessary proxy details:

```bash
# If you have a subscription URL
curl -L "SUBSCRIPTION_URL" -o config.yaml
cat config.yaml  # Review what you got
```

**Key things to note from config:**
- Proxy server addresses and ports
- Protocol type (vmess, ss, trojan, etc.)
- Available proxy groups and rules
- Any special configuration (TLS, websocket, etc.)

### Phase 2: Verify Proxy Server Connectivity

Before installing any clients, verify you can reach the proxy servers:

```bash
# Test with nc (netcat)
nc -zv proxy-host.com port

# Or test with telnet
telnet proxy-host.com port

# Or test with Python
python3 -c "import socket; s = socket.socket(); s.settimeout(5); print('✅ Connected' if s.connect_ex(('host', port)) == 0 else '❌ Failed'); s.close()"
```

**What to check:**
- If connection fails → proxy server may be down or blocked
- If connection succeeds → move to client installation

### Phase 3: Install Proxy Client (The Challenge Phase)

In restricted environments, you often can't download clients from GitHub directly. Try these approaches in order:

#### Approach A: Use Mirror Sites

```bash
# Try GitHub mirror sites
# Common mirrors:
# - https://ghproxy.com/
# - https://mirror.ghproxy.com/
# - https://gh.api.99988866.xyz/
# - https://hub.gitmirror.com/

# Example:
wget -O clash.gz https://ghproxy.com/https://github.com/Dreamacro/clash/releases/download/v1.18.0/clash-linux-amd64-v1.18.0.gz
```

#### Approach B: Use Domestic Hosting (Gitee, etc.)

```bash
# Check if project is mirrored on Gitee
# Search for project on https://gitee.com/

# Example for Clash alternatives:
# Look for "clash" on Gitee
```

#### Approach C: Manual Installation

If downloads fail completely:
1. Ask user to download the client locally
2. User uploads to server via scp/sftp/other means
3. Continue with configuration

#### Approach D: Use Alternative Clients

Consider lighter-weight alternatives:
- v2ray/xray (often easier to find mirrors)
- sing-box (modern alternative)
- shadowsocks-libev (simpler)

#### Approach E: Extract from GUI Packages

If user provides GUI packages (like lray, clashmi, Clash Verge, etc.):
- .deb/.rpm/AppImage packages often contain core service binaries
- Extract and look for backend/service executables

**For .deb packages:**
```bash
# Extract using ar and tar
mkdir -p extract && cd extract
ar x ../package.deb
tar -xf data.tar.xz  # or data.tar.gz
# Look for binaries in usr/bin/ or opt/
```

**For .rpm packages:**
```bash
mkdir -p extract && cd extract
rpm2cpio ../package.rpm | cpio -idmv
# Look for binaries in usr/bin/ or opt/
```

**For AppImage packages:**
```bash
chmod +x package.AppImage
./package.AppImage --appimage-extract
# Look in squashfs-root/usr/bin/ for core binaries like clash, clash-meta, etc.
```

**What to look for:**
- Files like `clash`, `clash-meta`, `*service`, `*backend`, or the core proxy binary itself
- These are often in usr/bin/ inside the extracted package
- This approach is extremely effective when user has GUI packages already downloaded!

### Phase 4: Configure and Start the Client

Once client is installed:

**Option A: Use the full config (if rule-providers are accessible)**
```bash
# For Clash:
mkdir -p ~/.clash
mv config.yaml ~/.clash/config.yaml
chmod +x ./clash

# Start in background
./clash -d ~/.clash &
```

**Option B: Use a simplified config first (for quick testing)**
If the original config has remote rule-providers that can't be downloaded yet, create a minimal config first:
```yaml
mode: rule
mixed-port: 10808
log-level: info
external-controller: '0.0.0.0:9090'

proxies:
  # Copy the first working proxy from your original config
  - name: "Proxy"
    type: vmess
    server: proxy-host.com
    port: 12345
    # ... rest of the proxy config ...

proxy-groups:
  - name: "🚀 Proxy"
    type: select
    proxies:
      - "Proxy"

rules:
  - MATCH,🚀 Proxy
```
This minimal config avoids needing to download rule-providers and gets you up and running quickly!

**Verify it's working:**
```bash
# Check ports (Clash default: 7890 for mixed, 9090 for API)
ss -tlnp | grep -E '7890|10808|9090'

# Test with curl through proxy
curl -x http://127.0.0.1:10808 -I --max-time 20 https://github.com
```

#### Updating an existing Clash/Mihomo subscription on a systemd service

When a Clash/Mihomo service is already installed and only the subscription changes:

```bash
# 1) Inspect current service, ports, and config path
ps -ef | egrep -i 'clash|mihomo' | grep -v egrep || true
systemctl status clash.service --no-pager
ss -tlnp | egrep ':(7890|10808|9090|1053)' || true

# 2) Download subscription with TLS fallback if needed
mkdir -p ~/.clash/subscriptions
curl -k -L --connect-timeout 15 --max-time 60 'SUBSCRIPTION_URL' -o ~/.clash/subscriptions/latest.yaml

# 3) Preserve the existing local service contract
# If the service currently exposes mixed-port 10808 and controller 9090, rewrite the new subscription to keep those ports,
# allow-lan/bind-address if previously required, and optional DNS listen 1053. Do not blindly accept subscription defaults.
cp ~/.clash/config-simple.yaml ~/.clash/config-simple.yaml.bak.$(date +%Y%m%d-%H%M%S)
# Use a YAML-aware script/editor to set: mixed-port, allow-lan, bind-address, external-controller, mode, log-level.

# 4) Validate before restart, then restart
~/.clash/clash-meta -t -d ~/.clash -f ~/.clash/config-simple.yaml
sudo systemctl restart clash.service
systemctl is-active clash.service
```

**Node-level verification (important):**
- Clash controller may show nodes as `alive:true` even when the upstream TCP route times out; always test real traffic.
- Test each node by switching the selector via the controller API, then curl through the mixed port:

```bash
# Example selector switch; URL-encode group/name in scripts for non-ASCII names
curl -X PUT http://127.0.0.1:9090/proxies/PROXY \
  -H 'Content-Type: application/json' \
  -d '{"name":"NODE_NAME"}'

curl -x http://127.0.0.1:10808 -I --max-time 10 https://www.gstatic.com/generate_204
```

If every node times out, also test raw TCP reachability to the subscription server/ports (Python socket or nc). If raw TCP times out for all subscription ports, report clearly that the config/service is applied but the upstream nodes are unreachable from this server/provider network.

### Phase 5: Set Up Environment Variables

Configure the system to use the proxy:

```bash
# Set temporary proxy (current session)
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7890

# Or for Clash mixed port (usually 7890 or 10808)
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

# Verify
env | grep -i proxy

# Test
curl -I https://github.com  # Should now work!
```

## Common Scenarios & Solutions

### Scenario 0: Clash Running But GitHub Fails (SSL Handshake)

**Symptoms:**
- Clash service is running, ports are listening
- `curl -x http://127.0.0.1:10808 -I https://baidu.com` works (domestic sites)
- `curl -x http://127.0.0.1:10808 -I https://github.com` fails with `SSL_ERROR_SYSCALL`
- Proxy configuration appears correct, but GitHub specifically has TLS handshake issues

**Diagnosis:** Clash node has upstream connectivity issues, or nodes are down but still appear in config. Clash controller may show nodes as alive.

**Solutions:**
1. Test each node individually via controller API (nodes marked alive may still timeout on real traffic)
2. Switch to a different provider or fresh subscription
3. **Fallback:** Use domestic npm mirrors and GitHub content CDNs (see below) instead of fixing proxy

**GitHub content CDNs that work even when proxy/GitHub fails:**
- `https://registry.npmmirror.com/-/binary/<package>/...` - npm binaries
- `https://gh.api.99988866.xyz/https://github.com/...` - GitHub proxy (may not work anymore)
- `https://cdn.jsdelivr.net/gh/<owner>/<repo>@<tag>/...` - jsDelivr GitHub CDN (for small files)

**Most reliable workaround today:** npmmirror / binary endpoint bypasses proxy entirely.

**Symptoms:**
- Successfully downloaded proxy config from subscription
- Can connect to proxy servers (nc test passes)
- Can't download client from GitHub (times out)

**Solutions:**
1. Try multiple GitHub mirrors in sequence
2. Ask user to upload client manually
3. Try alternative clients that might be easier to source
4. Look for pre-installed options on the server

### Scenario 2: Client Installed But Not Working

**Symptoms:**
- Client is running
- Ports are listening
- But connections still don't go through

**Troubleshooting:**
- Check client logs for errors
- Verify config file is correctly loaded
- Test different proxy nodes in the config
- Check for port conflicts

### Scenario 3: Working But Needs to Be Persistent

**Symptoms:**
- Proxy works when manually started
- But stops after reboot or session ends

**Solutions:**
1. Create systemd service
2. Add to crontab @reboot
3. Set environment variables in ~/.bashrc or ~/.profile

## Client-Specific Configuration

### Clash Configuration

**Config file location:** `~/.clash/config.yaml`
**Default ports:**
- Mixed proxy: 7890 (or 10808 in some configs)
- Web UI/API: 9090
- DNS: 53 or 1053

**Quick start:**
```bash
cd ~/.clash
./clash &  # Start in background
```

### v2ray/xray Configuration

**Config format:** JSON
**Typical ports:** 1080 (socks), 8080 (http)

## Verification Checklist

Before declaring success:
- [ ] Proxy subscription/config downloaded and verified
- [ ] Proxy server connectivity confirmed (nc/telnet test)
- [ ] Client software installed (or plan for manual upload)
- [ ] Client configured and running
- [ ] Ports are listening and accessible
- [ ] Environment variables set
- [ ] Tested through proxy (curl to previously blocked site)
- [ ] Considered persistence (auto-start on reboot)

## Tools & Clients

**Common proxy clients:**
- Clash (most popular, rule-based)
- v2ray/xray (flexible, multiple protocols)
- sing-box (modern, all-in-one)
- shadowsocks (simpler, single protocol)

**Useful Hermes tools:**
- `terminal` - for all installation and testing
- `write_file` - for creating configs and scripts
- `read_file` - for reviewing config files
- `process` - for managing background proxy processes
- `todo` - for organizing the setup steps

## Pitfalls to Avoid

❌ Don't skip proxy server connectivity test before installing client  \n❌ Don't only try one mirror - have multiple backups ready  \n❌ Don't forget to test the proxy after setup  \n❌ Don't leave the user without persistence (auto-start)  \n❌ Don't forget to document what was done (use memory!)  \n❌ Don't assume the user knows how to upload files - give clear instructions if needed  \n

## Memory Recording Pattern

After completing proxy setup (successful or not), ALWAYS record:

```
[DATE] Proxy configuration attempt: [summary of outcome]. [What worked, what didn't]. [Key learnings for future].
```

**Good example:**
> 2026-05-07 Proxy configuration: Successfully downloaded Clash config from subscription and verified proxy server connectivity. However, unable to download Clash client from GitHub or mirrors due to network restrictions. Documented manual upload approach for user.
