"""FEUSD Grid Trading Bot - Simple & Reliable."""
import asyncio
import logging

from . import config
from . import exchange as ex

log = logging.getLogger(__name__)


class GridBot:
    def __init__(self):
        self.last_capital = 0.0
        self.grid_prices = []
        self.order_size = 0.0
        self.running = False

    # =========== GRID CALCULATION ===========

    def calc_grid(self, capital: float) -> tuple[list[float], float]:
        """Calculate grid prices and order size based on capital.

        Returns: (grid_prices, order_size_in_feusd)
        """
        # Number of orders based on capital (min $11 per order)
        num = min(config.MAX_ORDERS, int(capital / config.MIN_ORDER))
        if num < 2:
            return [], 0.0

        # Logarithmic grid from LOWER to UPPER
        ratio = (config.UPPER / config.LOWER) ** (1 / (num - 1))
        prices = [round(config.LOWER * (ratio ** i), 4) for i in range(num)]

        # Order size: total capital / num orders / ~mid price
        mid_approx = (config.LOWER + config.UPPER) / 2
        size = round(capital / num / mid_approx, 2)

        return prices, size

    # =========== ORDER MANAGEMENT ===========

    def sync_grid(self, mid: float, post_only: bool = True) -> None:
        """Sync orders with grid - only place missing orders."""
        existing = ex.get_open_orders()
        existing_prices = set(existing.keys())
        grid_set = set(self.grid_prices)

        # Cancel orders not in grid
        to_cancel = [o["oid"] for p, o in existing.items() if p not in grid_set]
        for oid in to_cancel:
            ex.cancel(oid)
            log.info(f"Cancelled stale order {oid}")

        # Place missing orders
        to_place = []
        for price in self.grid_prices:
            if price in existing_prices:
                continue  # Already have this order
            is_buy = price < mid
            to_place.append({"is_buy": is_buy, "size": self.order_size, "price": price})

        if to_place:
            ex.place_batch(to_place, post_only=post_only)
            buys = sum(1 for o in to_place if o["is_buy"])
            sells = len(to_place) - buys
            log.info(f"Placed {buys} buys + {sells} sells (size: {self.order_size:.2f})")

    # =========== EVENT HANDLERS ===========

    async def on_fill(self, data: dict) -> None:
        """Handle order fill - place opposite order at same price."""
        price = float(data["price"])
        size = float(data["sz"])
        was_buy = data["side"] == "B"

        # Place opposite order (GTC, not post-only to ensure fill)
        ex.place(is_buy=not was_buy, size=size, price=price, post_only=False)
        side = "SELL" if was_buy else "BUY"
        log.info(f"Fill! Placed {side} {size:.2f} @ {price:.4f}")

    async def ws_callback(self, msg: dict) -> None:
        """WebSocket callback for order updates."""
        try:
            for update in msg.get("data", {}).get("updates", []):
                if update.get("status") == "filled":
                    await self.on_fill(update)
        except Exception as e:
            log.error(f"WS error: {e}")

    # =========== MAIN LOGIC ===========

    def init_grid(self) -> None:
        """Initialize grid on startup."""
        mid = ex.get_mid()
        usdc, feusd = ex.get_balances()
        capital = usdc + (feusd * mid)

        log.info(f"Capital: ${capital:.2f} | Mid: {mid:.4f}")

        self.grid_prices, self.order_size = self.calc_grid(capital)
        self.last_capital = capital

        if not self.grid_prices:
            log.error(f"Need at least ${config.MIN_ORDER * 2} to start")
            return

        log.info(f"Grid: {len(self.grid_prices)} levels, {self.order_size:.2f} FEUSD/order")
        self.sync_grid(mid, post_only=True)

    def check_compound(self) -> None:
        """Check if we should compound profits."""
        mid = ex.get_mid()
        usdc, feusd = ex.get_balances()
        capital = usdc + (feusd * mid)
        profit = capital - self.last_capital

        log.info(f"Check: ${capital:.2f} | Profit: ${profit:.2f}")

        if profit < config.COMPOUND_AT:
            log.info(f"Need ${config.COMPOUND_AT - profit:.2f} more to compound")
            return

        # Recalculate grid with new capital
        log.info(f"Compounding ${profit:.2f}!")
        self.grid_prices, self.order_size = self.calc_grid(capital)
        self.last_capital = capital

        # Cancel all and replace with new sizes
        ex.cancel_all()
        self.sync_grid(mid, post_only=True)

    async def run(self) -> None:
        """Main bot loop."""
        log.info("=" * 50)
        log.info("FEUSD Grid Bot Starting")
        log.info(f"Range: {config.LOWER} - {config.UPPER}")
        log.info(f"Max orders: {config.MAX_ORDERS} | Min: ${config.MIN_ORDER}")
        log.info(f"Compound at: ${config.COMPOUND_AT}")
        log.info("=" * 50)

        self.running = True
        ex.subscribe(self.ws_callback)
        self.init_grid()

        while self.running:
            await asyncio.sleep(config.REFRESH_SEC)
            self.check_compound()

    def stop(self) -> None:
        """Stop the bot."""
        log.info("Stopping...")
        self.running = False


bot = GridBot()
