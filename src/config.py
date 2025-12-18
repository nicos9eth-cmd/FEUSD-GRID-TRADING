"""Configuration for FEUSD Grid Trading Bot."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Credentials
ADDRESS = os.getenv("ADDRESS", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

# Grid Parameters
ASSET = "FEUSD"
LOWER = 0.98          # Protocol liquidation limit
UPPER = 1.20          # Protocol buyback limit
MAX_ORDERS = 100      # Max grid levels
MIN_ORDER = 11        # Hyperliquid minimum ($10 + margin)
USDC_RESERVE = 0.10   # Keep 10% USDC as reserve
COMPOUND_AT = 1.0     # Compound when profit >= $1
REFRESH_SEC = 300     # Check every 5 minutes

# Validation
if not ADDRESS or not PRIVATE_KEY:
    raise ValueError("Set ADDRESS and PRIVATE_KEY in .env")
