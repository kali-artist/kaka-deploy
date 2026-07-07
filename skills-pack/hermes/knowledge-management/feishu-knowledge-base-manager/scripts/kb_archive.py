#!/usr/bin/env python3
"""
飞书知识库自动化归档脚本
功能：文档归档、元数据补全、智能分类、质量评分
用法：python kb_archive.py <doc_token>
"""

import json
import os
import sys
import re
import argparse
import requests
from datetime import datetime

API_BASE = "https://open.feishu.cn/open-apis"
NO_PROXY = {"http": None, "https": None, "all": None}

# 知识库配置（固定 - kaka 的飞书知识库）
KB_APP_TOKEN = "{{FEISHU_KB_TOKEN}}"
KB_TABLE_ID = "{{FEISHU_KB_TABLE_ID}}"  # 真实 table_id

# 凭证优先级：~/.feishu/config.json > ~/.hermes/.env
CONFIG_PATHS = [
    os.path.expanduser("~/.feishu/config.json"),
    os.path.expanduser("~/.hermes/.env"),
]

# ============== 6 大知识库分类规则 ==============
KNOWLEDGE_BASES = {
    "SKL": {"name": "技能库", "emoji": "🤖", "keywords": ["技能", "skill", "自动化", "脚本", "工具", "使用指南", "操作手册", "SOP"]},
    "RES": {"name": "研究库", "emoji": "📚", "keywords": ["研究", "调研", "分析", "报告", "对比", "趋势", "竞品", "行业", "技术"]},
    "PRJ": {"name": "项目库", "emoji": "💻", "keywords": ["项目", "方案", "设计", "架构", "里程碑", "排期", "需求", "规划"]},
    "TPL": {"name": "模板库", "emoji": "📐", "keywords": ["模板", "template", "规范", "标准", "格式"]},
    "OPS": {"name": "运营库", "emoji": "📊", "keywords": ["运营", "统计", "报表", "KPI", "月报", "质量", "优化", "数据"]},
    "ARC": {"name": "归档库", "emoji": "📌", "keywords": ["旧版", "历史", "归档", "已废弃", "备份", "废弃"]},
}

# ============== 17 种 AI 角色匹配规则 ==============
AI_ROLES = {
    "飞书知识库管理员": {"keywords": ["飞书", "知识库", "文档", "归档", "分类"]},
    "开发工程师": {"keywords": ["代码", "开发", "python", "脚本", "API", "函数", "编程"]},
    "研究分析师": {"keywords": ["研究", "调研", "分析", "报告", "对比", "数据"]},
    "信息架构师": {"keywords": ["架构", "结构", "分类", "体系", "数据结构"]},
    "代码审查员": {"keywords": ["review", "审查", "代码质量", "最佳实践"]},
    "测试工程师": {"keywords": ["测试", "验证", "质量", "检查"]},
    "架构师": {"keywords": ["架构", "设计", "系统", "技术选型"]},
    "设计师": {"keywords": ["设计", "UI", "UX", "视觉", "界面"]},
    "文案撰写": {"keywords": ["文案", "撰写", "内容", "文字", "修辞"]},
    "项目经理": {"keywords": ["项目", "管理", "协调", "进度", "排期"]},
    "质量检查": {"keywords": ["质量", "检查", "验收", "审核"]},
    "流程优化师": {"keywords": ["流程", "优化", "效率", "改进"]},
    "数据分析师": {"keywords": ["数据", "分析", "统计", "可视化"]},
    "用户助手": {"keywords": ["用户", "助手", "支持", "解答"]},
}

# ============== 业务场景 ==============
BUSINESS_SCENES = ["知识库维护", "技能开发", "技术研究", "项目交付", "文档模板", "运营分析", "其他"]

# ============== 标签库 ==============
TAGS_POOL = ["飞书", "自动化", "技能", "最佳实践", "API", "Python", "研究", "方案", "模板", "运维", "数据分析", "质量"]


def load_config():
    """加载飞书凭证，直接复用 feishu-automation-suite 的配置"""
    import json
    from pathlib import Path
    
    feishu_config = Path.home() / ".feishu" / "config.json"
    if feishu_config.exists():
        with open(feishu_config) as f:
            cfg = json.load(f)
        return cfg["app_id"], cfg["app_secret"]
    
    hermes_env = Path.home() / ".hermes" / ".env"
    if hermes_env.exists():
        env = {}
        with open(hermes_env) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
        return env.get("FEISHU_APP_ID"), env.get("FEISHU_APP_SECRET")
    
    raise Exception("❌ 找不到飞书配置！")


def get_token(app_id, app_secret):
    resp = requests.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        proxies=NO_PROXY
    )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取 Token 失败: {data}")
    return data["tenant_access_token"]


def get_document_content(doc_token, headers):
    """读取飞书文档的纯文本内容，用于分类和评分"""
    url = f"{API_BASE}/docx/v1/documents/{doc_token}/blocks?page_size=500"
    resp = requests.get(url, headers=headers, proxies=NO_PROXY)
    result = resp.json()
    
    if result.get("code") != 0:
        print(f"   ⚠️ 读取文档内容失败: {result}")
        return ""
    
    # 简单提取所有文本内容
    content_parts = []
    for item in result["data"]["items"]:
        # 从各种块类型中提取文本
        for key in ["text", "heading1", "heading2", "heading3", "heading4", "code"]:
            if key in item and "elements" in item[key]:
                for elem in item[key]["elements"]:
                    if "text_run" in elem:
                        content_parts.append(elem["text_run"]["content"])
    
    return "\n".join(content_parts)


def check_doc_exists(doc_token, headers):
    """检查文档是否已经在知识库中（避免重复）"""
    url = f"{API_BASE}/bitable/v1/apps/{KB_APP_TOKEN}/tables/{KB_TABLE_ID}/records/search"
    
    resp = requests.post(url, headers=headers, json={
        "filter": {
            "conjunction": "and",
            "conditions": [{
                "field_name": "doc_token",
                "operator": "is",
                "value": doc_token
            }]
        },
        "page_size": 1
    }, proxies=NO_PROXY)
    
    result = resp.json()
    if result.get("code") != 0:
        return None
    
    records = result["data"].get("items", [])
    return records[0]["record_id"] if records else None


def write_to_bitable(headers, fields):
    """写入一条记录到多维表格"""
    url = f"{API_BASE}/bitable/v1/apps/{KB_APP_TOKEN}/tables/{KB_TABLE_ID}/records"
    
    resp = requests.post(url, headers=headers, json={"fields": fields}, proxies=NO_PROXY)
    result = resp.json()
    
    if result.get("code") == 0:
        return result["data"]["record"]["record_id"]
    else:
        print(f"   ❌ 写入多维表格失败: {result}")
        return None


def update_bitable(headers, record_id, fields):
    """更新多维表格中的一条记录"""
    url = f"{API_BASE}/bitable/v1/apps/{KB_APP_TOKEN}/tables/{KB_TABLE_ID}/records/{record_id}"
    
    resp = requests.patch(url, headers=headers, json={"fields": fields}, proxies=NO_PROXY)
    result = resp.json()
    
    if result.get("code") == 0:
        return True
    else:
        print(f"   ❌ 更新多维表格失败: {result}")
        return False


# ============== 6 大知识库分类规则 ==============

def classify_kb(content, title=""):
    """智能匹配知识库分类"""
    text = (title + " " + content).lower()
    scores = {}
    for kb_id, kb_info in KNOWLEDGE_BASES.items():
        score = sum(1 for kw in kb_info["keywords"] if kw.lower() in text)
        scores[kb_id] = score

    max_score = max(scores.values())
    if max_score >= 1:
        best_kb = max(scores.items(), key=lambda x: x[1])[0]
        return best_kb, KNOWLEDGE_BASES[best_kb]

    # 默认技能库
    return "SKL", KNOWLEDGE_BASES["SKL"]


def classify_role(content, title=""):
    """智能匹配负责AI角色"""
    text = (title + " " + content).lower()
    scores = {}
    for role, info in AI_ROLES.items():
        score = sum(1 for kw in info["keywords"] if kw.lower() in text)
        scores[role] = score

    max_score = max(scores.values())
    if max_score >= 1:
        return max(scores.items(), key=lambda x: x[1])[0]

    return "用户助手"


def recommend_tags(content, title="", count=4):
    """智能推荐标签"""
    text = (title + " " + content).lower()
    matched = [tag for tag in TAGS_POOL if tag.lower() in text]
    return matched[:count] if matched else ["待分类"]


def calc_quality_score(content, word_count, image_count=0):
    """计算文档质量评分（0-100分）"""
    score = 0

    # 1. 内容充实度 20分
    if word_count > 1000:
        score += 20
    elif word_count > 500:
        score += 15
    elif word_count > 200:
        score += 10
    else:
        score += 5

    # 2. 结构清晰度 25分
    h2_count = content.count("## ")
    h3_count = content.count("### ")
    if h2_count >= 3:
        score += 25
    elif h2_count >= 2:
        score += 20
    elif h2_count >= 1:
        score += 15
    else:
        score += 5

    # 3. 富文本多样性 15分
    list_count = content.count("\n- ") + content.count("\n1. ")
    code_count = content.count("```")
    table_count = content.count("| ")
    diversity = 0
    if list_count > 0:
        diversity += 5
    if code_count >= 2:
        diversity += 5
    if table_count > 0:
        diversity += 5
    score += diversity

    # 4. 图片丰富度 10分
    score += min(10, image_count * 3)

    # 5. 可复用价值 30分（基于内容特征判断）
    reusable_keywords = ["示例", "模板", "最佳实践", "指南", "步骤", "流程", "SOP"]
    reusable_score = sum(5 for kw in reusable_keywords if kw in content)
    score += min(30, reusable_score)

    return score


def score_to_stars(score):
    """分数转星级"""
    if score >= 90:
        return "⭐⭐⭐⭐⭐ 优秀"
    elif score >= 70:
        return "⭐⭐⭐⭐ 良好"
    elif score >= 50:
        return "⭐⭐⭐ 一般"
    else:
        return "⭐⭐ 待改进"


def count_words_and_images(content):
    """统计字数和图片数量"""
    # 移除 markdown 标记，统计纯文本
    clean_text = re.sub(r'[#*`\[\]()]', '', content)
    clean_text = re.sub(r'!\[.*?\]\(.*?\)', '', clean_text)
    word_count = len(clean_text.strip())

    # 统计图片数量
    image_count = content.count("![") + content.count("![[")

    return word_count, image_count


def archive_document(doc_token, title="未命名文档", content="", dry_run=False):
    """
    归档单个文档到 kaka 飞书知识库
    参数:
        doc_token: 飞书文档 token
        title: 文档标题
        content: 文档内容（不传则自动从飞书读取）
        dry_run: 演示模式，不真正写入多维表格
    """
    print(f"📥 开始归档文档: {doc_token}")
    print(f"📄 文档标题: {title}")
    print(f"📊 目标知识库: {KB_APP_TOKEN} / {KB_TABLE_ID}")
    
    # 1. 获取飞书 Token
    app_id, app_secret = load_config()
    token = get_token(app_id, app_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("   ✅ 飞书认证成功")
    
    # 2. 如果没传 content，自动从飞书文档读取
    if not content:
        print("   📖 正在读取飞书文档内容...")
        content = get_document_content(doc_token, headers)
        if not content:
            content = title  # fallback，至少用标题分类
    
    # 3. 统计字数和图片
    word_count, image_count = count_words_and_images(content)

    # 3. 智能分类
    kb_id, kb_info = classify_kb(content, title)
    role = classify_role(content, title)
    tags = recommend_tags(content, title)

    # 4. 质量评分
    quality_score = calc_quality_score(content, word_count, image_count)
    quality_stars = score_to_stars(quality_score)

    # 5. 生成元数据
    metadata = {
        "文档名称": f"【{kb_id}】{title}_v1.0",
        "文档链接": f"https://www.feishu.cn/docx/{doc_token}",
        "doc_token": doc_token,
        "知识库分类": f"{kb_info['emoji']} {kb_info['name']}",
        "负责AI角色": role,
        "业务场景": "知识库维护",
        "标签": tags,  # 多选字段需要传数组
        "优先级": "P2 - 中",
        "版本号": "v1.0",
        "字数统计": word_count,
        "图片数量": image_count,
        "更新次数": 1,
        "文档质量": quality_stars,
        "审核状态": "待审核",
        "效果评分": quality_score,
        "创建时间": int(datetime.now().timestamp() * 1000),
        "上次更新": int(datetime.now().timestamp() * 1000),
        "备注": f"自动归档于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    }

    print("\n🏷️  自动分类结果:")
    print(f"   知识库: {kb_info['emoji']} {kb_info['name']} ({kb_id})")
    print(f"   角色: {role}")
    print(f"   标签: {tags}")

    print(f"\n⭐ 质量评估: {quality_stars} ({quality_score}分)")
    print(f"   字数: {word_count} | 图片: {image_count}")
    
    # 7. 准备写入多维表格的字段
    now_ms = int(datetime.now().timestamp() * 1000)
    
    fields = {
        "文档名称": f"【{kb_id}】{title}",
        "文档链接": f"https://www.feishu.cn/docx/{doc_token}",
        "doc_token": doc_token,
        "备注": f"自动归档于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "负责AI角色": role,
        "业务场景": "知识库维护",
        "标签": tags,  # 多选字段需要传数组
        "优先级": "P2 - 中",
        "版本号": "v1.0",
        "字数统计": word_count,
        "图片数量": image_count,
        "更新次数": 1,
        "文档质量": quality_stars,
        "审核状态": "待审核",
        "效果评分": quality_score,
        "创建时间": now_ms,
        "上次更新": now_ms,
    }
    
    # 8. 检查是否已存在（避免重复归档）
    existing_record_id = check_doc_exists(doc_token, headers)
    
    if dry_run:
        print("\n🎯 演示模式 - 以下内容将写入多维表格:")
        for k, v in fields.items():
            print(f"   {k}: {v}")
        record_id = "demo_record"
    else:
        if existing_record_id:
            print(f"\n🔄 文档已存在，更新记录...")
            fields["更新次数"] = fields["更新次数"] + 1  # 更新次数+1
            success = update_bitable(headers, existing_record_id, fields)
            record_id = existing_record_id if success else None
        else:
            print(f"\n📤 正在写入多维表格...")
            record_id = write_to_bitable(headers, fields)
    
    if record_id:
        print(f"\n✅ 归档成功！记录 ID: {record_id}")
        print(f"🔗 知识库链接: https://{{FEISHU_DOMAIN}}.feishu.cn/base/{KB_APP_TOKEN}")
        return record_id
    else:
        print("\n❌ 归档失败！")
        return None


def main():
    parser = argparse.ArgumentParser(description="kaka 飞书知识库归档工具")
    parser.add_argument("doc_token", help="飞书文档 token")
    parser.add_argument("--title", default="未命名文档", help="文档标题")
    parser.add_argument("--content", default="", help="文档内容（不传则自动从飞书读取）")
    parser.add_argument("--dry-run", action="store_true", help="演示模式，不真正写入多维表格")
    args = parser.parse_args()

    archive_document(
        doc_token=args.doc_token,
        title=args.title,
        content=args.content,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
