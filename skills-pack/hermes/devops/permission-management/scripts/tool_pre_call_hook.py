#!/usr/bin/env python3
import sys
import json
import os

# 添加核心脚本路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from permission_core import permission_manager

def main():
    # 读取工具调用前传入的参数
    input_data = sys.stdin.read()
    try:
        context = json.loads(input_data)
    except:
        print(json.dumps({"allowed": True, "reason": "非标准上下文格式，跳过校验"}))
        return
    
    user_id = context.get("user_id", "unknown")
    tool_name = context.get("tool_name", "unknown")
    tool_args = context.get("args", "")
    current_skill = context.get("current_skill", None)
    
    # 校验权限
    result = permission_manager.check_tool_access(user_id, tool_name, tool_args, current_skill)
    
    # 返回校验结果
    print(json.dumps(result))
    
    if not result["allowed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
