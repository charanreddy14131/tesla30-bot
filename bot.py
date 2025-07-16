<<<<<<< HEAD
import time, asyncio, ccxt
from decimal import Decimal
from telegram import Bot
from dotenv import dotenv_values

cfg = dotenv_values(".env")

TRADE_SYMBOL   = cfg["TRADE_SYMBOL"]
TRADE_AMOUNT   = float(cfg["TRADE_AMOUNT"])
MIN_SPREAD_PCT = Decimal(cfg["MIN_SPREAD_PCT"])
DROP_PCT       = Decimal(cfg["PRICE_DROP_PCT"])
RISE_PCT       = Decimal(cfg["PRICE_RISE_PCT"])
POLL_INTERVAL  = int(cfg.get("POLL_INTERVAL", 5))

# Exchanges
binance = ccxt.binance({
    "apiKey": cfg["BINANCE_API_KEY"],
    "secret": cfg["BINANCE_API_SECRET"],
    "enableRateLimit": True,
})
kucoin = ccxt.kucoin({
    "apiKey": cfg["KUCOIN_API_KEY"],
    "secret": cfg["KUCOIN_API_SECRET"],
    "password": cfg["KUCOIN_PASSPHRASE"],
    "enableRateLimit": True,
})

# Telegram
bot = Bot(token=cfg["TELEGRAM_BOT_TOKEN"])
CHAT_ID = cfg["TELEGRAM_CHAT_ID"]

async def send_tg(msg: str):
    await bot.send_message(chat_id=CHAT_ID, text=msg)
    print("[TG]", msg)

# Main loop
async def main_loop():
    await send_tg("🤖 Bot started – monitoring Binance ⇄ KuCoin")

    base_bin_price = base_kuc_price = None
    last_update = time.time()
    buy_price = None  # For tracking previous buy

    while True:
        try:
            # Prices
            bin_orderbook = binance.fetch_order_book(TRADE_SYMBOL)
            kuc_orderbook = kucoin.fetch_order_book(TRADE_SYMBOL)
            bin_ask = Decimal(str(bin_orderbook["asks"][0][0]))
            kuc_bid = Decimal(str(kuc_orderbook["bids"][0][0]))
            spread  = (kuc_bid - bin_ask) / bin_ask * 100
            print(f"[INFO] Binance Ask: {bin_ask}, KuCoin Bid: {kuc_bid}, Spread: {spread:.2f}%")

            # Arbitrage Opportunity
            if spread >= MIN_SPREAD_PCT and buy_price is None:
                buy_price = float(bin_ask)
                await send_tg(f"💰 Bought BTC @ {buy_price} (Binance)")
                # binance.create_market_buy_order(TRADE_SYMBOL, TRADE_AMOUNT)

            # Check sell conditions
            if buy_price:
                current_price = float(kuc_bid)

                if current_price >= buy_price * 1.10:
                    await send_tg(f"✅ Sold BTC @ {current_price} — Profit ≈10%")
                    # kucoin.create_market_sell_order(TRADE_SYMBOL, TRADE_AMOUNT)
                    buy_price = None

                elif current_price <= buy_price * 0.95:
                    await send_tg(f"⚠️ Sold BTC @ {current_price} — Price dropped >5% from {buy_price}")
                    # kucoin.create_market_sell_order(TRADE_SYMBOL, TRADE_AMOUNT)
                    buy_price = None

            # 2-min price change alert
            if time.time() - last_update >= 120:
                current_bin = Decimal(str(binance.fetch_ticker(TRADE_SYMBOL)["last"]))
                current_kuc = Decimal(str(kucoin.fetch_ticker(TRADE_SYMBOL)["last"]))

                if base_bin_price is None:
                    base_bin_price, base_kuc_price = current_bin, current_kuc

                bin_pct = (current_bin - base_bin_price) / base_bin_price * 100
                kuc_pct = (current_kuc - base_kuc_price) / base_kuc_price * 100

                summary = f"[WATCH] 2 ‑min Δ Binance: {bin_pct:.2f}% | KuCoin: {kuc_pct:.2f}%"
                await send_tg(summary)

                if bin_pct <= -DROP_PCT:
                    await send_tg(f"⚠️ BTC dropped {abs(bin_pct):.2f}% on Binance\n{base_bin_price} ➞ {current_bin}")
                elif bin_pct >= RISE_PCT:
                    await send_tg(f"🚀 BTC rose +{bin_pct:.2f}% on Binance\n{base_bin_price} ➞ {current_bin}")

                if kuc_pct <= -DROP_PCT:
                    await send_tg(f"⚠️ BTC dropped {abs(kuc_pct):.2f}% on KuCoin\n{base_kuc_price} ➞ {current_kuc}")
                elif kuc_pct >= RISE_PCT:
                    await send_tg(f"🚀 BTC rose +{kuc_pct:.2f}% on KuCoin\n{base_kuc_price} ➞ {current_kuc}")

                base_bin_price, base_kuc_price = current_bin, current_kuc
                last_update = time.time()

        except Exception as e:
            print("[ERROR]", e)

        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())
=======
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
>>>>>>> 5cde3a973f012585fa013d34f109ea456d8ac0de
