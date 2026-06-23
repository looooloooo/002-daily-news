"""Email delivery (Gmail SMTP) + local Markdown archive."""
import logging
import smtplib
import time
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

logger = logging.getLogger("deliver")

CATEGORY_EMOJI = {"ai_tech": "🤖", "finance": "💰", "intl_trends": "🌍"}
CATEGORY_LABELS = {"ai_tech": "AI/科技", "finance": "财经", "intl_trends": "国际趋势"}
REGION_LABELS = {"overseas": "🌏 海外", "china": "🇨🇳 中国", "both": "🌏🇨🇳"}


def _date_cn() -> str:
    now = datetime.now()
    return f"{now.year}年{now.month}月{now.day}日"


def _nl2br(text: str) -> str:
    """Convert newlines to <br> for HTML rendering."""
    return text.replace("\n", "<br>")


def render_html(analysis, date_cn: str) -> str:
    """Render DailyAnalysis into HTML email body."""

    # ── Header: one-liner + keywords ──
    kw_html = f"🔥 {analysis.one_liner or ' · '.join(analysis.keywords)}"

    parts = []

    for cat_key in ["ai_tech", "finance", "intl_trends"]:
        key_articles = analysis.screened.get(cat_key, [])
        compact_articles = analysis.compact.get(cat_key, [])
        if not key_articles and not compact_articles:
            continue

        emoji = CATEGORY_EMOJI.get(cat_key, "")
        label = CATEGORY_LABELS.get(cat_key, cat_key)
        html = f'<div class="section"><h2 class="section-title">{emoji} {label}</h2>'

        # Background concepts
        bg = analysis.bg_concepts.get(cat_key, "")
        if bg:
            html += f'<div class="bg-box">📚 <strong>入门背景</strong><br>{_nl2br(bg)}</div>'

        deep_map = {da.article_id: da for da in analysis.deep_analyses}

        for region in ["overseas", "china"]:
            region_keys = [a for a in key_articles if a.region in (region, "both")]
            region_compact = [a for a in compact_articles if a.region in (region, "both")]
            if not region_keys and not region_compact:
                continue

            html += f'<h3>{REGION_LABELS.get(region, region)}</h3>'

            # Key articles — full cards
            for art in region_keys:
                stars = "⭐" * art.star_count()
                fire = " 🔥" if art.is_hot() else ""
                tag_html = '<span class="china-tag">中国</span>' if art.region == "china" else '<span class="overseas-tag">海外</span>'
                deep = deep_map.get(art.id)

                card = '<div class="card">'
                card += f'<div class="card-title">[{art.id}] {art.title} · {stars}{fire} {tag_html}</div>'
                card += f'<div class="card-meta">📰 {art.source_name}</div>'

                if deep:
                    card += f'<div class="card-section"><span class="label">📰 发生了什么</span><br>{_nl2br(deep.what_happened)}</div>'
                    card += f'<div class="card-section"><span class="label">🔍 为什么值得关注</span><br>{_nl2br(deep.why_matters)}</div>'
                    card += '<div class="impacts">'
                    card += f'<div class="impact"><span class="ilabel">⚡ 短期影响 (1-3月)</span><br>{"<br>".join("· " + i for i in deep.short_term_impact)}</div>'
                    card += f'<div class="impact"><span class="ilabel">🔮 中期影响 (3-12月)</span><br>{"<br>".join("· " + i for i in deep.mid_term_impact)}</div>'
                    card += '</div>'
                else:
                    card += f'<div class="card-section">{art.summary[:300]}</div>'
                    card += f'<div class="card-meta" style="margin-top:8px">{art.reason}</div>'

                card += '</div>'
                html += card

            # Compact articles — title + brief + link only
            if region_compact:
                html += '<div style="padding:8px 0">'
                html += '<div style="font-size:13px;color:#888;margin-bottom:6px">📋 更多关注</div>'
                for art in region_compact:
                    tag_html = '<span class="china-tag" style="font-size:10px">中国</span>' if art.region == "china" else '<span class="overseas-tag" style="font-size:10px">海外</span>'
                    # Mixed language: keep original summary language, don't force translate
                    brief = art.summary[:150] if art.summary else ""
                    html += (
                        f'<div style="margin:4px 0;font-size:13px;line-height:1.5">'
                        f'[{art.id}] {tag_html} <strong>{art.title}</strong><br>'
                        f'<span style="color:#666">{brief}</span> '
                        f'<a href="{art.url}" style="font-size:11px;color:#4a90d9">原文 →</a>'
                        f'</div>'
                    )
                html += '</div>'

        # Section summary
        summary = analysis.section_summaries.get(cat_key)
        if summary and summary.summary_text:
            indicators = " &nbsp;".join(f"📌 {i}" for i in summary.indicators_to_watch)
            html += f'<div class="summary-box">🗂 <strong>板块小结</strong><br>{_nl2br(summary.summary_text)}<br><br>{indicators}</div>'

        html += '</div>'
        parts.append(html)

    # Recommended read
    rec_html = ""
    if analysis.recommended_read:
        r = analysis.recommended_read
        rec_html = f'''<div class="recommend">
<h2>📖 今日深度推荐 — ~20分钟</h2>
<p><strong>📄 {r.title}</strong></p>
<p>来源：{r.source}</p>
<p>📌 <strong>为什么推荐：</strong>{_nl2br(r.why_recommend)}</p>
<p>🔗 <strong>与今日新闻的关联：</strong>{_nl2br(r.connection_to_today)}</p>
<p>📎 <a href="{r.url}">{r.url}</a></p>
</div>'''

    # Discussion footer
    discuss = '''<div class="discuss">
<h3>🗣 讨论 &amp; 深入</h3>
<p>打开 Claude Code → 进入 002-daily-news 目录</p>
<p>
<code>/brief</code> 简报 &nbsp;
<code>/discuss [id]</code> 深入 &nbsp;
<code>/deep [主题]</code> 专题 &nbsp;
<code>/insight [板块]</code> 关联图 &nbsp;
<code>/trend</code> 交叉趋势
</p>
</div>'''

    # Load template
    template_path = Path(__file__).parent / "templates" / "email.html"
    template = template_path.read_text(encoding="utf-8")

    body = template.replace("{{ date_cn }}", date_cn)
    body = body.replace("{{ keywords }}", kw_html)
    body = body.replace("{{ content }}", "\n".join(parts) + rec_html + discuss)

    return body


def render_markdown(analysis, date_cn: str) -> str:
    """Render DailyAnalysis into Markdown for local archive."""
    lines = [
        f"# 📬 每日简报 — {date_cn}",
        "",
        f"🔥 **{analysis.one_liner or ' · '.join(analysis.keywords)}**",
        "",
    ]

    deep_map = {da.article_id: da for da in analysis.deep_analyses}

    for cat_key in ["ai_tech", "finance", "intl_trends"]:
        key_articles = analysis.screened.get(cat_key, [])
        compact_articles = analysis.compact.get(cat_key, [])
        if not key_articles and not compact_articles:
            continue

        emoji = CATEGORY_EMOJI.get(cat_key, "")
        label = CATEGORY_LABELS.get(cat_key, cat_key)

        lines.append("---")
        lines.append(f"## {emoji} {label}")
        lines.append("")

        bg = analysis.bg_concepts.get(cat_key, "")
        if bg:
            lines.append("> 📚 **入门背景**")
            lines.append(f"> {bg}")
            lines.append("")

        for region in ["overseas", "china"]:
            region_keys = [a for a in key_articles if a.region in (region, "both")]
            region_compact = [a for a in compact_articles if a.region in (region, "both")]
            if not region_keys and not region_compact:
                continue
            lines.append(f"### {REGION_LABELS.get(region, region)}")
            lines.append("")

            # Key articles
            for art in region_keys:
                stars = "⭐" * art.star_count()
                fire = " 🔥" if art.is_hot() else ""
                deep = deep_map.get(art.id)

                lines.append(f"#### [{art.id}] {art.title} · {stars}{fire}")
                lines.append(f"*{art.source_name}*")
                lines.append("")

                if deep:
                    lines.append("**📰 发生了什么**")
                    lines.append(deep.what_happened)
                    lines.append("")
                    lines.append("**🔍 为什么值得关注**")
                    lines.append(deep.why_matters)
                    lines.append("")
                    lines.append("**⚡ 短期影响 (1-3月)**")
                    for i in deep.short_term_impact:
                        lines.append(f"- {i}")
                    lines.append("")
                    lines.append("**🔮 中期影响 (3-12月)**")
                    for i in deep.mid_term_impact:
                        lines.append(f"- {i}")
                    lines.append("")
                else:
                    lines.append(art.summary[:300])
                    lines.append(f"*{art.reason}*")
                    lines.append("")

            # Compact articles
            if region_compact:
                lines.append("📋 **更多关注**")
                lines.append("")
                for art in region_compact:
                    brief = art.summary[:150] if art.summary else ""
                    lines.append(f"- [{art.id}] **{art.title}** — {brief} [🔗]({art.url})")
                lines.append("")

        summary = analysis.section_summaries.get(cat_key)
        if summary and summary.summary_text:
            lines.append("> 🗂 **板块小结**")
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
        lines.append(f"**📄 [{r.title}]({r.url})**")
        lines.append(f"来源：{r.source}")
        lines.append(f"📌 **为什么推荐**：{r.why_recommend}")
        lines.append(f"🔗 **与今日新闻的关联**：{r.connection_to_today}")
        lines.append("")

    lines.append("---")
    lines.append("## 🗣 讨论 & 深入")
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
    """Send HTML email via Gmail SMTP."""
    if not cfg.gmail_username or not cfg.gmail_app_password:
        logger.error("Gmail credentials not configured")
        return False

    today_cn = _date_cn()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"📬 每日简报 — {today_cn}", "utf-8")
    msg["From"] = cfg.gmail_username
    msg["To"] = cfg.recipient_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    for attempt in range(cfg.retry_count):
        try:
            with smtplib.SMTP(cfg.gmail_smtp_server, cfg.gmail_smtp_port, timeout=30) as server:
                server.starttls()
                server.login(cfg.gmail_username, cfg.gmail_app_password)
                server.sendmail(cfg.gmail_username, cfg.recipient_email, msg.as_string())
            logger.info(f"Email sent to {cfg.recipient_email}")
            return True
        except Exception as e:
            logger.warning(f"SMTP attempt {attempt + 1}: {e}")
            if attempt < cfg.retry_count - 1:
                time.sleep(cfg.retry_delays[attempt])

    logger.error("All SMTP attempts failed")
    return False


def save_local(markdown_body: str, cfg) -> str:
    """Save Markdown to daily archive."""
    today = datetime.now().strftime("%Y-%m-%d")
    Path(cfg.daily_dir).mkdir(parents=True, exist_ok=True)
    filepath = Path(cfg.daily_dir) / f"{today}.md"
    filepath.write_text(markdown_body, encoding="utf-8")
    logger.info(f"Saved to {filepath}")
    return str(filepath)


def deliver(analysis, cfg) -> tuple[bool, str]:
    """Main entry: render, send, save. Returns (email_sent, local_path)."""
    date_cn = _date_cn()
    html_body = render_html(analysis, date_cn)
    markdown_body = render_markdown(analysis, date_cn)
    email_sent = send_email(html_body, cfg)
    local_path = save_local(markdown_body, cfg)
    return email_sent, local_path
