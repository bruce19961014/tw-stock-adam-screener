import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_adam_stocks():
    # 範例：抓取台灣市值較大的標的 (可自行擴充)
    stocks = [f"{i:04d}.TW" for i in range(1101, 1110)] + \
             [f"{i:04d}.TW" for i in range(2301, 2390)] + \
             [f"{i:04d}.TW" for i in range(2601, 2620)]
    
    qualified = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    for ticker in stocks:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) < 25: continue

            # 1. 成交量篩選：近一個月(22日)每日 > 1000張 (1,000,000股)
            vol_check = (df['Volume'].tail(22) >= 1000000).all()
            if not vol_check: continue

            # 2. 亞當趨勢篩選 (今日突破過去10日高點 + 5MA > 10MA)
            box_high = df['High'].iloc[-11:-1].max()
            current_close = df['Close'].iloc[-1]
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]

            if current_close > box_high and ma5 > ma10:
                qualified.append({
                    "代碼": ticker.replace(".TW", ""),
                    "股價": round(float(current_close), 2),
                    "漲幅": f"{round((current_close/df['Close'].iloc[-2]-1)*100, 2)}%"
                })
        except:
            continue
    return qualified

# 生成簡單的 HTML 網頁
qualified_list = get_adam_stocks()
html_content = f"""
<html>
<head><title>台股亞當趨勢篩選</title></head>
<body>
    <h1>台股翻亞當篩選結果 ({datetime.now().strftime('%Y-%m-%d')})</h1>
    <p>篩選條件：近一個月每日量 > 1000張 + 股價突破10日箱體</p>
    <table border="1">
        <tr><th>股票代碼</th><th>今日收盤</th><th>今日漲幅</th></tr>
        {''.join([f"<tr><td>{s['代碼']}</td><td>{s['股價']}</td><td>{s['漲幅']}</td></tr>" for s in qualified_list])}
    </table>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
