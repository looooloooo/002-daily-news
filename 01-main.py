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
    """Load a Python module from a numbered filename."""
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
    logger.info(f"Log: {log_file}")

    # Validate config
    issues = cfg_mod.validate_config(cfg)
    if issues:
        for issue in issues:
            logger.error(f"Config: {issue}")
        logger.error("Fix .env and retry")
        sys.exit(1)
    logger.info("Config OK")

    # Load sources
    try:
        sources_data = json.loads(Path(cfg.sources_file).read_text(encoding="utf-8"))
        total_sources = sum(len(v["sources"]) for v in sources_data.values())
        logger.info(f"Sources: {total_sources} RSS feeds")
    except Exception as e:
        logger.error(f"Sources load failed: {e}")
        sys.exit(1)

    # Step 1: Fetch
    logger.info("Step 1/3: Fetching...")
    fetch = _load_module("fetch", "03-fetch.py")
    try:
        grouped = fetch.fetch_all(sources_data, cfg)
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        sys.exit(1)

    total = sum(len(v) for v in grouped.values())
    if total == 0:
        logger.warning("No articles fetched — check network or RSS sources")
        sys.exit(0)
    logger.info(f"Fetched: {total} articles")

    # Step 2: Analyze
    logger.info("Step 2/3: Analyzing with DeepSeek...")
    analyze = _load_module("analyze", "04-analyze.py")
    try:
        analysis = analyze.analyze_news(grouped, cfg)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    screened_total = sum(len(v) for v in analysis.screened.values())
    logger.info(f"Screened: {screened_total} articles, {len(analysis.deep_analyses)} deep analyses")
    logger.info(f"Est. API cost: ${analysis.total_cost_estimate:.3f}")

    # Step 3: Deliver
    logger.info("Step 3/3: Delivering...")
    deliver = _load_module("deliver", "05-deliver.py")
    try:
        email_sent, local_path = deliver.deliver(analysis, cfg)
    except Exception as e:
        logger.error(f"Delivery failed: {e}")
        sys.exit(1)

    if email_sent:
        logger.info(f"Email sent → {cfg.recipient_email}")
    else:
        logger.warning("Email NOT sent — check Gmail config")
    logger.info(f"Local: {local_path}")

    logger.info("=" * 60)
    logger.info("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
