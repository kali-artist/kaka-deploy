#!/usr/bin/env python3
import sys
import json
import os

# 添加核心脚本路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from permission_core import permission_manager

def main():
    # 读取网关传入的消息
    input_data = sys.stdin.read()
    try:
        message = json.loads(input_data)
    except:
        # 非标准格式直接放行（由后续流程处理）
        print(json.dumps({"allowed": True, "reason": "非标准消息格式，跳过校验"}))
        return
    
    user_id = message.get("user_id", "unknown")
    content = message.get("content", "")
    
    # 校验权限
    result = permission_manager.check_gateway_access(user_id, content)
    
    # 返回校验结果（符合Hermes Hook规范）
    print(json.dumps(result))
    
    # 校验不通过直接退出非0状态，网关会拦截请求
    if not result["allowed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
