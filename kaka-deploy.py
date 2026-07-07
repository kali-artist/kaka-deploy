#!/usr/bin/env python3
"""
kaka-deploy - AI 辅助 Hermes Agent 一键部署工具
从源实例打包技能/配置，到目标实例一键部署

用法:
  python3 kaka-deploy.py pack     # 在源实例打包
  python3 kaka-deploy.py deploy   # 在目标实例部署
  python3 kaka-deploy.py status   # 检查部署状态
  python3 kaka-deploy.py list     # 列出技能包内容
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# 确保能 import lib 模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "lib"))


def cmd_pack(args):
    """打包模式：在源实例执行，生成技能包"""
    print("📦 kaka-deploy 打包模式\n")
    pack_script = os.path.join(SCRIPT_DIR, "scripts", "pack_skills.py")
    if not os.path.exists(pack_script):
        print(f"❌ 打包脚本不存在: {pack_script}")
        return 1
    r = subprocess.run([sys.executable, pack_script], cwd=SCRIPT_DIR)
    return r.returncode


def cmd_deploy(args):
    """部署模式：在目标实例执行"""
    print("🚀 kaka-deploy 部署模式\n")

    deploy_dir = SCRIPT_DIR
    env_path = args.env or os.path.expanduser("~/.hermes/kaka-deploy/env.yaml")
    template_path = os.path.join(deploy_dir, "config-templates", "env.template.yaml")

    # Step 0: 检查/生成 env.yaml
    if not os.path.exists(env_path):
        print(f"📝 配置文件不存在: {env_path}")
        os.makedirs(os.path.dirname(env_path), exist_ok=True)

        if args.ai_assist:
            from ai import interactive_fill_config
            interactive_fill_config(env_path, template_path)
        else:
            import shutil
            shutil.copy(template_path, env_path)
            print(f"✅ 模板已复制到 {env_path}")
            print("请编辑后重新运行: kaka-deploy deploy")
            return 0

    # 校验配置
    from ai import validate_config
    missing = validate_config(env_path)
    if missing:
        print(f"⚠️ 配置不完整，缺失: {', '.join(missing)}")
        print(f"请编辑: {env_path}")
        if not args.force:
            return 1

    # 确认
    if not args.yes:
        print(f"\n即将使用配置 {env_path} 部署。")
        confirm = input("确认部署? (y/N): ").strip().lower()
        if confirm != "y":
            print("已取消。")
            return 0

    # 执行部署
    from deploy import deploy
    steps = args.steps.split(",") if args.steps else None
    ok = deploy(env_path, deploy_dir, steps)
    return 0 if ok else 1


def cmd_status(args):
    """检查当前实例部署状态"""
    print("📊 kaka-deploy 状态检查\n")

    checks = []

    # Hermes 安装
    r = subprocess.run("which hermes", shell=True, capture_output=True, text=True)
    hermes_ok = r.returncode == 0
    checks.append(("Hermes Agent", hermes_ok, r.stdout.strip() if hermes_ok else "未安装"))

    # SOUL.md
    soul_path = os.path.expanduser("~/.hermes/SOUL.md")
    soul_ok = os.path.exists(soul_path)
    size = os.path.getsize(soul_path) if soul_ok else 0
    checks.append(("SOUL.md", soul_ok, f"{size} chars" if soul_ok else "缺失"))

    # config.yaml
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    config_ok = os.path.exists(config_path)
    checks.append(("config.yaml", config_ok, "存在" if config_ok else "缺失"))

    # 技能数量
    skills_dir = os.path.expanduser("~/.hermes/skills")
    skill_count = 0
    if os.path.exists(skills_dir):
        skill_count = sum(1 for d in os.listdir(skills_dir)
                         if os.path.isdir(os.path.join(skills_dir, d)))
    checks.append(("Hermes 技能", skill_count > 0, f"{skill_count} 个"))

    # Lark 技能
    lark_dir = os.path.expanduser("~/.agents/skills")
    lark_count = 0
    if os.path.exists(lark_dir):
        lark_count = sum(1 for d in os.listdir(lark_dir)
                        if os.path.isdir(os.path.join(lark_dir, d)))
    checks.append(("Lark 技能", lark_count > 0, f"{lark_count} 个"))

    # MEMORY/USER
    memory_path = os.path.expanduser("~/.hermes/memories/MEMORY.md")
    user_path = os.path.expanduser("~/.hermes/memories/USER.md")
    checks.append(("MEMORY.md", os.path.exists(memory_path), "存在" if os.path.exists(memory_path) else "缺失"))
    checks.append(("USER.md", os.path.exists(user_path), "存在" if os.path.exists(user_path) else "缺失"))

    # 输出
    for name, ok, detail in checks:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}: {detail}")

    all_ok = all(c[1] for c in checks)
    print(f"\n{'🎉 全部就绪！' if all_ok else '⚠️ 部分缺失，需要部署或修复。'}")
    return 0 if all_ok else 1


def cmd_list(args):
    """列出技能包内容"""
    manifest_path = os.path.join(SCRIPT_DIR, "skills-pack", "manifest.json")
    if not os.path.exists(manifest_path):
        print("❌ 技能包不存在，请先运行: kaka-deploy pack")
        return 1

    with open(manifest_path) as f:
        manifest = json.load(f)

    print("📋 技能包清单\n")

    # Hermes 技能
    skills = manifest.get("skills", {})
    hermes_skills = skills.get("hermes_skills", [])
    print(f"Hermes 技能 ({len(hermes_skills)} 个):")
    # 按分类分组显示
    by_category = {}
    for s in hermes_skills:
        parts = s.split("/", 1)
        cat = parts[0] if len(parts) > 1 else "other"
        name = parts[1] if len(parts) > 1 else parts[0]
        by_category.setdefault(cat, []).append(name)
    for cat in sorted(by_category):
        print(f"  [{cat}] ({len(by_category[cat])})")
        for s in sorted(by_category[cat]):
            print(f"    - {s}")

    # Lark 技能
    lark_skills = skills.get("lark_skills", [])
    print(f"\nLark 技能 ({len(lark_skills)} 个):")
    for s in sorted(lark_skills):
        print(f"  - {s}")

    # 联动组
    linkages = manifest.get("linkage_groups", {})
    if linkages:
        print(f"\n联动组 ({len(linkages)} 组):")
        for group_id, group in linkages.items():
            print(f"  [{group_id}] {group.get('name', '')} → {group.get('skills', [])}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="kaka-deploy - AI 辅助 Hermes Agent 一键部署工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s pack                    # 源实例打包
  %(prog)s deploy --ai-assist      # 目标实例 AI 辅助部署
  %(prog)s deploy --yes            # 跳过确认
  %(prog)s status                  # 检查状态
  %(prog)s list                    # 列出技能包
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # pack
    p_pack = subparsers.add_parser("pack", help="在源实例打包技能和配置")

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="在目标实例部署")
    p_deploy.add_argument("--env", help="env.yaml 路径（默认 ~/.hermes/kaka-deploy/env.yaml）")
    p_deploy.add_argument("--ai-assist", action="store_true", help="AI 辅助生成配置")
    p_deploy.add_argument("--yes", "-y", action="store_true", help="跳过确认")
    p_deploy.add_argument("--force", action="store_true", help="强制部署（忽略配置校验）")
    p_deploy.add_argument("--steps", help="指定步骤（逗号分隔: install,config,skills,hooks,start）")

    # status
    p_status = subparsers.add_parser("status", help="检查部署状态")

    # list
    p_list = subparsers.add_parser("list", help="列出技能包内容")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "pack": cmd_pack,
        "deploy": cmd_deploy,
        "status": cmd_status,
        "list": cmd_list,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
