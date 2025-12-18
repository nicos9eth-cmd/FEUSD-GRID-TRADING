#!/usr/bin/env python3
"""Standalone simulation script to test grid logic without dependencies."""

# === CONFIG ===
LOWER_BOUND = 0.98
UPPER_BOUND = 1.20
MAX_LEVELS = 100
USDC_UTILIZATION = 0.9
MIN_ORDER_SIZE = 11


def calculate_grid_levels(num_levels: int) -> list[float]:
    """Calculate logarithmically spaced grid price levels."""
    ratio = (UPPER_BOUND / LOWER_BOUND) ** (1 / (num_levels - 1))
    return [LOWER_BOUND * (ratio ** i) for i in range(num_levels)]


def calculate_optimal_levels(total_capital: float) -> int:
    """Calculate optimal number of grid levels based on available capital."""
    max_possible = int(total_capital / MIN_ORDER_SIZE)
    optimal = min(max_possible, MAX_LEVELS)
    return max(2, optimal)


def generate_grid_orders(mid_price: float, usdc_available: float,
                         feusd_available: float) -> list[dict]:
    """Generate all grid orders based on current balances."""
    total_capital = usdc_available + (feusd_available * mid_price)

    num_levels = calculate_optimal_levels(total_capital)
    grid_prices = calculate_grid_levels(num_levels)

    buy_prices = [p for p in grid_prices if p < mid_price]
    sell_prices = [p for p in grid_prices if p > mid_price]

    orders = []

    # Buy orders (using USDC)
    if buy_prices:
        avg_buy_price = sum(buy_prices) / len(buy_prices)
        total_feusd_to_buy = usdc_available / avg_buy_price
        buy_size = total_feusd_to_buy / len(buy_prices) if len(buy_prices) > 0 else 0

        if buy_size >= MIN_ORDER_SIZE:
            for price in buy_prices:
                orders.append({"is_buy": True, "size": buy_size, "price": price})

    # Sell orders (using FEUSD)
    if sell_prices:
        sell_size = feusd_available / len(sell_prices) if len(sell_prices) > 0 else 0

        if sell_size >= MIN_ORDER_SIZE:
            for price in sell_prices:
                orders.append({"is_buy": False, "size": sell_size, "price": price})

    return orders


def simulate_scenario(name: str, usdc: float, feusd: float, mid_price: float):
    """Simulate a trading scenario and display results."""
    print("\n" + "=" * 60)
    print(f"SCENARIO: {name}")
    print("=" * 60)

    usdc_available = usdc * USDC_UTILIZATION
    feusd_available = feusd

    total_capital = usdc_available + (feusd_available * mid_price)

    print(f"\nINPUT:")
    print(f"  USDC balance:     ${usdc:.2f}")
    print(f"  USDC available:   ${usdc_available:.2f} (90%)")
    print(f"  FEUSD balance:    {feusd:.2f}")
    print(f"  Mid price:        ${mid_price:.4f}")
    print(f"  Total capital:    ${total_capital:.2f}")

    num_levels = calculate_optimal_levels(total_capital)
    grid_prices = calculate_grid_levels(num_levels)

    print(f"\nGRID ANALYSIS:")
    print(f"  Optimal levels:   {num_levels}")
    print(f"  Price range:      ${grid_prices[0]:.4f} - ${grid_prices[-1]:.4f}")

    if num_levels > 1:
        spread_pct = ((grid_prices[1] / grid_prices[0]) - 1) * 100
        print(f"  Spread per level: {spread_pct:.3f}%")

    orders = generate_grid_orders(mid_price, usdc_available, feusd_available)

    buy_orders = [o for o in orders if o["is_buy"]]
    sell_orders = [o for o in orders if not o["is_buy"]]

    print(f"\nORDERS:")
    print(f"  Buy orders:       {len(buy_orders)}")
    print(f"  Sell orders:      {len(sell_orders)}")
    print(f"  Total orders:     {len(orders)}")

    if buy_orders:
        buy_size = buy_orders[0]["size"]
        print(f"\n  BUY SIDE:")
        print(f"    Size per order: {buy_size:.2f} FEUSD")
        print(f"    Price range:    ${buy_orders[-1]['price']:.4f} - ${buy_orders[0]['price']:.4f}")
        print(f"    Total USDC:     ~${usdc_available:.2f}")

    if sell_orders:
        sell_size = sell_orders[0]["size"]
        print(f"\n  SELL SIDE:")
        print(f"    Size per order: {sell_size:.2f} FEUSD")
        print(f"    Price range:    ${sell_orders[0]['price']:.4f} - ${sell_orders[-1]['price']:.4f}")
        print(f"    Total FEUSD:    {feusd_available:.2f}")

    print(f"\nSTATUS:")
    if not orders:
        print("  ⚠️  NO ORDERS - Capital insufficient!")
        print(f"     Need at least ${MIN_ORDER_SIZE * 2:.0f} for minimum grid")
    elif len(buy_orders) == 0:
        print("  ⚠️  NO BUY ORDERS - No USDC available or below minimum")
    elif len(sell_orders) == 0:
        print("  ⚠️  NO SELL ORDERS - No FEUSD available or below minimum")
    elif len(orders) < 10:
        print(f"  ⚠️  LOW COVERAGE - Only {len(orders)} orders")
    else:
        print("  ✓ Grid ready to deploy")

    return orders


def main():
    print("\n" + "#" * 60)
    print("# FEUSD GRID TRADING - SCENARIO SIMULATOR")
    print("#" * 60)

    # Scenario 1: 1500 FEUSD only at 1.02
    simulate_scenario(
        "1500 FEUSD only @ 1.02",
        usdc=0,
        feusd=1500,
        mid_price=1.02
    )

    # Scenario 2: USDC only at 0.99
    simulate_scenario(
        "1500 USDC only @ 0.99",
        usdc=1500,
        feusd=0,
        mid_price=0.99
    )

    # Scenario 3: 100 FEUSD + 10 USDC (insufficient)
    simulate_scenario(
        "100 FEUSD + 10 USDC (low capital)",
        usdc=10,
        feusd=100,
        mid_price=1.00
    )

    # Scenario 4: Balanced portfolio
    simulate_scenario(
        "1000 USDC + 1000 FEUSD @ 1.00 (balanced)",
        usdc=1000,
        feusd=1000,
        mid_price=1.00
    )

    # Scenario 5: Minimum viable
    simulate_scenario(
        "Minimum viable (~$1100)",
        usdc=550,
        feusd=550,
        mid_price=1.00
    )

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
