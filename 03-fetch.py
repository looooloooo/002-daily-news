"""RSS + Social media dual-channel news fetcher."""
import hashlib
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
    region: str
    published: datetime
    category: str
    social_signals: list = field(default_factory=list)
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


@dataclass
class SocialTrend:
    title: str
    source: str
    region: str
    score: float
    keywords: list


# ── Helpers ──────────────────────────────────────────────


def _make_article_id(url: str) -> str:
    return hashlib.md5((url or "").encode()).hexdigest()[:12]


def _clean_summary(raw: str, max_len: int = 300) -> str:
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def _is_recent(published_parsed, max_hours: int = 30) -> bool:
    if not published_parsed:
        return True
    try:
        pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - pub_dt
        return age < timedelta(hours=max_hours)
    except Exception:
        return True


def _extract_keywords(text: str, max_kw: int = 5) -> list[str]:
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "in", "on", "at", "to", "for", "of", "and", "or", "with",
        "this", "that", "it", "its", "from", "by", "as", "but",
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
        "都", "一", "个", "上", "也", "很", "到", "说", "要",
    }
    words = re.findall(r"[a-zA-Z一-鿿]{2,}", text.lower())
    filtered = [w for w in words if w not in stopwords]
    return list(dict.fromkeys(filtered))[:max_kw]


def _keyword_overlap(kw1: list[str], kw2: list[str]) -> float:
    if not kw1 or not kw2:
        return 0.0
    s1, s2 = set(kw1), set(kw2)
    return len(s1 & s2) / len(s1 | s2) if (s1 | s2) else 0.0


# ── RSS Channel ──────────────────────────────────────────


def fetch_rss_sources(sources_data: dict, cfg) -> list[Article]:
    all_sources = []
    for cat_key, cat_data in sources_data.items():
        for src in cat_data["sources"]:
            all_sources.append((cat_key, src))

    def _fetch_one(cat_key: str, src: dict) -> list[Article]:
        articles = []
        try:
            resp = httpx.get(
                src["url"], timeout=cfg.fetch_timeout, follow_redirects=True,
                headers={"User-Agent": "002-daily-news/1.0"}
            )
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[: cfg.max_articles_per_source]:
                if not _is_recent(getattr(entry, "published_parsed", None)):
                    continue
                link = entry.get("link", "")
                if not link:
                    continue
                articles.append(Article(
                    id=_make_article_id(link),
                    title=(entry.get("title") or "").strip(),
                    summary=_clean_summary(entry.get("summary") or entry.get("description") or ""),
                    url=link,
                    source_name=src["name"],
                    region=src["region"],
                    published=datetime.now(),
                    category=cat_key,
                ))
        except Exception as e:
            logger.warning(f"RSS [{src['name']}]: {e}")
        return articles

    all_articles = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch_one, ck, s): (ck, s["name"]) for ck, s in all_sources}
        for fut in as_completed(futures):
            cat_key, name = futures[fut]
            try:
                results = fut.result()
                all_articles.extend(results)
                logger.info(f"RSS [{name}] → {len(results)} articles")
            except Exception as e:
                logger.warning(f"RSS [{name}] thread: {e}")

    return all_articles


# ── Social Channel ───────────────────────────────────────


SOCIAL_SOURCES = {
    "reddit_ml": {
        "name": "Reddit r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/hot.json?limit=25",
        "region": "overseas",
    },
    "reddit_tech": {
        "name": "Reddit r/technology",
        "url": "https://www.reddit.com/r/technology/hot.json?limit=25",
        "region": "overseas",
    },
    "reddit_world": {
        "name": "Reddit r/worldnews",
        "url": "https://www.reddit.com/r/worldnews/hot.json?limit=25",
        "region": "overseas",
    },
    "reddit_investing": {
        "name": "Reddit r/investing",
        "url": "https://www.reddit.com/r/investing/hot.json?limit=25",
        "region": "overseas",
    },
    "reddit_china": {
        "name": "Reddit r/China",
        "url": "https://www.reddit.com/r/China/hot.json?limit=25",
        "region": "china",
    },
    "reddit_geopolitics": {
        "name": "Reddit r/geopolitics",
        "url": "https://www.reddit.com/r/geopolitics/hot.json?limit=25",
        "region": "overseas",
    },
}


def fetch_social_trends(cfg) -> list[SocialTrend]:
    trends = []
    headers = {"User-Agent": "002-daily-news/1.0"}

    for key, src in SOCIAL_SOURCES.items():
        try:
            resp = httpx.get(
                src["url"], headers=headers,
                timeout=cfg.fetch_timeout, follow_redirects=True
            )
            resp.raise_for_status()

            is_reddit = key.startswith("reddit")
            if is_reddit:
                data = resp.json()
                for post in data.get("data", {}).get("children", [])[:15]:
                    post_data = post["data"]
                    title = post_data.get("title", "")
                    trends.append(SocialTrend(
                        title=title,
                        source=src["name"],
                        region=src["region"],
                        score=min(post_data.get("score", 0) / 500, 1.0),
                        keywords=_extract_keywords(title),
                    ))
            else:
                # RSSHub format
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:15]:
                    title = entry.get("title", "").strip()
                    desc = entry.get("description", entry.get("summary", ""))
                    trends.append(SocialTrend(
                        title=title,
                        source=src["name"],
                        region=src["region"],
                        score=0.5,
                        keywords=_extract_keywords(f"{title} {desc}"),
                    ))

            logger.info(f"Social [{src['name']}] → {len(trends)} trends (running)")
        except Exception as e:
            logger.warning(f"Social [{src['name']}]: {e}")

    return trends


# ── Cross-Match ──────────────────────────────────────────


def cross_match_social(articles: list[Article], trends: list[SocialTrend], threshold: float = 0.6) -> list[Article]:
    for article in articles:
        art_kw = _extract_keywords(f"{article.title} {article.summary}")
        matched = []

        for trend in trends:
            overlap = _keyword_overlap(art_kw, trend.keywords)
            if overlap > threshold:
                matched.append({
                    "source": trend.source,
                    "score": trend.score,
                    "title": trend.title,
                })

        if len(matched) >= 2:
            article.heat_multiplier = 1.5
        elif len(matched) == 1:
            article.heat_multiplier = 1.3

        article.social_signals = matched

    return articles


def deduplicate_articles(articles: list[Article], threshold: float = 0.8) -> list[Article]:
    unique = []
    for art in articles:
        art_kw = _extract_keywords(art.title, max_kw=8)
        is_dup = False
        for existing in unique:
            ex_kw = _extract_keywords(existing.title, max_kw=8)
            overlap = _keyword_overlap(art_kw, ex_kw)
            if overlap > threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(art)
    return unique


# ── Main Entry ───────────────────────────────────────────


def fetch_all(sources_data: dict, cfg) -> dict[str, list[Article]]:
    logger.info("=== Fetch cycle start ===")

    # 1. RSS
    logger.info("Fetching RSS...")
    articles = fetch_rss_sources(sources_data, cfg)
    logger.info(f"RSS total: {len(articles)}")

    # 2. Social
    logger.info("Fetching social trends...")
    trends = fetch_social_trends(cfg)
    logger.info(f"Social trends: {len(trends)}")

    # 3. Cross-match
    logger.info("Cross-matching RSS ↔ Social...")
    articles = cross_match_social(articles, trends, threshold=cfg.social_cross_match_threshold)
    hot_count = sum(1 for a in articles if a.heat_multiplier > 1.0)
    logger.info(f"Cross-match: {hot_count} articles have social signals")

    # 4. Dedup
    articles = deduplicate_articles(articles, threshold=cfg.similarity_threshold)
    logger.info(f"After dedup: {len(articles)}")

    # 5. Group by category
    grouped = {"ai_tech": [], "finance": [], "intl_trends": []}
    for art in articles:
        if art.category in grouped:
            grouped[art.category].append(art)

    for cat, arts in grouped.items():
        logger.info(f"  {cat}: {len(arts)} articles")

    return grouped


if __name__ == "__main__":
    import importlib.util, sys

    def load_mod(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    cfg = load_mod("config", "02-config.py").load_config()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sources = json.load(open(cfg.sources_file, encoding="utf-8"))
    result = fetch_all(sources, cfg)
    for cat, arts in result.items():
        print(f"\n{cat}: {len(arts)} articles")
        for a in arts[:5]:
            hot = "🔥" if a.heat_multiplier > 1.0 else ""
            print(f"  [{a.source_name}] {a.title[:80]}... {hot}")
