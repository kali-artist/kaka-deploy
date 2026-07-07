#!/usr/bin/env python3
"""
企业信息智能查询工具

核心能力：
1. 使用 MiniMax mmx-cli 联网搜索，默认围绕企业做约 20 轮多维检索。
2. 根据用户目的（客户拜访/增购分析/尽职调查/通用调研/自定义目的）生成结构化报告。
3. 支持输出 Markdown、TXT，或直接创建飞书文档。

注意：
- 不在脚本中保存真实 API Key；优先读取 MINIMAX_API_KEY / ~/.config/mmx 等现有 CLI 配置。
- 飞书文档创建优先读取 ~/.feishu/config.json，也可读取 FEISHU_APP_ID / FEISHU_APP_SECRET。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

MMX_CLI_PATH = os.environ.get("MMX_CLI_PATH", "/home/ubuntu/.hermes/scripts/mmx.mjs")
NODE_PATH = os.environ.get("NODE_PATH", "/home/ubuntu/.hermes/node/bin/node")
DEFAULT_ROUNDS = int(os.environ.get("ENTERPRISE_QUERY_ROUNDS", "20"))
DEFAULT_OUTPUT_DIR = Path(os.environ.get("ENTERPRISE_QUERY_OUTPUT_DIR", "/tmp/enterprise-intelligence"))

REPORT_TYPE_ALIASES = {
    "1": "客户拜访报告",
    "visit": "客户拜访报告",
    "客户拜访": "客户拜访报告",
    "拜访": "客户拜访报告",
    "2": "增购分析报告",
    "upsell": "增购分析报告",
    "增购": "增购分析报告",
    "增购分析": "增购分析报告",
    "找增购点": "增购分析报告",
    "3": "尽职调查报告",
    "dd": "尽职调查报告",
    "due_diligence": "尽职调查报告",
    "尽职调查": "尽职调查报告",
    "尽调": "尽职调查报告",
    "4": "通用调研报告",
    "general": "通用调研报告",
    "通用": "通用调研报告",
    "通用报告": "通用调研报告",
}

OUTPUT_FORMAT_ALIASES = {
    "feishu": "feishu",
    "飞书": "feishu",
    "飞书文档": "feishu",
    "doc": "feishu",
    "docx": "feishu",
    "md": "md",
    "markdown": "md",
    "markdown文档": "md",
    "txt": "txt",
    "text": "txt",
    "文本": "txt",
    "文本文档": "txt",
}


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_name(text: str, max_len: int = 80) -> str:
    text = re.sub(r"[\\/:*?\"<>|\s]+", "_", text.strip())
    return text[:max_len].strip("_") or "enterprise_report"


def normalize_report_type(report_type: str) -> str:
    return REPORT_TYPE_ALIASES.get((report_type or "").strip(), report_type or "通用调研报告")


def normalize_output_format(output_format: str) -> str:
    fmt = OUTPUT_FORMAT_ALIASES.get((output_format or "md").strip().lower(), output_format or "md")
    if fmt not in {"md", "txt", "feishu"}:
        raise ValueError(f"不支持的输出格式: {output_format}，可选: feishu/md/txt")
    return fmt


def check_mmx_cli_available() -> bool:
    if not Path(NODE_PATH).exists() or not Path(MMX_CLI_PATH).exists():
        return False
    try:
        r = subprocess.run([NODE_PATH, MMX_CLI_PATH, "--version"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


def build_search_queries(company: str, report_type: str, purpose: str = "", rounds: int = DEFAULT_ROUNDS) -> List[str]:
    """围绕企业与用户目的生成多维搜索词，默认 20 轮左右。"""
    report_type = normalize_report_type(report_type)
    purpose_suffix = f" {purpose}" if purpose else ""

    base_queries = [
        f"{company} 工商信息 法定代表人 注册资本 成立日期 经营状态",
        f"{company} 统一社会信用代码 注册地址 经营范围 登记机关",
        f"{company} 股东结构 实际控制人 受益所有人",
        f"{company} 高管 董事 监事 经理 核心团队",
        f"{company} 官网 主营业务 产品 服务 解决方案",
        f"{company} 融资 投资 对外投资 子公司 分支机构",
        f"{company} 招投标 中标 采购 项目 合作伙伴",
        f"{company} 客户案例 合作客户 供应商 渠道",
        f"{company} 招聘 岗位 技术栈 数字化 信息化 IT投入",
        f"{company} 专利 商标 软件著作权 知识产权",
        f"{company} 司法风险 裁判文书 诉讼 开庭公告",
        f"{company} 被执行人 失信 限制高消费 经营异常 行政处罚",
        f"{company} 新闻 最新动态 2025 2026",
        f"{company} 行业 竞争对手 市场地位 竞品",
        f"{company} 财务 业绩 营收 利润 年报",
        f"{company} 产品痛点 业务痛点 数字化转型",
        f"{company} 安全 合规 数据治理 信息系统",
        f"{company} 云计算 AI 大模型 自动化 CRM ERP OA",
        f"{company} 舆情 投诉 评价 口碑",
        f"{company} 发展战略 规划 扩张 新业务",
    ]

    purpose_queries = []
    if report_type == "客户拜访报告":
        purpose_queries = [
            f"{company} 拜访准备 决策人 组织架构 近期重点{purpose_suffix}",
            f"{company} 业务痛点 合作切入点 销售线索{purpose_suffix}",
        ]
    elif report_type == "增购分析报告":
        purpose_queries = [
            f"{company} IT系统 现有供应商 增购机会 数字化需求{purpose_suffix}",
            f"{company} 预算 项目采购 招标 信息化建设{purpose_suffix}",
        ]
    elif report_type == "尽职调查报告":
        purpose_queries = [
            f"{company} 尽职调查 法律风险 财务风险 经营风险{purpose_suffix}",
            f"{company} 关联方 重大诉讼 行政处罚 合规风险{purpose_suffix}",
        ]
    else:
        purpose_queries = [
            f"{company} 企业调研 综合分析 风险 机会{purpose_suffix}",
        ]

    queries = []
    seen = set()
    for q in purpose_queries + base_queries:
        q = q.strip()
        if q and q not in seen:
            queries.append(q)
            seen.add(q)
    return queries[: max(1, rounds)]


def _run_mmx_command(cmd: List[str], query: str, timeout: int) -> Tuple[bool, Dict[str, Any]]:
    env = os.environ.copy()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return False, {"success": False, "query": query, "error": "timeout"}
    except Exception as e:
        return False, {"success": False, "query": query, "error": str(e)}

    if r.returncode != 0:
        return False, {
            "success": False,
            "query": query,
            "error": r.stderr.strip() or r.stdout.strip(),
            "return_code": r.returncode,
            "cmd": " ".join(cmd[:4] + ["..."]),
        }

    stdout = r.stdout.strip()
    try:
        data = json.loads(stdout)
    except Exception:
        data = {"raw_output": stdout}
    return True, {"success": True, "query": query, "data": data}


def search_via_mmx_cli(query: str, output_json: bool = True, timeout: int = 90) -> Dict[str, Any]:
    """Run one MiniMax MMX web-search query.

    The local mmx CLI version has changed flags across releases. The verified
    current form is `mmx search query --q <query> --output json`; older scripts
    used `--region cn --non-interactive`, which some versions reject. Try the
    verified minimal command first, then fall back to the older extended form.
    """
    base_cmd = [NODE_PATH, MMX_CLI_PATH, "search", "query", "--q", query]
    if output_json:
        base_cmd.extend(["--output", "json"])

    ok, result = _run_mmx_command(base_cmd, query, timeout)
    if ok:
        return result

    # Compatibility fallback for CLI builds that still accept these flags.
    fallback_cmd = [NODE_PATH, MMX_CLI_PATH, "search", "query", "--q", query, "--region", "cn", "--non-interactive"]
    if output_json:
        fallback_cmd.extend(["--output", "json"])
    ok2, fallback_result = _run_mmx_command(fallback_cmd, query, timeout)
    if ok2:
        fallback_result["compat_fallback_used"] = True
        return fallback_result

    result["fallback_error"] = fallback_result.get("error")
    return result


def run_mmx_research(company: str, report_type: str, purpose: str = "", rounds: int = DEFAULT_ROUNDS, workdir: Optional[Path] = None) -> Dict[str, Any]:
    if not check_mmx_cli_available():
        raise RuntimeError("mmx-cli 不可用：请检查 /home/ubuntu/.hermes/scripts/mmx.mjs 与 node 路径，或安装/配置 mmx-cli")

    report_type_name = normalize_report_type(report_type)
    queries = build_search_queries(company, report_type_name, purpose, rounds)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    workdir = workdir or (DEFAULT_OUTPUT_DIR / f"{safe_name(company)}_{ts}")
    raw_dir = workdir / "raw_mmx"
    raw_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    for idx, query in enumerate(queries, 1):
        print(f"🔎 MMX联网搜索 {idx}/{len(queries)}: {query}", flush=True)
        result = search_via_mmx_cli(query)
        result["index"] = idx
        results.append(result)
        (raw_dir / f"{idx:02d}_{safe_name(query, 60)}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        time.sleep(0.8)

    success_count = sum(1 for r in results if r.get("success"))
    research = {
        "company_name": company,
        "report_type": report_type_name,
        "purpose": purpose,
        "query_time": now_str(),
        "rounds_requested": rounds,
        "queries": queries,
        "results": results,
        "success_count": success_count,
        "raw_dir": str(raw_dir),
        "source": "MiniMax mmx-cli web search",
    }
    (workdir / "research.json").write_text(json.dumps(research, ensure_ascii=False, indent=2), encoding="utf-8")
    return research


def flatten_search_text(research: Dict[str, Any], max_chars: int = 36000) -> str:
    chunks: List[str] = []
    for item in research.get("results", []):
        query = item.get("query", "")
        data = item.get("data") if item.get("success") else {"error": item.get("error")}
        text = json.dumps(data, ensure_ascii=False, indent=2)
        chunks.append(f"### 搜索{item.get('index')}: {query}\n{text}")
    content = "\n\n".join(chunks)
    return content[:max_chars]


def extract_urls(obj: Any) -> List[str]:
    text = json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj
    urls = re.findall(r"https?://[^\s\]\)\}\"'<>]+", text)
    cleaned = []
    seen = set()
    for u in urls:
        u = u.rstrip(".,;，。；")
        if u not in seen:
            cleaned.append(u)
            seen.add(u)
    return cleaned[:30]


def evidence_table(research: Dict[str, Any]) -> str:
    rows = ["| 序号 | 检索主题 | 状态 | 有效线索数 |", "|---:|---|---:|---:|"]
    for item in research.get("results", []):
        status = "成功" if item.get("success") else f"失败：{str(item.get('error', ''))[:40]}"
        count = len(extract_search_items({"results": [item]}, research.get("company_name", ""))) if item.get("success") else 0
        rows.append(f"| {item.get('index')} | {item.get('query', '').replace('|', '/')} | {status.replace('|', '/')} | {count} |")
    return "\n".join(rows)


def clean_text(text: Any, max_len: int = 360) -> str:
    text = "" if text is None else str(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|\u3000", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len].rstrip()


def company_keywords(company: str) -> List[str]:
    """生成用于判断主体相关性的关键词。

    原则：完整公司名权重最高；城市/行业泛词不能单独构成相关；
    对“义乌橙琳科技电子有限公司”这类名称，提取“橙琳”等区分度词。
    """
    base = company.strip()
    no_suffix = re.sub(r"(有限责任公司|股份有限公司|有限公司|公司|集团)$", "", base)
    no_city = re.sub(r"^(义乌市?|北京市?|上海市?|深圳市?|广州市?|杭州 市?|浙江省?|金华市?)", "", no_suffix).strip()
    no_generic = re.sub(r"(科技|电子|商务|贸易|商贸|网络|信息|实业|有限|责任)", "", no_city)
    parts = [base, no_suffix, no_city, no_generic]
    # 连续中文片段中优先取 2-4 字的专名片段。
    for token in re.findall(r"[一-鿿]{2,6}", no_generic):
        parts.append(token)
    seen, out = set(), []
    for x in parts:
        x = re.sub(r"\s+", "", x or "")
        if len(x) >= 2 and x not in seen:
            out.append(x)
            seen.add(x)
    return out


def score_item_relevance(item: Dict[str, str], company: str) -> int:
    text = f"{item.get('title','')} {item.get('snippet','')} {item.get('link','')}"
    title = item.get("title", "")
    kws = company_keywords(company)
    score = 0
    if company and company in text:
        score += 30
    # 名称主干，如“义乌橙琳科技电子”。
    if len(kws) > 1 and kws[1] in text:
        score += 16
    # 去城市/行业后的区分词，如“橙琳”。
    distinctive = [kw for kw in kws[2:] if kw not in {"义乌", "科技", "电子", "商务", "网络", "信息"}]
    for kw in distinctive:
        if kw in text:
            score += 10 if len(kw) <= 3 else 8
    # 城市+区分词同时出现，可视为近似主体线索。
    if ("义乌" in text or "金华" in text) and any(kw in text for kw in distinctive):
        score += 5
    # 只有城市或行业泛词不给分，避免把义乌泛新闻/AI通稿当线索。
    if score == 0:
        return 0
    # 明显是其他公司但含少量近似词，保留为“近似线索”而非强事实。
    if company not in title and re.search(r"(有限公司|股份有限公司|集团|公司)$", title) and not any(kw in title for kw in distinctive):
        score = max(0, score - 8)
    return score


def iter_search_records(data: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(data, dict):
        for key in ("organic", "news", "results", "items"):
            val = data.get(key)
            if isinstance(val, list):
                for row in val:
                    if isinstance(row, dict):
                        yield row
        # 部分 CLI 版本可能把结果包在 data 字段下
        if isinstance(data.get("data"), (dict, list)):
            yield from iter_search_records(data.get("data"))
    elif isinstance(data, list):
        for row in data:
            if isinstance(row, dict):
                yield row


def extract_search_items(research: Dict[str, Any], company: str = "") -> List[Dict[str, str]]:
    company = company or research.get("company_name", "")
    items: List[Dict[str, str]] = []
    seen = set()
    for result in research.get("results", []):
        if not result.get("success"):
            continue
        query = result.get("query", "")
        data = result.get("data", {})
        for row in iter_search_records(data):
            title = clean_text(row.get("title") or row.get("name") or row.get("source") or "")
            link = clean_text(row.get("link") or row.get("url") or row.get("href") or "", 500)
            snippet = clean_text(row.get("snippet") or row.get("description") or row.get("summary") or row.get("content") or "")
            date = clean_text(row.get("date") or row.get("time") or row.get("publishedAt") or "", 80)
            if not (title or snippet or link):
                continue
            key = link or f"{title}|{snippet[:80]}"
            if key in seen:
                continue
            seen.add(key)
            item = {"title": title, "link": link, "snippet": snippet, "date": date, "query": query, "index": str(result.get("index", ""))}
            item["score"] = str(score_item_relevance(item, company))
            # 报告正文只采用与目标主体或近似主体有名称关联的线索；
            # 原始检索摘要仍完整保留，便于追溯搜索噪声。
            if int(item["score"] or 0) > 0:
                items.append(item)
    items.sort(key=lambda x: int(x.get("score", "0") or 0), reverse=True)
    return items


def theme_for_query(query: str) -> str:
    q = query or ""
    if re.search(r"工商|统一社会信用代码|注册地址|经营范围|登记机关|法定代表人|注册资本|成立日期|经营状态", q):
        return "客户基础信息"
    if re.search(r"股东|实控人|高管|董事|监事|经理|核心团队|受益所有人", q):
        return "股权与关键人"
    if re.search(r"官网|主营业务|产品|服务|解决方案|客户案例|合作客户|供应商|渠道|行业|竞品|市场地位", q):
        return "业务与产品"
    if re.search(r"新闻|动态|招聘|岗位|招投标|中标|采购|项目|融资|投资|分支机构|发展战略|扩张|新业务|财务|营收|利润", q):
        return "经营动态与增长信号"
    if re.search(r"诉讼|司法|被执行|失信|限制高消费|经营异常|行政处罚|舆情|投诉|口碑|合规", q):
        return "风险与合规"
    if re.search(r"专利|商标|软著|软件著作权|知识产权", q):
        return "知识产权与竞争力"
    if re.search(r"IT|信息化|数字化|云计算|AI|大模型|自动化|CRM|ERP|OA|数据治理|信息系统|安全", q, re.I):
        return "数字化与潜在需求"
    return "其他线索"


def group_items_by_theme(items: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    groups: Dict[str, List[Dict[str, str]]] = {}
    for item in items:
        theme = theme_for_query(item.get("query", ""))
        groups.setdefault(theme, []).append(item)
    return groups


def exact_company_items(items: List[Dict[str, str]], company: str) -> List[Dict[str, str]]:
    return [it for it in items if company and company in f"{it.get('title','')} {it.get('snippet','')}"]


def near_company_items(items: List[Dict[str, str]], company: str) -> List[Dict[str, str]]:
    return [it for it in items if it not in exact_company_items(items, company)]


def render_item_bullets(items: List[Dict[str, str]], limit: int = 5) -> str:
    if not items:
        return "- 暂未检索到足够明确的公开线索，建议通过官方工商平台、企业官网或第三方企业数据库补充核验。"
    lines = []
    for it in items[:limit]:
        title = it.get("title") or "未命名来源"
        snippet = it.get("snippet") or "无摘要"
        date = f"（{it.get('date')}）" if it.get("date") else ""
        link = it.get("link")
        source = f"[{title}]({link})" if link else title
        lines.append(f"- **{source}**{date}：{snippet}")
    return "\n".join(lines)


def render_source_table(items: List[Dict[str, str]], limit: int = 18) -> str:
    """把原始搜索结果转换成可读表格，而不是 JSON。"""
    if not items:
        return "- 暂未提取到可读的原始线索。"
    rows = ["| 序号 | 来源标题 | 摘要 | 日期 | 链接 |", "|---:|---|---|---|---|"]
    for idx, it in enumerate(items[:limit], 1):
        title = (it.get("title") or "未命名来源").replace("|", "/")
        snippet = (it.get("snippet") or "无摘要").replace("|", "/")[:180]
        date = (it.get("date") or "-").replace("|", "/")
        link = it.get("link") or ""
        link_cell = f"[打开]({link})" if link else "-"
        rows.append(f"| {idx} | {title} | {snippet} | {date} | {link_cell} |")
    return "\n".join(rows)


def render_query_findings(research: Dict[str, Any], company: str, limit_per_query: int = 3) -> str:
    """按检索主题输出可读线索，保留原始数据价值但不暴露 JSON。"""
    sections = []
    for result in research.get("results", []):
        query = result.get("query", "")
        idx = result.get("index", "")
        if not result.get("success"):
            sections.append(f"### 检索 {idx}：{query}\n- 检索失败：{clean_text(result.get('error', '未知错误'))}")
            continue
        temp_research = {"company_name": company, "results": [result]}
        items = extract_search_items(temp_research, company)
        if not items:
            sections.append(f"### 检索 {idx}：{query}\n- 未提取到与目标主体强相关的可读线索；原始搜索结果可能包含行业泛信息或近似主体，需要人工筛选。")
            continue
        sections.append(f"### 检索 {idx}：{query}\n{render_item_bullets(items, limit=limit_per_query)}")
    return "\n\n".join(sections)


def evidence_strength(items: List[Dict[str, str]], company: str) -> Tuple[str, str]:
    exact = sum(1 for it in items if company and company in f"{it.get('title','')} {it.get('snippet','')}")
    relevant = sum(1 for it in items if int(it.get("score", "0") or 0) > 0)
    if exact >= 3 or relevant >= 8:
        return "中-高", "公开搜索中出现多条与目标主体相关的线索，可作为初步调研依据。"
    if exact >= 1 or relevant >= 3:
        return "中", "存在部分相关线索，但仍需进一步核验主体一致性与字段准确性。"
    return "低", "公开搜索结果噪声较多，与目标主体强匹配的信息不足，报告以调研框架和待核验问题为主。"


def extract_profile_fields(items: List[Dict[str, str]], company: str = "") -> Dict[str, str]:
    # 只有完整公司名命中的线索才用于填充工商字段；近似公司不写入事实字段。
    confident = [it for it in items if company and company in f"{it.get('title','')} {it.get('snippet','')}"]
    text = "\n".join(f"{it.get('title','')} {it.get('snippet','')}" for it in confident[:80])
    specs = {
        "法定代表人": [r"法定代表人[：:\s]*([^，。；;\s]{2,12})"],
        "注册资本": [r"注册资本[：:\s]*([^，。；;]{2,30})"],
        "成立日期": [r"成立日期[：:\s]*([0-9]{4}[-年][0-9]{1,2}[-月][0-9]{1,2}日?)"],
        "经营状态": [r"经营状态[：:\s]*([^，。；;\s]{2,12})"],
        "统一社会信用代码": [r"统一社会信用代码[：:\s]*([0-9A-Z]{15,20})"],
        "注册地址": [r"注册地址[：:\s]*([^。；;]{4,80})"],
    }
    out: Dict[str, str] = {}
    for field, patterns in specs.items():
        val = ""
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                val = clean_text(m.group(1), 80)
                break
        out[field] = val or "未在公开搜索摘要中稳定识别，待官方渠道核验"
    return out


def profile_table(fields: Dict[str, str]) -> str:
    rows = ["| 字段 | 初步识别结果 | 核验建议 |", "|---|---|---|"]
    for k, v in fields.items():
        rows.append(f"| {k} | {str(v).replace('|','/')} | 以国家企业信用信息公示系统/企查查/天眼查等为准 |")
    return "\n".join(rows)


def signal_matrix(groups: Dict[str, List[Dict[str, str]]], company: str) -> str:
    order = ["客户基础信息", "股权与关键人", "业务与产品", "经营动态与增长信号", "风险与合规", "知识产权与竞争力", "数字化与潜在需求"]
    rows = ["| 主题 | 线索强度 | 可读结论 | 建议动作 |", "|---|---|---|---|"]
    for theme in order:
        items = groups.get(theme, [])
        strength, note = evidence_strength(items, company)
        if theme == "客户基础信息":
            action = "先核验主体名称、统一社会信用代码、经营状态和注册地址，避免同名/近似公司误判。"
        elif theme == "业务与产品":
            action = "提炼主营业务、主要产品/服务、上下游客户，判断合作匹配度。"
        elif theme == "经营动态与增长信号":
            action = "关注招聘、招投标、新闻和融资扩张信号，识别近期需求窗口。"
        elif theme == "风险与合规":
            action = "复核司法、行政处罚、经营异常、舆情投诉，按严重性分级。"
        elif theme == "数字化与潜在需求":
            action = "若用于销售/拜访，围绕系统、流程、数据和自动化需求设计问题。"
        else:
            action = "补充官方/第三方数据库核验，作为背景信息使用。"
        rows.append(f"| {theme} | {strength} | {note} | {action} |")
    return "\n".join(rows)


def purpose_sections(report_type: str, company: str, purpose: str) -> str:
    report_type = normalize_report_type(report_type)
    if report_type == "客户拜访报告":
        return f"""
## 8. 拜访策略与问题清单

### 拜访目标
- 快速确认 {company} 的真实业务范围、近期经营重点和关键决策链。
- 验证公开信息中的采购、招聘、招投标、数字化建设等信号。
- 围绕「{purpose or '客户拜访准备'}」形成可推进的下一步动作。

### 建议提问
| 主题 | 可问问题 | 目的 |
|---|---|---|
| 业务现状 | 今年最重要的增长方向或经营压力是什么？ | 找到真实优先级 |
| 流程效率 | 哪些环节仍依赖人工表格、人工沟通或重复录入？ | 识别数字化切入点 |
| 系统现状 | 当前使用哪些系统，哪些场景覆盖不足？ | 判断替换/增购空间 |
| 决策流程 | 类似项目通常由哪些部门参与评估？ | 明确决策链 |
| 风险合规 | 对数据、安全、审计、合规有什么硬性要求？ | 识别刚需 |
"""
    if report_type == "增购分析报告":
        return f"""
## 8. 增购机会与推进路径

| 机会方向 | 判断逻辑 | 建议动作 |
|---|---|---|
| 数字化/信息化建设 | 若出现招聘、招标、系统建设、数据治理等信号，通常代表预算或内部需求正在形成 | 追问现有系统边界、预算周期、采购流程 |
| 业务扩张 | 分支机构、新业务、招聘扩张、合作项目可能带来新增工具/服务需求 | 评估新增部门/区域的服务覆盖缺口 |
| 风险合规 | 诉讼、处罚、数据安全要求可能触发合规型采购 | 以合规、风控、审计可追溯作为价值切入 |
| 效率提升 | 业务复杂度上升但系统化不足时，容易出现自动化和数据闭环需求 | 用ROI和降本增效案例推进 |
"""
    if report_type == "尽职调查报告":
        return f"""
## 8. 尽调核查清单

| 维度 | 重点核查项 | 风险提示 |
|---|---|---|
| 工商主体 | 存续状态、注册资本、股权变更、实控人 | 以官方工商平台复核，避免搜索噪声误判 |
| 法律风险 | 诉讼、被执行、失信、行政处罚 | 关注近期、高频、大额、核心业务相关案件 |
| 经营风险 | 经营异常、舆情投诉、招投标异常 | 判断持续经营能力和履约能力 |
| 知识产权 | 专利、商标、软著、权属争议 | 判断技术壁垒与侵权风险 |
| 关联关系 | 对外投资、分支机构、关联方 | 识别潜在利益输送或债务风险 |
"""
    return f"""
## 8. 综合建议与下一步动作

1. **先核验主体**：优先确认 {company} 的统一社会信用代码、经营状态、注册地址、法定代表人，避免同名或近似主体干扰。
2. **再判断业务**：围绕主营业务、产品/服务、客户/供应商、行业位置，判断是否具备合作或研究价值。
3. **重点看风险**：司法、行政处罚、经营异常、舆情投诉属于合作前必须复核项。
4. **寻找机会点**：招聘、招投标、系统建设、融资/扩张、新业务动态可作为拜访或销售切入信号。
5. **形成访谈问题**：把公开信息中无法确认的内容转化为拜访问题，不直接当作事实下结论。
"""


def generate_markdown_report(research: Dict[str, Any], user_name: str = "用户") -> str:
    company = research["company_name"]
    report_type = research["report_type"]
    purpose = research.get("purpose", "")
    source_findings = render_query_findings(research, company, limit_per_query=3)
    items = extract_search_items(research, company)
    exact_items = exact_company_items(items, company)
    near_items = near_company_items(items, company)
    # 正文主题分析仅使用完整公司名命中的强相关线索；近似名称单独列为“混淆主体”，避免误当事实。
    groups = group_items_by_theme(exact_items)
    strength, strength_note = evidence_strength(exact_items, company)
    fields = extract_profile_fields(exact_items, company)
    relevant_links = [it.get("link") for it in exact_items if it.get("link")]
    if not relevant_links:
        relevant_links = [it.get("link") for it in near_items[:8] if it.get("link")]
    url_lines = "\n".join(f"- {u}" for u in relevant_links[:20]) or "- 暂未从搜索结果中提取到稳定 URL；请以原始搜索结果为准。"

    md = f"""# {company}｜{report_type}

> 生成时间：{research.get('query_time', now_str())}  
> 生成人：{user_name}  
> 用户目的：{purpose or report_type}  
> 数据来源：{research.get('source', 'MiniMax mmx-cli web search')}  
> 检索轮次：成功 {research.get('success_count', 0)} / 请求 {research.get('rounds_requested', 0)}  
> 重要提示：本报告是**公开信息调研文档**，不是原始搜索结果堆叠；所有关键事实仍需以官方渠道二次核验。

## 1. 执行摘要

- **总体判断**：本次公开检索对 **{company}** 的信息可见度为 **{strength}**。{strength_note}
- **使用方式**：建议将本文作为客户背景、拜访准备、合作评估或尽调前置材料；不要把搜索摘要中未核验字段直接作为最终事实。
- **下一步重点**：优先核验工商主体与经营状态，其次梳理主营业务/产品，再复核风险与近期经营信号。

## 2. 客户背景与调研结论

| 维度 | 结论 | 说明 |
|---|---|---|
| 主体识别 | 待官方核验 | 公开搜索存在噪声时，必须用统一社会信用代码锁定主体。 |
| 信息充分度 | {strength} | {strength_note} |
| 业务判断 | 需结合官网/工商经营范围/产品线进一步确认 | 若公开结果不足，拜访时应优先询问主营业务和客户结构。 |
| 合作/拜访价值 | 可作为初筛线索 | 需结合你的实际目的「{purpose or report_type}」判断是否进入下一步。 |

## 3. 客户基础信息（待核验）

{profile_table(fields)}

## 4. 主题化信息汇总

{signal_matrix(groups, company)}

## 5. 业务、产品与客户线索

{render_item_bullets(groups.get('业务与产品', []), limit=6)}

## 6. 经营动态与增长信号

{render_item_bullets(groups.get('经营动态与增长信号', []), limit=6)}

## 7. 风险、合规与负面信号

{render_item_bullets(groups.get('风险与合规', []), limit=6)}

## 7.1 股权、关键人与知识产权补充

### 股权与关键人
{render_item_bullets(groups.get('股权与关键人', []), limit=4)}

### 知识产权与竞争力
{render_item_bullets(groups.get('知识产权与竞争力', []), limit=4)}

### 数字化与潜在需求
{render_item_bullets(groups.get('数字化与潜在需求', []), limit=4)}

## 7.2 近似名称/潜在混淆主体

> 以下线索只说明搜索结果中出现了名称相近或关键词相近的主体，**不能直接等同于 {company}**。如需使用，必须先用统一社会信用代码或官方工商页确认。

{render_item_bullets(near_items, limit=6)}

{purpose_sections(report_type, company, purpose)}

## 9. 检索覆盖与证据追溯

### 检索覆盖表
{evidence_table(research)}

### 重点信息源/线索
{url_lines}

## 10. 原始检索线索（可读版，仅用于追溯）

> 下面把原始检索结果整理成可读线索，不使用 JSON 展示；正式汇报建议优先使用上方主题化结论。

{source_findings}

---

*免责声明：本报告基于公开互联网信息自动整理，不构成投资、法律、财务或商业决策建议。关键结论请以官方渠道和人工复核为准。*
"""
    return md

def markdown_to_text(md: str) -> str:
    text = re.sub(r"```[\s\S]*?```", lambda m: m.group(0).replace("```json", "").replace("```", ""), md)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1（\2）", text)
    text = text.replace("|", " ")
    return text


def load_feishu_credentials() -> Tuple[str, str]:
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    cfg_path = Path.home() / ".feishu" / "config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        app_id = cfg.get("app_id") or app_id
        app_secret = cfg.get("app_secret") or app_secret
    if not app_id or not app_secret:
        raise RuntimeError("缺少飞书凭证：请配置 ~/.feishu/config.json 或 FEISHU_APP_ID/FEISHU_APP_SECRET")
    return app_id, app_secret


def feishu_token() -> str:
    if requests is None:
        raise RuntimeError("缺少 requests 依赖，无法调用飞书 API")
    app_id, app_secret = load_feishu_credentials()
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=30,
    )
    data = r.json()
    if r.status_code != 200 or data.get("code") != 0:
        raise RuntimeError(f"飞书 token 获取失败: HTTP {r.status_code}, {data}")
    return data["tenant_access_token"]


def md_line_to_block(line: str) -> Optional[Dict[str, Any]]:
    if not line.strip():
        return None
    raw = line.rstrip()
    heading = re.match(r"^(#{1,3})\s+(.+)$", raw)
    if heading:
        level = len(heading.group(1))
        block_type = {1: 4, 2: 5, 3: 6}.get(level, 6)
        content = heading.group(2)
    else:
        block_type = 2
        content = raw
    return {
        "block_type": block_type,
        "text": {
            "elements": [{"text_run": {"content": content, "text_element_style": {}}}],
            "style": {"align": 1, "folded": False},
        },
    }


def create_feishu_doc_from_markdown(title: str, markdown: str) -> str:
    """创建飞书 docx 并按已验证 block_type=2/4/5/6 写入内容。"""
    token = feishu_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    create_resp = requests.post(
        "https://open.feishu.cn/open-apis/docx/v1/documents",
        headers=headers,
        json={"title": title},
        timeout=30,
    )
    create_data = create_resp.json()
    if create_resp.status_code != 200 or create_data.get("code") != 0:
        raise RuntimeError(f"飞书文档创建失败: HTTP {create_resp.status_code}, {create_data}")
    doc_id = create_data["data"]["document"]["document_id"]
    root_block_id = doc_id

    blocks = [b for b in (md_line_to_block(line) for line in markdown.splitlines()) if b]
    children_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{root_block_id}/children?child_index=9999"
    batch_size = 8
    for i in range(0, len(blocks), batch_size):
        payload = {"children": blocks[i : i + batch_size]}
        r = requests.post(children_url, headers=headers, json=payload, timeout=30)
        data = r.json()
        if r.status_code != 200 or data.get("code") != 0:
            raise RuntimeError(f"飞书内容写入失败 batch={i//batch_size+1}: HTTP {r.status_code}, {data}")
        time.sleep(0.3)
    return f"https://www.feishu.cn/docx/{doc_id}"


def query_and_generate_report(
    company_name: str,
    report_type: str = "通用报告",
    user_name: str = "用户",
    output_format: str = "md",
    output_file: Optional[str] = None,
    purpose: str = "",
    rounds: int = DEFAULT_ROUNDS,
) -> Dict[str, Any]:
    output_format = normalize_output_format(output_format)
    report_type_name = normalize_report_type(report_type)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    workdir = DEFAULT_OUTPUT_DIR / f"{safe_name(company_name)}_{ts}"
    workdir.mkdir(parents=True, exist_ok=True)

    research = run_mmx_research(company_name, report_type_name, purpose, rounds, workdir=workdir)
    markdown = generate_markdown_report(research, user_name=user_name)
    title = f"{company_name}｜{report_type_name}"

    md_path = Path(output_file) if output_file and output_format == "md" else workdir / f"{safe_name(title)}.md"
    txt_path = Path(output_file) if output_file and output_format == "txt" else workdir / f"{safe_name(title)}.txt"

    result: Dict[str, Any] = {"workdir": str(workdir), "research_json": str(workdir / "research.json"), "title": title}

    # 始终保留 md 备份，方便重试/同步飞书。
    md_path.write_text(markdown, encoding="utf-8")
    result["markdown_file"] = str(md_path)

    if output_format == "txt":
        txt = markdown_to_text(markdown)
        txt_path.write_text(txt, encoding="utf-8")
        result["text_file"] = str(txt_path)
        result["primary_output"] = str(txt_path)
    elif output_format == "feishu":
        doc_url = create_feishu_doc_from_markdown(title, markdown)
        result["feishu_url"] = doc_url
        result["primary_output"] = doc_url
    else:
        result["primary_output"] = str(md_path)

    return result


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="企业信息智能查询：MMX 20轮联网搜索 + 按目的生成报告")
    parser.add_argument("company", help="公司名称")
    parser.add_argument("report_type", nargs="?", default="通用报告", help="报告类型：客户拜访/增购分析/尽职调查/通用报告")
    parser.add_argument("output", nargs="?", default=None, help="兼容旧参数：输出文件路径，可选")
    parser.add_argument("search_mode", nargs="?", default="mmx", help="兼容旧参数，当前固定优先 mmx")
    parser.add_argument("--purpose", default="", help="用户目的/业务场景，例如：拜访前准备、找增购点、投资尽调")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help="MMX联网搜索轮次，默认20")
    parser.add_argument("--output-format", "--format", default="md", choices=["feishu", "md", "txt"], help="输出格式")
    parser.add_argument("--user-name", default="用户", help="报告生成人/用户称呼")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        result = query_and_generate_report(
            company_name=args.company,
            report_type=args.report_type,
            user_name=args.user_name,
            output_format=args.output_format,
            output_file=args.output,
            purpose=args.purpose,
            rounds=args.rounds,
        )
    except Exception as e:
        print(f"❌ 生成失败: {e}", file=sys.stderr)
        return 1

    print("✅ 企业查询报告已生成")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
