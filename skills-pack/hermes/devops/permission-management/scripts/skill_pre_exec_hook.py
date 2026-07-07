#!/usr/bin/env python3
import sys
import json
import os

# 添加核心脚本路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from permission_core import permission_manager

def main():
    # 读取技能执行前传入的参数
    input_data = sys.stdin.read()
    try:
        context = json.loads(input_data)
    except:
        print(json.dumps({"allowed": True, "reason": "非标准上下文格式，跳过校验"}))
        return
    
    user_id = context.get("user_id", "unknown")
    skill_name = context.get("skill_name", "unknown")
    required_tools = context.get("required_tools", [])
    
    # 校验权限
    result = permission_manager.check_skill_access(user_id, skill_name, required_tools)
    
    # 返回校验结果
    print(json.dumps(result))
    
    if not result["allowed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
