import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_adam_stocks():
    # 擴大掃描範圍：包含台灣市值前 100 大及熱門股
    stocks = [f"{i:04d}.TW" for i in range(2301, 2390)] + \
             [f"{i:04d}.TW" for i in range(2601, 2620)] + \
             [f"{i:04d}.TW" for i in range(2401, 2460)] + \
             ["2330.TW", "2317.TW", "2454.TW", "2603.TW", "3231.TW", "2382.TW"]
    
    # 刪除重複的代碼
    stocks = list(set(stocks))
    
    qualified = []
    # 抓取最近 60 天的數據，確保有足夠樣本計算均線與箱體
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    for ticker in stocks:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            # 必須有足夠的交易日數據
            if len(df) < 22: continue

            # --- 條件 1：成交量過濾 (最近 22 個交易日每天 > 1000 張) ---
            # 1000 張 = 1,000,000 股
            vol_series = df['Volume'].tail(22)
            if not (vol_series >= 1000000).all():
                continue

            # --- 條件 2：翻亞當趨勢 (突破 10 日箱體 + 強勢均線) ---
            last_date = df.index[-1].strftime('%Y-%m-%d')
            current_close = df['Close'].iloc[-1]
            current_high = df['High'].iloc[-1]
            current_low = df['Low'].iloc[-1]
            
            # 取得昨日的高低點與前 10 日最高價
            prev_high = df['High'].iloc[-2]
            prev_low = df['Low'].iloc[-2]
            box_high = df['High'].iloc[-11:-1].max()
            
            # 亞當理論核心：順勢突破 + 創新高
            # A. 收盤價突破 10 日箱體高點
            # B. 今日低點比昨日低點高 (不破低)
            # C. 5MA > 20MA (短期強勢趨勢)
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]

            if current_close > box_high and current_low > prev_low and ma5 > ma20:
                qualified.append({
                    "代碼": ticker.replace(".TW", ""),
                    "日期": last_date,
                    "收盤價": round(float(current_close), 2),
                    "成交量(張)": int(df['Volume'].iloc[-1] / 1000),
                    "狀態": "翻亞當突破"
                })
        except:
            continue
    return qualified, (df.index[-1].strftime('%Y-%m-%d') if not df.empty else "N/A")

# 執行篩選
results, latest_day = get_adam_stocks()

# --- 製作網頁 (index.html) ---
html_start = f"""
<html>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>台股亞當趨勢篩選</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; background-color: #f4f4f9; }}
        table {{ border-collapse: collapse; width: 100%; background: white; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #007bff; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .status {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>台股翻亞當篩選結果</h1>
    <p><strong>基準交易日：{latest_day}</strong></p>
    <p>篩選條件：1. 近 22 日每日成交量 > 1000 張 / 2. 股價突破 10 日箱體 / 3. 5MA > 20MA</p>
"""

if not results:
    html_body = "<div style='padding:20px; background:#fff;'>目前無符合「翻亞當」條件之股票，請繼續觀察。</div>"
else:
    html_body = "<table><tr><th>代碼</th><th>收盤價</th><th>今日量(張)</th><th>趨勢狀態</th></tr>"
    for s in results:
        html_body += f"<tr><td>{s['代碼']}</td><td>{s['收盤價']}</td><td>{s['成交量(張)']}</td><td class='status'>{s['狀態']}</td></tr>"
    html_body += "</table>"

html_end = f"<br><p>系統最後自動更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_start + html_body + html_end)
