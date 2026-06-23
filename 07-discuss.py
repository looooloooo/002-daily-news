"""Claude Code interaction commands for 002-daily-news.

These commands are invoked when user types slash commands inside Claude Code
with 002-daily-news as the working directory. Claude Code reads the user's
command and the relevant daily brief files, then responds conversationally.

Command reference for the discussion flow:
"""

from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DAILY_DIR = PROJECT_DIR / "daily"
REPORTS_DIR = PROJECT_DIR / "reports"

# Command map — documented for Claude Code context
COMMANDS = {
    "/brief": {
        "usage": "/brief [日期]",
        "description": "查看今日简报全文。可选参数 'MMDD' 查看历史某日（如 /brief 0623）",
        "action": "cmd_brief",
    },
    "/discuss": {
        "usage": "/discuss [id]",
        "description": "深入讨论某条新闻。加载原文→多角度分析（各方立场、争议点、历史脉络、可能走向）",
        "action": "cmd_discuss",
    },
    "/deep": {
        "usage": "/deep [主题]",
        "description": "生成1500-2000字专题深度报告。搜索最近7天简报中相关条目→历史背景→各方立场→关键节点→可能走向。报告存入 reports/ 目录",
        "action": "cmd_deep",
    },
    "/insight": {
        "usage": "/insight [板块]",
        "description": "生成本周某板块事件关联图谱（Mermaid格式）。板块可选：ai/科技/财经/国际/趋势",
        "action": "cmd_insight",
    },
    "/trend": {
        "usage": "/trend",
        "description": "跨板块交叉趋势分析：识别 AI/财经/国际趋势 三板块之间的因果关系链",
        "action": "cmd_trend",
    },
}

CATEGORY_MAP = {
    "ai": "ai_tech", "科技": "ai_tech", "aitech": "ai_tech",
    "财经": "finance", "finance": "finance", "经济": "finance",
    "国际": "intl_trends", "趋势": "intl_trends", "intl": "intl_trends",
}


def find_article_in_archives(article_id: str, days: int = 7) -> tuple[str, str, str] | None:
    """Search recent briefs for an article ID. Returns (date, full_brief_md, article_section) or None."""
    for md_file in sorted(DAILY_DIR.glob("*.md"), reverse=True)[:days]:
        content = md_file.read_text(encoding="utf-8")
        marker = f"[{article_id}]"
        if marker in content:
            # Extract the section around this article
            idx = content.find(marker)
            start = max(0, idx - 200)
            end = min(len(content), idx + 2000)
            section = content[start:end]
            return md_file.stem, content, section
    return None


def list_recent_briefs(days: int = 7) -> list[str]:
    """List available brief files."""
    files = sorted(DAILY_DIR.glob("*.md"), reverse=True)[:days]
    return [f.stem for f in files]


def search_topic_in_archives(topic: str, days: int = 7) -> list[tuple[str, str]]:
    """Search recent briefs for topic mentions. Returns list of (date, matching_section)."""
    results = []
    topic_lower = topic.lower()
    for md_file in sorted(DAILY_DIR.glob("*.md"), reverse=True)[:days]:
        content = md_file.read_text(encoding="utf-8")
        if topic_lower in content.lower():
            # Extract relevant paragraphs
            lines = content.split("\n")
            matches = []
            for i, line in enumerate(lines):
                if topic_lower in line.lower():
                    start = max(0, i - 2)
                    end = min(len(lines), i + 5)
                    matches.append("\n".join(lines[start:end]))
            results.append((md_file.stem, "\n\n".join(matches[:3])))
    return results


if __name__ == "__main__":
    briefs = list_recent_briefs()
    print(f"Available briefs: {briefs}")
    print(f"\nCommands:")
    for cmd, info in COMMANDS.items():
        print(f"  {info['usage']}")
        print(f"    {info['description']}")
