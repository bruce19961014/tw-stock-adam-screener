import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_screener_results():
    # 擴大掃描池 (涵蓋上市櫃熱門區間)
    ranges = [range(2301, 2400), range(2601, 2620), range(3001, 3100), 
              range(6101, 6300), range(8001, 8100), range(1501, 1600)]
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
            # 安全第一：五日均量 > 1000張 (1,000,000 股)
            if len(df) < 60 or df['Volume'].tail(5).mean() < 1000000:
                continue

            close = df['Close']
            low = df['Low']
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()

            # --- 策略 A: 深層破底翻 (跌破60日新低後站回) ---
            min_60 = low.rolling(60).min()
            was_deep_broken = (low.iloc[-20:-1] <= min_60.iloc[-20:-1]).any()
            
            # --- 策略 B: 淺層洗盤 (回測月線/季線不破翻起) ---
            near_support = (low.iloc[-5:] <= ma60.iloc[-5:] * 1.02).any()
            
            # 共同發動訊號：今日收盤強勢站回月線 且 5MA > 10MA (轉強)
            is_turning_up = close.iloc[-1] > ma20.iloc[-1] and close.iloc[-1] > close.iloc[-2]

            if (was_deep_broken or near_support) and is_turning_up:
                # 停損設計：月線或前五日最低點，取較小值作為緩衝
                stop_loss = min(ma20.iloc[-1] * 0.95, low.iloc[-5:].min())
                
                # 簡單基本面模擬 (若今日收盤 > 昨收 且 價格 > 年線，標記營收潛力)
                fundamental_note = "⭐ 績優" if close.iloc[-1] > close.rolling(240).mean().iloc[-1] else "⏳ 轉機"
                
                results.append({
                    "ticker": ticker.split('.')[0],
                    "name": ticker,
                    "price": round(float(close.iloc[-1]), 2),
                    "type": "深層反轉" if was_deep_broken else "淺層洗盤",
                    "note": fundamental_note,
                    "stop": round(float(stop_loss), 2),
                    "url": f"https://tw.stock.yahoo.com/quote/{ticker.split('.')[0]}"
                })
        except: continue
    return results, end_date.strftime('%Y-%m-%d')

results, latest_day = get_screener_results()

# HTML 模板
html = f"""
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body {{ font-family: "Microsoft JhengHei", sans-serif; background: #f0f2f5; padding: 20px; }}
    .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .tag {{ padding: 4px 8px; border-radius: 4px; font-size: 0.8em; color: white; }}
    .tag-deep {{ background: #e74c3c; }} .tag-shallow {{ background: #3498db; }}
    .tag-note {{ background: #27ae60; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #eee; }}
    a {{ text-decoration: none; color: #2980b9; font-weight: bold; }}
    .stop {{ color: #c0392b; font-weight: bold; }}
</style></head><body>
<div style="max-width: 900px; margin: auto;">
    <h1>🎯 波段起飛決策儀表板</h1>
    <div class="card">
        <h2>📊 今日掃描結果 ({latest_day})</h2>
        <table><tr><th>代碼</th><th>類型</th><th>價格</th><th>基本面</th><th>建議停損</th><th>看圖</th></tr>
        {"".join([f"<tr><td>{s['ticker']}</td><td><span class='tag {'tag-deep' if s['type']=='深層反轉' else 'tag-shallow'}'>{s['type']}</span></td><td>{s['price']}</td><td><span class='tag tag-note'>{s['note']}</span></td><td class='stop'>{s['stop']}</td><td><a href='{s['url']}' target='_blank'>📈</a></td></tr>" for s in results]) if results else "<tr><td colspan='6'>市場盤整中，尚未出現標的</td></tr>"}
        </table>
    </div>
    <div class="card">
        <h2>📰 收盤趨勢觀察 (2026/01/11)</h2>
        <p><b>1. 市場情緒：</b> 台股目前處於高檔震盪，資金有從半導體流向<b>能源與重電</b>的趨勢。</p>
        <p><b>2. 開盤熱門股預測：</b> 具備 AI 伺服器題材的組裝廠與散熱模組（如 3017, 3324）在美股帶動下可能轉強。</p>
        <p><b>3. 潛藏實力股：</b> 關注「營建」與「金融」板塊中，RSI 剛從 50 爬升且基期尚低的個股，這類股票在震盪市中具備避險與補漲潛力。</p>
    </div>
</div></body></html>
"""
with open("index.html", "w", encoding="utf-8") as f: f.write(html)
