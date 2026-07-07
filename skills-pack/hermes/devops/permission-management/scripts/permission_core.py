#!/usr/bin/env python3
import yaml
import os
from datetime import datetime
from typing import Dict, List, Optional

# 配置路径
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
PERMISSION_CONFIG = os.path.join(SKILL_DIR, "../config/permissions.yaml")
AUDIT_LOG = os.path.join(SKILL_DIR, "../logs/audit.log")
DEFAULT_PERMISSIONS = {
    "super_admins": ["{{WECHAT_USER_ID}}@im.wechat", "{{FEISHU_OPEN_ID}}", "{{FEISHU_OPEN_ID}}"],
    "global_protection_enabled": True,
    "default_user_permissions": {
        "allowed_skills": ["*query*", "search*", "minimax-web-search"],
        "blocked_tools": ["terminal", "write_file", "execute_code", "patch", "delete"],
        "allowed_tools": []
    },
    "user_permissions": {},
    "skill_required_tools": {},
    "blocked_operations": ["rm -rf /*", "dd if=/dev/zero", "mkfs.ext4 /dev/", ":(){ :|:& };:"],
    "audit_log_enabled": True
}

class PermissionManager:
    def __init__(self):
        # 确保目录存在
        os.makedirs(os.path.dirname(PERMISSION_CONFIG), exist_ok=True)
        os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
        
        # 加载配置
        if not os.path.exists(PERMISSION_CONFIG):
            self._save_config(DEFAULT_PERMISSIONS)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        with open(PERMISSION_CONFIG, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _save_config(self, config: Dict):
        with open(PERMISSION_CONFIG, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    
    def _log_audit(self, event_type: str, user_id: str, resource: str, result: str, detail: str = ""):
        if not self.config.get("audit_log_enabled", True):
            return
        log_line = f"{datetime.now().isoformat()} | {event_type} | {user_id} | {resource} | {result} | {detail}\n"
        with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(log_line)
    
    def is_super_admin(self, user_id: str) -> bool:
        return user_id in self.config.get("super_admins", [])
    
    def check_gateway_access(self, user_id: str, message_content: str) -> Dict:
        """网关层权限校验"""
        if not self.config.get("global_protection_enabled", True):
            return {"allowed": True, "reason": "全局防护已关闭"}
        
        if self.is_super_admin(user_id):
            return {"allowed": True, "reason": "超级管理员放行"}
        
        # 检查用户是否在黑名单
        if user_id in self.config.get("blocked_users", []):
            self._log_audit("gateway_block", user_id, "message_access", "blocked", "用户在黑名单中")
            return {"allowed": False, "reason": "您没有访问权限"}
        
        return {"allowed": True, "reason": "网关校验通过"}
    
    def check_skill_access(self, user_id: str, skill_name: str, required_tools: List[str] = None) -> Dict:
        """技能层权限校验"""
        if not self.config.get("global_protection_enabled", True):
            return {"allowed": True, "reason": "全局防护已关闭"}
        
        if self.is_super_admin(user_id):
            return {"allowed": True, "reason": "超级管理员放行"}
        
        # 保存技能必需工具列表
        if required_tools:
            self.config["skill_required_tools"][skill_name] = required_tools
            self._save_config(self.config)
        
        # 检查用户是否被禁止使用该技能
        user_perm = self.config["user_permissions"].get(user_id, {})
        blocked_skills = user_perm.get("blocked_skills", []) + self.config["default_user_permissions"].get("blocked_skills", [])
        if skill_name in blocked_skills or "*" in blocked_skills:
            self._log_audit("skill_block", user_id, skill_name, "blocked", "用户被禁止使用该技能")
            return {"allowed": False, "reason": "您没有权限使用该技能"}
        
        # 检查用户是否被允许使用该技能
        allowed_skills = user_perm.get("allowed_skills", []) + self.config["default_user_permissions"]["allowed_skills"]
        if skill_name in allowed_skills or "*" in allowed_skills:
            self._log_audit("skill_allow", user_id, skill_name, "allowed", "技能校验通过")
            return {"allowed": True, "reason": "技能使用权限校验通过"}
        
        # 通配符匹配
        for pattern in allowed_skills:
            if pattern.startswith("*") and pattern.endswith("*"):
                if pattern[1:-1] in skill_name:
                    return {"allowed": True, "reason": "技能使用权限校验通过"}
            elif pattern.startswith("*"):
                if skill_name.endswith(pattern[1:]):
                    return {"allowed": True, "reason": "技能使用权限校验通过"}
            elif pattern.endswith("*"):
                if skill_name.startswith(pattern[:-1]):
                    return {"allowed": True, "reason": "技能使用权限校验通过"}
        
        self._log_audit("skill_block", user_id, skill_name, "blocked", "技能不在允许列表中")
        return {"allowed": False, "reason": "您没有权限使用该技能"}
    
    def check_tool_access(self, user_id: str, tool_name: str, tool_args: str, current_skill: str = None) -> Dict:
        """工具层权限校验"""
        if not self.config.get("global_protection_enabled", True):
            return {"allowed": True, "reason": "全局防护已关闭"}
        
        if self.is_super_admin(user_id):
            return {"allowed": True, "reason": "超级管理员放行"}
        
        # 检查危险操作
        for op in self.config["blocked_operations"]:
            if op in str(tool_args):
                self._log_audit("tool_block", user_id, tool_name, "blocked", f"包含危险操作: {op}")
                return {"allowed": False, "reason": "操作包含危险内容，已被拦截"}
        
        # 检查用户是否被禁止使用该工具
        user_perm = self.config["user_permissions"].get(user_id, {})
        blocked_tools = user_perm.get("blocked_tools", []) + self.config["default_user_permissions"]["blocked_tools"]
        if tool_name in blocked_tools or "*" in blocked_tools:
            # 检查是否属于当前技能的必需工具
            if current_skill and tool_name in self.config["skill_required_tools"].get(current_skill, []):
                self._log_audit("tool_allow", user_id, tool_name, "allowed", f"技能[{current_skill}]必需工具，临时放行")
                return {"allowed": True, "reason": "工具属于当前技能必需组件，临时放行"}
            self._log_audit("tool_block", user_id, tool_name, "blocked", "用户被禁止使用该工具")
            return {"allowed": False, "reason": "您没有权限使用该工具"}
        
        # 检查用户是否被允许使用该工具
        allowed_tools = user_perm.get("allowed_tools", []) + self.config["default_user_permissions"]["allowed_tools"]
        if tool_name in allowed_tools or "*" in allowed_tools:
            self._log_audit("tool_allow", user_id, tool_name, "allowed", "工具校验通过")
            return {"allowed": True, "reason": "工具使用权限校验通过"}
        
        # 通配符匹配
        for pattern in allowed_tools:
            if pattern.startswith("*") and pattern.endswith("*"):
                if pattern[1:-1] in tool_name:
                    return {"allowed": True, "reason": "工具使用权限校验通过"}
            elif pattern.startswith("*"):
                if tool_name.endswith(pattern[1:]):
                    return {"allowed": True, "reason": "工具使用权限校验通过"}
            elif pattern.endswith("*"):
                if tool_name.startswith(pattern[:-1]):
                    return {"allowed": True, "reason": "工具使用权限校验通过"}
        
        # 检查是否属于当前技能的必需工具
        if current_skill and tool_name in self.config["skill_required_tools"].get(current_skill, []):
            self._log_audit("tool_allow", user_id, tool_name, "allowed", f"技能[{current_skill}]必需工具，临时放行")
            return {"allowed": True, "reason": "工具属于当前技能必需组件，临时放行"}
        
        self._log_audit("tool_block", user_id, tool_name, "blocked", "工具不在允许列表中")
        return {"allowed": False, "reason": "您没有权限使用该工具"}
    
    # 配置管理方法
    def add_allowed_skill(self, user_id: str, skill_name: str):
        if user_id not in self.config["user_permissions"]:
            self.config["user_permissions"][user_id] = {"allowed_skills": [], "blocked_skills": [], "allowed_tools": [], "blocked_tools": []}
        if skill_name not in self.config["user_permissions"][user_id]["allowed_skills"]:
            self.config["user_permissions"][user_id]["allowed_skills"].append(skill_name)
            self._save_config(self.config)
            self._log_audit("permission_change", user_id, skill_name, "allowed", "添加技能访问权限")
    
    def block_skill(self, user_id: str, skill_name: str):
        if user_id not in self.config["user_permissions"]:
            self.config["user_permissions"][user_id] = {"allowed_skills": [], "blocked_skills": [], "allowed_tools": [], "blocked_tools": []}
        if skill_name not in self.config["user_permissions"][user_id]["blocked_skills"]:
            self.config["user_permissions"][user_id]["blocked_skills"].append(skill_name)
            self._save_config(self.config)
            self._log_audit("permission_change", user_id, skill_name, "blocked", "禁止技能访问权限")
    
    def add_allowed_tool(self, user_id: str, tool_name: str):
        if user_id not in self.config["user_permissions"]:
            self.config["user_permissions"][user_id] = {"allowed_skills": [], "blocked_skills": [], "allowed_tools": [], "blocked_tools": []}
        if tool_name not in self.config["user_permissions"][user_id]["allowed_tools"]:
            self.config["user_permissions"][user_id]["allowed_tools"].append(tool_name)
            self._save_config(self.config)
            self._log_audit("permission_change", user_id, tool_name, "allowed", "添加工具访问权限")
    
    def block_tool(self, user_id: str, tool_name: str):
        if user_id not in self.config["user_permissions"]:
            self.config["user_permissions"][user_id] = {"allowed_skills": [], "blocked_skills": [], "allowed_tools": [], "blocked_tools": []}
        if tool_name not in self.config["user_permissions"][user_id]["blocked_tools"]:
            self.config["user_permissions"][user_id]["blocked_tools"].append(tool_name)
            self._save_config(self.config)
            self._log_audit("permission_change", user_id, tool_name, "blocked", "禁止工具访问权限")
    
    def toggle_global_protection(self, enable: bool):
        self.config["global_protection_enabled"] = enable
        self._save_config(self.config)
        self._log_audit("system_change", "system", "global_protection", "updated" , f"全局防护{'开启' if enable else '关闭'}")
    
    def get_audit_logs(self, limit: int = 100) -> List[str]:
        if not os.path.exists(AUDIT_LOG):
            return []
        with open(AUDIT_LOG, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-limit:] if limit > 0 else lines

# 单例实例
permission_manager = PermissionManager()
