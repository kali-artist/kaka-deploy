#!/usr/bin/env python3
"""
部署执行模块 - 执行实际的部署步骤
1. 安装 Hermes Agent
2. 写入配置文件
3. 复制技能包
4. 注册 hooks
5. 启动服务
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 添加 lib 到 path
sys.path.insert(0, str(Path(__file__).parent))
from ai import load_env_config, parse_simple_yaml


HERMES_HOME = os.path.expanduser("~/.hermes")
SKILLS_DIR = os.path.join(HERMES_HOME, "skills")
LARK_SKILLS_DIR = os.path.join(HERMES_HOME, ".agents", "skills")
MEMORIES_DIR = os.path.join(HERMES_HOME, "memories")


def run(cmd: str, check: bool = True, capture: bool = False) -> tuple:
    """执行 shell 命令"""
    if capture:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if check and r.returncode != 0:
            print(f"❌ 命令失败: {cmd}")
            print(r.stderr[-500:] if r.stderr else "")
        return r.returncode, r.stdout, r.stderr
    else:
        print(f"  ▸ {cmd}")
        r = subprocess.run(cmd, shell=True, timeout=300)
        if check and r.returncode != 0:
            raise RuntimeError(f"命令失败: {cmd} (exit={r.returncode})")
        return r.returncode, "", ""


def step_install_hermes(env: dict) -> bool:
    """Step 1: 安装 Hermes Agent"""
    print("\n📦 Step 1: 安装 Hermes Agent")

    # 检查是否已安装
    r = subprocess.run("which hermes", shell=True, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✅ Hermes 已安装")
        return True

    # 尝试 pip 安装
    print("  ⏳ 安装中...")
    code, _, err = run("pip install hermes-agent 2>&1", check=False, capture=True)
    if code != 0:
        # 尝试从 GitHub 安装
        print("  ⏳ pip 失败，尝试 GitHub...")
        code2, _, err2 = run(
            "pip install git+https://github.com/kali-artist/hermes-agent.git 2>&1",
            check=False, capture=True
        )
        if code2 != 0:
            print(f"  ❌ 安装失败: {err2[-300:]}")
            return False

    # 验证
    r = subprocess.run("which hermes", shell=True, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✅ Hermes 安装成功")
        return True
    else:
        print("  ❌ Hermes 安装后仍找不到命令")
        return False


def step_write_config(env: dict, deploy_dir: str) -> bool:
    """Step 2: 写入配置文件"""
    print("\n⚙️ Step 2: 写入配置")

    os.makedirs(HERMES_HOME, exist_ok=True)

    # 写入 SOUL.md
    soul_template = os.path.join(deploy_dir, "config-templates", "soul.template.md")
    if os.path.exists(soul_template):
        soul_content = render_template(soul_template, env)
        soul_path = os.path.join(HERMES_HOME, "SOUL.md")
        with open(soul_path, "w") as f:
            f.write(soul_content)
        print(f"  ✅ SOUL.md ({len(soul_content)} chars)")

    # 写入 MEMORY.md
    memory_path = os.path.join(MEMORIES_DIR, "MEMORY.md")
    os.makedirs(MEMORIES_DIR, exist_ok=True)
    memory_template = os.path.join(deploy_dir, "config-templates", "memory.template.md")
    if os.path.exists(memory_template):
        memory_content = render_template(memory_template, env)
        with open(memory_path, "w") as f:
            f.write(memory_content)
        print(f"  ✅ MEMORY.md ({len(memory_content)} chars)")
    else:
        # 最小化默认
        with open(memory_path, "w") as f:
            f.write("🔴 反虚报第一铁律：绝对禁止任何说谎、糊弄、瞎编、蒙混、虚报进度/功能的行为。\n")

    # 写入 USER.md
    user_path = os.path.join(MEMORIES_DIR, "USER.md")
    with open(user_path, "w") as f:
        master = env.get("identity", {}).get("master_name", "主人")
        f.write(f"# 用户档案\n- 用户名：{master}\n- 沟通偏好：待填写\n")
    print(f"  ✅ USER.md")

    # 写入 config.yaml（如不存在）
    config_path = os.path.join(HERMES_HOME, "config.yaml")
    if not os.path.exists(config_path):
        ai = env.get("ai", {})
        agent_name = env.get("identity", {}).get("agent_name", "agent")
        config_yaml = f"""# Hermes Agent 配置
model:
  provider: custom
  model: {ai.get('model', '')}
  api_base: {ai.get('api_base', '')}
  api_key: {ai.get('api_key', '')}

agent:
  name: {agent_name}
  soul: ~/.hermes/SOUL.md

memory:
  provider: holographic
  auto_extract: true
"""
        with open(config_path, "w") as f:
            f.write(config_yaml)
        print(f"  ✅ config.yaml (新建)")
    else:
        print(f"  ⏭️ config.yaml 已存在，跳过")

    return True


def step_copy_skills(env: dict, deploy_dir: str) -> bool:
    """Step 3: 复制技能包"""
    print("\n📂 Step 3: 复制技能包")

    skills_pack = os.path.join(deploy_dir, "skills-pack")
    hermes_skills = os.path.join(skills_pack, "hermes")
    lark_skills = os.path.join(skills_pack, "lark")

    # 复制 hermes 技能
    if os.path.exists(hermes_skills):
        os.makedirs(SKILLS_DIR, exist_ok=True)
        count = 0
        for category_dir in os.listdir(hermes_skills):
            cat_path = os.path.join(hermes_skills, category_dir)
            if not os.path.isdir(cat_path):
                continue
            for skill_dir in os.listdir(cat_path):
                src = os.path.join(cat_path, skill_dir)
                dst = os.path.join(SKILLS_DIR, skill_dir)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    count += 1
        print(f"  ✅ Hermes 技能: {count} 个")

    # 复制 lark 技能
    if os.path.exists(lark_skills):
        os.makedirs(LARK_SKILLS_DIR, exist_ok=True)
        count = 0
        for skill_dir in os.listdir(lark_skills):
            src = os.path.join(lark_skills, skill_dir)
            dst = os.path.join(LARK_SKILLS_DIR, skill_dir)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                count += 1
        print(f"  ✅ Lark 技能: {count} 个")

    return True


def step_register_hooks(env: dict, deploy_dir: str) -> bool:
    """Step 4: 注册 hooks"""
    print("\n🪝 Step 4: 注册 Hooks")

    # 检查 permission-management 技能
    perm_hook = os.path.join(SKILLS_DIR, "permission-management", "scripts", "tool_pre_call_hook.py")
    if os.path.exists(perm_hook):
        print(f"  ✅ permission-management hooks 已随技能安装")
    else:
        print(f"  ⏭️ permission-management 未安装，跳过 hooks")

    # 检查 config.yaml 中的 hooks 配置
    config_path = os.path.join(HERMES_HOME, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            content = f.read()
        if "hooks" not in content:
            # 追加 hooks 配置
            hooks_config = """
hooks:
  tool_pre_call:
    - command: "python3 ~/.hermes/skills/permission-management/scripts/tool_pre_call_hook.py"
      timeout: 5000
"""
            with open(config_path, "a") as f:
                f.write(hooks_config)
            print(f"  ✅ hooks 配置已追加到 config.yaml")
        else:
            print(f"  ⏭️ hooks 已配置")

    return True


def step_start_service(env: dict) -> bool:
    """Step 5: 启动服务"""
    print("\n🚀 Step 5: 启动服务")

    # 检查是否已有 hermes 在运行
    code, out, _ = run("pgrep -f 'hermes' -a", check=False, capture=True)
    if "hermes" in out and "gateway" in out:
        print("  ✅ Hermes 服务已在运行")
        return True

    # 启动 gateway
    print("  ⏳ 启动 Hermes Gateway...")
    code, _, err = run("hermes gateway start 2>&1", check=False, capture=True)
    if code == 0:
        print("  ✅ Gateway 启动成功")
        return True
    else:
        print(f"  ⚠️ Gateway 启动返回 {code}")
        print(f"  手动启动: hermes gateway start")
        return False


def render_template(template_path: str, env: dict) -> str:
    """渲染模板，替换占位符"""
    with open(template_path) as f:
        content = f.read()

    identity = env.get("identity", {})
    ai = env.get("ai", {})
    feishu = env.get("feishu", {})
    github = env.get("github", {})
    wechat = env.get("wechat", {})
    cloudflare = env.get("cloudflare", {})
    paths = env.get("paths", {})

    replacements = {
        "{{AGENT_NAME}}": identity.get("agent_name", "agent"),
        "{{MASTER_NAME}}": identity.get("master_name", "主人"),
        "{{CREATOR_NAME}}": identity.get("creator_name", identity.get("master_name", "主人")),
        "{{WECHAT_USER_ID}}": wechat.get("user_id", ""),
        "{{FEISHU_USER_ID}}": feishu.get("user_id", ""),
        "{{FEISHU_OPEN_ID}}": feishu.get("open_id", ""),
        "{{FEISHU_DOMAIN}}": feishu.get("domain", ""),
        "{{FEISHU_BASE_TOKEN}}": feishu.get("base_token", ""),
        "{{FEISHU_TABLE_ID}}": feishu.get("table_id", ""),
        "{{GITHUB_USERNAME}}": github.get("username", ""),
        "{{CLOUDFLARE_ACCOUNT_ID}}": cloudflare.get("account_id", ""),
        "{{SERVER_IP}}": env.get("server", {}).get("ip", ""),
        "{{AGENT_TMP_DIR}}": paths.get("agent_tmp_dir", "~/.hermes/tmp"),
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    return content


def deploy(env_path: str, deploy_dir: str, steps: list = None) -> bool:
    """执行完整部署流程"""
    env = load_env_config(env_path)
    if not env:
        print(f"❌ 无法加载配置: {env_path}")
        return False

    if not steps:
        steps = ["install", "config", "skills", "hooks", "start"]

    step_map = {
        "install": step_install_hermes,
        "config": step_write_config,
        "skills": step_copy_skills,
        "hooks": step_register_hooks,
        "start": step_start_service,
    }

    results = {}
    for step_name in steps:
        if step_name in step_map:
            try:
                results[step_name] = step_map[step_name](env, deploy_dir)
            except Exception as e:
                print(f"\n❌ Step {step_name} 异常: {e}")
                results[step_name] = False
                break

    # 汇总
    print("\n" + "=" * 50)
    print("📊 部署汇总")
    for step, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {step}")

    all_ok = all(results.values())
    if all_ok:
        print("\n🎉 部署完成！")
    else:
        print("\n⚠️ 部分步骤失败，请检查后重试。")
    return all_ok
