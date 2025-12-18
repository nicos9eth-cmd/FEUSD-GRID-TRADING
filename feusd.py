import asyncio
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

# === CONFIG ===
ADDRESS = "0xTonAdresse"
PRIVATE_KEY = "0xTaCleApi"
ASSET = "FEUSD"
URL = constants.MAINNET_API_URL

LOWER = 0.98
TARGET_MAX = 1.20
NUM_LEVELS = 100
USDC_UTIL = 0.9
REFRESH_SEC = 600

R = (TARGET_MAX / LOWER) ** (1 / (NUM_LEVELS - 1))
GRID = [LOWER * R**i for i in range(NUM_LEVELS)]

exchange = Exchange(ADDRESS, PRIVATE_KEY, base_url=URL)
info = Info(base_url=URL)

# === HELPERS ===
def balances():
    state = info.user_state(ADDRESS)["balances"]
    get = lambda c: float(next((b["sz"] for b in state if b["coin"] == c), 0))
    return get("USDC") * USDC_UTIL, get(ASSET)

def cancel_asset_orders():
    for o in info.open_orders(ADDRESS):
        if o["coin"] == ASSET:
            exchange.cancel(ASSET, o["oid"])

def place_orders(side, prices, total_qty, post_only):
    if not prices or total_qty <= 0:
        return
    qty = total_qty / len(prices)
    for p in prices:
        exchange.order(
            ASSET,
            side,
            qty if side else qty,
            p,
            {"limit": {"tif": "Gtc", "postOnly": post_only}}
        )

# === CORE ===
def place_grid(post_only=True):
    cancel_asset_orders()

    mid = float(info.all_mids().get(ASSET, 1))
    usdc, feusd = balances()

    buys  = [p for p in GRID if p < mid]
    sells = [p for p in GRID if p > mid]

    place_orders(True,  buys,  usdc / mid, post_only)
    place_orders(False, sells, feusd,      post_only)

# === WS CALLBACK ===
async def ws_callback(msg):
    try:
        updates = msg.get("data", {}).get("updates", [])
        for u in updates:
            if u.get("status") == "filled":
                side = u["side"] == "B"
                exchange.order(
                    ASSET,
                    not side,
                    float(u["sz"]),
                    float(u["price"]),
                    {"limit": {"tif": "Gtc", "postOnly": False}}
                )
    except Exception as e:
        print("WS error:", e)

# === MAIN ===
async def main():
    info.subscribe({"type": "userEvents", "user": ADDRESS}, ws_callback)
    info.subscribe({"type": "orderUpdates", "user": ADDRESS}, ws_callback)

    place_grid(True)

    while True:
        await asyncio.sleep(REFRESH_SEC)
        place_grid(True)

asyncio.run(main())
