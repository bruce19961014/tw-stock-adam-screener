import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_screener_results():
    # 掃描範圍：上市、上櫃、興櫃熱門區間
    ranges = [range(1501, 1620), range(2301, 2400), range(2601, 2650), 
              range(3001, 3100), range(6101, 6300), range(8001, 8100), range(5201, 5300)]
    tickers = []
    for r in ranges:
        for i in r:
            tickers.append(f"{i}.TW")
            tickers.append(f"{i}.TWO")

    results = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=150)

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            # 成交量過濾：5日均量 > 500張 (安全第一)
            if len(df) < 60 or df['Volume'].tail(5).mean() < 500000: continue

            close = df['Close']
            low = df['Low']
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()
            ma240 = close.rolling(240).mean()

            # 策略：破底翻 (20天內跌破前低後今日站回月線)
            min_recent = low.iloc[-20:-1].min()
            was_broken = (low.iloc[-20:-1] <= low.iloc[-60:-20].min()).any()
            is_turning_up = close.iloc[-1] > ma20.iloc[-1] and close.iloc[-1] > close.iloc[-2]

            if was_broken and is_turning_up:
                stop_loss = min(close.iloc[-1] * 0.94, low.iloc[-10:].min())
                fundamental = "⭐ 績優" if close.iloc[-1] > ma240.iloc[-1] else "⏳ 轉機"
                results.append({
                    "ticker": ticker.split('.')[0],
                    "price": round(float(close.iloc[-1
