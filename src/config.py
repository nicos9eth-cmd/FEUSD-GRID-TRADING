"""Configuration management for FEUSD Grid Trading Bot."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    # API credentials
    address: str = os.getenv("ADDRESS", "")
    private_key: str = os.getenv("PRIVATE_KEY", "")

    # Grid parameters
    asset: str = "FEUSD"
    lower_bound: float = float(os.getenv("LOWER_BOUND", "0.98"))
    upper_bound: float = float(os.getenv("UPPER_BOUND", "1.20"))
    max_levels: int = int(os.getenv("MAX_LEVELS", "100"))
    usdc_utilization: float = float(os.getenv("USDC_UTILIZATION", "0.9"))
    min_order_size: float = float(os.getenv("MIN_ORDER_SIZE", "11"))
    refresh_seconds: int = int(os.getenv("REFRESH_SECONDS", "600"))
    compound_threshold: float = float(os.getenv("COMPOUND_THRESHOLD", "1.0"))

    def __post_init__(self):
        if not self.address or not self.private_key:
            raise ValueError("ADDRESS and PRIVATE_KEY must be set in .env")
        if self.lower_bound >= self.upper_bound:
            raise ValueError("LOWER_BOUND must be less than UPPER_BOUND")
        if self.usdc_utilization <= 0 or self.usdc_utilization > 1:
            raise ValueError("USDC_UTILIZATION must be between 0 and 1")


config = Config()
