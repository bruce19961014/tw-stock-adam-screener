import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_screener_results():
    # 定義掃描範圍：台股熱門代碼區間 (上市 .TW, 上櫃/興櫃 .TWO)
    # 涵蓋大部分電子、航運、半導體與興櫃熱門股
    ranges = [range(2301, 2400), range(2601, 2620), range(3001, 3100), range(6101, 6300), range(8001, 8100)]
    tickers = []
    for r in ranges:
        for i in r:
            tickers.append(f"{i}.TW")
            tickers.append(f"{i}.TWO")

    results = {"main": [], "emerging": []}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            # 過濾：數據不足或成交量太小 (日均量 > 500張 為基準)
            if len(df) < 60 or df['Volume'].tail(5).mean() < 500000:
                continue

            close = df['Close']
            low = df['Low']
            
            # 破底翻邏輯：
            # 1. 過去 20 天內曾創下 60 日新低 (破底)
            min_60 = low.rolling(60).min()
            was_broken = (low.iloc[-20:-1] <= min_60.iloc[-20:-1]).any()
            
            # 2. 今日收盤強勢站回 20MA (月線)
            ma20 = close.rolling(20).mean()
            is_back_up = close.iloc[-1] > ma20.iloc[-1] and close.iloc[-2] <= ma20.iloc[-2] * 1.02
            
            if was_broken and is_back_up:
                # 停損建議：設在過去 20 天的最低點
                stop_loss = low.iloc[-20:].min()
                stock_data = {
                    "代碼": ticker.split('.')[0],
                    "價格": round(float(close.iloc[-1]), 2),
                    "建議停損": round(float(stop_loss), 2)
                }
                if ".TW" in ticker: results["main"].append(stock_data)
                else: results["emerging"].append(stock_data)
        except:
            continue
            
    return results, df.index[-1].strftime('%Y-%m-%d')

results, latest_day = get_screener_results()

# 生成網頁 HTML
html = f"""
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>台股破底翻神器</title>
<style>
    body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; }}
    .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    h2 {{ color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 5px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #eee; }}
    .stop {{ color: #d32f2f; font-weight: bold; }}
</style></head><body>
<div style="max-width: 800px; margin: auto;">
    <h1>🌪️ 全市場破底翻篩選結果</h1>
    <p>基準日：{latest_day} | 條件：假跌破後站回月線</p>
    <div class="card">
        <h2>🏛️ 上市 / 上櫃股票</h2>
        {"<table><tr><th>代碼</th><th>價格</th><th>建議停損</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td class='stop'>{s['建議停損']}</td></tr>" for s in results['main']]) + "</table>" if results['main'] else "目前無符合標的"}
    </div>
    <div class="card">
        <h2>🚀 興櫃熱門股</h2>
        {"<table><tr><th>代碼</th><th>價格</th><th>建議停損</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td class='stop'>{s['建議停損']}</td></tr>" for s in results['emerging']]) + "</table>" if results['emerging'] else "目前無符合標的"}
    </div>
    <p style="text-align:center; color:gray;">最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
