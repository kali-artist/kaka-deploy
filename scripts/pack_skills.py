#!/usr/bin/env python3
"""技能打包脚本 - 扫描、清理、占位符替换、输出"""

import json
import os
import re
import shutil
from pathlib import Path

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "..", "skills-pack", "manifest.json")
HERMES_SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
LARK_SKILLS_DIR = os.path.expanduser("~/.agents/skills")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "skills-pack")

# 占位符替换映射 (原值 → 占位符)，按长度降序排列避免部分匹配
PLACEHOLDER_MAP = [
    ("o9cq80x0qdZXmeUgF2y6MTNPkEuw", "{{WECHAT_USER_ID}}"),
    ("ou_9a8733eba2872a3ae5fa927c6ce25df8", "{{FEISHU_OPEN_ID}}"),
    ("ou_418b8f9cb7e9f3189b954c7aa89e1541", "{{FEISHU_OPEN_ID}}"),
    ("ou_1259171d0693a0176f0ad4c5804c3735", "{{FEISHU_OPEN_ID}}"),
    ("ou_eae08920be40b003e42fbc2c087348a6", "{{FEISHU_OPEN_ID}}"),
    ("08b2393951814d95ca057d9822eb3675", "{{CLOUDFLARE_ACCOUNT_ID}}"),
    ("FdOnbhQrBaMdIxsFFM3cNJS4njg", "{{FEISHU_BASE_TOKEN}}"),
    ("W3UmbBXcsa1nmksElh8cicVDnnT", "{{FEISHU_KB_TOKEN}}"),
    ("tblXCSJu59D3Dd0z", "{{FEISHU_TABLE_ID}}"),
    ("tblHY6nPi5turEK2", "{{FEISHU_KB_TABLE_ID}}"),
    ("ucng6d8rugac", "{{FEISHU_DOMAIN}}"),
    ("39.97.248.219", "{{SERVER_IP}}"),
    ("kali-artist", "{{GITHUB_USERNAME}}"),
    ("~/kaka-tmp", "{{AGENT_TMP_DIR}}"),
    ("wiredo", "{{FEISHU_USER_ID}}"),
]

# 需要特殊处理的替换（上下文敏感）
CONTEXT_REPLACEMENTS = [
    # frontmatter author: lili → author: kaka-deploy
    (r'(author:\s*)lili', r'\1kaka-deploy'),
    # 身份声明中的 kaka 和 卡力（仅在身份声明语境中替换）
    (r'我是\s*kaka', '我是 {{AGENT_NAME}}'),
    (r'kaka\s*是.*?由.*?创造', '{{AGENT_NAME}} 是由 {{CREATOR_NAME}} 创造'),
    (r'由\s*卡力\s*创造', '由 {{CREATOR_NAME}} 创造'),
    (r'称呼.*?卡力.*?为主人', '称呼 {{MASTER_NAME}} 为主人'),
    (r'卡力主人', '{{MASTER_NAME}} 主人'),
    # 单独出现的 lili（作为实例名，不在路径中）
    (r'(?<![/\w-])lili(?![/\w-])', '{{INSTANCE_NAME}}'),
    # ~/github-token 路径
    (r'~/\.github-token', '{{GITHUB_TOKEN_PATH}}'),
]

# 不替换的路径（标准路径，所有实例通用）
KEEP_PATHS = ["~/.hermes/skills", "~/.hermes/", "~/.agents/skills"]

# 文件扩展名白名单
VALID_EXTENSIONS = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".toml", ".cfg", ".conf"}


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def should_exclude(file_path, exclude_paths):
    """检查文件是否在排除路径中"""
    for ep in exclude_paths:
        if ep in file_path:
            return True
    return False


def clean_multicontent(content, clean_sections):
    """删除多实例同步章节"""
    for section in clean_sections:
        pattern = section["pattern"]
        flags = re.DOTALL if section.get("flags") == "DOTALL" else 0
        content = re.sub(pattern, "", content)
    return content


def replace_placeholders(content):
    """占位符替换"""
    # 先做上下文敏感替换
    for pattern, replacement in CONTEXT_REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    
    # 再做直接替换
    for original, placeholder in PLACEHOLDER_MAP:
        # 跳过在 KEEP_PATHS 中的
        if original in ("~/kaka-tmp",):
            # 只替换 ~/kaka-tmp，不替换 ~/.hermes/skills 等
            pass
        content = content.replace(original, placeholder)
    
    return content


def process_file(src_path, dst_path, manifest):
    """处理单个文件：清理+占位符替换"""
    try:
        with open(src_path, "r", errors="ignore") as f:
            content = f.read()
    except:
        return False
    
    # 清理多实例章节
    content = clean_multicontent(content, manifest.get("clean_sections", []))
    
    # 占位符替换
    content = replace_placeholders(content)
    
    # 写入目标
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "w") as f:
        f.write(content)
    
    return True


def pack_skill(src_dir, dst_dir, skill_name, manifest):
    """打包单个技能"""
    exclude_paths = manifest.get("exclude_paths", [])
    packed_files = 0
    
    if not os.path.exists(src_dir):
        print(f"  ⚠️ NOT FOUND: {skill_name} ({src_dir})")
        return 0
    
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            src_path = os.path.join(root, f)
            rel_path = os.path.relpath(src_path, src_dir)
            
            # 排除非必要文件
            if should_exclude(rel_path, exclude_paths):
                continue
            
            # 只处理文本文件
            ext = os.path.splitext(f)[1]
            if ext not in VALID_EXTENSIONS:
                # 非文本文件直接复制
                dst_path = os.path.join(dst_dir, rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                packed_files += 1
                continue
            
            dst_path = os.path.join(dst_dir, rel_path)
            if process_file(src_path, dst_path, manifest):
                packed_files += 1
    
    return packed_files


def pack_hermes_skills(manifest):
    """打包 Hermes 技能"""
    skills = manifest["skills"]["hermes_skills"]
    exclude = set(manifest.get("exclude_skills", []))
    output = os.path.join(OUTPUT_DIR, "hermes")
    total = 0
    
    print(f"\n📦 打包 Hermes 技能 ({len(skills)} 个)...")
    for skill_path in skills:
        if skill_path in exclude:
            print(f"  ❌ EXCLUDED: {skill_path}")
            continue
        
        skill_name = skill_path.split("/")[-1]
        src = os.path.join(HERMES_SKILLS_DIR, skill_path)
        dst = os.path.join(output, skill_path)
        
        count = pack_skill(src, dst, skill_path, manifest)
        if count > 0:
            total += count
            print(f"  ✅ {skill_path} ({count} files)")
    
    return total


def pack_lark_skills(manifest):
    """打包 lark-cli 技能"""
    skills = manifest["skills"]["lark_skills"]
    output = os.path.join(OUTPUT_DIR, "lark")
    total = 0
    
    print(f"\n📦 打包 lark-cli 技能 ({len(skills)} 个)...")
    for skill_name in skills:
        src = os.path.join(LARK_SKILLS_DIR, skill_name)
        dst = os.path.join(output, skill_name)
        
        count = pack_skill(src, dst, skill_name, manifest)
        if count > 0:
            total += count
            print(f"  ✅ {skill_name} ({count} files)")
    
    return total


def verify_placeholders(output_dir):
    """验证输出中不包含原始个性化值"""
    leaks = []
    sensitive_values = [
        "39.97.248.219", "o9cq80x0qdZXmeUgF2y6MTNPkEuw", "wiredo",
        "FdOnbhQrBaMdIxsFFM3cNJS4njg", "tblXCSJu59D3Dd0z",
        "W3UmbBXcsa1nmksElh8cicVDnnT", "tblHY6nPi5turEK2",
        "ucng6d8rugac", "08b2393951814d95ca057d9822eb3675",
        "ou_9a8733eba2872a3ae5fa927c6ce25df8",
        "ou_418b8f9cb7e9f3189b954c7aa89e1541",
    ]
    
    for root, dirs, files in os.walk(output_dir):
        for f in files:
            fpath = os.path.join(root, f)
            try:
                with open(fpath, "r", errors="ignore") as fh:
                    content = fh.read()
                    for val in sensitive_values:
                        if val in content:
                            rel = os.path.relpath(fpath, output_dir)
                            leaks.append(f"{rel}: contains {val[:20]}...")
            except:
                pass
    
    return leaks


def main():
    print("🚀 kaka-deploy 技能打包工具\n")
    
    manifest = load_manifest()
    
    # 清理输出目录
    output = os.path.join(OUTPUT_DIR, "hermes")
    if os.path.exists(output):
        shutil.rmtree(output)
    output = os.path.join(OUTPUT_DIR, "lark")
    if os.path.exists(output):
        shutil.rmtree(output)
    
    # 打包
    hermes_count = pack_hermes_skills(manifest)
    lark_count = pack_lark_skills(manifest)
    
    # 验证
    print("\n🔍 验证占位符替换...")
    all_output = os.path.join(OUTPUT_DIR, "hermes")
    leaks = verify_placeholders(all_output)
    all_output2 = os.path.join(OUTPUT_DIR, "lark")
    leaks += verify_placeholders(all_output2)
    
    if leaks:
        print(f"\n⚠️ 发现 {len(leaks)} 处未替换的个性化值:")
        for l in leaks[:20]:
            print(f"  🔴 {l}")
    else:
        print("✅ 所有人性化值已替换")
    
    print(f"\n✅ 打包完成: {hermes_count} hermes + {lark_count} lark 文件")
    return leaks


if __name__ == "__main__":
    main()
