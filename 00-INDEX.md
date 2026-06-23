# 002-daily-news

## 概述
每日 8 点自动推送全球新闻简报（AI/科技、财经、国际趋势三板块），RSS + 社交媒体双通道抓取，DeepSeek AI 分析，Gmail 发送 + 本地 Markdown 存档，支持 Claude Code 内深入讨论。

## 文件索引

| 编号 | 文件名 | 用途 | 说明 |
|------|--------|------|------|
| 00 | 00-INDEX.md | 项目索引 | 本文件 |
| 01 | 01-main.py | 主入口 | 串联抓取→分析→发送全流程，被 Windows 计划任务触发 |
| 02 | 02-config.py | 配置模块 | API Key、邮箱、RSS 源路径、阈值等所有配置项 |
| 03 | 03-fetch.py | 双通道抓取 | RSS 22 源 + Reddit/HN/知乎/微博社交热度，交叉匹配去重 |
| 04 | 04-analyze.py | AI 分析 | DeepSeek-V3 初筛评分 + DeepSeek-V4 深度分析 + 板块小结 + 推荐 |
| 05 | 05-deliver.py | 发送 & 存档 | Gmail SMTP HTML 邮件 + 本地 daily/YYYY-MM-DD.md |
| 06 | 06-sources.json | RSS 源清单 | 22 个 RSS 源，分三板块，海外/中国标签 |
| 07 | 07-discuss.py | 交互命令库 | Claude Code 内 `/brief` `/discuss` `/deep` 等命令的定义和查找逻辑 |
| 08 | 08-report.py | 专题报告生成 | `/deep` 命令的核心引擎，搜索 7 天存档 → DeepSeek 生成 1500-2000 字报告 |
| — | .env.example | 配置模板 | DeepSeek API Key + Gmail SMTP 凭据模板 |
| — | requirements.txt | Python 依赖 | feedparser, httpx, python-dotenv |
| — | setup.ps1 | 一键安装脚本 | 安装依赖 + 创建 Windows 计划任务 |
| — | templates/email.html | 邮件模板 | HTML 邮件样式模板 |

## 目录结构

```
002-daily-news/
├── 01-main.py            ← 入口
├── 02-config.py           ← 配置
├── 03-fetch.py            ← 抓取层
├── 04-analyze.py          ← AI 分析层
├── 05-deliver.py          ← 发送层
├── 06-sources.json        ← RSS 源
├── 07-discuss.py          ← 讨论命令
├── 08-report.py           ← 专题报告
├── .env                   ← 你的密钥（不提交）
├── .env.example           ← 密钥模板
├── requirements.txt       ← pip 依赖
├── setup.ps1              ← 一键安装
├── templates/email.html   ← 邮件样式
├── daily/                 ← 每日简报存档
│   └── YYYY-MM-DD.md
├── logs/                  ← 运行日志
├── cache/                 ← 去重缓存
├── reports/               ← /deep 命令生成的专题报告
└── docs/
    ├── design.md           ← 设计文档
    └── superpowers/plans/  ← 实现计划
```

## 使用方式

### 首次配置
1. 复制 `.env.example` 为 `.env`，填入：
   - `DEEPSEEK_API_KEY`：从 https://platform.deepseek.com 获取
   - `GMAIL_USERNAME`：你的 Gmail 地址
   - `GMAIL_APP_PASSWORD`：从 https://myaccount.google.com/apppasswords 获取
2. 以管理员身份运行 PowerShell，执行 `.\setup.ps1`
3. 脚本自动安装依赖 + 创建每日 7:50 的 Windows 计划任务

### 手动运行
```bash
cd "C:\Users\AlyssaLin\cc projects\002-daily-news"
python 01-main.py
```

### Claude Code 讨论
收到邮件后，打开 Claude Code 到此目录，使用以下命令：
- `/brief` — 查看今日简报
- `/brief 0623` — 查看历史简报
- `/discuss ai-01` — 深入分析某条新闻
- `/deep 台海` — 生成专题深度报告
- `/insight 财经` — 查看本周板块事件关联图
- `/trend` — 跨板块交叉趋势分析

## 依赖关系
```
01-main.py
  ├── 02-config.py          (读取配置 .env)
  ├── 03-fetch.py           (RSS + 社交抓取，使用 06-sources.json)
  ├── 04-analyze.py         (DeepSeek API 分析)
  └── 05-deliver.py         (Gmail + 本地存档，使用 templates/email.html)

07-discuss.py → daily/*.md  (读取存档提供交互)
08-report.py  → daily/*.md  (搜索存档 → DeepSeek → 写入 reports/)
```

## 外部依赖
- Python 3.10+
- feedparser, httpx, python-dotenv
- DeepSeek API Key
- Gmail App Password (SMTP)
- Windows Task Scheduler (或手动运行)
