import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_adam_stocks():
    # 精選台灣市場成交量大、具備代表性的標的清單 (涵蓋主要權值股與熱門股)
    base_stocks = [
        "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2603.TW", "2609.TW", 
        "2615.TW", "2337.TW", "2409.TW", "3481.TW", "2324.TW", "3231.TW", "2356.TW", 
        "2881.TW", "2882.TW", "2891.TW", "2886.TW", "2303.TW", "2376.TW", "2353.TW",
        "2327.TW", "2408.TW", "2610.TW", "2618.TW", "1605.TW", "2002.TW", "2344.TW"
    ]
    # 自動補齊一些常見代碼
    stocks = base_stocks + [f"{i}.TW" for i in range(2301, 2330)]
    stocks = list(set(stocks)) # 移除重複
    
    qualified = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    print(f"正在分析 {len(stocks)} 支股票...")

    for ticker in stocks:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) < 22: continue

            # 條件 1：成交量過濾 (近一個月/22個交易日，每天都要 > 1000 張)
            # 1000張 = 1,000,000股
            recent_vol = df['Volume'].tail(22)
            if not (recent_vol >= 1000000).all():
                continue

            # 條件 2：翻亞當趨勢
            # A. 今日收盤突破過去 10 日最高價 (突破箱體)
            # B. 5日均線 > 20日均線 (多頭排列)
            box_high = df['High'].iloc[-11:-1].max()
            current_close = df['Close'].iloc[-1]
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]

            if current_close > box_high and ma5 > ma20:
                diff = ((current_close - box_high) / box_high) * 100
                qualified.append({
                    "代碼": ticker.replace(".TW", ""),
                    "收盤": round(float(current_close), 2),
                    "漲幅": f"{round(float(diff), 2)}%",
                    "成交量": int(df['Volume'].iloc[-1] / 1000)
                })
        except Exception as e:
            continue
            
    return qualified, df.index[-1].strftime('%Y-%m-%d') if not df.empty else "N/A"

# 執行並生成 HTML
results, latest_day = get_adam_stocks()

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>台股翻亞當篩選</title>
    <style>
        body {{ font-family: "Microsoft JhengHei", sans-serif; padding: 20px; background: #f8f9fa; }}
        .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #d32f2f; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border: 1px solid #ddd; text-align: center; }}
        th {{ background: #d32f2f; color: white; }}
        .date {{ text-align: right; color: #666; font-size: 0.9em; }}
        .note {{ background: #fff3e0; padding: 10px; border-left: 5px solid #ff9800; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>台股亞當趨勢篩選器</h1>
        <p class="date">基準交易日：{latest_day}</p>
        <div class="note">
            條件：1. 近一個月每日量 > 1000張 | 2. 收盤價突破 10 日高點 | 3. 短期多頭趨勢
        </div>
"""

if not results:
    html_content += "<p style='text-align:center; padding: 40px;'>今日目前無符合「翻亞當」標準的標的。</p>"
else:
    html_content += "<table><tr><th>代碼</th><th>收盤價</th><th>突破幅度</th><th>今日量(張)</th></tr>"
    for s in results:
        html_content += f"<tr><td>{s['代碼']}</td><td>{s['收盤']}</td><td>{s['漲幅']}</td><td>{s['成交量']}</td></tr>"
    html_content += "</table>"

html_content += f"""
        <p style='font-size: 0.8em; color: #999; margin-top: 30px;'>最後更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
