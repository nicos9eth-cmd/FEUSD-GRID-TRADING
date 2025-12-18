# FEUSD Grid Trading Bot

Open-source grid trading bot for the **FEUSD/USDC** pair on [Hyperliquid](https://app.hyperliquid.xyz/join/NICOS9).<-4% discount fees

## ⚠️ IMPORTANT WARNINGS

> **NO STOP LOSS** - This bot does NOT implement any stop loss mechanism.
>
> **NO DEPEG PROTECTION** - This bot does NOT protect against FEUSD depegging.
>
> **USE AT YOUR OWN RISK** - While FEUSD is a stablecoin with relatively low volatility, stablecoins can and do depeg. You could lose your entire capital.

### Protocol Limits

- **Lower bound**: 0.98 (liquidation threshold)
- **Upper bound**: 1.20 (forced buyback with low liquidity)

## How It Works

The bot implements a classic **grid trading strategy**:

1. Places buy orders below current price, sell orders above
2. Uses **logarithmic spacing** for optimal distribution
3. When an order fills, places the **opposite order at the same price**
4. Automatically **compounds profits** by recalculating order sizes

### Capital Allocation

- **FEUSD**: 100% utilized for sell orders
- **USDC**: 90% utilized for buy orders (10% reserve)

### Order Types

- **Initial placement**: ALO (Add Liquidity Only) to avoid market orders
- **After fill**: GTC to ensure execution on volatile moves

## Requirements

- Python 3.10+
- Hyperliquid account with API access
- Minimum recommended capital: **$1,100** (for 100 grid levels)

## Installation

```bash
git clone https://github.com/yourusername/FEUSD-GRID-TRADING.git
cd FEUSD-GRID-TRADING
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:

```env
ADDRESS=0xYourWalletAddress
PRIVATE_KEY=0xYourPrivateKey
```

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LOWER_BOUND` | 0.98 | Grid lower price limit |
| `UPPER_BOUND` | 1.20 | Grid upper price limit |
| `MAX_LEVELS` | 100 | Maximum grid levels |
| `USDC_UTILIZATION` | 0.9 | USDC usage (90%) |
| `MIN_ORDER_SIZE` | 11 | Minimum USD per order |
| `REFRESH_SECONDS` | 600 | Grid refresh interval |
| `COMPOUND_THRESHOLD` | 1.0 | Profit threshold to compound ($) |

## Usage

```bash
python run.py
```

## Capital & Grid Levels

The bot **automatically adjusts** the number of grid levels based on your capital:

| Capital | Grid Levels | Order Size | Spread |
|---------|-------------|------------|--------|
| $1,100 | 100 | ~$11 | ~0.22% |
| $2,200 | 100 | ~$22 | ~0.22% |
| $550 | 50 | ~$11 | ~0.44% |

**Formula**: `levels = min(100, capital / MIN_ORDER_SIZE)`

## Architecture

```
FEUSD-GRID-TRADING/
├── run.py              # Entry point
├── src/
│   ├── config.py       # Configuration management
│   ├── exchange.py     # Hyperliquid API wrapper
│   ├── grid.py         # Grid calculation logic
│   └── bot.py          # Main bot orchestration
├── .env.example        # Configuration template
└── requirements.txt    # Dependencies
```

## License

MIT - Use at your own risk.

## Disclaimer

This software is provided "as is", without warranty of any kind. The authors are not responsible for any financial losses incurred through the use of this bot. Always test with small amounts first.
