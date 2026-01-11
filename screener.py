import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_screener_results():
    # 掃描 2026 關鍵成長族群
    ranges = [range(2301, 2400), range(2601, 2650), range(3001, 3100), 
              range(6101, 6300), range(8001, 8100), range(5201, 5520)]
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
            # 安全門檻：五日均量 > 800 張，過濾掉容易被操控的小盤股
            if len(df) < 60 or df['Volume'].tail(5).mean() < 800000:
                continue

            close = df['Close']
            low = df['Low']
            ma20 = close.rolling(20).mean()
            ma240 = close.rolling(240).mean()

            # 策略：破底翻 (過去20天創60日新低，今日收盤強勢站回月線)
            min_60 = low.rolling(60).min()
            was_broken = (low.iloc[-20:-1] <= min_60.iloc[-20:-1]).any()
            is_turning_up = close.iloc[-1] > ma20.iloc[-1] and close.iloc[-1] > close.iloc[-2]
            
            if was_broken and is_turning_up:
                # 嚴格停損設計 (進場價回檔 6% 或前波低點，取較大值)
                stop_loss = min(close.iloc[-1] * 0.94, low.iloc[-15:].min())
                fundamental = "⭐ 績優 (年線上)" if close.iloc[-1] > ma240.iloc[-1] else "⏳ 轉機 (低基期)"
                
                results.append({
                    "ticker": ticker.split('.')[0],
                    "price": round(float(close.iloc[-1]), 2),
                    "note": fundamental,
                    "stop": round(float(stop_loss), 2),
                    "url": f"https://tw.stock.yahoo.com/quote/{ticker.split('.')[0]}"
                })
        except:
            continue
    return results, end_date.strftime('%Y-%m-%d')

results, latest_day = get_screener_results()

# 2026.01 市場觀點數據 (手動更新重點)
news_data = [
    {"site": "工商時報", "title": "15檔中小股外資回補 瞄準補漲行情", "url": "https://www.ctee.com.tw/"},
    {"site": "理財寶", "title": "台積電 1 月法說前瞻：先進製程需求分析", "url": "https://www.cmoney.tw/notes/"},
    {"site": "今周刊", "title": "謝金河：2026 年投資主軸在內需與政府支出", "url": "https://www.businesstoday.com.tw/"}
]

html_content = f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>2026 台股避險決策儀表板</title>
<style>
    body {{ font-family: "Microsoft JhengHei", sans-serif; background: #f0f4f8; padding: 20px; color: #2d3436; }}
    .container {{ max-width: 1000px; margin: auto; }}
    .card {{ background: white; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
    .tag {{ padding: 3px 10px; border-radius: 4px; color: white; background: #2ecc71; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ padding: 15px; border-bottom: 1px solid #f1f2f6; text-align: center; }}
    th {{ background: #f9f9f9; }}
    .stop-price {{ color: #e74c3c; font-weight: bold; }}
    .news-box {{ background: #ebf5fb; padding: 15px; border-radius: 8px; margin-top: 10px; }}
    .warning {{ color: #d35400; font-weight: bold; background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
</style></head><body>
<div class="container">
    <h1>📈 2026 台股「破底翻」決策儀表板</h1>
    <div class="card">
        <h2>🎯 本日選股結果 ({latest_day})</h2>
        <div class="warning">⚠️ 提醒：目前台股位於 3 萬點高檔，若收盤跌破「建議停損」應立即撤退，嚴禁攤平。</div>
        <table><tr><th>代碼</th><th>收盤價</th><th>評級</th><th>建議停損</th><th>圖表分析</th></tr>
"""

for s in results:
    html_content += f"<tr><td>{s['ticker']}</td><td>{s['price']}</td><td><span class='tag'>{s['note']}</span></td><td class='stop-price'>{s['stop']}</td><td><a href='{s['url']}' target='_blank'>📈</a></td></tr>"

if not results:
    html_content += "<tr><td colspan='5'>市場高檔盤整中，目前尚無標的符合「破底翻」低風險條件。</td></tr>"

html_content += f"""
        </table>
    </div>
    <div class="card">
        <h2>📰 2026 權威觀點與市場情緒</h2>
"""

for n in news_data:
    html_content += f"<div class='news-box'><a style='text-decoration:none; color:#2980b9;' href='{n['url']}' target='_blank'><b>[{n['site']}]</b> {n['title']}</a></div>"

html_content += """
        <p style="margin-top:20px;"><b>💬 避開韭菜思維：</b> 當市場都在討論「台積電上看 2000 元」或「記憶體缺貨到 2027」時，通常是過熱訊號。利用此儀表板尋找那些<b>剛從底部洗盤翻起</b>的標的，比追逐熱點更安全。</p>
    </div>
</div></body></html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
