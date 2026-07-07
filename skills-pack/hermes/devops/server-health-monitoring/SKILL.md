---
name: server-health-monitoring
trigger: When performing server health checks, setting up automated monitoring, connecting to remote servers (SSH/RDP), or doing system administration tasks
description: Comprehensive server health monitoring, automated reporting, and remote server administration
version: 1.0.0
author: kaka (卡力的专属小机器人)
license: MIT
metadata:
  hermes:
    tags: [server, monitoring, health-check, remote-admin, ssh, rdp, winrm, windows-admin, cron, reporting]
    related_skills: [network-connectivity-troubleshooting, systemd-service-troubleshooting, proxy-server-configuration]
---

# Server Health Monitoring & Remote Administration

## Overview

This skill provides standardized procedures for:
1. Comprehensive server health checks (CPU, memory, disk, load, network)
2. Setting up automated monitoring reports via cron
3. Remote server connection management (SSH for Linux, RDP for Windows)
4. Gateway/service process monitoring

## When to Use

Use this skill when:
- User asks for server status or health check
- Setting up daily/periodic server monitoring reports
- Connecting to remote servers (Linux via SSH, Windows via RDP)
- Monitoring multiple gateway processes
- Diagnosing server performance issues

**Use this BEFORE:**
- Running random diagnostic commands
- Creating manual monitoring scripts
- Assuming server is "healthy" without metrics

## Comprehensive Health Check Template

Always include these metrics in a health check report:

```markdown
# 📊 Server Health Report
**📅 Check Time:** {datetime}
**📍 Server:** {hostname/IP}

---

## 🧠 Memory Status
- **Total:** {total} GiB
- **Used:** {used} GiB ({percent}%)
- **Available:** {available} GiB
- **Swap Usage:** {swap_used} MiB

## 💾 Disk Status
| Mount | Total | Used | Available | Usage % | Status |
|-------|-------|------|-----------|---------|--------|
| /     |       |      |           |         | ✅/⚠️/❌ |

## ⚡ CPU Status
- **Cores:** {cores} vCPU
- **Load Average (1/5/15 min):** {load1}, {load5}, {load15}
- **Current Usage:** {cpu_usage}%

## 📈 System Uptime
- **Uptime:** {uptime}
- **Process Count:** {processes}

## 🔧 Gateway/Service Status
| Service | Status | PID | Connection |
|---------|--------|-----|------------|
| default | running/stopped | N/A | ✅/❌ |
| tiao    | running/stopped | N/A | ✅/❌ |
| hang    | running/stopped | N/A | ✅/❌ |

## 🌐 Network Status
- **Public IP:** {ip}
- **Internet Connectivity:** ✅/❌
- **Ping Latency:** {latency} ms

---

## 🎯 Overall Status: ✅ Healthy / ⚠️ Warning / ❌ Critical
```

## Automated Cron Reporting Setup

### Pattern for Daily Reports:

```bash
# Create report script in ~/.hermes/scripts/daily_check.py
# Then create cron job:
hermes cron create --name "服务器每日巡检报告" \
  --deliver origin \
  "0 0 * * *" \
  "Generate comprehensive server health report including memory, disk, CPU, load, and gateway statuses. Format with emojis for readability."
```

### Key Cron Parameters:
- `--deliver origin`: Deliver to the user's primary chat
- `--repeat forever`: For recurring reports
- Schedule format: `0 0 * * *` = daily at midnight

## Remote Server Administration

### Linux (SSH)

**Check connection capability first:**
```bash
# Check SSH client
which ssh

# Test connectivity before adding credentials
ping -c 3 {server_ip}
nc -zv -w 3 {server_ip} 22  # Test SSH port

# Verify keys exist (optional)
ls -la ~/.ssh/
```

**Connection Checklist:**
- [ ] Server IP address
- [ ] SSH port (default: 22)
- [ ] Username (root, ubuntu, etc.)
- [ ] Auth method: Password or SSH key
- [ ] Network connectivity verified

### Windows (RDP)

**Prerequisites:**
```bash
# Install RDP client
sudo apt-get install -y freerdp2-x11

# Verify installation
which xfreerdp
```

**Connection Checklist:**
- [ ] Server IP address
- [ ] RDP port (default: 3389)
- [ ] Username (typically Administrator)
- [ ] Password
- [ ] Test port connectivity: `nc -zv {ip} 3389`

**Test connection (auth-only mode):**
```bash
xfreerdp /v:{ip} /u:{user} /p:{password} /cert:tofu /cert-ignore +auth-only
```

**Note:** Headless servers cannot display RDP GUI, but authentication and port testing work. For command execution on Windows, enable WinRM.

### Windows (WinRM Remote Command Execution)

WinRM (Windows Remote Management) allows executing PowerShell commands remotely from Linux, without needing a GUI.

**Step 1: Install required tools on Linux**

Choose ONE of these options (pywinrm is recommended for programmatic use):

**Option A: pywinrm (Recommended for Python scripts)**
```bash
# IMPORTANT: Install to SYSTEM Python, not hermes venv!
# Hermes runs in a virtualenv that doesn't have pip
/usr/bin/python3 -m pip install pywinrm --break-system-packages

# Verify installation
/usr/bin/python3 -c "import winrm; print('pywinrm ready')"
```

**Option B: impacket (CLI-based)**
```bash
pip install impacket
# Find wmiexec.py location:
find /usr -name 'wmiexec.py' 2>/dev/null
```

**Option C: xfreerdp for auth testing**
```bash
which xfreerdp
```

**⚠️ CRITICAL: Python Environment Pitfall**

Hermes executes scripts inside a virtual environment at `/home/ubuntu/.hermes/hermes-agent/venv/` that:
1. Does NOT have `pip` installed
2. Does NOT share packages with system Python

**Always use explicit system Python path for WinRM:**
```bash
# ❌ BAD (fails in hermes venv):
python3 your_script.py

# ✅ GOOD (works reliably):
/usr/bin/python3 your_script.py
```

**Step 2: Configure WinRM on Windows Server (Manual Setup)**

First RDP into the Windows server, then open PowerShell as Administrator and run:

```powershell
# 1. Enable WinRM service
Enable-PSRemoting -Force

# 2. Set WinRM to start automatically
Set-Service WinRM -StartupType Automatic

# 3. Configure firewall to allow WinRM
Enable-NetFirewallRule -Name "WINRM-HTTP-In-TCP"

# 4. Allow unencrypted transport (for testing - disable in production!)
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# 5. Allow basic authentication
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true

# 6. Restart WinRM to apply changes
Restart-Service WinRM

# 7. Verify configuration
Test-WSMan localhost
```

**Step 3: Verify WinRM ports are open from Linux**
```bash
# WinRM HTTP = port 5985, WinRM HTTPS = port 5986
nc -zv -w 3 {windows_ip} 5985
nc -zv -w 3 {windows_ip} 5986
```

**Step 4: Execute commands remotely**

**Option A: pywinrm (Recommended for automation)**

```python
#!/usr/bin/python3
import winrm

# Connect using NTLM transport (most reliable for Windows)
s = winrm.Session(
    'http://{windows_ip}:5985/wsman',
    auth=('{username}', '{password}'),
    transport='ntlm'
)

# Execute CMD command
result = s.run_cmd('hostname')
hostname = result.std_out.decode('gbk', errors='ignore').strip()
print(f"Hostname: {hostname}")

# Execute PowerShell command
result = s.run_ps('Get-Service WinRM')
output = result.std_out.decode('gbk', errors='ignore')
print(output)

# Launch browser (visible on the Windows desktop)
result = s.run_ps("Start-Process 'msedge.exe' -ArgumentList 'https://baidu.com'")
# or Chrome:
result = s.run_ps("Start-Process 'chrome.exe' -ArgumentList 'https://baidu.com', '--start-maximized'")
```

**⚠️ IMPORTANT: Windows Output Encoding**

Windows command output uses GBK encoding, not UTF-8. Always decode with error handling:
```python
# ❌ Fails on Chinese characters
output = result.std_out.decode('utf-8')

# ✅ Works reliably with Chinese Windows
output = result.std_out.decode('gbk', errors='ignore')
```

**Option B: impacket (CLI execution)**
```bash
# Basic command execution
python /path/to/wmiexec.py {username}:{password}@{ip} "powershell -Command \"Invoke-WebRequest -Uri 'https://baidu.com' -UseBasicParsing\""

# Get system information
python /path/to/wmiexec.py {username}:{password}@{ip} "systeminfo"

# Open browser to a URL (interactive session only)
python /path/to/wmiexec.py {username}:{password}@{ip} "start msedge.exe https://baidu.com"
```

**WinRM Troubleshooting Checklist:**
- [ ] Port 5985/5986 open? Test with `nc -zv`
- [ ] WinRM service running on Windows? `Get-Service WinRM`
- [ ] Firewall rule enabled on Windows? `Get-NetFirewallRule -Name *WINRM*`
- [ ] Basic auth enabled? `Get-Item WSMan:\localhost\Service\Auth\Basic`
- [ ] Unencrypted allowed? `Get-Item WSMan:\localhost\Service\AllowUnencrypted`
- [ ] Credentials correct (username without domain prefix)
- [ ] **pywinrm installed to SYSTEM Python, not hermes venv!**
- [ ] **Using `/usr/bin/python3` explicitly, not just `python3`**
- [ ] **Output decoded with GBK encoding, not UTF-8**

**Common pywinrm Errors & Fixes:**

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'winrm'` | Package installed in wrong Python | Install with `/usr/bin/python3 -m pip install pywinrm` |
| `HTTP 401 Unauthorized` | Auth misconfiguration | Verify basic auth enabled + credentials correct |
| Garbled text output | Encoding mismatch | Use `.decode('gbk', errors='ignore')` |
| Connection timeout | Firewall/network | Verify port 5985 is open from both sides |

---

## ⚠️ CRITICAL: Windows Session Isolation (The "Invisible Program" Problem)

This is the single most common gotcha when first working with WinRM.

**The Problem:** Programs you launch via WinRM run in **Session 0** (the background service session), which is COMPLETELY ISOLATED from the interactive desktop that the user sees via RDP.

So this happens:
1. You run: `s.run_ps("Start-Process 'chrome.exe' 'https://baidu.com'")`
2. ✅ Chrome process STARTS (you can see it via `tasklist`)
3. ❌ But the user sees NOTHING on their RDP desktop
4. User asks: "Why didn't it open?" - You are confused because the command succeeded

**This is NOT a bug - this is Windows security design.**

---

## The Solution: PsExec for Interactive Desktop Execution

To run a program that the user can SEE on their desktop, you need to use **PsExec** from Sysinternals to launch the program in the correct session ID.

### Step 1: Find the Active Session ID

First, determine which session the user is actually logged into:

```python
import winrm
s = winrm.Session('http://{ip}:5985/wsman', auth=('{user}', '{pass}'), transport='ntlm')

r = s.run_cmd('query session')
print(r.std_out.decode('gbk', errors='ignore'))
```

**Typical output:**
```
 SESSIONNAME       USERNAME                 ID  STATE   TYPE        DEVICE 
>services                                    0  Disc                        
 console           Administrator             1  Active                      
 rdp-tcp                                 65536  Listen
```

Look for the row with **`Active`** state - the ID column shows the session number. In this example, the user is on **Session 1**.

### Step 2: Download PsExec to the Windows Server

```python
ps_cmd = '''
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://live.sysinternals.com/PsExec.exe" -OutFile "$env:TEMP\PsExec.exe"
'''
s.run_ps(ps_cmd)
```

PsExec is a single EXE, no installation needed.

### Step 3: Launch Program in the User's Session

Now launch the program using PsExec with `-i {session_id}`:

```python
# Launch Chrome on Session 1 (user's interactive desktop)
s.run_cmd(r'%TEMP%\PsExec.exe -accepteula -i 1 -d "C:\Program Files\Google\Chrome\Application\chrome.exe" "https://www.baidu.com"')
```

**Parameters explained:**
- `-accepteula`: Auto-accept the EULA (required on first run)
- `-i 1`: Run in Session 1 (interactive desktop)
- `-d`: Don't wait for program to exit (return immediately)

✅ **Now the user will SEE the browser open on their desktop!**

### Step 4: Verify Sessions Available

Use this to always get the active session dynamically:

```python
def get_active_session(s):
    """Return the active console/rdp session ID"""
    r = s.run_cmd('query session')
    output = r.std_out.decode('gbk', errors='ignore')
    
    for line in output.split('\n'):
        if 'Active' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part.isdigit() and i > 0:
                    return int(part)
    return 1  # Default fallback
```

### Session ID Reference Table

| Session ID | Purpose | Visible to User? |
|------------|---------|------------------|
| 0 | Services, WinRM commands | ❌ NEVER visible |
| 1 | Console / First RDP session | ✅ Usually visible |
| 2+ | Additional RDP sessions | ✅ If that's where user is |
| 65536 | RDP listener (not an actual session) | ❌ |

---

## Important: GUI Automation Limitations (What We Learned the Hard Way)

**Critical Reality:** You CANNOT simulate button clicks, keyboard input, or GUI interactions on remotely-launched programs from a WinRM session. **This is not a bug - it is intentional Windows security design.**

**Why it fails:** Even when you use PsExec to launch a program in Session 1, any automation script (PowerShell SendKeys, pyautogui, etc.) that you run via WinRM still executes in Session 0 context. Windows security prevents Session 0 processes from sending input to Session 1 processes.

**What ACTUALLY WORKS remotely via WinRM (verified):**
- ✅ Launch a program visible to the user (using PsExec -i)
- ✅ Kill processes
- ✅ Run silent/quiet installers (no GUI interaction needed)
- ✅ Execute command-line tools and PowerShell scripts
- ✅ Take screenshots (if session is active)
- ✅ File operations (copy, move, delete)
- ✅ Service management (start, stop, configure)

**What DEFINITELY DOESN'T WORK remotely:**
- ❌ Simulate clicking buttons on a GUI installer
- ❌ Send keystrokes to a visible application
- ❌ Automate wizard-based installations from WinRM
- ❌ pyautogui or similar GUI automation libraries from WinRM
- ❌ PowerShell SendKeys from WinRM (fails silently or triggers in Session 0 only)

**Practical Solution For User:** For GUI-based installers that cannot be silenced:
1. First try documented silent installation parameters
2. If silent install fails: launch the installer visible to the user using `PsExec -i {session_id} -d installer.exe`
3. Tell the user the installer is visible on the remote desktop and requires manual interaction
4. Verify completion by checking installed files/services/registry entries

---

## Software Installation on Windows Remotely

### Silent Installation is the Only Reliable Remote Method

Most Windows installers support silent/quiet modes. Always try these first:

**Common Silent Install Parameters:**
| Installer Type | Parameter |
|----------------|-----------|
| Inno Setup (most common) | `/VERYSILENT /NORESTART /SP-` |
| MSI packages | `/quiet /norestart` |
| NSIS | `/S` |
| InstallShield | `/s /v"/qn"` |

**Example: Silent install attempt**
```powershell
# Try documented silent parameters first; exact flags depend on installer technology
SomeSetup.exe /VERYSILENT /NORESTART /NOCANCEL /SP-

# If that doesn't work for a custom GUI installer:
# Launch it visible via PsExec and ask the user to complete the wizard over RDP
```

**If Silent Install Fails:**
1. Launch the installer visible to the user: `PsExec -i 1 -d installer.exe`
2. Tell the user: "The installer is now visible on your desktop, please click Install"
3. Wait and verify installation completes

---

## Software Selection for Remote Windows Servers

When users ask to install software on remote Windows servers, always prefer:

1. **CLI-first / headless versions** - Software designed for server use, no GUI required
2. **API/SDK-based solutions** - e.g., WeChatFerry instead of manual WeChat GUI
3. **Open-source automation frameworks** - Prefer mature GitHub projects over custom scripts
4. **Software with silent install support** - Avoid wizard-based installers

**Example: WeChat on Windows Servers**
- ❌ WeChat PC GUI installer: Requires manual clicks, no working silent install parameters exist, very difficult to automate
- ✅ **WeChatFerry SDK**: API-based control, Python integration, mature GitHub community (5000+ stars), designed for automation
- ⚠️ Web-based WeChat: Often blocked by Tencent for new accounts, unreliable

**WeChatFerry Installation Workflow:**
1. First install PC WeChat normally (requires user to click install via RDP)
2. Then install WeChatFerry SDK from GitHub
3. Use the Python client `wcferry` to automate WeChat programmatically

**Research Pattern:**
1. Check GitHub for CLI/SDK alternatives first
2. Look for projects with 1000+ stars and recent commits
3. Verify: "Does this run without a GUI?"
4. Verify: "Can this be installed silently?"

---

## Advanced: Remote Desktop Screenshots

Once you have interactive programs running, you can capture what the user sees:

```powershell
# PowerShell script to capture the primary screen
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$screen = [System.Windows.Forms.Screen]::PrimaryScreen
$bounds = $screen.Bounds

$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

$stream = New-Object System.IO.MemoryStream
$bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
$bytes = $stream.ToArray()
$stream.Close()
$bitmap.Dispose()
$graphics.Dispose()

[Convert]::ToBase64String($bytes)
```

Then in Python, decode the base64 data back to an image file:

```python
r = s.run_ps(ps_script)
b64_data = r.std_out.decode('utf-8').strip()
with open('/tmp/screenshot.png', 'wb') as f:
    f.write(base64.b64decode(b64_data))
```

**Note:** Screenshots only work reliably if the user has an active RDP session. Disconnected sessions may return black/blank images.

---

## The Two Modes of Operation (User Workflow Decision)

We established with the user that there are **two distinct operating modes** for Windows remote servers. **ALWAYS use the correct mode based on what the user asks for.**

| Mode | Trigger Phrase | Session Used | Purpose |
|------|---------------|--------------|---------|
| **Default / Background Mode** | Any command NOT including "show me", "display", "on my desktop", "I need to see" | Session 0 | Running scripts, installing services, background tasks, anything that doesn't need a visible GUI |
| **Show-On-Desktop Mode** | User says: "show me", "display", "on my desktop", "I need to see", "so I can see it" | User's ACTIVE RDP session (use `query session` to find ID, then `PsExec -i {id}`) | Launching programs the user needs to interact with, showing results visually, anything that needs to be visible via RDP |

**Default Rule:** Unless the user EXPLICITLY asks to see something, use **Background Mode (Session 0)**. Don't launch things on their desktop unless they ask for it.

**Example:** User says: "Install Python on the Windows server"
- ✅ Background mode: Silent install via WinRM in Session 0
- ❌ Don't: Launch the installer GUI on their desktop

**Example:** User says: "Open Chrome so I can see it"
- ✅ Desktop mode: Use `PsExec -i 1` to launch in their Session
- ❌ Don't: Launch Chrome in Session 0 where they can't see it

## Complete Workflow: "Open Chrome for the user"

When the user says: "Open Chrome on the Windows server so I can see it":

1. ✅ **First check:** Run `query session` to find the active session ID
2. ✅ **Download PsExec** if not already present
3. ✅ **Launch with PsExec -i {session_id}** not just `Start-Process`
4. ✅ **Tell user:** "Chrome should now be visible on your desktop!"

**❌ DON'T DO THIS (program invisible):**
```python
s.run_ps("Start-Process 'chrome.exe' 'https://baidu.com'")  # Session 0 = invisible!
```

**✅ DO THIS (program visible):**
```python
s.run_cmd(r'%TEMP%\PsExec.exe -accepteula -i 1 -d "C:\Program Files\Google\Chrome\Application\chrome.exe" "https://baidu.com"')  # Session 1 = visible!
```

## Gateway Monitoring Pattern

For multi-gateway setups (default, tiao, hang, etc.):

```python
import json
from pathlib import Path

profiles = [
    ("kaka (default)", ""),
    ("tiao (少佐小猫)", "tiao"),
    ("hang", "hang")
]

for name, profile in profiles:
    if profile:
        path = f"/home/ubuntu/.hermes/profiles/{profile}/gateway_state.json"
    else:
        path = "/home/ubuntu/.hermes/gateway_state.json"
    
    if Path(path).exists():
        with open(path) as f:
            data = json.load(f)
        state = data.get('gateway_state', 'unknown')
        pid = data.get('pid', 'N/A')
        weixin = data.get('platforms', {}).get('weixin', {}).get('state', 'unknown')
        print(f"✅ {name}: {state} (PID:{pid}) 微信:{weixin}")
    else:
        print(f"❌ {name}: No state file")
```

## Common Issues & Solutions

### Issue 1: Gateway shows "running" but PID is dead
**Symptoms:** gateway_state.json says "running" but process doesn't exist
**Solution:**
```bash
# Remove stale state file and restart
rm /home/ubuntu/.hermes/gateway_state.json
# OR for profiles
rm /home/ubuntu/.hermes/profiles/{name}/gateway_state.json
# Then restart gateway
```

### Issue 2: Cron job not executing
**Symptoms:** Job shows "scheduled" but never runs
**Check:**
- [ ] Lock file exists? (`/home/ubuntu/.hermes/cron/.tick.lock`)
- [ ] Gateway is running?
- [ ] Next run time is in the future?
**Solution:** Restart gateway

### Issue 3: Windows RDP fails in headless
**Symptoms:** Error "failed to open display"
**Solution:** This is expected in headless Linux. Use for:
- Port connectivity verification
- Authentication testing
- Not for GUI access (use WinRM for command execution instead)

## Large File Transfer Between Servers (Linux → Windows via WinRM)

When transferring files larger than ~10MB between servers using WinRM, direct base64-encoded command line approaches fail due to WinRM command length limits. Use these proven strategies instead.

### Strategy 1: Let the Target Server Pull It (FASTEST if Network Allows)

This is ALWAYS the first strategy to try. If the Windows server can reach the internet directly, have it download the file itself. This bypasses all WinRM transfer limits.

**Use Case:** File is available on GitHub or any HTTP server that the Windows server can reach.

```python
#!/usr/bin/python3
import winrm
import time

s = winrm.Session('http://{windows_ip}:5985/wsman', auth=('{user}', '{pass}'), transport='ntlm')

# Option A: Python-based download with automatic resume (MOST RELIABLE)
download_script = '''
import urllib.request
import os
import time

url = "https://github.com/owner/repo/releases/download/v1.0/file.exe"
output = r"C:\\Downloads\\file.exe"
max_retries = 500

def download_with_resume():
    file_size = os.path.getsize(output) if os.path.exists(output) else 0
    
    req = urllib.request.Request(url)
    if file_size > 0:
        req.add_header('Range', f'bytes={file_size}-')
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req, timeout=120)
        mode = 'ab' if file_size > 0 else 'wb'
        
        with open(output, mode) as f:
            while True:
                chunk = response.read(512*1024)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except Exception as e:
        return False

for attempt in range(max_retries):
    if download_with_resume():
        if os.path.getsize(output) > {expected_size}:
            break
    time.sleep(2)

print(f"Final: {os.path.getsize(output)} bytes")
'''

# Write and execute in background
ps_cmd = f'''
@"
{download_script}
"@ | Out-File -FilePath "C:\\Downloads\\download.py" -Encoding utf8
Start-Process python -ArgumentList "C:\\Downloads\\download.py" -WindowStyle Hidden
'''
s.run_ps(ps_cmd)

# Monitor progress periodically
while True:
    result = s.run_ps('(Get-Item "C:\\\\Downloads\\\\file.exe").Length')
    current = int(result.std_out.decode('gbk', errors='ignore').strip())
    if current >= expected_size:
        break
    time.sleep(30)
```

**Option B: PowerShell Background Download**
```python
ps_script = '''
$ProgressPreference = 'SilentlyContinue'
$url = "https://github.com/.../file.exe"
$output = "C:\\Downloads\\file.exe"
$wc = New-Object System.Net.WebClient
$wc.Headers.Add("User-Agent", "Mozilla/5.0")
Register-ObjectEvent -InputObject $wc -EventName DownloadProgressChanged -Action { } | Out-Null
$wc.DownloadFileAsync($url, $output)
# Monitor $wc.IsBusy for completion
'''
```

### Strategy 2: HTTP Bridge Transfer

When Windows cannot reach the source (e.g., file is only on the Linux server), start a temporary HTTP server on Linux and have Windows pull from it.

**Use Case:** File exists locally on the Linux server, Windows can reach Linux on some port.

```python
# Step 1: Start HTTP server in background on Linux (terminal with background=true)
# cd /tmp && python3 -m http.server 8888

# Step 2: Have Windows pull from the Linux server
ps_script = '''
$ProgressPreference = 'SilentlyContinue'
$url = "http://{linux_server_ip}:8888/file.exe"
$output = "C:\\Downloads\\file.exe"
Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
'''
s.run_ps(ps_script)
```

**⚠️ Common Issue:** Firewalls/security groups may block the HTTP port between servers. Always test port connectivity first:
```bash
nc -zv -w 3 {target_ip} {port}
```

If port is blocked, go to Strategy 3.

### Strategy 3: WinRM Chunked Transfer (SLOW BUT RELIABLE)

When all network paths are blocked except WinRM port 5985, use small base64-encoded chunks appended sequentially. This works for any size file, but is SLOW (~30KB per request).

**Use Case:** Only Strategy 1 and 2 failed. WinRM is the only open port.

```python
#!/usr/bin/python3
import winrm
import base64
import os

s = winrm.Session('http://{windows_ip}:5985/wsman', auth=('{user}', '{pass}'), transport='ntlm')

local_file = "/path/to/local/file.exe"
remote_file = "C:\\\\Downloads\\\\file.exe"
expected_size = os.path.getsize(local_file)

# Check how much is already transferred
result = s.run_ps(f'''
if (Test-Path "{remote_file}") {{
    Write-Host (Get-Item "{remote_file}").Length
}} else {{
    Write-Host 0
}}
''')
remote_size = int(result.std_out.decode('gbk', errors='ignore').strip())

print(f"Already transferred: {remote_size / 1024 / 1024:.2f} MB")

# CRITICAL: Keep chunk size VERY SMALL to avoid "command too long" errors
# 30KB raw = ~40KB base64 encoded - STILL may cause "filename or extension too long" errors
# 10KB raw = ~13KB base64 encoded = SAFE but SLOW (~1-2 MB/minute total transfer speed)
chunk_size = 10 * 1024  # Use 10KB as safe default, try 20KB for better speed if it works
total_chunks = (expected_size - remote_size + chunk_size - 1) // chunk_size

with open(local_file, 'rb') as f:
    f.seek(remote_size)
    for i in range(total_chunks):
        chunk = f.read(chunk_size)
        b64_data = base64.b64encode(chunk).decode('ascii')
        
        # Append to remote file
        ps_append = f'''
$bytes = [System.Convert]::FromBase64String("{b64_data}")
$fs = [System.IO.File]::Open("{remote_file}", [System.IO.FileMode]::Append)
$fs.Write($bytes, 0, $bytes.Length)
$fs.Close()
'''
        s.run_ps(ps_append)
        
        if (i + 1) % 50 == 0:
            progress = (remote_size + (i + 1) * chunk_size) / expected_size * 100
            print(f"Progress: {progress:.1f}%")

print("Transfer complete!")
```

### Strategy 4: Python Receiver on Windows (No Real Command Length Benefit)

This was tried and doesn't actually help with the core WinRM command length limit. The base64 data still has to pass through WinRM as a command parameter when writing the chunk temp file, so you hit the same command length limits. The only benefit is slightly faster append operation, but this is negligible compared to WinRM round-trip latency.

Use Strategy 3 directly, it's simpler and just as fast.

### Performance Comparison

| Strategy | Speed | Reliability | Prerequisites |
|----------|-------|-------------|---------------|
| **Target Pulls from GitHub** | Fast (full bandwidth) | ⭐⭐⭐⭐⭐ | Windows has internet access |
| **HTTP Bridge** | Fast (full server bandwidth) | ⭐⭐⭐⭐ | Port open between servers |
| **WinRM Chunked** | Very Slow (~0.5-1 MB/minute) | ⭐⭐⭐⭐⭐ | Only WinRM port needed |
| **Python Receiver** | ~Same as raw chunked | ⭐⭐⭐ | Python on Windows (no command length benefit) |

### Decision Tree for File Transfer

```
User asks to transfer file to Windows server?
├── Is file on GitHub/internet?
│   └── YES → Use Strategy 1 (Windows pulls directly)
│
├── Is file local to Linux server?
│   ├── Can Windows reach Linux on some port?
│   │   └── YES → Use Strategy 2 (HTTP bridge)
│   └── NO → Use Strategy 3 (WinRM chunked)
│
└── Transfer size > 100MB?
    └── Try Strategy 1 or 2 first, only fall back to 3 if blocked
```

### Monitoring Long Transfers with Cron

For slow chunked transfers or background downloads, set up a monitoring cron job:

```bash
hermes cron create --name "File Transfer Monitor" \
  --deliver origin \
  --repeat 24 \
  "every 5m" \
  "Check if file transfer to Windows server {ip} is complete. File should be > {size}MB at C:\\Downloads\\file.exe. Report progress percentage to the user. Notify immediately when complete."
```

### Real-Time Download Progress Check (Single Execution)

To check the current progress of an ongoing download or file transfer:

```python
#!/usr/bin/python3
import winrm

s = winrm.Session('http://{windows_ip}:5985/wsman', auth=('{user}', '{pass}'), transport='ntlm')

# Check file size and calculate progress
ps_script = '''
$file = Get-Item "C:\\Downloads\\{filename}" -ErrorAction SilentlyContinue
if ($file) {{
    Write-Host "FILE_EXISTS:YES"
    Write-Host "FILE_SIZE_BYTES:$($file.Length)"
    $sizeMB = [math]::Round($file.Length / 1MB, 2)
    Write-Host "FILE_SIZE_MB:$sizeMB"
    Write-Host "TARGET_SIZE_MB:{target_size_mb}"
    if ($file.Length -gt {target_size_mb}MB) {{
        Write-Host "STATUS:COMPLETE"
    }} else {{
        Write-Host "STATUS:IN_PROGRESS"
        $percent = [math]::Round(($file.Length / {target_size_mb}MB) * 100, 2)
        Write-Host "PROGRESS_PERCENT:$percent"
    }}
}} else {{
    Write-Host "FILE_EXISTS:NO"
}}
'''

result = s.run_ps(ps_script)
output = result.std_out.decode('gbk', errors='ignore')
print(output)
```

**Example output format:**
```
FILE_EXISTS:YES
FILE_SIZE_BYTES:50607997
FILE_SIZE_MB:48.26
TARGET_SIZE_MB:260
STATUS:IN_PROGRESS
PROGRESS_PERCENT:18.56
```

**Key points for progress monitoring:**
1. Always use `/usr/bin/python3` explicitly (not hermes venv)
2. Decode output with GBK encoding (not UTF-8)
3. Use expected file size from release notes/official docs as target
4. For large files (>200MB), check periodically every 5-15 minutes
5. When `STATUS:COMPLETE` is detected, notify user immediately with completion message

### Common WinRM Transfer Errors & Fixes (Verified!)

| Error | Cause | Solution |
|-------|-------|----------|
| `Bad HTTP response returned from server. Code 500` | Chunk too large, command line too long | Reduce `chunk_size` to ≤ 20KB |
| `Filename or extension too long` | Base64 data overflowing command limits | Reduce chunk size to ≤ 10KB |
| Connection timeout mid-transfer | Slow network or chunk too big | Smaller chunks + retry loop |
| Transfer is "working" but never finishes | Process was killed mid-transfer | Check `Get-Process python` and restart background download |

---

## Linux-to-Linux Server Deployment & Large File Transfer

Use this workflow when deploying agent configurations, codebases, or large datasets from one Linux server to another.

### SSH Connection Verification (New Server Setup)

First verify connectivity before attempting any transfers:

```bash
# 1. Test basic connectivity
ping -c 3 {server_ip}

# 2. Test SSH port is open
nc -zv -w 5 {server_ip} 22

# 3. Verify SSH auth works (with password - use sshpass)
sudo apt-get install -y sshpass  # First install if missing
sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{server_ip} 'echo "✅ Connection successful! Hostname: $(hostname)"'
```

### Rsync Large Directory Transfer (Linux → Linux)

For directories > 1GB, rsync is the most reliable method. Use this pattern:

```bash
# Basic rsync with progress and common exclusions
sshpass -p '{password}' rsync -avz --progress \
  --exclude='*.lock' \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='profiles/*' \       # If deploying Hermes, skip per-server profiles
  --exclude='sessions/*' \       # Skip historical chat sessions
  --rsh="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30" \
  /path/to/source/dir/ \
  root@{server_ip}:/path/to/dest/dir/
```

**Recommended Hermes Deployment Exclusions:**
| Path | Why Exclude? |
|------|-------------|
| `profiles/*` | Server-specific gateway profiles |
| `sessions/*` | Historical chat session data |
| `*.lock` files | Temporary lock files (will be recreated) |
| `gateway.pid` | Process ID files |
| `node_modules` | Can be reinstalled if needed |
| `.git` | Version control history |

**Transfer Monitoring:**
```bash
# On target server, verify transfer progress in another SSH session
sshpass -p '{password}' ssh root@{server_ip} 'du -sh /path/to/dest/dir/'
```

### Creating Per-Server Reusable Skills

For servers you'll administer repeatedly, create a dedicated skill file. This is the pattern we used for server {{SERVER_IP}}:

```yaml
name: server-{ip-address}
version: 1.0.0
description: "{Description - e.g., Master cloud server}"
author: kaka
category: server

# Skill content should include:
# 1. Server IP and credentials
# 2. Quick connect commands
# 3. System specs (CPU, RAM, OS)
# 4. Common admin tasks
# 5. Installed software inventory
```

**Benefits of per-server skills:**
- ✅ No need to look up credentials every time
- ✅ Documented server-specific quirks and workarounds
- ✅ Inventory of installed software
- ✅ Quick reference for common tasks

### Typical Deployment Workflow

When setting up a new server as an agent replica:

1. **Verify SSH connectivity** using the steps above
2. **Do a dry-run** of rsync with `-n` flag to preview changes:
   ```bash
   sshpass -p '{pass}' rsync -avzn --exclude=... source/ root@{ip}:/dest/
   ```
3. **Run the actual transfer** (background mode for large transfers)
4. **Verify file counts/sizes** match source
5. **Create per-server skill** for future admin tasks
6. **Test gateway startup** on the new server if applicable

### Performance Notes

| Transfer Size | Estimated Time | Strategy |
|---------------|---------------|----------|
| < 100MB | < 1 minute | Foreground, single run |
| 100MB - 1GB | 2-10 minutes | Foreground with progress |
| > 1GB | 10+ minutes | Background with notify_on_complete |

**For transfers > 1GB:** Always use `terminal(background=true, notify_on_complete=true)`.

### Common Rsync Issues & Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection closed mid-transfer | Network instability | Run rsync again - it resumes automatically |
| Permission denied | Source/dest permissions | Verify user has read/write on both sides |
| "Host key verification failed" | First connection | Add `-o StrictHostKeyChecking=no` to SSH args |

---

## Verification Checklist

Before completing any monitoring task:
- [ ] Memory usage checked with percentage
- [ ] Disk usage checked with mount points
- [ ] System load and uptime verified
- [ ] Gateway status checked (ALL profiles)
- [ ] Network connectivity tested
- [ ] Report formatted with emojis for readability
- [ ] If automated: cron job verified, next run time confirmed

## Pitfalls to Avoid

❌ **Don't run pywinrm in hermes virtualenv - always use system Python `/usr/bin/python3`
❌ **Don't decode Windows output as UTF-8 - always use GBK encoding
❌ **Don't use `Start-Process` for desktop-interactive apps - they run in Session 0 (invisible)!** The user will say "I can't see anything"
❌ **Don't forget PsExec with `-i {session_id}` to launch visible programs on the user's desktop
❌ Don't assume Session 1 is always correct - run `query session` to verify active session ID
❌ Don't try to automate GUI button clicks remotely - it WON'T work from WinRM session; ask the user to click via RDP instead (we verified this with WeChat installer!)
❌ Don't forget to try silent installation parameters before attempting GUI-based installs
❌ Don't launch GUI installers on the user's desktop unless they ask to see it - default to background/silent mode

## Quick WinRM Workflow (What We Just Did)

When user asks to "do something on Windows server":
1.  `nc -zv {ip} 5985` - Verify WinRM port open
2.  `/usr/bin/python3 -c "import winrm; ..."` - Connect with pywinrm
3.  Run your command, decode with GBK
4.  Report results

**Example: Open baidu.com on remote Windows desktop:**
```python
import winrm
s = winrm.Session('http://{{SERVER_IP}}:5985/wsman', auth=('Administrator', 'AdminSsc1306@'), transport='ntlm')
s.run_ps("Start-Process 'msedge.exe' -ArgumentList 'https://www.baidu.com'")
```

## Remote Software Installation on Windows via WinRM

Install software silently on Windows servers without RDP access. Use domestic mirrors for faster downloads in China.

### Python Installation (Silent)

```powershell
# Download from Huawei mirror (faster in China)
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"

# Silent install (all users, add to PATH)
& "$env:TEMP\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

# Wait 60-90 seconds then verify
python --version
```

### Git Installation (Silent)

```powershell
# Download from npmmirror (faster in China)
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://registry.npmmirror.com/-/binary/git-for-windows/v2.45.0.windows.1/Git-2.45.0-64-bit.exe" -OutFile "$env:TEMP\git-installer.exe"

# Silent install
& "$env:TEMP\git-installer.exe" /VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES

# Wait 30 seconds then verify
git --version
```

### Chrome Browser Installation (Silent)

```powershell
# Download enterprise MSI
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://dl.google.com/tag/s/dl/chrome/install/googlechromestandaloneenterprise64.msi" -OutFile "$env:TEMP\chrome-installer.msi"

# Silent MSI install
msiexec /i "$env:TEMP\chrome-installer.msi" /quiet /norestart

# Wait 30 seconds then verify
Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### Chocolatey Package Manager (Optional)

```powershell
# Install Chocolatey package manager
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Then install packages: choco install nodejs -y
```

### Python Script Pattern for Batch Installation

```python
#!/usr/bin/python3
import winrm
import time

s = winrm.Session('http://{ip}:5985/wsman', auth=('{user}', '{pass}'), transport='ntlm')

# Install Python
ps_script = '''
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"
'''
s.run_ps(ps_script)
s.run_cmd("%TEMP%\\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0")
time.sleep(90)  # Wait for installation to complete

# Verify
r = s.run_cmd('python --version')
print("Python:", r.std_out.decode('gbk', errors='ignore').strip())
```

**⚠️ Installation Timeouts:**
- Python: 60-90 seconds
- Git: 20-30 seconds
- Chrome: 20-30 seconds
- Always use `time.sleep()` between install and verification
- Set generous timeout values for remote commands (120-180s)

## Post-Monitoring Notes

Do **not** save routine health-check results, daily report contents, or completed monitoring outcomes to persistent memory. These are task/session outcomes, not durable preferences or reusable procedures. If historical reports are needed, use cron/job delivery history or session_search rather than memory.
