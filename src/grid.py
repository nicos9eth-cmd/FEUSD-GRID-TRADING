"""Grid calculation and order management logic."""
import logging
from dataclasses import dataclass

from .config import config

log = logging.getLogger(__name__)


@dataclass
class GridState:
    """Holds the current grid state for compound interest tracking."""
    initial_capital: float = 0.0
    last_compound_capital: float = 0.0


state = GridState()


def calculate_grid_levels(num_levels: int) -> list[float]:
    """Calculate logarithmically spaced grid price levels.

    Args:
        num_levels: Number of price levels to generate

    Returns:
        List of prices from lower_bound to upper_bound
    """
    ratio = (config.upper_bound / config.lower_bound) ** (1 / (num_levels - 1))
    return [config.lower_bound * (ratio ** i) for i in range(num_levels)]


def calculate_optimal_levels(total_capital: float) -> int:
    """Calculate optimal number of grid levels based on available capital.

    Ensures each order meets minimum size requirement.

    Args:
        total_capital: Total capital in USD equivalent

    Returns:
        Number of levels (capped at max_levels)
    """
    # Each side needs capital / 2, and we want min_order_size per order
    max_possible = int(total_capital / config.min_order_size)
    optimal = min(max_possible, config.max_levels)
    return max(2, optimal)  # Minimum 2 levels (1 buy, 1 sell)


def get_profit_since_compound(current_capital: float) -> float:
    """Get profit since last compound."""
    if state.last_compound_capital == 0:
        return 0.0
    return current_capital - state.last_compound_capital


def should_compound(current_capital: float) -> bool:
    """Check if we should recalculate grid for compound interest.

    Returns True if capital increased by compound_threshold since last compound.
    """
    return get_profit_since_compound(current_capital) >= config.compound_threshold


def update_compound_state(capital: float) -> None:
    """Update the compound state after grid recalculation."""
    if state.initial_capital == 0:
        state.initial_capital = capital
    state.last_compound_capital = capital


def calculate_order_size(total_for_side: float, num_orders: int) -> float:
    """Calculate size per order for a given side.

    Args:
        total_for_side: Total capital available for this side
        num_orders: Number of orders on this side

    Returns:
        Size per order, or 0 if below minimum
    """
    if num_orders == 0:
        return 0.0

    size = total_for_side / num_orders
    if size < config.min_order_size:
        log.warning(f"Order size {size:.2f} below minimum {config.min_order_size}")
        return 0.0
    return size


def generate_grid_orders(mid_price: float, usdc_available: float,
                         feusd_available: float) -> list[dict]:
    """Generate all grid orders based on current balances.

    Args:
        mid_price: Current mid price
        usdc_available: USDC available (already adjusted for utilization)
        feusd_available: FEUSD available (100% utilization)

    Returns:
        List of order dicts: {is_buy, size, price}
    """
    total_capital = usdc_available + (feusd_available * mid_price)

    # Check for compound interest
    if should_compound(total_capital):
        log.info(f"Compounding! Capital: {state.last_compound_capital:.2f} -> {total_capital:.2f}")

    update_compound_state(total_capital)

    # Calculate optimal number of levels
    num_levels = calculate_optimal_levels(total_capital)
    grid_prices = calculate_grid_levels(num_levels)

    # Split grid by mid price
    buy_prices = [p for p in grid_prices if p < mid_price]
    sell_prices = [p for p in grid_prices if p > mid_price]

    orders = []

    # Buy orders (using USDC)
    if buy_prices:
        # Convert USDC to FEUSD quantity at average buy price
        avg_buy_price = sum(buy_prices) / len(buy_prices)
        total_feusd_to_buy = usdc_available / avg_buy_price
        buy_size = calculate_order_size(total_feusd_to_buy, len(buy_prices))

        if buy_size > 0:
            for price in buy_prices:
                orders.append({"is_buy": True, "size": buy_size, "price": price})

    # Sell orders (using FEUSD)
    if sell_prices:
        sell_size = calculate_order_size(feusd_available, len(sell_prices))

        if sell_size > 0:
            for price in sell_prices:
                orders.append({"is_buy": False, "size": sell_size, "price": price})

    log.info(f"Grid: {len(buy_prices)} buys, {len(sell_prices)} sells, "
             f"capital: ${total_capital:.2f}, levels: {num_levels}")

    return orders


def generate_flip_order(filled_order: dict) -> dict:
    """Generate the opposite order after a fill.

    Args:
        filled_order: The order that was filled

    Returns:
        Order dict for the flip order
    """
    was_buy = filled_order["side"] == "B"
    return {
        "is_buy": not was_buy,
        "size": float(filled_order["sz"]),
        "price": float(filled_order["price"])
    }
