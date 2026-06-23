"""Configuration loader for 002-daily-news."""
import os
from dataclasses import dataclass, field
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
    retry_delays: list = field(default_factory=lambda: [60, 120, 300])


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
