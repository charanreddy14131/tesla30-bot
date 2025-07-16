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
