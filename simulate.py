#!/usr/bin/env python3
"""Simulate grid scenarios without API calls."""

# === CONFIG (same as src/config.py) ===
LOWER = 0.98
UPPER = 1.20
MAX_ORDERS = 100
MIN_ORDER = 11
USDC_RESERVE = 0.10


def calc_grid(capital: float) -> tuple[list[float], float]:
    """Calculate grid prices and order size."""
    num = min(MAX_ORDERS, int(capital / MIN_ORDER))
    if num < 2:
        return [], 0.0

    ratio = (UPPER / LOWER) ** (1 / (num - 1))
    prices = [round(LOWER * (ratio ** i), 4) for i in range(num)]
    size = round(capital / num / ((LOWER + UPPER) / 2), 2)

    return prices, size


def simulate(name: str, usdc: float, feusd: float, mid: float):
    """Run a simulation scenario."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name}")
    print(f"{'='*60}")

    usdc_avail = usdc * (1 - USDC_RESERVE)
    capital = usdc_avail + (feusd * mid)

    print(f"\nInput:")
    print(f"  USDC: ${usdc:.2f} (available: ${usdc_avail:.2f})")
    print(f"  FEUSD: {feusd:.2f}")
    print(f"  Mid price: ${mid:.4f}")
    print(f"  Total capital: ${capital:.2f}")

    prices, size = calc_grid(capital)

    if not prices:
        print(f"\n❌ INSUFFICIENT CAPITAL")
        print(f"   Need at least ${MIN_ORDER * 2} (got ${capital:.2f})")
        return

    buys = [p for p in prices if p < mid]
    sells = [p for p in prices if p >= mid]
    spread = ((prices[1] / prices[0]) - 1) * 100 if len(prices) > 1 else 0

    print(f"\nGrid:")
    print(f"  Levels: {len(prices)}")
    print(f"  Spread: {spread:.3f}%")
    print(f"  Order size: {size:.2f} FEUSD (~${size * mid:.2f})")

    print(f"\nOrders:")
    print(f"  Buy orders:  {len(buys)} ({prices[0]:.4f} - {buys[-1]:.4f})" if buys else "  Buy orders:  0")
    print(f"  Sell orders: {len(sells)} ({sells[0]:.4f} - {prices[-1]:.4f})" if sells else "  Sell orders: 0")

    # Profit per round-trip (0.22% spread - 0.08% fees)
    profit_per_rt = size * mid * (spread / 100 - 0.0008)
    print(f"\nEstimated profit/round-trip: ${profit_per_rt:.4f}")

    print(f"\n✅ READY" if len(prices) >= 10 else f"\n⚠️ LOW COVERAGE ({len(prices)} orders)")


def main():
    print("\n" + "#" * 60)
    print("# FEUSD GRID TRADING SIMULATOR")
    print("#" * 60)

    # Test scenarios
    simulate("1500 FEUSD only @ 1.02", usdc=0, feusd=1500, mid=1.02)
    simulate("1500 USDC only @ 0.99", usdc=1500, feusd=0, mid=0.99)
    simulate("100 FEUSD + 10 USDC", usdc=10, feusd=100, mid=1.00)
    simulate("Balanced $2000 @ 1.00", usdc=1000, feusd=1000, mid=1.00)
    simulate("Minimum viable $1100", usdc=550, feusd=550, mid=1.00)
    simulate("Low capital $500", usdc=250, feusd=250, mid=1.00)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
