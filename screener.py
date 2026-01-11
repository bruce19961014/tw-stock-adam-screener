import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

def get_screener_results():
    # 1. 定義標的池
    # 穩定推升組 (大型權值股)
    stable_pool = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2881.TW", "2882.TW", "2603.TW", "2609.TW", "2002.TW"]
    # 大起大落組 (熱門中小型股/題材股)
    volatile_pool = [
        "2337.TW", "2409.TW", "3481.TW", "3231.TW", "2356.TW", "2376.TW", "2353.TW", 
        "6235.TW", "1513.TW", "1504.TW", "2368.TW", "3037.TW", "3711.TW", "2618.TW"
    ]
    
    all_results = {"stable": [], "volatile": []}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=100) # 抓長一點計算 60MA

    for pool_name, pool_list in [("stable", stable_pool), ("volatile", volatile_pool)]:
        for ticker in pool_list:
            try:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if len(df) < 60: continue

                # --- 技術指標計算 ---
                # 1. 均線
                df['MA5'] = ta.sma(df['Close'], length=5)
                df['MA20'] = ta.sma(df['Close'], length=20)
                df['MA60'] = ta.sma(df['Close'], length=60)
                
                # 2. RSI
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # 3. 布林通道
                bbands = ta.bbands(df['Close'], length=20, std=2)
                df['BBU'] = bbands['BBU_20_2.0'] # 上軌
                
                # --- 篩選條件 ---
                curr = df.iloc[-1]
                prev = df.iloc[-2]
                
                # 條件 A: 底部起飛 (收盤價突破過去20日高點)
                box_high_20 = df['High'].iloc[-21:-1].max()
                is_breakout = curr['Close'] > box_high_20
                
                # 條件 B: 多頭排列 (5 > 20 > 60)
                is_trending = curr['MA5'] > curr['MA20'] and curr['MA20'] > curr['MA60']
                
                # 條件 C: RSI 強勢 (> 60)
                is_strong = curr['RSI'] > 60
                
                # 條件 D: 布林突破 (收盤接近或高於上軌)
                is_bband_attack = curr['Close'] >= curr['BBU'] * 0.98
                
                # 條件 E: 成交量過濾 (波段操作建議均量 > 1000張，避免流動性風險)
                is_volume_ok = df['Volume'].tail(5).mean() > 1000000

                if is_breakout and is_trending and is_strong and is_bband_attack and is_volume_ok:
                    # 停損價計算：取前一根K線低點或20MA，取較大者
                    stop_loss = max(prev['Low'], curr['MA20'])
                    
                    all_results[pool_name].append({
                        "代碼": ticker.replace(".TW", ""),
                        "價格": round(float(curr['Close']), 2),
                        "RSI": round(float(curr['RSI']), 1),
                        "停損價": round(float(stop_loss), 2),
                        "潛在漲幅": f"{round(((curr['Close']/stop_loss)-1)*100, 2)}%"
                    })
            except:
                continue
    return all_results, df.index[-1].strftime('%Y-%m-%d')

results, latest_day = get_screener_results()

# --- HTML 生成 ---
html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>波段選股神器</title>
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
        .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .stable-h {{ border-left: 8px solid #2196F3; color: #1565C0; }}
        .volatile-h {{ border-left: 8px solid #f44336; color: #c62828; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th {{ background: #eee; padding: 10px; text-align: center; }}
        td {{ padding: 12px; text-align: center; border-bottom: 1px solid #ddd; }}
        .stop-loss {{ color: #d32f2f; font-weight: bold; }}
    </style>
</head>
<body>
    <div style="max-width: 900px; margin: auto;">
        <h1>📈 波段起飛選股神器</h1>
        <p>基準日：{latest_day} | 週期：2週~2個月</p>
        <p style="font-size:0.8em; color:gray;">指標：RSI>60 + 布林突破 + 5/20/60MA多頭排列</p>

        <div class="card stable-h">
            <h2>🛡️ 穩定推升組 (權值龍頭)</h2>
            {f"<table><tr><th>代碼</th><th>進場參考</th><th>RSI</th><th>建議停損</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td>{s['RSI']}</td><td class='stop-loss'>{s['停損價']}</td></tr>" for s in results['stable']]) + "</table>" if results['stable'] else "<p>今日無符合標的</p>"}
        </div>

        <div class="card volatile-h">
            <h2>🚀 大起大落組 (強勢飆股)</h2>
            {f"<table><tr><th>代碼</th><th>進場參考</th><th>RSI</th><th>建議停損</th></tr>" + "".join([f"<tr><td>{s['代碼']}</td><td>{s['價格']}</td><td>{s['RSI']}</td><td class='stop-loss'>{s['停損價']}</td></tr>" for s in results['volatile']]) + "</table>" if results['volatile'] else "<p>今日無符合標的</p>"}
        </div>
        
        <p class="date" style="text-align:center;">最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
