"""Deep-dive report generator for 002-daily-news.
Used by /deep command to generate comprehensive topic reports.
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import httpx

logger = logging.getLogger("report")

PROJECT_DIR = Path(__file__).parent
DAILY_DIR = PROJECT_DIR / "daily"
REPORTS_DIR = PROJECT_DIR / "reports"

DEEP_REPORT_PROMPT = """你是资深研究分析师。基于以下过去7天的相关新闻条目，生成一份1500-2000字的专题深度报告。

报告主题：{topic}

相关新闻条目：
{articles_context}

报告结构：
1. **背景概述** (200-300字) — 这个主题的历史脉络，为什么现在成为关注焦点
2. **各方立场与动态** (400-500字) — 按国家/机构/利益方分别梳理，说清各方的核心诉求和行动
3. **关键节点与时间线** (200-300字) — 过去一周和未来可预见的关键事件/日期
4. **可能走向** (300-400字) — 2-3种可能的演进方向，每种给出概率判断和判断依据
5. **对中国的影响** (200-300字，如适用) — 经济/科技/外交层面的具体影响
6. **读者应盯住的指标/信号** (100-200字) — 接下来2-4周该关注什么来判断走向

要求：
- 面向有基础阅读能力但不一定是该领域专家的读者
- 数据和具体事件要准确（基于提供的新闻条目，不要编造）
- 观点标注信息来源
- 用中文撰写，专业术语保留英文原文
"""


def search_topic(topic: str, days: int = 7) -> list[dict]:
    """Search all recent briefs for topic mentions. Returns list of relevant article dicts."""
    results = []
    topic_lower = topic.lower()

    for md_file in sorted(DAILY_DIR.glob("*.md"), reverse=True)[:days]:
        content = md_file.read_text(encoding="utf-8")
        if topic_lower not in content.lower():
            continue

        # Extract article IDs and titles
        for match in re.finditer(r"#### \[([^\]]+)\]\s*(.+?)(?:·|$)", content):
            art_id = match.group(1)
            title = match.group(2).strip()
            if topic_lower in title.lower() or topic_lower in content[match.start():match.start()+500].lower():
                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 800)
                results.append({
                    "date": md_file.stem,
                    "id": art_id,
                    "title": title,
                    "context": content[start:end],
                })

    return results


def generate_report(topic: str, api_key: str, base_url: str = "https://api.deepseek.com") -> str | None:
    """Generate a deep-dive report on a topic using DeepSeek API."""
    articles = search_topic(topic)
    if not articles:
        return None

    # Build context
    articles_context = ""
    for art in articles:
        articles_context += f"\n[{art['date']}] [{art['id']}] {art['title']}\n"
        articles_context += f"{art['context'][:500]}\n"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是资深研究分析师。输出格式良好的Markdown。不要用JSON格式输出。"},
            {"role": "user", "content": DEEP_REPORT_PROMPT.format(
                topic=topic,
                articles_context=articles_context[:8000],
            )},
        ],
        "temperature": 0.5,
        "max_tokens": 4096,
    }

    try:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/v1/chat/completions",
            headers=headers, json=body, timeout=180,
        )
        resp.raise_for_status()
        result = resp.json()
        report = result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return None

    # Save to reports/
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    safe_topic = re.sub(r"[^\w一-鿿\-]", "", topic)[:20]
    filepath = REPORTS_DIR / f"{today}-{safe_topic}.md"

    full_report = f"# 📊 专题报告：{topic}\n\n"
    full_report += f"> 生成日期：{today}\n"
    full_report += f"> 数据来源：过去7天 {len(articles)} 条相关新闻\n\n"
    full_report += report
    full_report += f"\n\n---\n*报告由 DeepSeek 生成，基于本地简报存档。仅供研究参考。*"

    filepath.write_text(full_report, encoding="utf-8")
    logger.info(f"Report saved to {filepath}")

    return full_report


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python 08-report.py <topic> <api_key>")
        print("Example: python 08-report.py 台海局势 sk-xxx")
        sys.exit(1)

    topic = sys.argv[1]
    api_key = sys.argv[2]
    report = generate_report(topic, api_key)
    if report:
        print(report)
    else:
        print(f"No articles found for topic: {topic}")
