import asyncio, time, ccxt
from decimal import Decimal, getcontext
from dotenv import dotenv_values
from telegram import Bot

# ── precision ─────────────────────────────────────
getcontext().prec = 18
PAIR = "BTC/USDT"

# ── load .env ─────────────────────────────────────
cfg = dotenv_values(".env")

#  Telegram
tg_bot = Bot(token=cfg["TELEGRAM_BOT_TOKEN"])
async def send_tg(msg: str):
    await tg_bot.send_message(chat_id=cfg["TELEGRAM_CHAT_ID"], text=msg)

#  Exchanges
binance = ccxt.binance({
    "apiKey": cfg["BINANCE_KEY"],
    "secret": cfg["BINANCE_SECRET"],
    "enableRateLimit": True,
})
kucoin = ccxt.kucoin({
    "apiKey": cfg["KUCOIN_KEY"],
    "secret": cfg["KUCOIN_SECRET"],
    "password": cfg["KUCOIN_PASSPHRASE"],
    "enableRateLimit": True,
})

#  Parameters
TRADE_AMOUNT  = Decimal(cfg["TRADE_SIZE_BTC"])
MIN_SPREAD    = Decimal(cfg["MIN_SPREAD_PCT"])
POLL_SEC      = int(cfg["POLL_SEC"])
FEE_TOTAL_PCT = (Decimal(cfg["BINANCE_FEE"]) + Decimal(cfg["KUCOIN_FEE"])) * 100

DROP_PCT = Decimal(cfg["PRICE_DROP_PCT"])
RISE_PCT = Decimal(cfg["PRICE_RISE_PCT"])

# ── helpers ───────────────────────────────────────
def best_prices():
    b_ob = binance.fetch_order_book(PAIR)
    k_ob = kucoin.fetch_order_book(PAIR)
    return (
        Decimal(str(b_ob["asks"][0][0])),  # b_ask
        Decimal(str(b_ob["bids"][0][0])),  # b_bid
        Decimal(str(k_ob["asks"][0][0])),  # k_ask
        Decimal(str(k_ob["bids"][0][0])),  # k_bid
    )

def balances():
    return binance.fetch_balance(), kucoin.fetch_balance()

def mkt(ex, side, amt):
    return ex.create_market_order(PAIR, side, float(amt))

# ── arbitrage task ────────────────────────────────
async def arbitrage_loop():
    await send_tg("🤖 Arbitrage bot started (Binance ⇄ KuCoin)")
    while True:
        try:
            b_ask, b_bid, k_ask, k_bid = best_prices()

            # direction 1: buy Binance, sell KuCoin
            spread1 = (k_bid - b_ask) / b_ask * 100 - FEE_TOTAL_PCT
            # direction 2: buy KuCoin, sell Binance
            spread2 = (b_bid - k_ask) / k_ask * 100 - FEE_TOTAL_PCT

            # choose profitable direction
            if spread1 >= MIN_SPREAD:
                bin_bal, ku_bal = balances()
                need_usdt = TRADE_AMOUNT * b_ask
                if Decimal(bin_bal["USDT"]["free"]) >= need_usdt and Decimal(ku_bal["BTC"]["free"]) >= TRADE_AMOUNT:
                    mkt(binance, "buy",  TRADE_AMOUNT)
                    mkt(kucoin,  "sell", TRADE_AMOUNT)
                    await send_tg(f"✅ Trade executed\nBUY Binance {b_ask}\nSELL KuCoin {k_bid}\nNet {spread1:.2f}%")
            elif spread2 >= MIN_SPREAD:
                bin_bal, ku_bal = balances()
                need_usdt = TRADE_AMOUNT * k_ask
                if Decimal(ku_bal["USDT"]["free"]) >= need_usdt and Decimal(bin_bal["BTC"]["free"]) >= TRADE_AMOUNT:
                    mkt(kucoin,  "buy",  TRADE_AMOUNT)
                    mkt(binance, "sell", TRADE_AMOUNT)
                    await send_tg(f"✅ Trade executed\nBUY KuCoin {k_ask}\nSELL Binance {b_bid}\nNet {spread2:.2f}%")
        except Exception as e:
            print("[ARB‑ERR]", e)
        await asyncio.sleep(POLL_SEC)

# ── price‑alert task ──────────────────────────────
async def price_watch():
    last = None
    while True:
        try:
            price = Decimal(str(binance.fetch_ticker(PAIR)["last"]))
            if last:
                change = (price - last) / last * 100
                if change <= -DROP_PCT:
                    await send_tg(f"⚠️ BTC dropped {change:.2f}%\n{last} → {price}")
                elif change >= RISE_PCT:
                    await send_tg(f"🚀 BTC spiked +{change:.2f}%\n{last} → {price}")
            last = price
        except Exception as e:
            print("[WATCH‑ERR]", e)
        await asyncio.sleep(POLL_SEC)

# ── run both tasks ────────────────────────────────
async def main():
    await asyncio.gather(arbitrage_loop(), price_watch())

if __name__ == "__main__":
    asyncio.run(main())
