---
name: human-assisted-browser-login
description: "人机协作式浏览器登录操作流程 - 用户提供验证码/密码，逐步完成网站登录"
version: 1.0.0
author: kaka (卡力的专属小机器人)
license: MIT
tags: ["browser", "login", "human-assisted", "otp", "verification-code", "interactive", "automation"]
related_skills: ["headless-browser-cjk-fonts", "stagehand-browser-automation", "web-access"]
trigger: |
  When you need to log into a website, whether through human-assisted authentication (phone/email OTP, username/password supplied by the user, QR scan, MFA, CAPTCHA) or through a fully automated persistent session for scheduled/cron runs. Also use when you need to maintain browser login state across headless Playwright/Chromium runs using a persistent profile, or when standard selectors fail and visual analysis is needed.
---

# Human-Assisted Browser Login Workflow

## Overview
This skill defines the standard workflow for **interactive human-assisted browser login** where the agent completes the form step-by-step and the user provides the verification code (OTP) or password via chat.

Common scenarios:
- Cloud provider console login (Volcengine, Aliyun, Tencent Cloud, etc.)
- SaaS service login requiring phone verification
- Any website where 2FA/OTP is needed and user provides the code

## Standard Workflow

### Step 1: Navigate to Login Page
- Use `browser_navigate` to open the login URL
- Wait for page to fully load
- Verify login form is displayed

### Step 2: Select Login Method
- Identify the correct login tab/button (e.g., "手机号登录")
- Click to switch to that method
- Confirm the form inputs are visible

### Step 3: Fill Static Information
- Input phone number/email/username that user provided
- Click the input field first (`browser_click`) then type (`browser_type`)
- If checkbox "I agree to terms" is required, click it to enable the button

### Step 4: Request Verification Code
- Click "获取验证码" / "Get Code" button
- **Immediately inform the user**: "I've clicked to get the code, please tell me the verification code you received"
- Wait for user to provide the 4-6 digit code

### Step 5: Complete Verification Code Input
- Find the verification code input field
- Click and input the code provided by user
- User may send it with spaces (e.g., "12 345") → clean to "12345" before input

### Step 6: Click Login/Submit
- Click the final "登录" / "Login" / "Submit" button
- Wait for page redirect/dashboard to load

### Step 7: Navigate to Target Page
- After successful login, navigate to the target page (e.g., billing, quota, usage)
- Extract the requested information

## Automated Persistent Login for Scheduled/Cron Runs

Use this pattern when you need a headless browser to stay logged in across repeated automated runs (e.g. a cron job that checks quota/usage/billing). It is a fully automated counterpart to the interactive human-assisted flow above.

### Persistent Profile Setup

1. **Pick two profile locations**
   - A durable backup profile: e.g. `~/.config/hermes-browser-profiles/<site>` or `~/snap/chromium/common/hermes-browser-profiles/<site>`.
   - A fast working profile for the current run: e.g. `/tmp/stagehand-<site>/browser-profile`.

2. **Seed the working profile from the durable backup**
   - If the working directory is empty or missing, copy the durable profile into it before launching Chromium. This avoids a known Chromium/Playwright behavior where an empty `userDataDir` may not persist session data to disk.

3. **Launch with Playwright persistent context**
   ```ts
   import { chromium } from "playwright";
   import { cpSync, existsSync, mkdirSync, readdirSync } from "fs";
   import os from "os";
   import path from "path";

   const durableProfile = path.join(os.homedir(), ".config/hermes-browser-profiles", "example");
   const workProfile = "/tmp/stagehand-example/browser-profile";

   if (!existsSync(workProfile) || readdirSync(workProfile).length === 0) {
     mkdirSync(workProfile, { recursive: true });
     if (existsSync(durableProfile)) {
       cpSync(durableProfile, workProfile, { recursive: true, force: true });
     }
   }

   const context = await chromium.launchPersistentContext(workProfile, {
     headless: true,
     executablePath: "/snap/bin/chromium", // or /usr/bin/chromium-browser
     args: [
       "--no-sandbox",
       "--disable-gpu",
       "--disable-dev-shm-usage",
       "--window-size=1920,3000",
     ],
   });
   const page = context.pages()[0] || await context.newPage();
   ```

4. **Detect login state and log in automatically if needed**
   - Load the target dashboard.
   - If a known authenticated element is present (e.g. usage bar, account menu), you are already logged in.
   - Otherwise, perform the automated login steps (fill username/password from environment, load a saved cookie, or fall back to human-assisted OTP).

5. **Sync the updated profile back to the durable location after the run**
   ```ts
   import { rmSync, cpSync } from "fs";
   if (existsSync(durableProfile)) {
     rmSync(durableProfile, { recursive: true, force: true });
   }
   cpSync(workProfile, durableProfile, { recursive: true, force: true });
   ```

### Key Pitfalls for Persistent Profiles

- ❌ **Do not start from an empty persistent profile** — session cookies may not be written to disk. Always seed from a known-good backup.
- ❌ **Do not store credentials in the script** — load username/password from environment variables or a secret file.
- ❌ **Do not run too fast after login** — wait for the post-login redirect/dashboard element before extracting data.
- ❌ **Do not use recursive `chmod`/`chown`** on the profile directory; Chromium will recreate permissions as needed.
- ✅ **Verify the durable profile actually grew** after the run (file count, Cookies size) to confirm persistence worked.

### When to Combine with Human-Assisted Login

If the site enforces OTP/MFA on every login and you cannot obtain a long-lived cookie, schedule the job so that the first run is done interactively (this skill's human-assisted flow) and all later runs reuse the resulting persistent profile.

## Common Patterns by Website Type

### Chinese Mobile Login Form
| Element | Typical ref pattern |
|---------|---------------------|
| Phone login tab | `tab "手机号登录" [ref=eXX]` |
| Phone input | `textbox "请输入手机号" [ref=eXX]` |
| Get code button | `button "获取验证码" [ref=eXX]` |
| Code input | `textbox "请输入验证码" [ref=eXX]` |
| Login button | `button "登录 / 注册" [ref=eXX]` or `button "登录" [ref=eXX]` |

### Handling Empty Snapshots
If `browser_snapshot` returns "(empty page)" after navigation:
1. Don't panic - this is common with large JS applications
2. Re-navigate with `browser_navigate` again
3. Elements usually reappear after refresh
4. If still empty, fallback to `browser_vision` to visually identify elements

## Pitfalls to Avoid

❌ **Don't ask user for code before clicking the button** - click first, *then* ask
❌ **Don't forget to click the input field before typing** - some forms require focus
❌ **Don't accept messy code input without cleaning** - user may type with spaces/newlines, clean to digits only
❌ **Don't skip waiting after login** - allow time for JavaScript redirect
❌ **Don't assume elements have the same ref after page refresh** - always get a fresh snapshot after navigation/click

## Example Conversation Flow

```
Agent: I'll help you log in to check the quota. Let me open the login page...
Agent: ✓ Switched to phone login, input your number 133xxxx1442. Now clicking "Get Code"...
Agent: I've clicked to get the code! Please tell me the verification code you received.
User: 123456
Agent: Got it! Inputting code 123456 and clicking login...
### Element selector matching timeout/failure (no verification code scenarios)
If standard selectors (input[name=\"xxx\"], button[type=\"submit\"]) fail to match:
1. Take a full page screenshot of the current form
2. Call `vision_analyze` to identify element features (placeholder text, visual features, button text)
3. Adjust selectors to use placeholder matching (`input[placeholder*=\"账户\"]`), type matching (`input[type=\"password\"]`), or XPath text matching (`//*[normalize-space(text())=\"登录\"]`)
4. As a last resort, press Enter directly in the password field to submit the form: `page.press('input[type=\"password\"]', 'Enter')`

## When to Use This Skill
- User says: "Help me check my quota / usage / balance" and login is required
- User says: "Log into [website], I'll give you the verification code"
- Any interactive login where second factor is provided manually by the user
- Pure automated login scenarios without human verification (no CAPTCHA/OTP), using the selector troubleshooting process above if needed

## When NOT to Use This Skill
- Credentials are already saved in environment variables → use direct API
- Fully automated login with stable pre-tested selectors is already available
- Login requires scanning QR code → use the cookie import fallback method described in the troubleshooting section

---

## Troubleshooting

### Button stays disabled after phone input
- Check if there's an "I agree to terms" checkbox that needs clicking
- Verify phone number length (usually 11 digits for China mobile)

### After clicking Get Code, user doesn't receive SMS
- Agent just waits, user will provide when they get it
- If user clicks resend, just click the button again

### Page doesn't redirect after login
- Wait a few seconds (JS apps can be slow)
- If still not redirecting, check if there's an extra button to click

### Anti-bot/Reptile Detection Block (4401/403/blank page errors)
If the login page is blocked by anti-bot detection and cannot load properly:
1. First try refreshing the page (F5) 2-3 times
2. If still blocked, inform the user of the two options:
   - Option 1: User logs into the website in their local browser, exports the cookies for the target domain, provides the cookie string/file to the agent
   - Option 2: Agent adjusts browser anti-identification parameters and retries loading
3. If user chooses cookie import: Load the cookies into the browser session directly, skip the login form process
4. This also works for QR code login scenarios that cannot be completed automatically
