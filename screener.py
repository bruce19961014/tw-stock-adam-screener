import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_screener_results():
    # 掃描範圍：包含 2026 年熱門的 IC 封測、PCB 與低基期轉機股
    ranges = [range(1501, 1620), range(2301, 2400), range(2601, 2650), 
              range(3001, 3100), range(6101, 6300), range(8001, 8100), range(5201, 5520)]
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
            # 2026 市場量能大，將門檻設為 500 張 (500,000 股) 以過濾雜訊
            if len(df) < 60 or df['Volume'].tail(5).mean() < 500000: continue

            close = df['Close']
            low = df['Low']
            ma20 = close.rolling(20).mean()
            ma240 = close.rolling(240).mean()

            # 破底翻策略：過去20天創60日新低後，今日收盤站回月線 (MA20)
            min_60 = low.rolling(60).min()
            was_broken = (low.iloc[-20:-1] <= min_60.iloc[-20:-1]).any()
            is_turning_up = close.iloc[-1] > ma20.iloc[-1] and close.iloc[-1] > close.iloc[-2]

            if was_broken and is_turning_up:
                # 停損建議：前波洗盤低點與月線取平衡
                stop_loss = min(close.iloc[-1] * 0.94, low.iloc[-10:].min())
                fundamental = "⭐ 績優(年線上)" if close.iloc[-1] > ma240.iloc[-1] else "⏳ 轉機(低基期)"
                
                results.append({
                    "ticker": ticker.split('.')[0],
                    "price": round(float(close.iloc[-1]), 2),
                    "note": fundamental,
                    "stop": round(float(stop_loss), 2),
                    "url": f"https://tw.stock.yahoo.com/quote/{ticker.split('.')[0]}"
                })
        except: continue
    return results, end_date.strftime('%Y-%m-%d')

results, latest_day = get_screener_results()

# 2026.01 權威財經觀點連結
news_data = [
    {"site": "經濟日報", "title": "台股3萬點後續展望：多頭格局未變", "url": "https://money.udn.com/"},
    {"site": "工商時報", "title": "2026飆股名單：IC封測與PCB接力演出", "url": "https://www.ctee.
