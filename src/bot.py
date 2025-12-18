"""Main bot orchestration for FEUSD Grid Trading."""
import asyncio
import logging

from .config import config
from .exchange import client
from .grid import generate_grid_orders, generate_flip_order

log = logging.getLogger(__name__)


class GridBot:
    """FEUSD Grid Trading Bot."""

    def __init__(self):
        self.running = False

    def place_initial_grid(self) -> None:
        """Place the initial grid with ALO (post-only) orders."""
        log.info("Placing initial grid (ALO orders)...")

        # Cancel any existing orders
        client.cancel_all_orders()

        # Get current state
        mid_price = client.get_mid_price()
        usdc, feusd = client.get_balances()

        log.info(f"Mid: {mid_price:.4f} | USDC: {usdc:.2f} | FEUSD: {feusd:.2f}")

        # Generate and place orders
        orders = generate_grid_orders(mid_price, usdc, feusd)

        if orders:
            client.place_orders_batch(orders, post_only=True)
        else:
            log.warning("No orders to place - check capital requirements")

    def refresh_grid(self) -> None:
        """Refresh the grid - check for compound interest opportunity."""
        log.info("Refreshing grid...")

        mid_price = client.get_mid_price()
        usdc, feusd = client.get_balances()
        total = usdc + (feusd * mid_price)

        log.info(f"Capital: ${total:.2f} | Mid: {mid_price:.4f}")

        # Cancel and replace all orders to apply compound interest
        client.cancel_all_orders()
        orders = generate_grid_orders(mid_price, usdc, feusd)

        if orders:
            client.place_orders_batch(orders, post_only=True)

    async def handle_fill(self, filled_order: dict) -> None:
        """Handle a filled order by placing the opposite order.

        Uses GTC (not post-only) to ensure execution on volatile moves.
        """
        flip = generate_flip_order(filled_order)
        side = "BUY" if flip["is_buy"] else "SELL"
        log.info(f"Fill detected! Placing {side} @ {flip['price']:.4f}")

        # GTC order (not post-only) to ensure fill on volatile moves
        client.place_order(
            is_buy=flip["is_buy"],
            size=flip["size"],
            price=flip["price"],
            post_only=False
        )

    async def ws_callback(self, msg: dict) -> None:
        """WebSocket callback for order updates."""
        try:
            updates = msg.get("data", {}).get("updates", [])
            for update in updates:
                if update.get("status") == "filled":
                    await self.handle_fill(update)
        except Exception as e:
            log.error(f"WebSocket error: {e}")

    async def run(self) -> None:
        """Main bot loop."""
        log.info("=" * 50)
        log.info("FEUSD Grid Trading Bot Starting")
        log.info(f"Grid: {config.lower_bound} - {config.upper_bound}")
        log.info(f"Max levels: {config.max_levels} | Min order: ${config.min_order_size}")
        log.info(f"USDC utilization: {config.usdc_utilization * 100:.0f}%")
        log.info(f"Compound threshold: ${config.compound_threshold}")
        log.info("=" * 50)

        self.running = True

        # Subscribe to order events
        client.subscribe_user_events(self.ws_callback)

        # Place initial grid
        self.place_initial_grid()

        # Main loop
        while self.running:
            await asyncio.sleep(config.refresh_seconds)
            self.refresh_grid()

    def stop(self) -> None:
        """Stop the bot."""
        log.info("Stopping bot...")
        self.running = False
        client.cancel_all_orders()


bot = GridBot()
