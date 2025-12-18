"""Hyperliquid exchange wrapper with batch operations."""
import logging
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

from .config import config

log = logging.getLogger(__name__)


class HyperliquidClient:
    """Wrapper for Hyperliquid API with batch order support."""

    def __init__(self):
        self.exchange = Exchange(
            config.address,
            config.private_key,
            base_url=constants.MAINNET_API_URL
        )
        self.info = Info(base_url=constants.MAINNET_API_URL)

    def get_balances(self) -> tuple[float, float]:
        """Get USDC and FEUSD balances.

        Returns:
            Tuple of (usdc_available, feusd_balance)
            USDC is multiplied by utilization rate (90%)
        """
        state = self.info.user_state(config.address)["balances"]

        def get_balance(coin: str) -> float:
            return float(next((b["sz"] for b in state if b["coin"] == coin), 0))

        usdc = get_balance("USDC") * config.usdc_utilization
        feusd = get_balance(config.asset)
        return usdc, feusd

    def get_mid_price(self) -> float:
        """Get current mid price for FEUSD."""
        return float(self.info.all_mids().get(config.asset, 1))

    def get_open_orders(self) -> list:
        """Get all open orders for FEUSD."""
        return [o for o in self.info.open_orders(config.address)
                if o["coin"] == config.asset]

    def cancel_all_orders(self) -> None:
        """Cancel all open FEUSD orders."""
        orders = self.get_open_orders()
        if not orders:
            return

        # Batch cancel
        cancels = [{"coin": config.asset, "oid": o["oid"]} for o in orders]
        if cancels:
            self.exchange.bulk_cancel(cancels)
            log.info(f"Cancelled {len(cancels)} orders")

    def place_order(self, is_buy: bool, size: float, price: float,
                    post_only: bool = True) -> None:
        """Place a single order."""
        self.exchange.order(
            config.asset,
            is_buy,
            size,
            price,
            {"limit": {"tif": "Gtc", "postOnly": post_only}}
        )

    def place_orders_batch(self, orders: list[dict], post_only: bool = True) -> None:
        """Place multiple orders in a single batch call.

        Args:
            orders: List of dicts with keys: is_buy, size, price
            post_only: If True, orders are ALO (Add Liquidity Only)
        """
        if not orders:
            return

        order_requests = []
        for o in orders:
            order_requests.append({
                "coin": config.asset,
                "is_buy": o["is_buy"],
                "sz": o["size"],
                "limit_px": o["price"],
                "order_type": {"limit": {"tif": "Gtc", "postOnly": post_only}},
                "reduce_only": False
            })

        self.exchange.bulk_orders(order_requests)
        log.info(f"Placed {len(orders)} orders (postOnly={post_only})")

    def subscribe_user_events(self, callback) -> None:
        """Subscribe to user order events via WebSocket."""
        self.info.subscribe(
            {"type": "userEvents", "user": config.address},
            callback
        )
        self.info.subscribe(
            {"type": "orderUpdates", "user": config.address},
            callback
        )


client = HyperliquidClient()
