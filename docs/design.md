# 002-daily-news 设计文档

> 创建日期：2026-06-23
> 状态：待实现
> 最后更新：2026-06-23 (v2 — DeepSeek API + 社交热度混合)

---

## 1. 愿景

每天早上 8:00 通过 Gmail 收到一份 10 分钟可读完的全球新闻简报，包含 AI/科技、财经、国际趋势三个板块，中英文源混合覆盖。每条新闻讲清"发生了什么"和"为什么重要"，帮助从入门到形成独立判断。收到后可在 Claude Code 中继续追问、深挖任何一篇。

---

## 2. 架构

```
Windows Task Scheduler (每天 7:50)
        │
        ▼
  01-main.py (主控)
        │
        ├── 03-fetch.py (双通道并行抓取)
        │       │
        │       ├── RSS 通道：feedparser 解析 22 个 RSS 源
        │       │       → 输出 ~150 条原始新闻
        │       │
        │       └── 社交通道：Reddit / HN / 知乎 / 微博
        │               → 输出热点话题 + 讨论量
        │       │
        │       ├── 交叉匹配：RSS 标题 ↔ 社交热词
        │       │       → 热度乘数标签
        │       │
        │       └── 去重 + 当日过滤
        │               → 输出 ~150 条带热度标签的新闻
        │
        ├── 04-analyze.py (DeepSeek 两阶段处理)
        │       · DeepSeek-V3 初筛：评分 1-5 + 按板块归类
        │         → 筛剩 ~30-40 条
        │       · DeepSeek-V4 深度分析（仅 ⭐⭐⭐ 新闻）
        │         → "发生+背景+短期影响+中期影响"
        │       · DeepSeek-V4 板块小结 + 入门背景框
        │       · DeepSeek-V4 今日推荐长文（1篇）
        │
        └── 05-deliver.py
                · 渲染 HTML 邮件模板
                · Gmail SMTP 发送 (smtp.gmail.com:587)
                · 本地存档 → daily/YYYY-MM-DD.md
                · 失败重试 3 次，最终错误写入日志
```

---

## 3. 输出格式

### 邮件/存档结构

```
📬 每日简报 — 2026年6月23日
━━━━━━━━━━━━━━━━━━━━━━━━━━

┌ 今日关键词卡片（一句话定调，3-5个关键词）
└

🤖 AI/科技
  📚 入门背景框（当日相关概念 100-150 字）
  🌏 海外（每条带[id]标签）
    ┌─ [ai-01] 标题 · ⭐⭐⭐ · 🔥双重验证 ────┐
    │ 📰 发生了什么 (100-150字)                 │
    │ 🔍 为什么值得关注 (100-150字)              │
    │ ⚡ 短期影响 (1-3月) · 🔮 中期影响 (3-12月) │
    └──────────────────────────────────────────┘
    [ai-02] ⭐⭐ (格式同上，无影响分析)
  🇨🇳 中国（同上结构）
  🗂 板块小结（150-200字串联事件逻辑）

💰 财经（同上三栏结构）
🌍 国际趋势（同上三栏结构）

📖 今日深度推荐 (~20分钟)
  · 推荐文章标题+来源+热度说明
  · 推荐理由（与今日新闻的关联）
  · 原文链接

🗣 讨论入口
  /brief  查看今日简报
  /discuss [id]  深入讨论某条
  /deep [主题]  专题深度报告
  /insight [板块]  本周事件关联图谱
  /trend  跨板块交叉趋势
```

### 条数策略
- 不设固定条数，由当天新闻质量决定
- DeepSeek 评分 ≥3 入选，≥4 带 ⭐⭐，5 带 ⭐⭐⭐
- RSS+社交双源交叉命中的自动 +1 星
- 预期：每板块 4-7 条，总计 12-20 条
- ⭐⭐⭐ 每板块 ≤3 条，超量则择优

---

## 4. 数据源

### 4.1 RSS 源（06-sources.json）

```json
{
  "ai_tech": {
    "label": "AI/科技",
    "sources": [
      {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "region": "overseas"},
      {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "region": "overseas"},
      {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "region": "overseas"},
      {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "region": "overseas"},
      {"name": "Hacker News (AI)", "url": "https://hnrss.org/frontpage?q=ai+OR+ml+OR+llm", "region": "overseas"},
      {"name": "机器之心", "url": "https://jiqizhixin.com/rss", "region": "china"},
      {"name": "量子位", "url": "https://www.qbitai.com/feed", "region": "china"},
      {"name": "差评", "url": "https://rsshub.app/chaping/newsflashes", "region": "china"}
    ]
  },
  "finance": {
    "label": "财经",
    "sources": [
      {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews", "region": "overseas"},
      {"name": "CNBC Top News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "region": "overseas"},
      {"name": "FT World News", "url": "https://www.ft.com/rss/world", "region": "overseas"},
      {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss", "region": "overseas"},
      {"name": "华尔街见闻", "url": "https://rsshub.app/wallstreetcn/latest", "region": "china"},
      {"name": "财新网", "url": "https://rsshub.app/caixin/latest", "region": "china"},
      {"name": "36氪", "url": "https://36kr.com/feed", "region": "china"}
    ]
  },
  "intl_trends": {
    "label": "国际趋势",
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

### 4.2 社交媒体热度源

| 源 | API/方式 | 覆盖 | 说明 |
|---|---|---|---|
| Reddit r/MachineLearning | Reddit JSON API (免费) | AI/学术 | 技术圈最活跃的 AI 讨论 |
| Reddit r/technology | Reddit JSON API (免费) | 科技消费 | 大众科技视角 |
| Reddit r/worldnews | Reddit JSON API (免费) | 国际 | 全球新闻讨论热度 |
| Reddit r/investing | Reddit JSON API (免费) | 财经 | 零售投资者情绪 |
| Hacker News | HN API (免费) | 科技/创业 | 硅谷工程师圈热度 |
| 知乎热榜 | RSSHub (免费) | 中文各领域 | 中文知识圈讨论 |
| 微博热搜 | RSSHub (免费) | 中文大众 | 中国大众关注度 |

### 4.3 热度交叉评分

```
基础分 = DeepSeek-V3 初筛评分 (1-5)
        ×
热度乘数 =
  · 仅 RSS 出现 → ×1.0
  · RSS + 1个社交源交叉 → ×1.3，标记 🔥
  · RSS + 2+个社交源交叉 → ×1.5，标记 🔥🔥
  · 仅社交出现但无 RSS → 候选补入，DeepSeek判断是否值得
        ↓
最终评分 = round(基础分 × 热度乘数)
```

交叉匹配逻辑：
- 对每条 RSS 新闻提取关键词
- 与社交热榜标题/话题做余弦相似度匹配
- 阈值 >0.6 视为交叉命中
- 命中的 → 带上热度数据传给分析层

### 源管理原则
- 每个 RSS 源每日最多取 15 条（feedparser entries[:15]）
- 失败源静默跳过，最终日志记录
- 社交 API 全免费，HTTP 请求即可
- 每月人工审查一次源质量，可增删
- RSSHub 源（机器之心、知乎热榜等）可能需要验证可用性，不可用则替换

---

## 5. AI 处理策略

### 技术栈：DeepSeek API

```
Python 脚本（Windows 定时任务）
    └── DeepSeek API（分析引擎）

Claude Code 讨论环节（/brief /discuss /deep）
    └── 当前环境模型（无需额外 API Key）
```

### 模型选择与成本

| 环节 | 模型 | 估算输入 | 估算输出 | 日成本 |
|---|---|---|---|---|
| 初筛评分 | DeepSeek-V3 | ~50K | ~5K | ~$0.01 |
| 深度分析 (8条×500字) | DeepSeek-V4 | ~20K | ~4K | ~$0.05 |
| 板块小结 (3×200字) | DeepSeek-V4 | ~10K | ~1K | ~$0.02 |
| 入门背景 (3×150字) | DeepSeek-V4 | ~5K | ~0.5K | ~$0.01 |
| 推荐长文 | DeepSeek-V4 | ~15K | ~0.5K | ~$0.02 |
| **日合计** | | **~100K** | **~11K** | **~$0.11** |
| **月合计** | | **~3M** | **~330K** | **~$3.50** |

> 注：讨论环节（Claude Code 内 `/discuss` `/deep` 等）走当前环境订阅额度，不额外计费。

### 初筛 Prompt 设计要点
- 输入：板块 + 中国/海外标签 + 标题 + 摘要 + 社交热度标签
- 评分维度：时效性、影响广度、与已选新闻的互补性、社交验证
- 去重：标题相似度 >80% 的合并，择优保留
- 社交热度作为加分项而非决定项（避免社交泡沫）
- 输出：JSON `[{id, title, summary, score, reason, region, social_signals}]`

### 深度分析 Prompt 设计要点
- 输入：单篇新闻全文（通过原文链接 fetch 补充）
- 输出 "发生+背景+影响" 三段式
- 背景部分面向入门用户，解释核心概念
- 影响分析分为短期(1-3月)和中期(3-12月)
- 语言：海外新闻用中文输出但保留关键术语英文原文
- 含社交热度讨论点（如 "Reddit 社区主要争议在..."）

### 板块小结 Prompt
- 输入：本板块今日所有入选新闻
- 输出：150-200 字，串联事件逻辑
- 格式："主题A 呈现 X→Y→Z 传导路径；主题B 正在酝酿..."
- 附带 2-3 个"后续盯住指标"

### 入门背景框
- 仅当日有新概念出现时生成
- 从新闻中提取 2-3 个核心概念，简短解释
- 可复用（同一概念一周内不重复生成）

---

## 6. 邮件投递

### Gmail SMTP 配置
```
服务器：smtp.gmail.com
端口：587 (STARTTLS)
认证：Gmail App Password（非登录密码）
```

### 邮件格式
- HTML 邮件，内联 CSS
- 使用 table 结构化卡片布局
- emoji 做视觉锚点
- 颜色方案：深灰标题栏 + 白色内容区 + ⭐星级 + 🔥社交热度
- 移动端响应式（max-width: 600px）

### 失败处理
- 发送失败重试 3 次，间隔 60s/120s/300s
- 三次失败后写错误日志到 `logs/errors.log`
- 本地存档始终生成（即使邮件发送失败）

---

## 7. 本地存档

### 目录结构
```
002-daily-news/
├── daily/
│   ├── 2026-06-23.md
│   ├── 2026-06-24.md
│   └── ...
├── logs/
│   ├── fetch.log
│   ├── analyze.log
│   └── errors.log
├── cache/
│   └── seen_urls.json    # 去重缓存，滚动7天
└── reports/              # /deep 命令生成的专题报告
    └── 2026-06-23-台海局势.md
```

### 存档格式
- Markdown，与邮件正文内容一致
- 文件名 `YYYY-MM-DD.md`
- 便于 Claude Code 内直接读取讨论

---

## 8. Claude Code 交互命令（07-discuss.py）

| 命令 | 行为 |
|---|---|
| `/brief` | 打印今日简报全文 |
| `/discuss [id]` | 加载新闻原文→调用 DeepSeek 做多角度深度分析（各方立场、争议点、社交讨论、历史脉络、可能走向） |
| `/deep [主题]` | 搜索最近 7 天存量+当日新闻中相关条目→生成 1500-2000 字专题报告→存入 `reports/` |
| `/insight [板块]` | 调取本周该板块所有新闻→生成事件关联图谱（Mermaid 格式） |
| `/trend` | 跨板块交叉分析：识别三板块之间的因果关系链 |
| `/brief [日期]` | 查看历史某日简报（如 `/brief 0622`） |

---

## 9. Windows 任务计划程序配置

```
触发器：每天 7:50
操作：启动程序 → python C:\Users\AlyssaLin\cc projects\002-daily-news\01-main.py
条件：仅当计算机使用交流电源时 → 关闭（笔记本电池也跑）
      唤醒计算机运行此任务 → 关闭（不强制唤醒）
```

手动设置一次即可，setup 脚本提供参考命令。

---

## 10. 风险与缓解

| 风险 | 缓解 |
|---|---|
| RSS 源失效 | `try/except` 跳过，日志记录；每月审查替换 |
| DeepSeek API 调用失败 | 重试 3 次 + 降级（跳过深度分析，至少发标题摘要） |
| Gmail SMTP 限制 | 每日 1 封远低于 Gmail 500 封/天限制 |
| 社交 API 不可用 | Reddit/HN 免费 API 稳定，RSSHub 若失效改直接爬取 |
| 社交泡沫放大噪音 | 热度只做乘数不决定入选，初筛评分为主 |
| 分析质量波动 | 初筛评分兜底（即使 AI 失准，筛选逻辑仍有下限） |
| token 成本超预期 | 月度硬上限 $10，接近时自动降级到 DeepSeek-V3-only |

---

## 11. 后续迭代方向（v2 考虑）

- 自动生成每日 5-8 分钟播客（TTS）
- Telegram Bot 推送作为 Gmail 备选通道
- 个性化偏好学习（你标记"不感兴趣"的领域自动降权）
- 周末特别版：本周复盘 + 下周前瞻
