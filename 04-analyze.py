"""DeepSeek AI analysis — screening, deep analysis, summaries, recommendations."""
import json
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("analyze")

CATEGORY_LABELS = {"ai_tech": "AI/科技", "finance": "财经", "intl_trends": "国际趋势"}
CATEGORY_PREFIX = {"ai_tech": "ai", "finance": "fin", "intl_trends": "intl"}


# ── Data Classes ─────────────────────────────────────────

@dataclass
class ScreenedArticle:
    id: str              # display ID like "ai-01"
    title: str
    summary: str
    url: str
    source_name: str
    region: str
    score: int
    final_score: float
    reason: str
    category: str
    heat_multiplier: float
    social_signals: list = field(default_factory=list)

    def star_count(self) -> int:
        if self.final_score >= 5: return 3
        elif self.final_score >= 4: return 2
        return 1

    def is_hot(self) -> bool:
        return self.heat_multiplier > 1.0

    def is_key(self) -> bool:
        return self.final_score >= 4.5

    @classmethod
    def from_article(cls, article, score=3, reason="", final_score=3.0):
        return cls(id="", title=article.title, summary=article.summary,
                   url=article.url, source_name=article.source_name, region=article.region,
                   score=score, final_score=final_score, reason=reason,
                   category=article.category, heat_multiplier=article.heat_multiplier,
                   social_signals=article.social_signals)


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
    one_liner: str
    screened: dict[str, list]      # key articles only (top N)
    compact: dict[str, list]       # secondary articles (title+link)
    deep_analyses: list
    section_summaries: dict[str, SectionSummary]
    bg_concepts: dict[str, str]
    recommended_read: RecommendedRead | None
    total_cost_estimate: float


# ── Prompts ──────────────────────────────────────────────

SCREENING_PROMPT = """你是新闻主编。为以下 RSS 新闻评分（1-5分，5分最高）。

评分标准：
- 5分：会对行业/市场/地缘产生实质性影响的重大事件
- 4分：重要动态，值得关注但非转折性事件
- 3分：一般性新闻，有信息量但影响有限
- 2分：趣味性内容，行业杂谈
- 1分：广告/软文/无实质信息

新闻列表：
{articles_json}

输出严格JSON：
{{"scored": [{{"id": "...", "score": 3, "reason": "一句话理由(中文)", "adjusted_score": 3.0}}]}}
adjusted_score = score × heat_multiplier（round 到 0.1）"""


KEYWORDS_PROMPT = """基于今日新闻（三个板块），提取 5 个关键词，写一句 30 字内的一句话定调。

今日要闻摘要：
{summary}

输出JSON：
{{"keywords": ["关键词1", "关键词2", ...], "one_liner": "一句话总结今日核心趋势"}}"""


DEEP_ANALYSIS_PROMPT = """你是资深分析师。为以下新闻撰写深度分析，面向入门读者。用中文写，技术术语保留英文原文。

新闻标题：{title}
来源：{source}
原文摘要：{summary}

输出以下四个字段（严格JSON）：
1. what_happened: 100-150字，讲清事件核心。人物/公司/数据要具体。
2. why_matters: 100-150字，补充必要背景知识，解释这个事件的行业/经济/地缘意义。假设读者刚入门。
3. short_term_impact: 2-3条短期影响（1-3个月），每条一句话。
4. mid_term_impact: 2-3条中期影响（3-12个月），每条一句话。

JSON格式：
{{"what_happened": "", "why_matters": "", "short_term_impact": ["", ""], "mid_term_impact": ["", ""]}}"""


SECTION_SUMMARY_PROMPT = """你是板块主编。基于今日该板块要点新闻，写一段 120-180 字的板块小结。

板块：{category_label}
今日要点：
{articles_summary}

要求：
- 串联事件之间的逻辑关系（如 A 导致 B、A 与 B 共同指向 C 趋势）
- 给出 2-3 个"后续该盯住的指标/事件"
- 面向入门读者

输出JSON：
{{"summary_text": "...", "indicators_to_watch": ["...", "..."]}}"""


BG_CONCEPTS_PROMPT = """为以下新闻提取 2-3 个当日出现的核心概念/术语，给入门读者简短解释。

板块：{category_label}
新闻：
{articles_summary}

只提取当日出现的新概念。每项 50-80 字中文解释。全都是常规话题则返回空数组。

输出JSON：
{{"concepts": [{{"term": "...", "explanation": "..."}}]}}"""


RECOMMEND_PROMPT = """你是阅读推荐编辑。从今日新闻中推荐一篇值得深度阅读的长文。

今日要闻：
{all_titles}

推荐标准：与今日重要新闻深度相关、预计阅读 15-25 分钟、质量好、有独特观点。

输出JSON：
{{"title": "", "url": "", "source": "", "why_recommend": "100字推荐理由", "connection_to_today": "50字关联说明"}}"""


# ── DeepSeek Client ──────────────────────────────────────

class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.total_cost = 0.0

    def _call(self, system_prompt: str, user_prompt: str,
              model: str = "deepseek-chat", temperature: float = 0.3,
              max_tokens: int = 4096) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": temperature, "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        for attempt in range(3):
            try:
                resp = httpx.post(f"{self.base_url}/v1/chat/completions", headers=headers, json=body, timeout=120)
                resp.raise_for_status()
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                self.total_cost += (usage.get("prompt_tokens", 0) * 0.14 + usage.get("completion_tokens", 0) * 0.28) / 1_000_000
                return json.loads(content)
            except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"API attempt {attempt + 1}: {e}")
                if attempt == 2: raise
        return {}

    def screen_articles(self, articles: list, category: str, region: str) -> list[ScreenedArticle]:
        if not articles: return []
        articles_json = json.dumps([{
            "id": a.id, "title": a.title, "summary": a.summary[:200],
            "heat_multiplier": a.heat_multiplier,
        } for a in articles], ensure_ascii=False)
        try:
            result = self._call(
                system_prompt="你是专业新闻主编。只输出JSON。",
                user_prompt=SCREENING_PROMPT.format(articles_json=articles_json),
                model="deepseek-chat", temperature=0.2,
            )
        except Exception as e:
            logger.warning(f"Screening failed {category}/{region}: {e}")
            return [ScreenedArticle.from_article(a, score=3, reason="(fallback)", final_score=3.0 * a.heat_multiplier) for a in articles[:15]]

        score_map = {s["id"]: s for s in result.get("scored", [])}
        scored = []
        for a in articles:
            s = score_map.get(a.id, {})
            final = s.get("adjusted_score", s.get("score", 3))
            if final >= 3:
                scored.append(ScreenedArticle.from_article(a, score=s.get("score", 3), reason=s.get("reason", ""), final_score=final))
        return scored

    def generate_keywords(self, screened: dict) -> tuple[list[str], str]:
        lines = []
        for cat in ["ai_tech", "finance", "intl_trends"]:
            arts = screened.get(cat, [])
            if arts:
                lines.append(f"{CATEGORY_LABELS.get(cat, cat)}:")
                lines.extend(f"  - {a.title}" for a in arts[:5])
        try:
            result = self._call(
                system_prompt="你是新闻主编。只输出JSON。",
                user_prompt=KEYWORDS_PROMPT.format(summary="\n".join(lines)),
                model="deepseek-chat", temperature=0.4, max_tokens=512,
            )
            return result.get("keywords", [])[:5], result.get("one_liner", "")
        except Exception as e:
            logger.warning(f"Keywords failed: {e}")
            return ["全球", "科技", "财经", "国际", "今日"], ""

    def deep_analyze(self, article: ScreenedArticle) -> DeepAnalysis:
        try:
            result = self._call(
                system_prompt="你是资深分析师。只输出JSON。",
                user_prompt=DEEP_ANALYSIS_PROMPT.format(title=article.title, source=article.source_name, summary=article.summary),
                model="deepseek-chat", temperature=0.4, max_tokens=2048,
            )
        except Exception as e:
            logger.warning(f"Deep failed [{article.id}]: {e}")
            return DeepAnalysis(article_id=article.id, what_happened=article.summary[:200], why_matters=f"来自 {article.source_name}。{article.reason}", short_term_impact=[], mid_term_impact=[])
        return DeepAnalysis(article_id=article.id, what_happened=result.get("what_happened", ""), why_matters=result.get("why_matters", ""), short_term_impact=result.get("short_term_impact", []), mid_term_impact=result.get("mid_term_impact", []))

    def summarize_section(self, category: str, articles: list[ScreenedArticle]) -> SectionSummary:
        if not articles: return SectionSummary(category=category, summary_text="", indicators_to_watch=[])
        summary = "\n".join(f"- [{a.id}] {a.title}" for a in articles[:10])
        try:
            result = self._call(
                system_prompt="你是板块主编。只输出JSON。",
                user_prompt=SECTION_SUMMARY_PROMPT.format(category_label=CATEGORY_LABELS.get(category, category), articles_summary=summary),
                model="deepseek-chat", temperature=0.5, max_tokens=1024,
            )
        except Exception as e:
            logger.warning(f"Summary failed [{category}]: {e}")
            return SectionSummary(category=category, summary_text="", indicators_to_watch=[])
        return SectionSummary(category=category, summary_text=result.get("summary_text", ""), indicators_to_watch=result.get("indicators_to_watch", []))

    def generate_bg_concepts(self, category: str, articles: list[ScreenedArticle]) -> str:
        if not articles: return ""
        summary = "\n".join(f"- {a.title}: {a.reason}" for a in articles[:8])
        try:
            result = self._call(
                system_prompt="你是科普编辑。只输出JSON。",
                user_prompt=BG_CONCEPTS_PROMPT.format(category_label=CATEGORY_LABELS.get(category, category), articles_summary=summary),
                model="deepseek-chat", temperature=0.3, max_tokens=1024,
            )
        except Exception as e:
            logger.warning(f"BG failed [{category}]: {e}")
            return ""
        concepts = result.get("concepts", [])
        return "  \n".join(f"**{c['term']}**：{c['explanation']}" for c in concepts) if concepts else ""

    def recommend_read(self, all_screened: dict[str, list]) -> RecommendedRead | None:
        lines = []
        for cat, articles in all_screened.items():
            lines.append(f"【{CATEGORY_LABELS.get(cat, cat)}】")
            lines.extend(f"- {a.title}" for a in articles[:5])
        if not lines: return None
        try:
            result = self._call(
                system_prompt="你是阅读推荐编辑。只输出JSON。",
                user_prompt=RECOMMEND_PROMPT.format(all_titles="\n".join(lines)),
                model="deepseek-chat", temperature=0.5, max_tokens=1024,
            )
        except Exception as e:
            logger.warning(f"Recommend failed: {e}")
            return None
        return RecommendedRead(title=result.get("title", ""), url=result.get("url", ""), source=result.get("source", ""), why_recommend=result.get("why_recommend", ""), connection_to_today=result.get("connection_to_today", ""))


# ── Helpers ──────────────────────────────────────────────

def _assign_display_ids(screened: dict[str, list]) -> tuple[dict, dict]:
    """Key = only ⭐⭐⭐ (final_score >= 4.5), deep analysis. Compact = ⭐⭐ + ⭐.
    Balanced: up to 3 per region for key, up to 5 per region for compact."""
    key_arts = {}
    compact_arts = {}

    for cat, articles in screened.items():
        prefix = CATEGORY_PREFIX.get(cat, cat)
        articles = sorted(articles, key=lambda x: x.final_score, reverse=True)

        overseas = [a for a in articles if a.region in ("overseas", "both")]
        china = [a for a in articles if a.region in ("china", "both")]

        # Key: ⭐⭐⭐ only (final_score >= 4.5), max 3 per region
        key_ov = [a for a in overseas if a.final_score >= 4.5][:3]
        key_cn = [a for a in china if a.final_score >= 4.5 and a not in key_ov][:3]
        key_list = key_ov + key_cn

        # Compact: ⭐⭐ + ⭐ (final_score >= 3), max 5 per region, exclude key
        key_ids = {a.url for a in key_list}
        rest_ov = [a for a in overseas if a.url not in key_ids and a.final_score >= 3]
        rest_cn = [a for a in china if a.url not in key_ids and a.final_score >= 3]
        compact_list = rest_cn[:5] + rest_ov[:5]
        # Dedup compact by url
        seen = set()
        compact_dedup = []
        for a in compact_list:
            if a.url not in seen:
                seen.add(a.url)
                compact_dedup.append(a)
        compact_list = compact_dedup

        for i, art in enumerate(key_list, 1):
            art.id = f"{prefix}-{i:02d}"
        for i, art in enumerate(compact_list, 1):
            art.id = f"{prefix}-c{i:02d}"

        key_arts[cat] = key_list
        compact_arts[cat] = compact_list

        logger.info(f"  {cat}: {len(key_ov)}ov+{len(key_cn)}cn ⭐⭐⭐, {len(rest_cn[:5])}cn+{len(rest_ov[:5])}ov compact")

    return key_arts, compact_arts


# ── Main Entry ───────────────────────────────────────────

def analyze_news(grouped_articles: dict[str, list], cfg) -> DailyAnalysis:
    logger.info("=== Analysis cycle start ===")
    client = DeepSeekClient(api_key=cfg.deepseek_api_key, base_url=cfg.deepseek_base_url)

    # Step 1: Screen all categories
    screened = {}
    for cat in ["ai_tech", "finance", "intl_trends"]:
        articles = grouped_articles.get(cat, [])
        if not articles:
            screened[cat] = []
            continue
        overseas = [a for a in articles if a.region in ("overseas", "both")]
        china = [a for a in articles if a.region in ("china", "both")]
        ov = client.screen_articles(overseas, cat, "overseas") if overseas else []
        cn = client.screen_articles(china, cat, "china") if china else []
        screened[cat] = sorted(ov + cn, key=lambda x: x.final_score, reverse=True)
        logger.info(f"  Screened {cat}: {len(screened[cat])} (from {len(articles)})")

    # Step 2: Assign display IDs, split key vs compact
    key_articles, compact_articles = _assign_display_ids(screened)

    # Step 3: Keywords + one-liner (DeepSeek generated)
    keywords, one_liner = client.generate_keywords(key_articles)

    # Step 4: Deep analysis — ALL key articles (they are all ⭐⭐⭐)
    deep_analyses = []
    for cat, articles in key_articles.items():
        for article in articles:
            try:
                deep_analyses.append(client.deep_analyze(article))
                logger.info(f"  Deep: [{article.id}] {article.title[:50]}...")
            except Exception as e:
                logger.warning(f"  Deep failed [{article.id}]: {e}")

    # Step 5: Section summaries
    section_summaries = {}
    for cat, articles in key_articles.items():
        try:
            section_summaries[cat] = client.summarize_section(cat, articles)
        except Exception as e:
            logger.warning(f"  Summary failed [{cat}]: {e}")
            section_summaries[cat] = SectionSummary(cat, "", [])

    # Step 6: Background concepts
    bg_concepts = {}
    for cat, articles in key_articles.items():
        try:
            bg_concepts[cat] = client.generate_bg_concepts(cat, articles)
        except Exception as e:
            logger.warning(f"  BG failed [{cat}]: {e}")
            bg_concepts[cat] = ""

    # Step 7: Recommended read
    recommended = client.recommend_read(key_articles)

    logger.info(f"=== Analysis complete — est. cost ${client.total_cost:.3f} ===")
    logger.info(f"  Key articles: {sum(len(v) for v in key_articles.values())}")
    logger.info(f"  Compact: {sum(len(v) for v in compact_articles.values())}")
    logger.info(f"  Deep analyses: {len(deep_analyses)}")

    return DailyAnalysis(
        keywords=keywords, one_liner=one_liner,
        screened=key_articles, compact=compact_articles,
        deep_analyses=deep_analyses,
        section_summaries=section_summaries, bg_concepts=bg_concepts,
        recommended_read=recommended, total_cost_estimate=client.total_cost,
    )
