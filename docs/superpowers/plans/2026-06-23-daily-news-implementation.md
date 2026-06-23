# Daily News Brief — Implementation Plan

> **For agentic workers:** Execute tasks sequentially. Each task is independently testable.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build automated daily news pipeline: RSS+social fetch → DeepSeek AI analysis → Gmail delivery + local archive, with Claude Code discussion commands.

**Architecture:** Python pipeline orchestrated by `01-main.py`. Four layers: fetch (RSS+social dual-channel), analyze (DeepSeek-V3 screening → DeepSeek-V4 deep analysis), deliver (Gmail SMTP + local .md), discuss (Claude Code interaction commands). Windows Task Scheduler triggers daily at 7:50.

**Tech Stack:** Python 3.10+, feedparser, httpx, deepseek SDK, smtplib, python-dotenv

## Global Constraints

- All files under `C:\Users\AlyssaLin\cc projects\002-daily-news\`
- Python 3.10+ (match Windows environment)
- DeepSeek API for AI analysis (V3 for cheap screening, V4 for deep analysis)
- Gmail SMTP (smtp.gmail.com:587, STARTTLS, App Password)
- All output in Chinese, technical terms retain English originals
- Monthly API cost cap: $10 (auto-degrade to V3-only when approaching)
- Error handling: retry 3×, silent skip on non-critical failures, log to `logs/`

---

### Task 1: Project scaffolding & dependencies

**Files:**
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `logs/.gitkeep`
- Create: `daily/.gitkeep`
- Create: `cache/.gitkeep`
- Create: `reports/.gitkeep`
- Create: `templates/email.html`

**Interfaces:**
- Produces: project directory structure, dependency manifest, email template skeleton

- [ ] **Step 1: Create .env.example**

```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-key-here

# Gmail SMTP
GMAIL_USERNAME=your.email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
RECIPIENT_EMAIL=your.email@gmail.com
```

- [ ] **Step 2: Create requirements.txt**

```
feedparser>=6.1.0
httpx>=0.27.0
python-dotenv>=1.0.0
jinja2>=3.1.0
```

- [ ] **Step 3: Create .gitignore**

```
.env
logs/*.log
cache/seen_urls.json
__pycache__/
*.pyc
```

- [ ] **Step 4: Create empty subdirectories**

```bash
mkdir -p "C:/Users/AlyssaLin/cc projects/002-daily-news/logs"
mkdir -p "C:/Users/AlyssaLin/cc projects/002-daily-news/daily"
mkdir -p "C:/Users/AlyssaLin/cc projects/002-daily-news/cache"
mkdir -p "C:/Users/AlyssaLin/cc projects/002-daily-news/reports"
mkdir -p "C:/Users/AlyssaLin/cc projects/002-daily-news/templates"
```

- [ ] **Step 5: Create HTML email template skeleton**

```html
<!-- templates/email.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
  .header { background: #1a1a2e; color: #fff; padding: 24px; border-radius: 8px 8px 0 0; }
  .header h1 { margin: 0; font-size: 20px; }
  .header .date { color: #a0a0b0; font-size: 14px; margin-top: 4px; }
  .keywords { background: #16213e; color: #e94560; padding: 12px 24px; font-size: 14px; }
  .section { background: #fff; margin: 0; padding: 20px 24px; border-bottom: 1px solid #eee; }
  .section-title { font-size: 18px; margin: 0 0 12px 0; }
  .bg-box { background: #f0f4ff; border-left: 3px solid #4a90d9; padding: 12px 16px; margin: 12px 0; font-size: 13px; color: #333; border-radius: 0 4px 4px 0; }
  .card { border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; margin: 12px 0; }
  .card-title { font-size: 15px; font-weight: 600; margin: 0 0 8px 0; }
  .card-meta { font-size: 12px; color: #888; margin-bottom: 8px; }
  .card-section { font-size: 14px; margin: 8px 0; line-height: 1.6; }
  .card-section .label { font-weight: 600; }
  .impacts { display: flex; gap: 12px; margin-top: 8px; }
  .impact { flex: 1; background: #fafafa; padding: 10px; border-radius: 4px; font-size: 13px; }
  .impact .label { font-size: 11px; color: #666; }
  .summary-box { background: #fffdf0; border-left: 3px solid #f0c040; padding: 12px 16px; margin: 12px 0; font-size: 14px; border-radius: 0 4px 4px 0; }
  .recommend { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 20px 24px; border-radius: 0 0 8px 8px; }
  .recommend a { color: #ffd700; }
  .footer { font-size: 12px; color: #999; text-align: center; padding: 16px; }
  .star-gold { color: #f0c040; }
  .star-silver { color: #a0a0a0; }
  .fire { color: #e94560; }
  .china-tag { background: #e94560; color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 3px; }
  .overseas-tag { background: #4a90d9; color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 3px; }
</style>
</head>
<body>
<div class="header">
  <h1>📬 每日简报</h1>
  <div class="date">{{ date_cn }}</div>
</div>
<div class="keywords">{{ keywords }}</div>
{{ content }}
<div class="footer">
  <p>🤖 Generated with DeepSeek · 每日自动推送 · <a href="https://github.com">002-daily-news</a></p>
  <p>📂 打开 Claude Code → 002-daily-news 目录 → 输入 /discuss [id] 深入讨论</p>
</div>
</body>
</html>
```

- [ ] **Step 6: Verify**

```bash
ls -R "C:/Users/AlyssaLin/cc projects/002-daily-news/"
# Should show: .env.example, requirements.txt, .gitignore, 00-INDEX.md, docs/, logs/, daily/, cache/, reports/, templates/
```

---

### Task 2: Configuration module

**Files:**
- Create: `02-config.py`

**Interfaces:**
- Produces: `Config` dataclass with all settings, `load_config()` → `Config`, all paths resolved as absolute

- [ ] **Step 1: Write 02-config.py**

```python
"""Configuration loader for 002-daily-news."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    deepseek_api_key: str
    deepseek_base_url: str
    gmail_smtp_server: str
    gmail_smtp_port: int
    gmail_username: str
    gmail_app_password: str
    recipient_email: str
    project_dir: str
    sources_file: str
    daily_dir: str
    logs_dir: str
    cache_dir: str
    reports_dir: str
    templates_dir: str
    max_articles_per_source: int
    max_deep_analysis: int
    monthly_cost_cap: float
    similarity_threshold: float
    social_cross_match_threshold: float
    fetch_timeout: int
    retry_count: int
    retry_delays: list


def load_config() -> Config:
    project_dir = os.path.dirname(os.path.abspath(__file__))

    return Config(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url="https://api.deepseek.com",
        gmail_smtp_server="smtp.gmail.com",
        gmail_smtp_port=587,
        gmail_username=os.getenv("GMAIL_USERNAME", ""),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        recipient_email=os.getenv("RECIPIENT_EMAIL", os.getenv("GMAIL_USERNAME", "")),
        project_dir=project_dir,
        sources_file=os.path.join(project_dir, "06-sources.json"),
        daily_dir=os.path.join(project_dir, "daily"),
        logs_dir=os.path.join(project_dir, "logs"),
        cache_dir=os.path.join(project_dir, "cache"),
        reports_dir=os.path.join(project_dir, "reports"),
        templates_dir=os.path.join(project_dir, "templates"),
        max_articles_per_source=15,
        max_deep_analysis=8,
        monthly_cost_cap=10.0,
        similarity_threshold=0.8,
        social_cross_match_threshold=0.6,
        fetch_timeout=30,
        retry_count=3,
        retry_delays=[60, 120, 300],
    )


def validate_config(cfg: Config) -> list[str]:
    issues = []
    if not cfg.deepseek_api_key or "sk-" not in cfg.deepseek_api_key:
        issues.append("DEEPSEEK_API_KEY missing or invalid (should start with 'sk-')")
    if not cfg.gmail_username or "@" not in cfg.gmail_username:
        issues.append("GMAIL_USERNAME missing or invalid")
    if not cfg.gmail_app_password or len(cfg.gmail_app_password) < 16:
        issues.append("GMAIL_APP_PASSWORD missing or too short (should be 16 chars)")
    return issues
```

- [ ] **Step 2: Verify import**

```bash
cd "C:/Users/AlyssaLin/cc projects/002-daily-news"
python -c "from config import load_config; c = load_config(); print(f'OK — project_dir={c.project_dir}')"
# Expected output: OK — project_dir=C:\Users\AlyssaLin\cc projects\002-daily-news
```

> Note: Python import uses `config` not `02-config` because we rename on import. Actually — keep the numbered filename for filesystem convention. Python imports: use `import importlib; mod = importlib.import_module('02-config')` in main — OR rename at import. Simpler: just use the numbered filenames on disk and import via `import_module`. Or better: create an `__init__.py`? No — keep it simple. Use `import importlib.util` or just put non-numbered symlinks? The cleanest approach: keep numbered files, use `exec(open('02-config.py').read())` — no. Actually the simplest: use `python -c "import importlib; m = importlib.import_module('02-config')"` — but Python can't import modules starting with digits. 

Let's handle this in the main script by using `runpy` or `importlib`. Or even simpler: rename the module at import time:

```python
import importlib.util
spec = importlib.util.spec_from_file_location("config", "02-config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
```

Actually, the cleanest solution is to NOT use numbered filenames for Python modules. Numbers in filenames are for documentation/ordering, but Python can't import them. Two clean solutions:

A) Use a wrapper that does `importlib` magic (ugly)
B) Keep the numbered files but each one has a clean importable name used internally

Actually, the simplest practical approach: just use non-numbered Python filenames but keep the number in 00-INDEX.md for reference. Or better yet: use dashes like `01-main.py` → main script that uses `importlib` to load other modules.

Let me just use `importlib` approach — it's explicit and works:

```python
import importlib.util
import sys

def _load_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
```

OK. I'll note this import pattern in the plan for Task 10.

- [ ] **Step 3: Create .env from example (remind user)**

```bash
cp .env.example .env
# Then edit .env with actual values
```

---

### Task 3: RSS sources JSON

**Files:**
- Create: `06-sources.json`

**Interfaces:**
- Produces: JSON file consumed by `03-fetch.py`

- [ ] **Step 1: Write 06-sources.json**

```json
{
  "ai_tech": {
    "label": "AI/科技",
    "intro_concepts": ["大语言模型(LLM)", "AI监管", "开源vs闭源"],
    "sources": [
      {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "region": "overseas"},
      {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "region": "overseas"},
      {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "region": "overseas"},
      {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "region": "overseas"},
      {"name": "Hacker News AI", "url": "https://hnrss.org/frontpage?q=ai+OR+ml+OR+llm+OR+openai+OR+anthropic", "region": "overseas"},
      {"name": "机器之心", "url": "https://jiqizhixin.com/rss", "region": "china"},
      {"name": "量子位", "url": "https://www.qbitai.com/feed", "region": "china"},
      {"name": "差评", "url": "https://rsshub.app/chaping/newsflashes", "region": "china"}
    ]
  },
  "finance": {
    "label": "财经",
    "intro_concepts": ["联储政策", "利率", "通胀指标CPI", "PMI"],
    "sources": [
      {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews", "region": "overseas"},
      {"name": "CNBC Top News", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "region": "overseas"},
      {"name": "MarketWatch Top", "url": "https://feeds.marketwatch.com/marketwatch/topstories", "region": "overseas"},
      {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss", "region": "overseas"},
      {"name": "华尔街见闻", "url": "https://rsshub.app/wallstreetcn/latest", "region": "china"},
      {"name": "财新网", "url": "https://rsshub.app/caixin/latest", "region": "china"},
      {"name": "36氪", "url": "https://36kr.com/feed", "region": "china"}
    ]
  },
  "intl_trends": {
    "label": "国际趋势",
    "intro_concepts": ["地缘政治", "多极化", "供应链安全", "国际法"],
    "sources": [
      {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "region": "overseas"},
      {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews", "region": "overseas"},
      {"name": "Foreign Affairs", "url": "https://www.foreignaffairs.com/feed", "region": "overseas"},
      {"name": "CFR Daily Brief", "url": "https://www.cfr.org/feed", "region": "overseas"},
      {"name": "SCMP", "url": "https://www.scmp.com/rss/91/feed", "region": "both"},
      {"name": "参考消息", "url": "https://rsshub.app/cankaoxiaoxi/import", "region": "china"},
      {"name": "联合早报", "url": "https://www.zaobao.com.sg/rss", "region": "both"}
    ]
  }
}
```

- [ ] **Step 2: Verify JSON is valid**

```bash
cd "C:/Users/AlyssaLin/cc projects/002-daily-news"
python -c "import json; data=json.load(open('06-sources.json')); print(f'OK — {len(data)} categories'); [print(f'  {k}: {len(v[\"sources\"])} sources') for k,v in data.items()]"
# Expected:
# OK — 3 categories
#   ai_tech: 8 sources
#   finance: 7 sources
#   intl_trends: 7 sources
```

---

### Task 4: Fetch module — RSS + Social dual channel + cross-match

**Files:**
- Create: `03-fetch.py`

**Interfaces:**
- Consumes: `06-sources.json` (reads directly), `02-config.py` (Config object passed in)
- Produces: `fetch_all(cfg: Config) → dict[category, list[Article]]`
- Article dataclass: `{id, title, summary, url, source_name, region, published, category, social_signals: list, heat_multiplier: float}`

- [ ] **Step 1: Write 03-fetch.py — imports and dataclass**

```python
"""RSS + Social media dual-channel news fetcher."""
import json
import logging
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
import httpx

logger = logging.getLogger("fetch")


@dataclass
class Article:
    id: str
    title: str
    summary: str
    url: str
    source_name: str
    region: str  # "overseas" | "china" | "both"
    published: datetime
    category: str  # "ai_tech" | "finance" | "intl_trends"
    social_signals: list[dict] = field(default_factory=list)
    heat_multiplier: float = 1.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "source_name": self.source_name,
            "region": self.region,
            "published": self.published.isoformat(),
            "category": self.category,
            "social_signals": self.social_signals,
            "heat_multiplier": self.heat_multiplier,
        }
```

- [ ] **Step 2: Write 03-fetch.py — RSS fetching**

```python
def _make_article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _clean_summary(raw: str, max_len: int = 300) -> str:
    """Strip HTML tags, truncate."""
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _is_today(published_parsed, today: datetime) -> bool:
    """Check if article was published in last 24 hours."""
    if not published_parsed:
        return True  # include if no date
    try:
        pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        return (today.astimezone(timezone.utc) - pub_dt) < timedelta(hours=30)
    except Exception:
        return True


def fetch_rss_sources(sources_data: dict, cfg) -> list[Article]:
    """Fetch all RSS sources in parallel. Return list of Article."""
    today = datetime.now()
    all_articles = []
    all_sources = []
    for cat_key, cat_data in sources_data.items():
        for src in cat_data["sources"]:
            all_sources.append((cat_key, src))

    def _fetch_one(cat_key: str, src: dict) -> list[Article]:
        articles = []
        try:
            resp = httpx.get(src["url"], timeout=cfg.fetch_timeout, follow_redirects=True)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[: cfg.max_articles_per_source]:
                if not _is_today(getattr(entry, "published_parsed", None), today):
                    continue
                article = Article(
                    id=_make_article_id(entry.get("link", entry.get("id", ""))),
                    title=entry.get("title", "").strip(),
                    summary=_clean_summary(entry.get("summary", entry.get("description", ""))),
                    url=entry.get("link", ""),
                    source_name=src["name"],
                    region=src["region"],
                    published=datetime.now(),
                    category=cat_key,
                )
                articles.append(article)
        except Exception as e:
            logger.warning(f"RSS fetch failed [{src['name']}]: {e}")
        return articles

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch_one, ck, s): (ck, s["name"]) for ck, s in all_sources}
        for fut in as_completed(futures):
            cat_key, name = futures[fut]
            try:
                results = fut.result()
                all_articles.extend(results)
                logger.info(f"RSS [{name}] → {len(results)} articles")
            except Exception as e:
                logger.warning(f"RSS [{name}] thread error: {e}")

    return all_articles
```

- [ ] **Step 3: Write 03-fetch.py — social media signals**

```python
# Social media API endpoints (all free, no auth required)
SOCIAL_SOURCES = {
    "reddit_ml": {
        "name": "Reddit r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/hot.json?limit=25",
        "region": "overseas",
        "category_hint": "ai_tech",
    },
    "reddit_tech": {
        "name": "Reddit r/technology",
        "url": "https://www.reddit.com/r/technology/hot.json?limit=25",
        "region": "overseas",
        "category_hint": "ai_tech",
    },
    "reddit_world": {
        "name": "Reddit r/worldnews",
        "url": "https://www.reddit.com/r/worldnews/hot.json?limit=25",
        "region": "overseas",
        "category_hint": "intl_trends",
    },
    "reddit_investing": {
        "name": "Reddit r/investing",
        "url": "https://www.reddit.com/r/investing/hot.json?limit=25",
        "region": "overseas",
        "category_hint": "finance",
    },
    "hn_top": {
        "name": "Hacker News",
        "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "region": "overseas",
        "category_hint": "ai_tech",
    },
    "zhihu_hot": {
        "name": "知乎热榜",
        "url": "https://rsshub.app/zhihu/hotlist",
        "region": "china",
        "category_hint": None,
    },
    "weibo_hot": {
        "name": "微博热搜",
        "url": "https://rsshub.app/weibo/search/hot",
        "region": "china",
        "category_hint": None,
    },
}


@dataclass
class SocialTrend:
    title: str
    source: str
    region: str
    score: float  # normalized 0-1
    keywords: list[str]


def _extract_keywords(text: str, max_kw: int = 5) -> list[str]:
    """Simple keyword extraction by splitting and filtering short words."""
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "in", "on", "at", "to", "for", "of", "and", "or", "with",
                 "this", "that", "it", "its", "from", "by", "as", "but",
                 "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
                 "都", "一", "一", "个", "上", "也", "很", "到", "说", "要"}
    words = re.findall(r"[a-zA-Z一-鿿]{2,}", text.lower())
    filtered = [w for w in words if w not in stopwords]
    return list(dict.fromkeys(filtered))[:max_kw]


def fetch_social_trends(cfg) -> list[SocialTrend]:
    """Fetch trending topics from social platforms."""
    trends = []
    headers = {"User-Agent": "002-daily-news/1.0 (news aggregator)"}

    for key, src in SOCIAL_SOURCES.items():
        try:
            resp = httpx.get(src["url"], headers=headers, timeout=cfg.fetch_timeout, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json() if "json" in resp.headers.get("content-type", "") else None

            if "reddit" in key and data:
                # Reddit JSON format
                for post in data.get("data", {}).get("children", [])[:15]:
                    post_data = post["data"]
                    trends.append(SocialTrend(
                        title=post_data.get("title", ""),
                        source=src["name"],
                        region=src["region"],
                        score=min(post_data.get("score", 0) / 500, 1.0),
                        keywords=_extract_keywords(post_data.get("title", "")),
                    ))
            elif key == "hn_top" and isinstance(data, list):
                # HN returns list of IDs — fetch titles in parallel (simplified: just note presence)
                # For full implementation: fetch top 10 story details
                pass  # HN detail fetch in separate step if needed
            elif "rsshub" in src["url"]:
                # RSSHub returns RSS format
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:15]:
                    title = entry.get("title", "")
                    desc = entry.get("description", entry.get("summary", ""))
                    # Normalize score from description if available
                    score = 0.5
                    trends.append(SocialTrend(
                        title=title.strip(),
                        source=src["name"],
                        region=src["region"],
                        score=score,
                        keywords=_extract_keywords(f"{title} {desc}"),
                    ))

            logger.info(f"Social [{src['name']}] → {len(trends)} trends (running total)")
        except Exception as e:
            logger.warning(f"Social fetch failed [{src['name']}]: {e}")

    return trends


def _keyword_overlap(kw1: list[str], kw2: list[str]) -> float:
    """Simple Jaccard-like overlap between keyword lists."""
    if not kw1 or not kw2:
        return 0.0
    s1, s2 = set(kw1), set(kw2)
    intersection = len(s1 & s2)
    union = len(s1 | s2)
    return intersection / union if union > 0 else 0.0


def cross_match_social(articles: list[Article], trends: list[SocialTrend], threshold: float = 0.6) -> list[Article]:
    """Cross-match RSS articles with social trends. 
    Articles that match social trends get heat_multiplier > 1.0."""
    for article in articles:
        art_kw = _extract_keywords(f"{article.title} {article.summary}")
        max_overlap = 0.0
        matched_trends = []

        for trend in trends:
            overlap = _keyword_overlap(art_kw, trend.keywords)
            if overlap > threshold:
                matched_trends.append({"source": trend.source, "score": trend.score, "title": trend.title})
                max_overlap = max(max_overlap, overlap)

        if len(matched_trends) >= 2:
            article.heat_multiplier = 1.5
        elif len(matched_trends) == 1:
            article.heat_multiplier = 1.3
        article.social_signals = matched_trends

    return articles


def deduplicate_articles(articles: list[Article], threshold: float = 0.8) -> list[Article]:
    """Remove near-duplicate articles based on title keyword overlap."""
    unique = []
    for art in articles:
        is_dup = False
        for existing in unique:
            overlap = _keyword_overlap(
                _extract_keywords(art.title, max_kw=8),
                _extract_keywords(existing.title, max_kw=8),
            )
            if overlap > threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(art)
    return unique
```

- [ ] **Step 4: Write 03-fetch.py — main orchestration**

```python
def fetch_all(sources_data: dict, cfg) -> dict[str, list[Article]]:
    """Main entry point. Fetch RSS + social, cross-match, deduplicate.
    Returns dict keyed by category: {"ai_tech": [...], "finance": [...], "intl_trends": [...]}
    """
    logger.info("=== Starting fetch cycle ===")

    # 1. Fetch RSS
    logger.info("Fetching RSS sources...")
    articles = fetch_rss_sources(sources_data, cfg)
    logger.info(f"RSS total: {len(articles)} articles")

    # 2. Fetch social trends
    logger.info("Fetching social trends...")
    trends = fetch_social_trends(cfg)
    logger.info(f"Social trends total: {len(trends)} trends")

    # 3. Cross-match
    logger.info("Cross-matching RSS ↔ Social...")
    articles = cross_match_social(articles, trends, threshold=cfg.social_cross_match_threshold)
    hot_count = sum(1 for a in articles if a.heat_multiplier > 1.0)
    logger.info(f"Cross-match: {hot_count} articles have social signal match")

    # 4. Deduplicate
    articles = deduplicate_articles(articles, threshold=cfg.similarity_threshold)
    logger.info(f"After dedup: {len(articles)} articles")

    # 5. Group by category
    grouped = {"ai_tech": [], "finance": [], "intl_trends": []}
    for art in articles:
        if art.category in grouped:
            grouped[art.category].append(art)

    for cat, arts in grouped.items():
        logger.info(f"  {cat}: {len(arts)} articles")

    return grouped


if __name__ == "__main__":
    # Quick test
    import sys
    sys.path.insert(0, ".")
    import importlib.util

    def load_mod(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    cfg_mod = load_mod("config", "02-config.py")
    cfg = cfg_mod.load_config()

    logging.basicConfig(level=logging.INFO)
    sources = json.load(open(cfg.sources_file))
    result = fetch_all(sources, cfg)
    for cat, arts in result.items():
        print(f"\n{cat}: {len(arts)} articles")
        for a in arts[:5]:
            hot = "🔥" if a.heat_multiplier > 1.0 else ""
            print(f"  [{a.source_name}] {a.title[:80]}... {hot}")
```

- [ ] **Step 5: Test RSS fetch (requires .env with API key not needed for fetch)**

```bash
cd "C:/Users/AlyssaLin/cc projects/002-daily-news"
python -c "
import importlib.util
spec = importlib.util.spec_from_file_location('config', '02-config.py')
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)
c = cfg.load_config()
print(f'Config OK — sources={c.sources_file}')
"
# Expected: Config OK — sources=...\002-daily-news\06-sources.json
```

---

### Task 5: Analyze module — DeepSeek AI

**Files:**
- Create: `04-analyze.py`

**Interfaces:**
- Consumes: `Config`, `dict[category, list[Article]]`
- Produces: `analyze_news(grouped_articles, cfg) → dict` with keys: `screened`, `deep_analyses`, `section_summaries`, `bg_concepts`, `recommended_read`, `keywords`

- [ ] **Step 1: Write 04-analyze.py — DeepSeek client + screening**

```python
"""DeepSeek AI analysis module — screening, deep analysis, summaries."""
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger("analyze")


@dataclass
class ScreenedArticle:
    id: str
    title: str
    summary: str
    url: str
    source_name: str
    region: str
    score: int  # 1-5 after AI screening
    final_score: float  # score × heat_multiplier
    reason: str
    category: str
    heat_multiplier: float
    social_signals: list = field(default_factory=list)

    def star_count(self) -> int:
        if self.final_score >= 5:
            return 3
        elif self.final_score >= 4:
            return 2
        return 1

    def is_hot(self) -> bool:
        return self.heat_multiplier > 1.0


@dataclass
class DeepAnalysis:
    article_id: str
    what_happened: str
    why_matters: str
    short_term_impact: list[str]
    mid_term_impact: list[str]


@dataclass
class SectionSummary:
    category: str
    summary_text: str
    indicators_to_watch: list[str]


@dataclass
class RecommendedRead:
    title: str
    url: str
    source: str
    why_recommend: str
    connection_to_today: str


@dataclass
class DailyAnalysis:
    keywords: list[str]
    screened: dict[str, list[ScreenedArticle]]  # category → articles
    deep_analyses: list[DeepAnalysis]
    section_summaries: dict[str, SectionSummary]
    bg_concepts: dict[str, str]  # category → background text
    recommended_read: Optional[RecommendedRead]
    total_cost_estimate: float
```

- [ ] **Step 2: Write 04-analyze.py — API call helper + screening prompt**

```python
SCREENING_PROMPT = """你是新闻主编。为以下 RSS 新闻评分（1-5分，5分最高）。

评分标准：
- 5分：会对行业/市场/地缘产生实质性影响的重大事件
- 4分：重要动态，值得关注但非转折性事件
- 3分：一般性新闻，有信息量但影响有限
- 2分：趣味性内容，行业杂谈
- 1分：广告/软文/无实质信息

每篇文章附带：{social_tag} 表示社交媒体讨论热度。如有社交验证，同分情况下优先选择。

输入：板块={category}，地区={region}

新闻列表：
{articles_json}

输出严格JSON格式（不要任何其他文字）：
{{"scored": [{{"id": "...", "score": 3, "reason": "一句话理由", "adjusted_score": 3.0}}]}}
注意：adjusted_score = score × heat_multiplier（如有社交热度标签则乘系数）"""


DEEP_ANALYSIS_PROMPT = """你是资深分析师。为以下新闻撰写深度分析，面向入门读者。

新闻：
标题：{title}
来源：{source}
原文摘要：{summary}

要求：
1. 📰 发生了什么：100-150字，讲清事件核心。用中文，技术术语保留英文原文。
2. 🔍 为什么值得关注：100-150字，提供必要背景知识，解释这个事件的行业/经济/地缘意义。假设读者刚入门。
3. ⚡ 短期影响（1-3个月）：2-3条，每条一句话
4. 🔮 中期影响（3-12个月）：2-3条，每条一句话

输出严格JSON：
{{"what_happened": "...", "why_matters": "...", "short_term_impact": ["...", "..."], "mid_term_impact": ["...", "..."]}}"""


SECTION_SUMMARY_PROMPT = """你是板块主编。基于今日该板块所有入选新闻，写一段150-200字的板块小结。

板块：{category}
今日入选新闻：
{articles_summary}

要求：
- 串联事件之间的逻辑关系（A导致B、A与B共同指向C趋势等）
- 点出本周该赛道的关键变化方向
- 给出2-3个"后续该盯住的指标/事件"
- 面向入门读者，概念要解释

输出JSON：
{{"summary_text": "...", "indicators_to_watch": ["...", "..."]}}"""


BG_CONCEPTS_PROMPT = """为以下新闻板块提取2-3个核心概念，给入门读者简短解释。

板块：{category}
今日新闻摘要：
{articles_summary}

只提取当日出现的新概念/新术语。如果都是常规话题，返回空。

输出JSON：
{{"concepts": [{{"term": "...", "explanation": "50-80字解释"}}]}}"""


RECOMMEND_PROMPT = """你是阅读推荐编辑。从今日相关源中推荐一篇值得深度阅读的长文/报告。

今日新闻摘要（全部三个板块）：
{all_summaries}

推荐标准：
1. 与今日⭐新闻直接相关或有深度延伸
2. 预计阅读时间15-25分钟
3. 社区热度较高或有争议性
4. 质量好、观点独特

输出JSON：
{{"title": "...", "url": "原文链接（如果能找到则填，否则填搜索建议）", "source": "...", "why_recommend": "100字推荐理由", "connection_to_today": "50字说明与今日新闻的关联"}}"""
```

- [ ] **Step 3: Write 04-analyze.py — DeepSeek API client**

```python
class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.total_cost = 0.0  # rough estimate in USD

    def _call(self, system_prompt: str, user_prompt: str, model: str = "deepseek-chat",
              temperature: float = 0.3, max_tokens: int = 4096) -> dict:
        """Call DeepSeek API, return parsed JSON."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(3):
            try:
                resp = httpx.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()
                content = result["choices"][0]["message"]["content"]

                # Track rough cost
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                # DeepSeek pricing ~$0.14/1M input, $0.28/1M output (V3)
                cost = (prompt_tokens * 0.14 + completion_tokens * 0.28) / 1_000_000
                if "deepseek-chat" not in model:
                    cost *= 2  # V4 is more expensive, rough estimate
                self.total_cost += cost

                return json.loads(content)
            except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"DeepSeek API attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
        return {}

    def screen_articles(self, articles: list, category: str, region: str) -> list[ScreenedArticle]:
        """Screen and score articles for one category+region group."""
        articles_json = json.dumps(
            [{
                "id": a.id,
                "title": a.title,
                "summary": a.summary[:200],
                "heat_multiplier": a.heat_multiplier,
                "social_signals": [s["source"] for s in a.social_signals],
            } for a in articles],
            ensure_ascii=False,
        )
        social_tag = "🔥 有社交讨论热度" if any(a.heat_multiplier > 1.0 for a in articles) else ""

        user_prompt = SCREENING_PROMPT.format(
            category=category,
            region=region,
            articles_json=articles_json,
            social_tag=social_tag,
        )

        result = self._call(
            system_prompt="你是专业新闻主编。只输出JSON。",
            user_prompt=user_prompt,
            model="deepseek-chat",  # V3, cheap
            temperature=0.2,
        )

        scored = []
        score_map = {s["id"]: s for s in result.get("scored", [])}
        for a in articles:
            s = score_map.get(a.id, {})
            scored.append(ScreenedArticle(
                id=a.id,
                title=a.title,
                summary=a.summary,
                url=a.url,
                source_name=a.source_name,
                region=a.region,
                score=s.get("score", 3),
                final_score=s.get("adjusted_score", s.get("score", 3)),
                reason=s.get("reason", ""),
                category=a.category,
                heat_multiplier=a.heat_multiplier,
                social_signals=a.social_signals,
            ))

        # Filter: only score ≥ 3
        return [s for s in scored if s.final_score >= 3]
```

- [ ] **Step 4: Write 04-analyze.py — deep analysis + summary + recommend**

```python
    def deep_analyze(self, article: ScreenedArticle) -> DeepAnalysis:
        """Generate deep analysis for a high-priority article."""
        user_prompt = DEEP_ANALYSIS_PROMPT.format(
            title=article.title,
            source=article.source_name,
            summary=article.summary,
        )
        result = self._call(
            system_prompt="你是资深分析师，面向入门读者。只输出JSON。",
            user_prompt=user_prompt,
            model="deepseek-chat",  # Could use V4 if available
            temperature=0.4,
            max_tokens=2048,
        )
        return DeepAnalysis(
            article_id=article.id,
            what_happened=result.get("what_happened", ""),
            why_matters=result.get("why_matters", ""),
            short_term_impact=result.get("short_term_impact", []),
            mid_term_impact=result.get("mid_term_impact", []),
        )

    def summarize_section(self, category: str, articles: list[ScreenedArticle]) -> SectionSummary:
        """Generate section summary connecting events."""
        articles_summary = "\n".join(
            f"- [{a.id}] {a.title} ({a.reason})" for a in articles[:15]
        )
        user_prompt = SECTION_SUMMARY_PROMPT.format(
            category=category,
            articles_summary=articles_summary,
        )
        result = self._call(
            system_prompt="你是板块主编。只输出JSON。",
            user_prompt=user_prompt,
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=1024,
        )
        return SectionSummary(
            category=category,
            summary_text=result.get("summary_text", ""),
            indicators_to_watch=result.get("indicators_to_watch", []),
        )

    def generate_bg_concepts(self, category: str, articles: list[ScreenedArticle]) -> str:
        """Generate beginner-friendly background concepts."""
        articles_summary = "\n".join(
            f"- {a.title}: {a.reason}" for a in articles[:10]
        )
        user_prompt = BG_CONCEPTS_PROMPT.format(
            category=category,
            articles_summary=articles_summary,
        )
        result = self._call(
            system_prompt="你是科普编辑。只输出JSON。",
            user_prompt=user_prompt,
            model="deepseek-chat",
            temperature=0.3,
            max_tokens=1024,
        )
        concepts = result.get("concepts", [])
        if not concepts:
            return ""
        lines = [f"**{c['term']}**：{c['explanation']}" for c in concepts]
        return "  \n".join(lines)

    def recommend_read(self, all_screened: dict[str, list]) -> RecommendedRead:
        """Recommend one deep reading article for today."""
        all_summaries = ""
        for cat, articles in all_screened.items():
            all_summaries += f"\n{cat}:\n"
            all_summaries += "\n".join(f"- {a.title}" for a in articles[:8])

        user_prompt = RECOMMEND_PROMPT.format(all_summaries=all_summaries)
        result = self._call(
            system_prompt="你是阅读推荐编辑。只输出JSON。",
            user_prompt=user_prompt,
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=1024,
        )
        return RecommendedRead(
            title=result.get("title", ""),
            url=result.get("url", ""),
            source=result.get("source", ""),
            why_recommend=result.get("why_recommend", ""),
            connection_to_today=result.get("connection_to_today", ""),
        )
```

- [ ] **Step 5: Write 04-analyze.py — main orchestration**

```python
CATEGORY_LABELS = {
    "ai_tech": "AI/科技",
    "finance": "财经",
    "intl_trends": "国际趋势",
}


def analyze_news(grouped_articles: dict[str, list], cfg) -> DailyAnalysis:
    """Main entry point: screen, deep analyze, summarize. 
    Returns DailyAnalysis with all processed content."""
    logger.info("=== Starting analysis cycle ===")
    client = DeepSeekClient(api_key=cfg.deepseek_api_key, base_url=cfg.deepseek_base_url)

    # Step 1: Screen all categories
    screened = {}
    for cat, articles in grouped_articles.items():
        overseas = [a for a in articles if a.region in ("overseas", "both")]
        china = [a for a in articles if a.region in ("china", "both")]

        overseas_scored = client.screen_articles(overseas, cat, "overseas") if overseas else []
        china_scored = client.screen_articles(china, cat, "china") if china else []

        screened[cat] = sorted(overseas_scored + china_scored, key=lambda x: x.final_score, reverse=True)
        logger.info(f"  {cat}: {len(screened[cat])} passed screening (from {len(articles)})")

    # Step 2: Deep analysis for top ⭐⭐⭐ articles (final_score ≥ 4.5)
    deep_analyses = []
    for cat, articles in screened.items():
        top = [a for a in articles if a.final_score >= 4.5][:3]
        for article in top:
            try:
                analysis = client.deep_analyze(article)
                deep_analyses.append(analysis)
                logger.info(f"  Deep analysis: [{article.id}] {article.title[:50]}...")
            except Exception as e:
                logger.warning(f"  Deep analysis failed [{article.id}]: {e}")

    # Step 3: Section summaries
    section_summaries = {}
    for cat, articles in screened.items():
        try:
            section_summaries[cat] = client.summarize_section(cat, articles)
        except Exception as e:
            logger.warning(f"  Summary failed [{cat}]: {e}")
            section_summaries[cat] = SectionSummary(cat, "", [])

    # Step 4: Background concepts
    bg_concepts = {}
    for cat, articles in screened.items():
        try:
            bg_concepts[cat] = client.generate_bg_concepts(cat, articles)
        except Exception as e:
            logger.warning(f"  BG concepts failed [{cat}]: {e}")
            bg_concepts[cat] = ""

    # Step 5: Recommended read
    recommended = None
    try:
        recommended = client.recommend_read(screened)
    except Exception as e:
        logger.warning(f"  Recommend failed: {e}")

    # Step 6: Keywords
    all_titles = []
    for articles in screened.values():
        all_titles.extend(a.title for a in articles[:5])
    keywords = _extract_keywords_from_titles(all_titles)

    logger.info(f"=== Analysis complete — cost ~${client.total_cost:.3f} ===")

    return DailyAnalysis(
        keywords=keywords,
        screened=screened,
        deep_analyses=deep_analyses,
        section_summaries=section_summaries,
        bg_concepts=bg_concepts,
        recommended_read=recommended,
        total_cost_estimate=client.total_cost,
    )


def _extract_keywords_from_titles(titles: list[str], max_kw: int = 5) -> list[str]:
    """Extract top keywords from a list of titles for the daily keyword card."""
    all_words = []
    stopwords = {"the", "a", "an", "is", "are", "in", "on", "at", "to", "for", "of",
                 "and", "or", "with", "this", "that", "it", "its", "from", "by", "as",
                 "的", "了", "在", "是", "和", "就", "不", "都", "一", "个", "上", "也"}
    import re
    for title in titles:
        words = re.findall(r"[\w一-鿿]{2,}", title.lower())
        all_words.extend(w for w in words if w not in stopwords)

    from collections import Counter
    counter = Counter(all_words)
    return [word for word, _ in counter.most_common(max_kw)]


if __name__ == "__main__":
    # Quick test (requires .env with DEEPSEEK_API_KEY)
    import sys, importlib.util

    def load_mod(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    cfg = load_mod("config", "02-config.py").load_config()
    fetch = load_mod("fetch", "03-fetch.py")

    logging.basicConfig(level=logging.INFO)
    sources = json.load(open(cfg.sources_file))
    grouped = fetch.fetch_all(sources, cfg)
    result = analyze_news(grouped, cfg)
    print(f"\nKeywords: {result.keywords}")
    for cat, articles in result.screened.items():
        print(f"\n{cat}: {len(articles)} screened")
        for a in articles[:5]:
            stars = "⭐" * a.star_count()
            hot = "🔥" if a.is_hot() else ""
            print(f"  {stars} {hot} {a.title[:60]}...")
```

---

### Task 6: Deliver module — Gmail + local archive

**Files:**
- Create: `05-deliver.py`

**Interfaces:**
- Consumes: `Config`, `DailyAnalysis`, `dict[category, list[Article]]` (original articles for reference)
- Produces: Sends HTML email via Gmail SMTP, writes `daily/YYYY-MM-DD.md`

- [ ] **Step 1: Write 05-deliver.py — HTML renderer**

```python
"""Email delivery + local archive module."""
import json
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

logger = logging.getLogger("deliver")

CATEGORY_EMOJI = {
    "ai_tech": "🤖",
    "finance": "💰",
    "intl_trends": "🌍",
}

REGION_LABELS = {
    "overseas": "🌏 海外",
    "china": "🇨🇳 中国",
    "both": "🌏🇨🇳",
}


def render_html(analysis, date_cn: str) -> str:
    """Render DailyAnalysis into HTML email body."""

    # Keywords card
    keywords_html = "🔥 今日关键词：" + " · ".join(analysis.keywords)

    content_parts = []

    for cat_key in ["ai_tech", "finance", "intl_trends"]:
        articles = analysis.screened.get(cat_key, [])
        if not articles:
            continue

        emoji = CATEGORY_EMOJI.get(cat_key, "")
        label = {"ai_tech": "AI/科技", "finance": "财经", "intl_trends": "国际趋势"}[cat_key]

        # Section header
        section_html = f'<div class="section"><h2 class="section-title">{emoji} {label}</h2>'

        # Background concepts
        bg = analysis.bg_concepts.get(cat_key, "")
        if bg:
            section_html += f'<div class="bg-box">📚 <strong>入门背景</strong><br>{bg}</div>'

        # Articles by region
        for region in ["overseas", "china"]:
            region_articles = [a for a in articles if a.region in (region, "both")]
            if not region_articles:
                continue

            region_label = REGION_LABELS.get(region, region)
            section_html += f"<h3>{region_label}</h3>"

            for art in region_articles:
                stars = "⭐" * art.star_count()
                fire = " 🔥" if art.is_hot() else ""
                region_tag = "china" if art.region == "china" else "overseas"
                tag_class = f"{region_tag}-tag"
                tag_text = "中国" if art.region == "china" else "海外"

                # Find deep analysis if available
                deep = None
                for da in analysis.deep_analyses:
                    if da.article_id == art.id:
                        deep = da
                        break

                card_html = f'<div class="card">'
                card_html += f'<div class="card-title">[{art.id}] {art.title} · {stars}{fire} <span class="{tag_class}">{tag_text}</span></div>'
                card_html += f'<div class="card-meta">📰 {art.source_name} · 评分 {art.final_score:.1f}</div>'

                if deep:
                    card_html += f'<div class="card-section"><span class="label">📰 发生了什么</span><br>{deep.what_happened}</div>'
                    card_html += f'<div class="card-section"><span class="label">🔍 为什么值得关注</span><br>{deep.why_matters}</div>'
                    card_html += '<div class="impacts">'
                    card_html += f'<div class="impact"><span class="label">⚡ 短期影响 (1-3月)</span><br>{"<br>".join(f"· {i}" for i in deep.short_term_impact)}</div>'
                    card_html += f'<div class="impact"><span class="label">🔮 中期影响 (3-12月)</span><br>{"<br>".join(f"· {i}" for i in deep.mid_term_impact)}</div>'
                    card_html += '</div>'
                else:
                    card_html += f'<div class="card-section">{art.summary[:300]}</div>'
                    card_html += f'<div class="card-meta">{art.reason}</div>'

                card_html += '</div>'
                section_html += card_html

        # Section summary
        summary = analysis.section_summaries.get(cat_key)
        if summary and summary.summary_text:
            indicators = " · ".join(f"📌 {i}" for i in summary.indicators_to_watch)
            section_html += f'<div class="summary-box">🗂 <strong>板块小结</strong><br>{summary.summary_text}<br><br>{indicators}</div>'

        section_html += '</div>'
        content_parts.append(section_html)

    # Recommended read
    rec_html = ""
    if analysis.recommended_read:
        r = analysis.recommended_read
        rec_html = f'''<div class="recommend">
<h2>📖 今日深度推荐 — ~20分钟</h2>
<p><strong>📄 {r.title}</strong></p>
<p>来源：{r.source}</p>
<p>📌 <strong>为什么推荐：</strong>{r.why_recommend}</p>
<p>🔗 <strong>与今日新闻的关联：</strong>{r.connection_to_today}</p>
<p>📎 <a href="{r.url}">原文链接</a></p>
</div>'''

    # Discussion footer
    discuss_html = '''<div class="section">
<h3>🗣 讨论 & 深入</h3>
<p>打开 Claude Code → 进入 002-daily-news 目录</p>
<p><code>/brief</code> 查看今日简报 &nbsp; <code>/discuss [id]</code> 深入讨论 &nbsp; <code>/deep [主题]</code> 专题报告</p>
<p><code>/insight [板块]</code> 事件关联图 &nbsp; <code>/trend</code> 跨板块交叉趋势</p>
</div>'''

    # Wrap in template
    with open(Path(__file__).parent / "templates" / "email.html", encoding="utf-8") as f:
        template = f.read()

    body = template.replace("{{ date_cn }}", date_cn)
    body = body.replace("{{ keywords }}", keywords_html)
    body = body.replace("{{ content }}", "\n".join(content_parts) + rec_html + discuss_html)

    return body
```

- [ ] **Step 2: Write 05-deliver.py — SMTP sender + local save**

```python
def render_markdown(analysis, date_cn: str) -> str:
    """Render DailyAnalysis into Markdown for local archive."""
    lines = []
    lines.append(f"# 📬 每日简报 — {date_cn}")
    lines.append("")
    lines.append(f"🔥 **今日关键词**：{' · '.join(analysis.keywords)}")
    lines.append("")

    for cat_key in ["ai_tech", "finance", "intl_trends"]:
        articles = analysis.screened.get(cat_key, [])
        if not articles:
            continue

        emoji = CATEGORY_EMOJI.get(cat_key, "")
        label = {"ai_tech": "AI/科技", "finance": "财经", "intl_trends": "国际趋势"}[cat_key]
        lines.append(f"---")
        lines.append(f"## {emoji} {label}")
        lines.append("")

        bg = analysis.bg_concepts.get(cat_key, "")
        if bg:
            lines.append(f"> 📚 **入门背景**  ")
            lines.append(f"> {bg}")
            lines.append("")

        for region in ["overseas", "china"]:
            region_articles = [a for a in articles if a.region in (region, "both")]
            if not region_articles:
                continue
            region_label = REGION_LABELS.get(region, region)
            lines.append(f"### {region_label}")
            lines.append("")

            for art in region_articles:
                stars = "⭐" * art.star_count()
                fire = " 🔥" if art.is_hot() else ""
                deep = None
                for da in analysis.deep_analyses:
                    if da.article_id == art.id:
                        deep = da
                        break

                lines.append(f"#### [{art.id}] {art.title} · {stars}{fire}")
                lines.append(f"*{art.source_name}* · 评分 {art.final_score:.1f}")
                lines.append("")

                if deep:
                    lines.append(f"**📰 发生了什么**  ")
                    lines.append(deep.what_happened)
                    lines.append("")
                    lines.append(f"**🔍 为什么值得关注**  ")
                    lines.append(deep.why_matters)
                    lines.append("")
                    lines.append(f"**⚡ 短期影响 (1-3月)**  ")
                    for i in deep.short_term_impact:
                        lines.append(f"- {i}")
                    lines.append("")
                    lines.append(f"**🔮 中期影响 (3-12月)**  ")
                    for i in deep.mid_term_impact:
                        lines.append(f"- {i}")
                    lines.append("")
                else:
                    lines.append(art.summary[:300])
                    lines.append(f"*{art.reason}*")
                    lines.append("")

        summary = analysis.section_summaries.get(cat_key)
        if summary and summary.summary_text:
            lines.append(f"> 🗂 **板块小结**  ")
            lines.append(f"> {summary.summary_text}")
            if summary.indicators_to_watch:
                lines.append("> ")
                for i in summary.indicators_to_watch:
                    lines.append(f"> 📌 {i}")
            lines.append("")

    if analysis.recommended_read:
        r = analysis.recommended_read
        lines.append("---")
        lines.append("## 📖 今日深度推荐 — ~20分钟")
        lines.append("")
        lines.append(f"**📄 [{r.title}]({r.url})**  ")
        lines.append(f"来源：{r.source}  ")
        lines.append(f"📌 **为什么推荐**：{r.why_recommend}  ")
        lines.append(f"🔗 **与今日新闻的关联**：{r.connection_to_today}  ")
        lines.append("")

    lines.append("---")
    lines.append("## 🗣 讨论 & 深入")
    lines.append("")
    lines.append("打开 Claude Code → 进入 002-daily-news 目录")
    lines.append("")
    lines.append("| 命令 | 功能 |")
    lines.append("|------|------|")
    lines.append("| `/brief` | 查看今日简报 |")
    lines.append("| `/discuss [id]` | 深入讨论某条新闻 |")
    lines.append("| `/deep [主题]` | 生成专题深度报告 |")
    lines.append("| `/insight [板块]` | 本周事件关联图谱 |")
    lines.append("| `/trend` | 跨板块交叉趋势 |")
    lines.append("")

    return "\n".join(lines)


def send_email(html_body: str, cfg) -> bool:
    """Send HTML email via Gmail SMTP. Returns True on success."""
    if not cfg.gmail_username or not cfg.gmail_app_password:
        logger.error("Gmail credentials not configured")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📬 每日简报 — {datetime.now().strftime('%Y年%m月%d日')}"
    msg["From"] = cfg.gmail_username
    msg["To"] = cfg.recipient_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    for attempt, delay in enumerate(cfg.retry_delays, 1):
        try:
            with smtplib.SMTP(cfg.gmail_smtp_server, cfg.gmail_smtp_port, timeout=30) as server:
                server.starttls()
                server.login(cfg.gmail_username, cfg.gmail_app_password)
                server.sendmail(cfg.gmail_username, cfg.recipient_email, msg.as_string())
            logger.info(f"Email sent to {cfg.recipient_email}")
            return True
        except Exception as e:
            logger.warning(f"SMTP attempt {attempt} failed: {e}")
            if attempt < len(cfg.retry_delays):
                import time
                time.sleep(delay)

    logger.error("All SMTP attempts failed")
    return False


def save_local(markdown_body: str, cfg) -> str:
    """Save Markdown to daily archive. Returns file path."""
    today = datetime.now().strftime("%Y-%m-%d")
    Path(cfg.daily_dir).mkdir(parents=True, exist_ok=True)
    filepath = Path(cfg.daily_dir) / f"{today}.md"
    filepath.write_text(markdown_body, encoding="utf-8")
    logger.info(f"Local archive saved to {filepath}")
    return str(filepath)


def deliver(analysis, cfg) -> tuple[bool, str]:
    """Main entry point: render, send email, save local. Returns (email_sent, local_path)."""
    date_cn = datetime.now().strftime("%Y年%m月%d日")

    html_body = render_html(analysis, date_cn)
    markdown_body = render_markdown(analysis, date_cn)

    email_sent = send_email(html_body, cfg)
    local_path = save_local(markdown_body, cfg)

    return email_sent, local_path
```

---

### Task 7: Main orchestrator

**Files:**
- Create: `01-main.py`

**Interfaces:**
- Consumes: all modules (via importlib)
- Produces: complete pipeline execution, exit code 0 on success

- [ ] **Step 1: Write 01-main.py**

```python
#!/usr/bin/env python3
"""002-daily-news — Main orchestrator.
Triggered by Windows Task Scheduler daily at 7:50.
Usage: python 01-main.py
"""
import importlib.util
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent


def _load_module(name: str, filename: str):
    """Load a Python module from a numbered filename (e.g., '02-config.py' → 'config')."""
    filepath = PROJECT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def setup_logging(logs_dir: Path):
    """Configure logging to file + stdout."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_file


def main():
    # Load config
    cfg_mod = _load_module("config", "02-config.py")
    cfg = cfg_mod.load_config()

    # Setup logging
    log_file = setup_logging(Path(cfg.logs_dir))
    logger = logging.getLogger("main")
    logger.info("=" * 60)
    logger.info("002-daily-news starting")
    logger.info(f"Log file: {log_file}")

    # Validate config
    issues = cfg_mod.validate_config(cfg)
    if issues:
        for issue in issues:
            logger.error(f"Config error: {issue}")
        logger.error("Aborting — fix .env and retry")
        sys.exit(1)

    # Load sources
    try:
        sources_data = json.loads(Path(cfg.sources_file).read_text(encoding="utf-8"))
        logger.info(f"Loaded {sum(len(v['sources']) for v in sources_data.values())} RSS sources")
    except Exception as e:
        logger.error(f"Failed to load sources: {e}")
        sys.exit(1)

    # Step 1: Fetch
    logger.info("Step 1/3: Fetching news...")
    fetch = _load_module("fetch", "03-fetch.py")
    try:
        grouped = fetch.fetch_all(sources_data, cfg)
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        sys.exit(1)

    total_articles = sum(len(v) for v in grouped.values())
    if total_articles == 0:
        logger.warning("No articles fetched — check network or RSS sources")
        sys.exit(0)
    logger.info(f"Fetched {total_articles} articles across 3 categories")

    # Step 2: Analyze
    logger.info("Step 2/3: Analyzing with DeepSeek...")
    analyze = _load_module("analyze", "04-analyze.py")
    try:
        analysis = analyze.analyze_news(grouped, cfg)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    logger.info(f"Analysis complete — {sum(len(v) for v in analysis.screened.values())} articles screened")
    logger.info(f"Estimated API cost: ${analysis.total_cost_estimate:.3f}")

    # Step 3: Deliver
    logger.info("Step 3/3: Delivering...")
    deliver = _load_module("deliver", "05-deliver.py")
    try:
        email_sent, local_path = deliver.deliver(analysis, cfg)
    except Exception as e:
        logger.error(f"Delivery failed: {e}")
        sys.exit(1)

    if email_sent:
        logger.info(f"Email sent to {cfg.recipient_email}")
    else:
        logger.warning("Email NOT sent (check Gmail credentials)")
    logger.info(f"Local archive: {local_path}")
    logger.info("=" * 60)
    logger.info("Done!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Verify imports resolve**

```bash
cd "C:/Users/AlyssaLin/cc projects/002-daily-news"
python -c "
import sys
sys.path.insert(0, '.')
# Verify all numbered files exist
from pathlib import Path
files = ['01-main.py', '02-config.py', '03-fetch.py', '04-analyze.py', '05-deliver.py', '06-sources.json']
for f in files:
    p = Path(f)
    if p.exists():
        print(f'✅ {f}')
    else:
        print(f'❌ {f} MISSING')
"
```

---

### Task 8: Setup script & Windows Task Scheduler

**Files:**
- Create: `setup.ps1`

- [ ] **Step 1: Write setup.ps1**

```powershell
# 002-daily-news setup script
# Run once to install Python dependencies and create scheduled task

Write-Host "=== 002-daily-news Setup ===" -ForegroundColor Cyan

# Check Python
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    $python = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $python) {
    Write-Host "ERROR: Python not found. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $python" -ForegroundColor Green

# Install dependencies
Write-Host "`nInstalling Python packages..." -ForegroundColor Yellow
& $python -m pip install -r requirements.txt --quiet
Write-Host "Dependencies installed." -ForegroundColor Green

# Check .env
$envFile = "C:\Users\AlyssaLin\cc projects\002-daily-news\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "`nCreating .env from example..." -ForegroundColor Yellow
    Copy-Item "$envFile.example" $envFile
    Write-Host "Please edit $envFile with your API keys:" -ForegroundColor Red
    Write-Host "  - DEEPSEEK_API_KEY" -ForegroundColor Red
    Write-Host "  - GMAIL_USERNAME" -ForegroundColor Red
    Write-Host "  - GMAIL_APP_PASSWORD" -ForegroundColor Red
}

# Create scheduled task
$taskName = "002-daily-news"
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "`nScheduled task '$taskName' already exists. Removing old..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $python `
    -Argument "C:\Users\AlyssaLin\cc projects\002-daily-news\01-main.py" `
    -WorkingDirectory "C:\Users\AlyssaLin\cc projects\002-daily-news"

$trigger = New-ScheduledTaskTrigger -Daily -At 7:50AM

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -WakeToRun:$false  # Don't wake computer

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Daily news brief — fetch RSS, analyze with DeepSeek, send via Gmail"

Write-Host "`n✅ Scheduled task '$taskName' created — runs daily at 7:50 AM" -ForegroundColor Green

# Test run
Write-Host "`nTest run? (y/n)" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "y") {
    Write-Host "Running test..." -ForegroundColor Cyan
    & $python "C:\Users\AlyssaLin\cc projects\002-daily-news\01-main.py"
}
```

---

### Task 9: Discuss module — Claude Code commands

**Files:**
- Create: `07-discuss.py`
- Create: `08-report.py`

**Interfaces:**
- Consumes: local archive files in `daily/`, `reports/`, cached articles
- Produces: interactive analysis via Claude Code

- [ ] **Step 1: Write 07-discuss.py**

```python
"""Claude Code interaction commands for 002-daily-news.
These are invoked by the user within Claude Code when the working
directory is 002-daily-news. Claude reads this file and executes
the appropriate function based on the user's slash command.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_DIR = Path(__file__).parent
DAILY_DIR = PROJECT_DIR / "daily"
REPORTS_DIR = PROJECT_DIR / "reports"


def cmd_brief(date_str: str = None):
    """Show today's (or specified date's) brief.
    Usage: /brief          → today
           /brief 0623     → June 23
    """
    if date_str:
        # Parse "0623" → "2026-06-23"
        month, day = int(date_str[:2]), int(date_str[2:4])
        year = datetime.now().year
        target = f"{year}-{month:02d}-{day:02d}"
    else:
        target = datetime.now().strftime("%Y-%m-%d")

    filepath = DAILY_DIR / f"{target}.md"
    if not filepath.exists():
        available = sorted(DAILY_DIR.glob("*.md"))
        if not available:
            return "尚无任何简报存档。"

        # Find closest
        available_str = "\n".join(f"  {p.stem}" for p in available[-7:])
        return (
            f"未找到 {target} 的简报。\n\n"
            f"最近 7 天可用简报：\n{available_str}\n\n"
            f"用法：`/brief 0623` 查看指定日期"
        )

    return filepath.read_text(encoding="utf-8")


def cmd_discuss(article_id: str, analysis):
    """Deep-dive discussion on a specific article.
    Usage: /discuss ai-01
    """
    # Search all briefs for this article ID
    found = None
    for md_file in sorted(DAILY_DIR.glob("*.md"), reverse=True)[:7]:
        content = md_file.read_text(encoding="utf-8")
        if f"[{article_id}]" in content:
            found = content
            break

    if not found:
        return f"未找到文章 [{article_id}]。请检查 ID 是否正确。"

    # TODO: Extract the article section and feed to analysis module for deeper analysis
    return f"找到 [{article_id}]。需要进一步分析的内容：\n\n（此处加载文章原文并调用 DeepSeek 做多角度深度分析——各方立场、争议点、历史脉络、可能走向）"


def cmd_deep(topic: str, analysis):
    """Generate a deep-dive report on a topic spanning 7 days of news.
    Usage: /deep 台海局势
    """
    # Search recent 7 days of briefs for topic-related articles
    related = []
    for md_file in sorted(DAILY_DIR.glob("*.md"), reverse=True)[:7]:
        content = md_file.read_text(encoding="utf-8").lower()
        if topic.lower() in content:
            related.append(md_file.stem)

    if not related:
        return f"最近 7 天简报中未找到与「{topic}」相关的内容。"

    # TODO: Load relevant articles, feed to DeepSeek for 1500-2000 word report
    return (
        f"## 📊 专题报告：{topic}\n\n"
        f"相关简报：{', '.join(related)}\n\n"
        f"（生成 1500-2000 字深度报告：历史背景 → 各方立场 → 关键节点 → 可能走向）"
    )


def cmd_insight(category: str, analysis):
    """Generate event correlation map for a category over the week.
    Usage: /insight 财经
    """
    cat_map = {"ai": "ai_tech", "科技": "ai_tech", "财经": "finance", "国际": "intl_trends", "趋势": "intl_trends"}
    cat_key = cat_map.get(category, category)

    # Collect articles from past 7 days in this category
    # TODO: Generate Mermaid diagram showing event correlations
    return f"## 🗺 {category}板块 — 本周事件关联\n\n（Mermaid 关联图 + 关键传导路径分析）"


def cmd_trend():
    """Cross-category trend analysis.
    Usage: /trend
    """
    # Load past 3 days, identify cross-category causal chains
    return "## 🔀 跨板块交叉趋势\n\n（AI/财经/国际趋势三板块因果关系链 + 交互影响分析）"
```

---

### Task 10: End-to-end verification

- [ ] **Step 1: Dry run test (no API key required for config validation)**

```bash
cd "C:/Users/AlyssaLin/cc projects/002-daily-news"
python -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('config', '02-config.py')
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)
c = cfg.load_config()
issues = cfg.validate_config(c)
if issues:
    for i in issues:
        print(f'⚠️  {i}')
    print('Config has issues (expected if .env not filled)')
else:
    print('✅ Config valid')
"
```

- [ ] **Step 2: With .env configured, manual full run**

```bash
cd "C:/Users/AlyssaLin/cc projects/002-daily-news"
python 01-main.py
```

Expected: news fetched, analyzed, email sent, `daily/YYYY-MM-DD.md` created.

- [ ] **Step 3: Check output**

```bash
ls daily/
cat daily/$(date +%Y-%m-%d).md | head -50
```

- [ ] **Step 4: Test scheduled task run**

```powershell
# In PowerShell as Administrator:
Start-ScheduledTask -TaskName "002-daily-news"
# Check Task Scheduler UI for result
```

---

### Task 11: Update 00-INDEX.md

- [ ] **Step 1: Finalize 00-INDEX.md**

Verify all file counts, descriptions, and dependency graph match the delivered files. Already created in Task 0, but update if any files changed during implementation.

---

## Implementation Order

```
Task 1  → scaffolding, directories, requirements
Task 2  → config module
Task 3  → sources JSON
Task 4  → fetch module (largest, most complex)
Task 5  → analyze module
Task 6  → deliver module
Task 7  → main orchestrator
Task 8  → setup script
Task 9  → discuss commands
Task 10 → end-to-end verification
Task 11 → finalize index
```

Tasks 2-3 can be done in parallel. Tasks 4-6 build sequentially. Task 7 ties them together.
