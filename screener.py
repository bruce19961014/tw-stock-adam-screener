import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_screener_results():
    # 建立掃描清單 (上市上櫃 1101-9999, 興櫃通常也在這範圍內)
    # 為了執行效率，我們先針對成交量較大的熱門區間進行掃描
    test_ranges = [range(2301, 2399), range(2401, 2499), range(2601, 2620), 
                   range(3001, 3099), range(6101, 6299), range(8001, 8099)]
    
    tickers = []
    for r in test_ranges:
        for i in r:
            tickers.append(f"{i}.TW")  # 上市
            tickers.append(f"{i}.TWO") # 上櫃/興櫃

    results = {"main": [], "emerging": []} # main: 上市櫃, emerging: 興櫃
    end_date = datetime.now()
    start_date = end_date - timedelta(days=100)

    print(f"開始掃描全市場，預計測試 {len(tickers)} 組代碼...")

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) < 60 or df['Volume'].iloc[-1] < 500000: continue # 過濾掉極低成交量

            close = df['Close']
            low = df['Low']
            
            # --- 破底翻邏輯 ---
            # 1. 找出 60 日最低點
            min_60 = low.rolling(60).min()
            # 2. 判斷過去 10 天內是否有「破底」動作 (跌破 60 日低點)
            was_broken = (low.iloc[-10:-1] <= min_60.iloc[-10:-1]).any()
            
            # 3. 判斷今日是否「翻起」 (收盤站上月線 20MA)
            ma20 = close.rolling(20).mean().iloc[-1]
            is_back_up = close.iloc[-1] > ma20 and close.iloc[-2] <= ma20 * 1.02
            
            # 4. 輔助指標：RSI 轉強
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]

            if was_broken and is_back_up and rsi > 50:
                # 停損設在破底的那個低點
                stop_loss = low.iloc[-10:].min()
                data = {
                    "代碼": ticker.split('.')[0],
                    "價格": round(float(close.iloc[-1]), 2),
                    "停損": round(float(stop_loss), 2),
                    "RSI": round(float(rsi), 1)
                }
                if ".TW" in ticker: results["main"].append(data)
                else: results["emerging"].append(data)
        except: continue
            
    return results, df.index[-1].strftime('%Y-%m-%d')

results, latest_day = get_screener_results()

# --- HTML 生成 ---
html = f"""
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>破底翻選股神器</title>
<style>
    body {{ font-family: sans-serif; background: #f4f7f6; padding: 15px; }}
    .container {{ max-width: 800px; margin: auto; }}
    .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
    h2 {{ color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #eee; }}
    th {{ background: #f9f9f9; }}
    .stop {{ color: #e74c3c; font-weight: bold; }}
    .badge {{ background: #e74c3c; color: white; padding: 3px 8px; border-radius: 5px; font-size: 0.8em; }}
</style></head><body>
<div class="container">
    <h1>🌪️ 全市場破底翻篩選</h1>
    <p>基準日：{latest_day} | 策略：洗盤後重回月線</p>
    
    <div class="card">
        <h2>🏛️ 上市 / 上櫃公司</h2>
        {"<table><tr><th>代碼</th><th>價格</th><th>RSI</th><th>建議停損</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td>{s['RSI']}</td><td class='stop'>{s['停損']}</td></tr>" for s in results['main']]) + "</table>" if results['main'] else "今日無符合標的"}
    </div>

    <div class="card">
        <h2>🚀 興櫃熱門股</h2>
        {"<table><tr><th>代碼</th><th>價格</th><th>RSI</th><th>建議停損</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td>{s['RSI']}</td><td class='stop'>{s['停損']}</td></tr>" for s in results['emerging']]) + "</table>" if results['emerging'] else "今日無符合標的"}
    </div>
    <p style="text-align:center; color:gray;">最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>
"""
with open("index.html", "w", encoding="utf-8") as f: f.write(html)
