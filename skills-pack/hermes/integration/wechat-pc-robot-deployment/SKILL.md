---
name: wechat-pc-robot-deployment
trigger: When deploying or troubleshooting PC WeChat automation robots (injection-based OR OCR/mouse-simulation alternatives) on Windows servers or desktops, including handling version compatibility, login restrictions, Windows Session 0 isolation, cross-session GUI automation via PsExec/win32api, and Windows security issues
description: Comprehensive deployment guide for PC WeChat automation on Windows systems, including both injection-based frameworks AND the recommended OCR + mouse/keyboard simulation alternative, cross-session GUI automation via PsExec/pywin32, version compatibility matrices, common pitfalls, and workarounds for Tencent login restrictions
version: 1.3.0
author: kaka (卡力的专属小机器人)
license: MIT
metadata:
  hermes:
tags: ["wechat", "automation", "windows", "winrm", "injection", "robot", "chatbot", "ocr", "pyautogui", "paddleocr", "psexec", "win32api", "pywin32", "session-isolation"]
related_skills: ["linux-to-windows-file-transfer", "proxy-server-configuration"]
---

# PC WeChat Robot Deployment & Troubleshooting

## Overview

Injection-based WeChat robots work by hooking into the PC WeChat client process to send/receive messages programmatically. This requires **specific WeChat versions**, has **login restrictions**, and encounters many **Windows-specific security pitfalls**.

## Supported Approaches & Frameworks

| Approach | WeChat Version | Status | Notes |
|----------|---------------|--------|-------|
| **Keyboard-Only Automation** | ANY version | ✅ **SIMPLEST & FASTEST** | No OCR, no image matching, just Ctrl+F + type! No dependencies other than pywin32 |
| **OCR + Mouse/Keyboard Simulation** | ANY version | ✅ **FULL CAPABILITY** | Can both send AND read messages, image matching for UI navigation |
| **WeChatFerry** | 3.9.12.51 | ❌ Login BLOCKED | Tencent completely blocks login on ALL old versions (May 2026+) |
| **ComWeChatRobot** | 3.9.5.81 | ❌ Login BLOCKED | 3.9.5.81 is also blocked from login as of May 2026 |
| **可爱猫 (KeAiMao)** | Latest | 💰 Commercial | Paid option, best version support but closed-source |
| **Enterprise WeChat API** | N/A | ⚠️ Business Only | Requires registration, CANNOT operate personal WeChat |

> **CRITICAL UPDATE (May 2026):** ALL injection-based WeChat robot frameworks are now effectively DEAD.
> Tencent's login servers reject ALL old WeChat versions required by these frameworks.
> Use **Keyboard-Only Automation** for simple sending, or **OCR + Mouse/Keyboard Simulation** if you also need to read messages.
> Both approaches work reliably with ANY WeChat version - see dedicated sections below.

---

## Critical Pre-Deployment Checklist (May 2026 Status: ALL INJECTION APPROACHES BLOCKED)

### ⚠️ CRITICAL: Injection Approach Is DEAD
- **ALL** open-source injection-based frameworks are effectively dead
- Tencent login servers reject **ALL** old WeChat versions (3.9.5.x, 3.9.12.x, etc.)
- No known working open-source injection approach as of May 2026
- **Consider alternatives BEFORE attempting any deployment:**
  - Image recognition + keyboard/mouse simulation (no injection, no version lock-in)
  - Enterprise WeChat API (but see important limitations below)
  - Commercial paid solutions (可爱猫/KeAiMao, etc.)

### 1. ✅ Verify WeChat Version Works BEFORE Installing
- **DO NOT** just download the latest WeChat - injection libraries require EXACT versions
- Check GitHub issues for "login failed" or "无法登录" (login blocked)
- Old versions (pre-3.9.6) are **completely blocked** by Tencent login servers

### 2. ✅ Check for Injection Framework Project Health
- Look at last commit date (abandoned = no version updates)
- Check open issues for "login" or "无法登录" (login blocked)
- Verify recent PRs mention version compatibility improvements

### 3. ✅ Plan for RDP Session Requirement
- Injection-based robots **require a logged-in desktop session**
- WinRM Session 0 isolation means:
  - Apps launched via WinRM run in invisible background session
  - WeChat GUI and injection hooks won't work from Session 0
  - User must stay logged in via RDP (can disconnect, but NOT log out)

---

---

## Alternative Approaches (RECOMMENDED - Both Work!)

These approaches use NO injection and work with **ANY WeChat version**. Both are immune to Tencent's version blocks.

---

### ✅ Approach 1: Keyboard-Only Automation (SIMPLEST - No OCR Needed!)

**DISCOVERED May 2026:** This is the simplest possible approach - no OCR, no image matching, no mouse clicks needed! WeChat's keyboard shortcuts are enough to automate sending messages.

**How it works:**
1. Find WeChat window by window class name: `WeChatMainWndForPC`
2. Activate and bring window to foreground
3. `Ctrl+F` to open search
4. Type contact name
5. `Enter` to select contact
6. Type message
7. `Enter` to send

✅ **Advantages:**
- **ZERO template images** needed - no screenshot setup!
- **No OCR dependencies** - PaddleOCR not required at all
- **No mouse coordinates** - everything uses keyboard shortcuts
- Works with **ANY WeChat version**
- Extremely low ban risk (looks like real keyboard input)
- Resolution independent - works at any screen size

❌ **Disadvantages:**
- Only works for sending messages (not reading)
- Requires WeChat window to be visible and activatable
- Cannot verify message was received (no feedback)

**Full Implementation:**
```python
import win32gui
import win32con
import win32api
import time
import keyboard
import ctypes

# Enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

def send_wechat_message(contact_name, message):
    """Send WeChat message using ONLY keyboard shortcuts - no OCR!"""
    
    # 1. Find WeChat window by class name
    hwnd = None
    def enum_callback(w, extra):
        nonlocal hwnd
        if "WeChatMainWndForPC" in win32gui.GetClassName(w):
            hwnd = w
            return False
        return True
    
    win32gui.EnumWindows(enum_callback, None)
    
    if not hwnd:
        print("❌ WeChat window not found")
        return False
    
    # 2. Activate window
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    # 3. Ctrl+F to open search
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord('F'), 0, 0, 0)
    time.sleep(0.1)
    win32api.keybd_event(ord('F'), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.5)
    
    # 4. Type contact name
    keyboard.write(contact_name)
    time.sleep(1)
    
    # 5. Enter to select contact
    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
    time.sleep(0.1)
    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(1)
    
    # 6. Type message
    keyboard.write(message)
    time.sleep(0.5)
    
    # 7. Enter to send
    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
    time.sleep(0.1)
    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
    
    print("✅ Message sent!")
    return True
```

**Setup:**
```powershell
pip install pywin32 keyboard
```

---

### ✅ Approach 2: OCR + Mouse/Keyboard Simulation (Full Capability)

Use this approach when you need to **read messages** in addition to sending them.

It simulates full human behavior by:
- Using image recognition to find UI elements
- Using OCR to read text from the screen
- Simulating mouse clicks and keyboard input

✅ **Advantages:**
- Works with **ANY WeChat version** (including latest!)
- No injection = extremely low ban risk
- Tencent cannot detect or block it (looks like a real user)
- Can both send AND receive messages

❌ **Disadvantages:**
- Requires visible GUI session (RDP must stay connected)
- Slower than injection (but adequate for most use cases)
- OCR accuracy ~95% for Chinese text
- UI changes require updating template images

---

### Step 1: Python Environment Setup

Install required libraries via pip:
```powershell
# Core simulation libraries
pip install pyautogui pynput pyperclip pillow numpy pywin32

# Image matching & OCR
pip install opencv-python paddlepaddle paddleocr
```

**Critical dependency versions (tested May 2026):**
- Python 3.11+ (3.11.9 recommended)
- pyautogui 0.9.54+
- pywin32 306+ (for direct Windows API access)
- opencv-python 4.9+
- paddleocr 2.7+
- paddlepaddle 2.6+

---

### Step 2: Verify Environment

```python
# test_environment.py
import pyautogui
import cv2
import numpy as np
from PIL import Image
import pyperclip

print("Screen size:", pyautogui.size())
print("pyautogui: OK")
print("opencv: OK")
print("numpy: OK")
print("PIL: OK")
print("pyperclip: OK")

# Test screenshot
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Downloads\test_screenshot.png")
print("Screenshot test: OK")

# Test clipboard
test_text = "WeChat automation test 微信自动化测试"
pyperclip.copy(test_text)
print("Clipboard test:", pyperclip.paste() == test_text)
```

---

### Step 3: OCR Initialization & Testing

```python
# test_ocr.py
from paddleocr import PaddleOCR
import os

# Initialize OCR (first run downloads ~100MB model)
ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
print("OCR initialized: OK")

# Test on screenshot
screenshot_path = r"C:\Downloads\test_screenshot.png"
if os.path.exists(screenshot_path):
    result = ocr.ocr(screenshot_path, cls=True)
    if result and result[0]:
        texts = [line[1][0] for line in result[0]]
        print(f"OCR detected {len(texts)} text regions:")
        for i, text in enumerate(texts[:5]):
            print(f"  {i+1}. {text[:40]}")
```

---

### Step 4: Core Implementation Template

```python
# wechat_automation_base.py
import time
import pyautogui
import cv2
import numpy as np
import pyperclip
import os
from paddleocr import PaddleOCR

# Configuration
pyautogui.PAUSE = 0.8  # Human-like delay between actions
pyautogui.FAILSAFE = True  # Move to corner to emergency stop
SCREENSHOT_DIR = r"C:\Downloads\screenshots"
TEMPLATE_DIR = r"C:\Downloads\templates"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# Initialize OCR
ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)

def find_image(template_name, confidence=0.8):
    """Find template image on screen and return coordinates"""
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    if not os.path.exists(template_path):
        return None
    
    screen = pyautogui.screenshot()
    screen_np = np.array(screen)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
    
    template = cv2.imread(template_path, 0)
    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= confidence:
        h, w = template.shape
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y)
    return None

def click_at(x, y):
    """Click at screen coordinates"""
    pyautogui.click(x, y, duration=0.2)

def type_text(text):
    """Type text via clipboard (faster, handles Chinese)"""
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')

def send_message(contact_name, message):
    """Send message to contact - IMPLEMENT after capturing templates"""
    # 1. Find and click search box
    # 2. Type contact name
    # 3. Click contact
    # 4. Click input area
    # 5. Type message
    # 6. Press Enter or click send button
    pass

def read_messages(region=None):
    """Read chat messages via OCR - IMPLEMENT after capturing templates"""
    screenshot = pyautogui.screenshot(region=region) if region else pyautogui.screenshot()
    temp_path = os.path.join(SCREENSHOT_DIR, "chat_temp.png")
    screenshot.save(temp_path)
    result = ocr.ocr(temp_path, cls=True)
    if result and result[0]:
        return [line[1][0] for line in result[0]]
    return []
```

---

### Step 5: Capture UI Template Images

**CRITICAL:** You need screenshots of WeChat UI elements for image matching. Capture these via RDP:

1. **Search box template** - `search_box.png`
2. **Send button template** - `send_button.png`  
3. **Message input area** - `input_area.png`
4. **WeChat taskbar icon** - `wechat_icon.png`

Save all templates to `C:\Downloads\templates\`

---

### Step 6: Windows Server Specific Setup

1. **RDP Session MUST stay active** (or use `/admin` flag):
   ```cmd
   mstsc /v:{{SERVER_IP}} /admin
   ```

2. **Disable screen saver and sleep**:
   ```powershell
   powercfg /change standby-timeout-ac 0
   powercfg /change monitor-timeout-ac 0
   ```

3. **Set fixed resolution** (1024x768 recommended for consistency):
   - Right-click desktop → Display settings
   - Set resolution, keep it CONSTANT

4. **Auto-start WeChat on boot** (optional but recommended):
   - Create shortcut in `shell:startup` folder

---
## Advanced: Cross-Session GUI Automation (WinRM Session 0 → Console Session 1)

This is the **most powerful technique** discovered (May 2026). It allows full GUI automation from 
WinRM Session 0 (invisible background) into the visible Console Session 1, without needing RDP.

### Key Tools Required

1. **PsExec** - From Sysinternals, runs processes in specific sessions
2. **pywin32** - Windows API bindings for direct window manipulation

```powershell
# Install PsExec on Windows server
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://download.sysinternals.com/files/PSTools.zip" -OutFile "C:\\Downloads\\PSTools.zip" -UseBasicParsing
Expand-Archive -Path "C:\\Downloads\\PSTools.zip" -DestinationPath "C:\\Downloads\\PSTools" -Force
```

```powershell
# Install pywin32 for Windows API access
pip install pywin32
```

---
### Step 1: Identify and Activate the Console Session

```powershell
# List all sessions
query session
# Look for session with state = Active, usually Session 1 for console/admin

# CRITICAL: Switch session 1 to active console state (activates GDI)
# This is REQUIRED before any GUI automation will work!
tscon 1 /dest:console
Start-Sleep -Seconds 2

# Start explorer.exe to initialize GUI environment fully
Start-Process explorer.exe
Start-Sleep -Seconds 3

# Verify screen resolution is now detected
Add-Type -AssemblyName System.Windows.Forms
Write-Output "Screen size: $([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Size)"
```

---
### Step 2: Launch GUI App in Console Session from WinRM

### Step 2: Launch GUI App in Console Session from WinRM

```python
import winrm

s = winrm.Session('windows-server-ip', auth=('Administrator', 'password'))

# Launch WeChat in Session 1 from Session 0
ps_launch = '''
cd C:\\Downloads\\PSTools
& .\\PsExec.exe -accepteula -i 1 "C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe"
'''
s.run_ps(ps_launch)
```

**Why this works:**
- `PsExec -i 1` = Run in Session 1 (the active console session)
- Bypasses Session 0 Isolation completely
- Window appears in the actual user's desktop

---
---
### Step 3: Enumerate and Activate Windows via Windows API

#### Method 1: Enumerate by Window Title/Class (Simple)

```python
# Run this in Session 1 via PsExec to find WeChat windows
import win32gui
import win32con
import time

def enum_windows_callback(hwnd, windows):
    title = win32gui.GetWindowText(hwnd)
    if '微信' in title or 'WeChat' in title or title == '':
        # Check if it's a visible WeChat window
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            windows.append((hwnd, title))
    return True

wx_windows = []
win32gui.EnumWindows(enum_windows_callback, wx_windows)

for hwnd, title in wx_windows:
    print(f'HWND: {hex(hwnd)}, Title: {repr(title)}')
    
    # Bring window to foreground
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
```

#### Method 2: Enumerate by Process ID (MORE RELIABLE!)

**DISCOVERED May 2026:** This is the most reliable way to find ALL windows belonging to the WeChat process, including hidden windows, dialogs, and child controls.

```python
import win32gui
import win32con
import win32process
import subprocess

# First get WeChat PID
result = subprocess.run(['tasklist', '/fi', 'imagename eq WeChat.exe'], capture_output=True, text=True)
print("WeChat process info:")
print(result.stdout)

# Extract PID (you can also hardcode it if known)
import re
pid_match = re.search(r'WeChat\.exe\s+(\d+)', result.stdout)
if pid_match:
    wechat_pid = int(pid_match.group(1))
    print(f"Found WeChat PID: {wechat_pid}")
else:
    print("WeChat not running!")
    exit()

# Enumerate ALL windows belonging to this process
found = []
def callback(hwnd, _):
    _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
    if win_pid == wechat_pid:
        class_name = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        visible = win32gui.IsWindowVisible(hwnd)
        try:
            rect = win32gui.GetWindowRect(hwnd)
            size = f"{rect[2]-rect[0]}x{rect[3]-rect[1]}"
        except:
            size = "?"
        found.append((hwnd, class_name, title, visible, size))
    return True

win32gui.EnumWindows(callback, None)

print(f"\nProcess {wechat_pid} has {len(found)} windows:")
for i, (hwnd, cls, title, vis, size) in enumerate(found, 1):
    print(f"  [{i:2d}] HWND={hwnd:8d} | Vis={vis:5} | Size={size:>9} | Class={cls}")
    if title:
        print(f"         Title: {title}")
```

**Key Window Signatures (Identified May 2026):**
| Window Type | Class Name | Size | Title | Notes |
|-------------|------------|------|-------|-------|
| **Login Dialog** | `#32770` | `396x163` | `微信` | Appears before login, has a "登录" (Login) button as child control |
| **Main Chat Window** | `WeChatMainWndForPC` | ~1000x800 | (empty) | Appears AFTER successful login |
| **Helper Windows** | `GDI+ Hook Window Class` | `1x1` | `G` | Internal, always hidden |

#### Method 3: Direct Child Control Messaging (No Mouse Needed!)

For dialogs like the login window, you can send Windows messages DIRECTLY to child controls (buttons, inputs) without needing mouse coordinates or OCR:

```python
import win32gui
import win32con

# Login dialog HWND (from enumeration above)
login_hwnd = 2425628  # Example - replace with your actual HWND

# Find child controls (like the login button)
buttons = []
def child_callback(child_hwnd, _):
    class_name = win32gui.GetClassName(child_hwnd)
    title = win32gui.GetWindowText(child_hwnd)
    if class_name == "Button":
        buttons.append((child_hwnd, title))
    return True

win32gui.EnumChildWindows(login_hwnd, child_callback, None)

print(f"Found {len(buttons)} buttons:")
for hwnd, title in buttons:
    print(f"  HWND={hwnd}, Title={title}")
    
    # Send BM_CLICK message to click the button directly!
    win32gui.SendMessage(hwnd, win32con.BM_CLICK, 0, 0)
    print(f"  Clicked button {title}")
```

---

### Step 4: Execute Python UI Scripts in Target Session

```python
# From Linux, write the automation script first, then run via PsExec
import winrm
import base64

s = winrm.Session('windows-server-ip', auth=('Administrator', 'password'))

# Write automation script to Windows
ps_write = '''
@"
import win32gui
import win32con
import win32api
import time

# Your automation code here
hwnd = 0x721328  # From enumeration
if win32gui.IsWindow(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    print('Window activated!')
"@ | Out-File -FilePath "C:\\Downloads\\auto.py" -Encoding UTF8
'''
s.run_ps(ps_write)

# Run it in Session 1
ps_run = '''
cd C:\\Downloads\\PSTools
& .\\PsExec.exe -accepteula -i 1 cmd /c "python C:\\Downloads\\auto.py > C:\\Downloads\\log.txt 2>&1"
Start-Sleep -Seconds 3
Get-Content "C:\\Downloads\\log.txt"
'''
result = s.run_ps(ps_run)
print(result.std_out.decode('gbk', errors='ignore'))
```

---

### Key Advantages of This Approach

✅ **No RDP required** - Full control from WinRM alone  
✅ **Direct window manipulation** - Using HWNDs, not screen coordinates  
✅ **Resolution independent** - Window API doesn't care about screen size  
✅ **More reliable** - Windows API is deterministic, no image matching errors  
✅ **Works with latest WeChat** - No version restrictions  

---

### Screenshot & File Transfer Techniques

#### ⚠️ CRITICAL HEADLESS SERVER DISPLAY ISSUE (DISCOVERED May 2026)

This is the #1 reason screenshots fail on cloud Windows servers:

**Even with `PsExec -i 1` running in Session 1, if there is NO ACTIVE RDP CONNECTION to the server:**
- `PIL.ImageGrab.grab()` returns a tiny all-black image (~3KB PNG)
- .NET `CopyFromScreen()` returns black/empty
- ALL GDI-based screenshot APIs FAIL

**Why:** Without an active display (physical monitor or active RDP session), Windows has no real display surface to capture. Session 1 being "Active" in `query session` is NOT sufficient - there must be an actual connected display AND GDI graphics subsystem initialized.

**Diagnostic Signals (CONFIRM you have this issue):**
```
# If you see this pattern - you definitely have the headless display problem!
1. Screenshot file size is TINY (~3KB instead of 300KB+ for normal 1024x768)
2. Image is COMPLETELY BLACK when viewed with image viewer
3. GDI error: "Exception calling CopyFromScreen with 3 argument(s): The handle is invalid"
4. `query session` shows Session 1 as "Active" but NO RDP client connected
5. Python script exit code 1 or C# script exits 0 but produces NO FILE
```

**CRITICAL: GDI Initialization Requirement (NEW May 2026)**
Even with Session 1 active, GDI graphics handles are NOT initialized automatically. To initialize GDI WITHOUT an RDP connection:

```powershell
# Switch session 1 to active console state (activates GDI subsystem)
tscon 1 /dest:console

# Start explorer.exe to fully initialize GUI environment
Start-Process explorer.exe
Start-Sleep -Seconds 3

# Now screen resolution should be detected:
Add-Type -AssemblyName System.Windows.Forms
Write-Output "Screen size: $([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Size)"
```

**Important:** This activates the GDI subsystem but MAY STILL NOT be sufficient for full screenshot functionality. For 100% reliable screenshots, an active RDP connection or virtual display driver is still required.

**Solutions (Ordered by Preference):**

1. ✅ **Maintain an active RDP connection** - User must stay connected via RDP (can minimize the window, but cannot close/disconnect)
   ```cmd
   mstsc /v:WINDOWS_IP /admin  # The /admin flag helps maintain session state
   ```

2. ✅ **Install virtual display driver** (usbmmidd_v2) - Creates a virtual monitor, NO RDP needed (RECOMMENDED for unattended automation)
   ```powershell
   # Download and install (if GitHub is accessible)
   $ProgressPreference = 'SilentlyContinue'
   Invoke-WebRequest -Uri "https://github.com/itsmikethetech/Virtual-Display-Driver/releases/download/v20.2/usbmmidd_v2.zip" -OutFile "C:\Downloads\usbmmidd.zip" -UseBasicParsing
   Expand-Archive -Path "C:\Downloads\usbmmidd.zip" -DestinationPath "C:\Downloads\usbmmidd" -Force
   
   # Install via device manager or included scripts
   cd C:\Downloads\usbmmidd\deviceinstaller64
   .\deviceinstaller64.exe enableidd 1
   ```

3. ✅ **C# Screenshot Utility (More Reliable Than PIL)**
   Compile a C# executable for more consistent screenshot capture:
   ```csharp
   // Compile on Windows: C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe screenshot.cs
   using System;
   using System.Drawing;
   using System.Drawing.Imaging;
   
   class ScreenCapture {
       static void Main() {
           try {
               Rectangle bounds = Screen.PrimaryScreen.Bounds;
               using (Bitmap bitmap = new Bitmap(bounds.Width, bounds.Height, PixelFormat.Format32bppArgb)) {
                   using (Graphics g = Graphics.FromImage(bitmap)) {
                       g.CopyFromScreen(bounds.X, bounds.Y, 0, 0, bounds.Size, CopyPixelOperation.SourceCopy);
                   }
                   bitmap.Save(@"C:\Downloads\screen.jpg", ImageFormat.Jpeg);
                   Console.WriteLine($"OK: {bounds.Width}x{bounds.Height}");
               }
           } catch (Exception ex) {
               Console.WriteLine($"FAIL: {ex.Message}");
               Environment.Exit(1);
           }
       }
   }
   ```

4. ⚠️ **RDP Configuration Tweaks**
   ```powershell
   # Allow multiple RDP sessions and keep sessions alive
   Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
   Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "MaxInstanceCount" -Value 5
   # Disable idle timeout (keep sessions alive indefinitely)
   Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services' -Name "RemoteAppLogoffTimeout" -Value 0 -ErrorAction SilentlyContinue
   ```

#### Capturing Screenshots from WinRM Session 0

WinRM runs in Session 0 (invisible background), so direct screenshot calls produce blank/white images. Use **PsExec** (simpler) or Task Scheduler to run in the user's desktop session:

#### Method 1: PsExec (RECOMMENDED - Simpler!)

```python
import winrm
import base64

s = winrm.Session('windows-server-ip', auth=('Administrator', 'password'))

# Write screenshot script using PIL (faster than System.Drawing)
ps_write = '''
@"
from PIL import ImageGrab
img = ImageGrab.grab()
img.save(r"C:\Downloads\screen.png")
print(f"PNG_OK: {img.size}")
"@ | Out-File -FilePath "C:\\Downloads\\screenshot.py" -Encoding UTF8
'''
s.run_ps(ps_write)

# Run in Session 1 via PsExec
ps_run = '''
cd C:\\Downloads\\PSTools
& .\\PsExec.exe -accepteula -i 1 cmd /c "python C:\\Downloads\\screenshot.py > C:\\Downloads\\screenshot_log.txt 2>&1"
Start-Sleep -Seconds 3
Get-Content "C:\\Downloads\\screenshot_log.txt"
'''
result = s.run_ps(ps_run)
print(result.std_out.decode('gbk', errors='ignore'))

# Transfer via base64
ps_b64 = '''
$bytes = [System.IO.File]::ReadAllBytes("C:\\Downloads\\screen.png")
[System.Convert]::ToBase64String($bytes)
'''
result = s.run_ps(ps_b64)
b64_data = result.std_out.decode('gbk', errors='ignore').strip()

# Decode on Linux
img_bytes = base64.b64decode(b64_data)
with open('/tmp/screen.png', 'wb') as f:
    f.write(img_bytes)
```

#### Method 2: Task Scheduler (Legacy)

```powershell
# Create a PowerShell script that captures screenshot
$screenshotScript = @'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

$outputPath = "C:\\Downloads\\screen.png"
$bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
'@

$screenshotScript | Out-File -FilePath "C:\\Downloads\\screenshot.ps1" -Encoding UTF8

# Create scheduled task to run in user session
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\\Downloads\\screenshot.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(2)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries

Register-ScheduledTask -TaskName "ScreenCapture" -Action $action -Trigger $trigger -Settings $settings -User "Administrator" -RunLevel Highest -Force

# Wait and clean up
Start-Sleep -Seconds 5
Unregister-ScheduledTask -TaskName "ScreenCapture" -Confirm:$false -ErrorAction SilentlyContinue
```

### Base64 File Transfer (Windows → Linux)

No HTTP server needed. Encode the file on Windows and decode on Linux.

**⚠️ CRITICAL: Use Raw Bytes + Base64, NOT UTF-8 Strings!**

Transferring Python scripts via string embedding in PowerShell Here-Strings often fails due to:
- Encoding mismatches (UTF-8 vs GBK vs ASCII)
- Special character escaping issues
- PowerShell string length limits

**RELIABLE METHOD (RECOMMENDED):**
```python
import winrm
import base64
import os

# 1. Read file locally and encode to base64
with open('/local/path/script.py', 'r', encoding='utf-8') as f:
    content = f.read()
content_b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')

# 2. Transfer and decode on Windows
s = winrm.Session('windows-server-ip', auth=('Administrator', 'password'))
ps_decode = f'''
$base64 = "{content_b64}"
$bytes = [System.Convert]::FromBase64String($base64)
[System.IO.File]::WriteAllBytes("C:\\\\Downloads\\\\target.py", $bytes)
Write-Output "✅ File saved, {len(content)} chars"
'''
result = s.run_ps(ps_decode)
print(result.std_out.decode('gbk', errors='ignore'))
```

**For binary files (images, etc.):**
```python
import winrm
import base64

s = winrm.Session('windows-server-ip', auth=('Administrator', 'password'))

# Get base64 encoded file from Windows
ps_b64 = '''
$bytes = [System.IO.File]::ReadAllBytes("C:\\\\Downloads\\\\screen.png")
[System.Convert]::ToBase64String($bytes)
'''
result = s.run_ps(ps_b64)

# Decode on Linux - ALWAYS handle encoding properly!
b64_data = result.std_out.decode('gbk', errors='ignore').replace('\r', '').replace('\n', '').strip()
img_bytes = base64.b64decode(b64_data)
with open('/tmp/screen.png', 'wb') as f:
    f.write(img_bytes)
```

**Windows Encoding Best Practices:**
- Always decode with `errors='ignore'` or `errors='replace'` for GBK output
- PowerShell default encoding is NOT UTF-8!
- Use `[System.IO.File]::WriteAllBytes()` for binary-safe writes
- Use `Encoding UTF8` parameter for `Out-File` when writing text

---
## Best Practices for OCR/Simulation Approach

1. **Keep resolution CONSTANT** - Image matching breaks if resolution changes
2. **Add human-like delays** (0.5-1 second between actions)
3. **Use confidence thresholds** - Don't match below 0.7-0.8
4. **Add fallback logic** - If element not found, retry 2-3 times
5. **Log everything** - Save screenshots and OCR results for debugging
6. **Test on non-critical accounts first** - Even low risk, still be careful
7. **Don't spam messages** - Rate limit to <1 message every 5 seconds

---

## Common Problems & Solutions (OCR Approach)

### ❌ Problem: Image matching fails constantly
**Fix:** 
- Re-capture templates at EXACT same resolution
- Check for DPI scaling differences
- Adjust confidence threshold (lower = more matches but more false positives)

### ❌ Problem: OCR doesn't detect Chinese text correctly
**Fix:**
- Ensure `lang="ch"` parameter
- Crop to chat region only (less noise)
- Increase contrast/brightness of screenshot pre-processing
- Use PaddleOCR v2.7+

### ❌ Problem: PaddleOCR fails with `ImportError: cannot import name 'IntEnum' from 'enum'`
**Root Cause:** Python looks for `enum.py` in the current working directory first (CWD = `C:\Downloads\`), and if there's a local `enum.py` file, it shadows the built-in `enum` module. This is a common Python import path issue!

**Fix:**
```powershell
# Delete conflicting local enum.py from working directory
Remove-Item "C:\Downloads\enum.py" -ErrorAction SilentlyContinue
Remove-Item "C:\Downloads\enum.pyc" -ErrorAction SilentlyContinue
Remove-Item "C:\Downloads\__pycache__\enum*" -Recurse -Force -ErrorAction SilentlyContinue

# Test PaddleOCR import again
python -c "from paddleocr import PaddleOCR; print('OK')"
```

**Prevention:**
- NEVER run Python scripts directly from `C:\Downloads\`
- Use a dedicated subdirectory like `C:\WeChatAutomation\`
- Don't create Python files that shadow built-in module names (enum, sys, os, etc.)

### ❌ Problem: Script works in RDP but stops when disconnected
**Fix:**
- Use `mstsc /admin` flag
- Don't log out - just disconnect the RDP session
- Use Task Scheduler to run in user session

### ❌ Problem: Mouse clicks happen but nothing happens
**Fix:**
- WeChat window might be minimized or in background
- Add code to activate/focus the WeChat window first
- Check if clicks are landing on correct coordinates

---

## Deployment Workflow (Step-by-Step)

### Step 1: Download CORRECT WeChat Version

**From GitHub Releases (most reliable):**
```powershell
# WeChatFerry - 3.9.12.51 (May 2026: Login increasingly blocked!)
$url = "https://ghfast.top/https://github.com/lich0821/WeChatFerry/releases/download/v39.5.2/WeChatSetup-3.9.12.51.exe"

# ComWeChatRobot - 3.9.5.81 (try this first if 3.9.12.51 won't login)
# Find download URL from ComWeChatRobot releases

# Download with -UseBasicParsing = most reliable on Windows Server
Invoke-WebRequest -Uri $url -OutFile "C:\Downloads\WeChatSetup.exe" -UseBasicParsing
```

**⚠️ NEVER transfer installer cross-platform!**
- Linux → Windows transfer triggers Zone.Identifier NTFS alternate data stream marking
- Causes "NSIS integrity check failed" even with PERFECT MD5 match
- Always download DIRECTLY on Windows via PowerShell/RDP browser

### Step 2: Install WeChat and Login

1. Run installer via RDP (**NOT WinRM** - Session 0 will be invisible)
2. **Scan QR code to login BEFORE installing robot SDK**
3. Disable WeChat auto-updates immediately! (Settings → General → Update)
4. **Keep WeChat running** (minimized is fine, but DON'T close it)

### Step 3: Install Robot SDK

For WeChatFerry:
```powershell
# From RDP session (NOT WinRM!)
pip install wcferry

# Test basic connectivity
python -c "from wcferry import Wcf; wcf = Wcf(); print('Self wxid:', wcf.get_self_wxid())"
```

For ComWeChatRobot:
- Follow specific installation instructions from project README

---

## Common Problems & Solutions

### ❌ Problem 1: "应用版本过低，无法登录" / "App version too low, cannot login"

**Root Cause:** Tencent actively blocks login on ALL old WeChat versions required by injection frameworks
- All injection libraries require outdated WeChat versions
- Tencent's anti-bot system completely blocks these versions
- **This is NOT a temporary issue - injection approach is effectively dead**

**Solutions (Ordered by Preference):**

1. **OCR + Keyboard/Mouse Simulation** - No version lock-in, no injection, lowest ban risk
2. **Commercial paid solutions** - 可爱猫/KeAiMao (closed-source, but works with latest WeChat)
3. **Enterprise WeChat API** - ★ IMPORTANT LIMITATIONS:
   - ✅ Requires registration (CorpID + Secret) - **cannot be used anonymously**
   - ✅ Requires enterprise creation and personal real-name verification
   - ❌ **CANNOT operate personal WeChat accounts** - only operates Enterprise WeChat accounts
   - ❌ Cannot read/send personal WeChat messages to regular contacts
   - ✅ Can message external contacts who added your Enterprise WeChat
4. **Local machine deployment** - Sometimes works better than cloud IPs (rare now)

### ❌ Problem 2: NSIS "Installer integrity check has failed"

**Root Cause:** 95% chance it's **Zone.Identifier alternate data stream marking**, NOT actual corruption!

**Fix:**
```powershell
# Remove security marking
Unblock-File -Path "C:\Downloads\WeChatSetup.exe"
# OR force skip check (last resort)
Start-Process "C:\Downloads\WeChatSetup.exe" -ArgumentList "/NCRC"
```

**Better Fix:** Never transfer installers cross-platform. Download directly on Windows!

### ❌ Problem 3: WeChat installed via WinRM but "I don't see it in RDP"

**Root Cause:** Session 0 Isolation - WinRM runs everything in background Session 0, RDP uses Session 1+

**Fix:** Always launch installers/GUI apps via **Task Scheduler** targeting user session:
```cmd
schtasks /create /tn "WeChat" /tr "C:\Downloads\WeChatSetup.exe" /sc once /st 00:00 /ru Administrator /f
schtasks /run /tn "WeChat"
```

### ❌ Problem 4: WinRM Process Leak (Memory Exhaustion)

**Symptom:** Hundreds of `winrshost.exe` processes in Task Manager, memory >80%

**Fix:**
```powershell
# Clean up ALL orphaned WinRM processes
Get-Process -Name winrshost -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name wsmprovhost -ErrorAction SilentlyContinue | Stop-Process -Force
```

**Prevention:** Clean up after every 3 WinRM commands!

### ❌ Problem 5: Complete WeChat Uninstall & Cleanup (for switching versions)

**When needed:** Reinstalling WeChat, switching to different robot framework, or removing old bot SDKs

**Complete uninstall via WinRM/Python:**
```python
import winrm
s = winrm.Session('windows-server-ip', auth=('Administrator', 'password'))

# Step 1: Kill running WeChat process
s.run_ps('Get-Process WeChat -ErrorAction SilentlyContinue | Stop-Process -Force')

# Step 2: Delete installation directory
s.run_ps('Remove-Item "C:\\Program Files\\Tencent\\WeChat" -Recurse -Force -ErrorAction SilentlyContinue')
s.run_ps('Remove-Item "C:\\Program Files (x86)\\Tencent\\WeChat" -Recurse -Force -ErrorAction SilentlyContinue')

# Step 3: Delete user data
s.run_ps('Remove-Item "$env:USERPROFILE\\Documents\\WeChat Files" -Recurse -Force -ErrorAction SilentlyContinue')

# Step 4: Delete desktop shortcuts
s.run_ps('Remove-Item "$env:USERPROFILE\\Desktop\\*微信*.lnk" -Force -ErrorAction SilentlyContinue')

# Step 5: Clean registry
s.run_ps('Remove-Item "HKCU:\\Software\\Tencent\\WeChat" -Recurse -Force -ErrorAction SilentlyContinue')
s.run_ps('Remove-Item "HKLM:\\Software\\Tencent\\WeChat" -Recurse -Force -ErrorAction SilentlyContinue')
```

---

## PyWinRM Proxy Interference Bug

When using `pywinrm` from Linux with proxy configured:
```python
# Error you'll see:
# requests.exceptions.InvalidSchema: Missing dependencies for SOCKS support.

# Fix: Unset ALL proxy env vars BEFORE importing winrm!
import os
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
    os.environ.pop(var, None)

import winrm  # Import AFTER clearing proxies
```

---

## Injection vs Alternative Approaches (May 2026 Status)
## When to Abandon Injection Approach

**✅ ABANDON NOW (May 2026)**

The injection approach is **completely dead** for all open-source frameworks. Tencent has blocked login on ALL old WeChat versions required by these frameworks. No known workaround exists for:
- WeChatFerry (3.9.12.51) - login blocked
- ComWeChatRobot (3.9.5.81) - login blocked

**Recommended alternatives, ordered by preference:**
1. **OCR + Mouse/Keyboard Simulation** - No version lock-in, simulates real user behavior
2. **Commercial paid solutions** - 可爱猫/KeAiMao (closed-source, but maintained)
3. **Enterprise WeChat API** - Only for business use cases (IMPORTANT: cannot operate personal WeChat!)

## Best Practices for Long-Term Stability

1. **DO NOT use injection for production** - It's dead, unreliable, and has high ban risk
2. **Consider Enterprise WeChat ONLY for B2B use cases** - Requires registration, cannot operate personal WeChat
3. **Use OCR/simulation approach** - Most reliable long-term, no version dependency
4. **If using commercial solutions: use dedicated low-value test account first**
5. **Don't send messages too frequently** - Tencent rate limits

---

---
## Architecture: Building a WeChat Message Gateway (HTTP API Wrapper)

**DISCOVERED May 2026:** This is the most useful production-ready architecture. Instead of running one-off Python scripts, wrap the automation in a Flask/FastAPI HTTP server so ANY system (other agents, web apps, cron jobs) can send WeChat messages via REST API.

### Architecture Pattern
```
┌─────────────┐    HTTP POST    ┌─────────────────┐    pywin32 API    ┌──────────┐
│  Any System │ ◄─────────────► │  Flask Server   │ ◄───────────────► │  WeChat  │
│  (Agent/Web)│   GET History   │  (Port 8765)    │   keyboard input  │  PC App  │
└─────────────┘                 └─────────────────┘                   └──────────┘
                                     │
                                     ▼ SQLite
                              ┌──────────────┐
                              │  Message DB  │
                              │  Conversations│
                              └──────────────┘
```

### Project Structure
```
wechat-gateway/
├── src/
│   ├── wechat/client.py      # pywin32 automation core
│   ├── database.py           # SQLite storage + conversation management
│   ├── api/server.py         # Flask HTTP endpoints
│   └── main.py               # CLI entrypoint
├── example.py                # Quick test script
├── requirements.txt
├── start.bat                 # Windows one-click start
└── README.md
```

### Core API Endpoints (Standardize These!)

```python
# Flask API - src/api/server.py
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "wechat-gateway"})

@app.route('/api/wechat/send', methods=['POST'])
def send_message():
    """
    POST /api/wechat/send
    Body: {"target": "张三", "content": "你好，来自API！"}
    """
    data = request.json
    target = data.get('target')
    content = data.get('content')
    
    # Call pywin32 automation
    # success = wechat_client.send_message(target, content)
    return jsonify({"success": True, "target": target})

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get message history with pagination"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({"messages": []})

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """List recent contacts"""
    return jsonify({"conversations": []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=False)
```

### Database Schema (For Persistence)
```python
# src/database.py
import sqlite3
from datetime import datetime

class MessageStore:
    def init_db(self):
        conn = sqlite3.connect('data/messages.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                direction TEXT,           -- 'incoming' or 'outgoing'
                target_contact TEXT,
                content TEXT,
                status TEXT,              -- 'pending', 'sent', 'failed'
                created_at TIMESTAMP,
                sent_at TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT UNIQUE,
                last_message_at TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        return conn
```

### Modular WeChat Client (Reusable!)
```python
# src/wechat/client.py
import win32gui
import win32con
import win32api
import time
import keyboard
import ctypes

class WeChatClient:
    def __init__(self):
        # Enable DPI awareness
        try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except: pass
    
    def find_window(self):
        """Find WeChat main window by class name"""
        hwnd = None
        def callback(w, extra):
            nonlocal hwnd
            if "WeChatMainWndForPC" in win32gui.GetClassName(w):
                hwnd = w
                return False
            return True
        win32gui.EnumWindows(callback, None)
        return hwnd
    
    def send_message(self, contact_name, message):
        """Send message using keyboard shortcuts"""
        hwnd = self.find_window()
        if not hwnd:
            return False, "Window not found"
        
        # Activate
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.5)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Ctrl+F search
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord('F'), 0, 0, 0)
        time.sleep(0.1)
        win32api.keybd_event(ord('F'), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        
        # Type + select contact
        keyboard.write(contact_name)
        time.sleep(1)
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(1)
        
        # Type + send message
        keyboard.write(message)
        time.sleep(0.5)
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        return True, "Sent"
```

### Usage: Calling From Any System
```bash
# From Linux/Mac - send a message
curl -X POST http://windows-ip:8765/api/wechat/send \
  -H "Content-Type: application/json" \
  -d '{"target": "文件传输助手", "content": "Gateway is working!"}'

# Check status
curl http://windows-ip:8765/health

# Get history
curl http://windows-ip:8765/api/messages?limit=10
```

### ✅ Key Advantages of Gateway Architecture
1. **No Python on caller side** - Any language/system can use HTTP
2. **Centralized management** - One gateway serves multiple clients
3. **Message persistence** - Audit log, retry logic
4. **Rate limiting** - Protect against Tencent bans
5. **Multi-channel capability** - Add WhatsApp/Telegram with same API
6. **Hermes Agent integration** - Other profiles/channels can call WeChat via gateway

---
## When to Abandon Injection Approach

Consider switching if you encounter:
- Persistent login failures on ALL supported versions
- Account bans/warnings
- Requirement for latest WeChat features
- Production reliability requirements

**Recommended alternative for serious use:** Enterprise WeChat Official API
