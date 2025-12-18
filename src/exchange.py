"""Hyperliquid API wrapper."""
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

from . import config

# Initialize API clients
exchange = Exchange(config.ADDRESS, config.PRIVATE_KEY, base_url=constants.MAINNET_API_URL)
info = Info(base_url=constants.MAINNET_API_URL)


def get_mid() -> float:
    """Get current FEUSD mid price."""
    return float(info.all_mids().get(config.ASSET, 1.0))


def get_balances() -> tuple[float, float]:
    """Get (usdc_available, feusd) balances. USDC has reserve applied."""
    state = info.user_state(config.ADDRESS)["balances"]
    usdc = feusd = 0.0
    for b in state:
        if b["coin"] == "USDC":
            usdc = float(b["sz"]) * (1 - config.USDC_RESERVE)
        elif b["coin"] == config.ASSET:
            feusd = float(b["sz"])
    return usdc, feusd


def get_open_orders() -> dict[float, dict]:
    """Get open orders as {price: {oid, side, size}}."""
    orders = {}
    for o in info.open_orders(config.ADDRESS):
        if o["coin"] == config.ASSET:
            orders[float(o["limitPx"])] = {
                "oid": o["oid"],
                "side": o["side"],
                "size": float(o["sz"])
            }
    return orders


def cancel(oid: int) -> None:
    """Cancel a single order."""
    exchange.cancel(config.ASSET, oid)


def cancel_all() -> None:
    """Cancel all FEUSD orders."""
    orders = get_open_orders()
    if orders:
        cancels = [{"coin": config.ASSET, "oid": o["oid"]} for o in orders.values()]
        exchange.bulk_cancel(cancels)


def place(is_buy: bool, size: float, price: float, post_only: bool = True) -> None:
    """Place a single order."""
    exchange.order(
        config.ASSET,
        is_buy,
        size,
        price,
        {"limit": {"tif": "Gtc", "postOnly": post_only}}
    )


def place_batch(orders: list[dict], post_only: bool = True) -> None:
    """Place multiple orders. Orders: [{is_buy, size, price}, ...]"""
    if not orders:
        return
    reqs = [{
        "coin": config.ASSET,
        "is_buy": o["is_buy"],
        "sz": o["size"],
        "limit_px": o["price"],
        "order_type": {"limit": {"tif": "Gtc", "postOnly": post_only}},
        "reduce_only": False
    } for o in orders]
    exchange.bulk_orders(reqs)


def subscribe(callback) -> None:
    """Subscribe to order fill events."""
    info.subscribe({"type": "userEvents", "user": config.ADDRESS}, callback)
    info.subscribe({"type": "orderUpdates", "user": config.ADDRESS}, callback)
