#!/usr/bin/env python3
"""
AI 辅助模块 - 用 AI 接口完成配置生成和交互式问答
支持 OpenAI 兼容接口（OpenAI、Anthropic via proxy、MiniMax 等）
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def call_ai(prompt: str, system: str = "", config: dict = None) -> str:
    """调用 AI 接口，返回文本响应"""
    if not config:
        config = load_env_config()

    api_base = config.get("ai", {}).get("api_base", "")
    api_key = config.get("ai", {}).get("api_key", "")
    model = config.get("ai", {}).get("model", "")

    if not all([api_base, api_key, model]):
        return "[ERROR] AI 配置不完整，请在 env.yaml 中填写 api_base, api_key, model"

    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return f"[ERROR] AI API HTTP {e.code}: {body[:200]}"
    except Exception as e:
        return f"[ERROR] AI 调用失败: {e}"


def load_env_config(env_path: str = None) -> dict:
    """加载 env.yaml 配置"""
    if not env_path:
        env_path = os.path.expanduser("~/.hermes/kaka-deploy/env.yaml")
    if not os.path.exists(env_path):
        # 尝试当前目录
        env_path = "env.yaml"
    if not os.path.exists(env_path):
        return {}
    with open(env_path, "r") as f:
        # 简单 YAML 解析（避免依赖 pyyaml）
        return parse_simple_yaml(f.read())


def parse_simple_yaml(text: str) -> dict:
    """简易 YAML 解析器（不依赖 pyyaml）"""
    result = {}
    stack = [result]
    current_indent = 0

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        # 弹栈到正确层级
        while stack and indent < len(stack) - 1:
            stack.pop()
        parent = stack[-1]
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value:
                parent[key] = value
            else:
                new_dict = {}
                parent[key] = new_dict
                stack.append(new_dict)
    return result


def generate_config_from_input(user_input: str, template: str, config: dict = None) -> str:
    """用 AI 根据用户自然语言输入生成配置"""
    system = """你是一个配置生成助手。根据用户的自然语言描述，生成 YAML 配置文件。
只输出 YAML 内容，不要额外解释。保持模板结构，填入具体值。"""
    prompt = f"""模板：
{template}

用户描述：
{user_input}

请根据用户描述，填充模板中的空值。只输出填充后的 YAML。"""
    return call_ai(prompt, system, config)


def interactive_fill_config(env_path: str, template_path: str, config: dict = None):
    """交互式填充配置"""
    with open(template_path) as f:
        template = f.read()

    print("\n📝 配置向导")
    print("请描述你的部署需求，AI 会帮你生成配置。")
    print("例如：'我叫张三，机器人叫小助手，用 Claude 模型，飞书账号 app_id=xxx'\n")

    user_input = input("请描述（或输入 'manual' 手动编辑）: ").strip()
    if user_input.lower() == "manual":
        # 手动模式：复制模板让用户编辑
        import shutil
        shutil.copy(template_path, env_path)
        print(f"✅ 模板已复制到 {env_path}，请手动编辑。")
        return

    if not user_input:
        print("⚠️ 未输入内容，跳过。")
        return

    print("\n🤖 AI 生成中...")
    result = generate_config_from_input(user_input, template, config)
    if result.startswith("[ERROR]"):
        print(result)
        print("⚠️ AI 生成失败，回退到手动模式。")
        import shutil
        shutil.copy(template_path, env_path)
        print(f"✅ 模板已复制到 {env_path}，请手动编辑。")
        return

    with open(env_path, "w") as f:
        f.write(result)
    print(f"✅ 配置已生成到 {env_path}")
    print("请检查并修改后继续。")


def validate_config(env_path: str) -> list:
    """校验配置完整性，返回缺失项列表"""
    config = load_env_config(env_path)
    missing = []

    ai = config.get("ai", {})
    if not ai.get("api_base"):
        missing.append("ai.api_base")
    if not ai.get("api_key"):
        missing.append("ai.api_key")
    if not ai.get("model"):
        missing.append("ai.model")

    identity = config.get("identity", {})
    if not identity.get("agent_name"):
        missing.append("identity.agent_name")
    if not identity.get("master_name"):
        missing.append("identity.master_name")

    return missing
