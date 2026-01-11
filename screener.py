import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_screener_results():
    # 穩定推升組 (權值龍頭)
    stable_pool = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2881.TW", "2882.TW", "2603.TW", "2609.TW", "2002.TW"]
    # 大起大落組 (中小型飆股)
    volatile_pool = ["2337.TW", "2409.TW", "3481.TW", "3231.TW", "2356.TW", "2376.TW", "2353.TW", "1513.TW", "6235.TW", "3037.TW"]
    
    all_results = {"stable": [], "volatile": []}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)

    for pool_name, pool_list in [("stable", stable_pool), ("volatile", volatile_pool)]:
        for ticker in pool_list:
            try:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if len(df) < 60: continue

                # --- 手寫技術指標 (不依賴外部套件) ---
                close = df['Close']
                # 1. 均線
                df['MA5'] = close.rolling(5).mean()
                df['MA20'] = close.rolling(20).mean()
                df['MA60'] = close.rolling(60).mean()
                
                # 2. RSI (14日)
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                # 3. 布林通道 (20日, 2倍標準差)
                std = close.rolling(20).std()
                df['BBU'] = df['MA20'] + (std * 2)
                
                # --- 篩選條件 ---
                curr = df.iloc[-1]
                prev = df.iloc[-2]
                box_high_20 = df['High'].iloc[-21:-1].max()
                
                # 條件邏輯
                cond1 = curr['Close'] > box_high_20 # 突破20日高點
                cond2 = curr['MA5'] > curr['MA20'] > curr['MA60'] # 多頭排列
                cond3 = curr['RSI'] > 60 # 動能轉強
                cond4 = curr['Close'] >= df['BBU'].iloc[-1] * 0.98 # 觸碰或突破布林上軌
                cond5 = df['Volume'].tail(5).mean() > 1000000 # 五日均量 > 1000張

                if cond1 and cond2 and cond3 and cond4 and cond5:
                    # 停損建議：取前低或月線高者
                    stop_loss = max(prev['Low'], curr['MA20'])
                    all_results[pool_name].append({
                        "代碼": ticker.replace(".TW", ""),
                        "價格": round(float(curr['Close']), 2),
                        "RSI": round(float(curr['RSI']), 1),
                        "停損價": round(float(stop_loss), 2)
                    })
            except: continue
    return all_results, df.index[-1].strftime('%Y-%m-%d')

# 生成 HTML 
results, latest_day = get_screener_results()
html = f"""
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>波段選股神器</title>
<style>
    body {{ font-family: sans-serif; background: #f0f2f5; padding: 15px; line-height: 1.5; }}
    .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .stable-h {{ border-left: 8px solid #2196F3; }}
    .volatile-h {{ border-left: 8px solid #f44336; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #f8f9fa; padding: 10px; border-bottom: 2px solid #ddd; }}
    td {{ padding: 12px; text-align: center; border-bottom: 1px solid #eee; }}
    .stop {{ color: #d32f2f; font-weight: bold; }}
</style></head><body>
<div style="max-width: 800px; margin: auto;">
    <h2>📈 波段起飛選股神器</h2>
    <p>基準交易日：{latest_day} | 核心指標：RSI + 布林突破</p>
    <div class="card stable-h"><h3>🛡️ 穩定推升組</h3>
    {"<table><tr><th>代碼</th><th>價格</th><th>RSI</th><th>停損價</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td>{s['RSI']}</td><td class='stop'>{s['停損價']}</td></tr>" for s in results['stable']]) + "</table>" if results['stable'] else "目前無符合標的"}</div>
    <div class="card volatile-h"><h3>🚀 中小飆股組</h3>
    {"<table><tr><th>代碼</th><th>價格</th><th>RSI</th><th>停損價</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td>{s['RSI']}</td><td class='stop'>{s['停損價']}</td></tr>" for s in results['volatile']]) + "</table>" if results['volatile'] else "目前無符合標的"}</div>
    <p style="font-size:0.8em; color:gray; text-align:center;">最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>
"""
with open("index.html", "w", encoding="utf-8") as f: f.write(html)
