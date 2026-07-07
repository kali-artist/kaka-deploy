#!/usr/bin/env python3
import os
import yaml
import datetime
import subprocess
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "permissions.yaml"
LOG_PATH = BASE_DIR / "logs" / "audit.log"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# 获取当前时间
now = datetime.datetime.now()
three_days_ago = now - datetime.timedelta(days=3)
report_time = now.strftime("%Y-%m-%d %H:%M:%S")
report_file = REPORT_DIR / f"permission_report_{now.strftime('%Y%m%d')}.html"

# 1. 读取三层Hook配置
hook_config = {}
hook_paths = [
    ("网关层前置Hook", "~/.hermes/hooks/gateway/pre/gateway_pre_hook.py"),
    ("技能层执行前Hook", "~/.hermes/hooks/skill/pre_exec/skill_pre_exec_hook.py"),
    ("工具层调用前Hook", "~/.hermes/hooks/tool/pre_call/tool_pre_call_hook.py"),
]
for name, path in hook_paths:
    full_path = os.path.expanduser(path)
    if os.path.exists(full_path):
        hook_config[name] = "✅ 已启用，正常运行"
    else:
        hook_config[name] = "❌ 未部署/未启用"

# 2. 读取用户权限策略
permission_rules = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            permission_rules = yaml.safe_load(f) or {}
    except:
        permission_rules = {"default": "默认规则生效：仅{{MASTER_NAME}} 主人拥有全部权限，其他用户默认最小权限"}
else:
    permission_rules = {"default": "默认规则生效：仅{{MASTER_NAME}} 主人拥有全部权限，其他用户默认最小权限"}

# 3. 读取最近三天的权限日志
logs = []
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                log_time = datetime.datetime.strptime(line.split("|")[0].strip(), "%Y-%m-%d %H:%M:%S")
                if log_time >= three_days_ago:
                    logs.append(line)
            except:
                continue

# 生成纯文本报表
report_text = f"""🔐 Hermes权限管理系统3天报表
生成时间：{report_time}
统计周期：{three_days_ago.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}

🛡️ 三层Hook防护状态
"""
for name, status in hook_config.items():
    report_text += f"- {name}：{status}\n"

report_text += """
👤 用户权限策略
"""
if permission_rules:
    for k, v in permission_rules.items():
        report_text += f"- {k}：{v}\n"
report_text += "- 默认规则：超级管理员（{{MASTER_NAME}} 主人）拥有所有权限，其他用户默认仅可调用普通查询类技能，禁止所有写/执行类危险操作\n"

report_text += f"""
📝 最近3天权限日志（共{len(logs)}条）
"""
if logs:
    for log in logs[-20:]:
        report_text += f"- {log}\n"
    if len(logs) > 20:
        report_text += f"... 仅显示最近20条，完整日志请查看 {LOG_PATH}\n"
else:
    report_text += "- 最近3天无权限操作/拦截日志\n"

report_text += """
---
本报表由权限管理系统自动生成
"""

# 保存报表
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report_text)

print(f"✅ 权限报表已生成：{report_file}")
print("="*50)
print(report_text)
print("="*50)
