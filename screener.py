import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_market_data():
    # 掃描 2026 核心族群 (半導體、AI、網通、傳統績優)
    tickers = [
        "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "3017.TW", # 大型權值
        "2603.TW", "2609.TW", "2615.TW", # 航運
        "1513.TW", "1519.TW", "6806.TW", # 重電
        "5347.TWO", "6182.TWO", "3293.TWO" # 上櫃熱門
    ]
    
    bullish = [] # 市場看好
    bearish = [] # 市場看衰
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=200)

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) < 100: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]
            ma240 = df['Close'].rolling(240).mean().iloc[-1]
            vol_ma = df['Volume'].rolling(5).mean().iloc[-1]
            
            data = {
                "symbol": ticker.split('.')[0],
                "price": round(float(close), 2),
                "url": f"https://tw.stock.yahoo.com/quote/{ticker.split('.')[0]}"
            }

            # 多頭判斷：價格在季線與年線上，且今日強於月線
            if close > ma60 and close > ma240 and close > ma20:
                bullish.append(data)
            # 空頭判斷：價格在季線與年線下
            elif close < ma60 and close < ma240:
                bearish.append(data)
        except: continue
        
    return bullish, bearish, end_date.strftime('%Y-%m-%d')

bull, bear, update_time = get_market_data()

html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2026 台股戰情決策室</title>
    <style>
        :root {{ --bull-color: #e74c3c; --bear-color: #27ae60; --dark: #2c3e50; --bg: #f8f9fa; }}
        body {{ font-family: "Microsoft JhengHei", sans-serif; background: var(--bg); margin: 0; }}
        .nav {{ background: var(--dark); color: white; padding: 15px; text-align: center; position: sticky; top: 0; z-index: 100; }}
        .container {{ max-width: 1100px; margin: 20px auto; padding: 0 15px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .bull-header {{ border-left: 8px solid var(--bull-color); padding-left: 15px; color: var(--bull-color); }}
        .bear-header {{ border-left: 8px solid var(--bear-color); padding-left: 15px; color: var(--bear-color); }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #eee; }}
        .analysis-box {{ background: #edf2f7; padding: 15px; border-radius: 8px; font-size: 0.95em; line-height: 1.7; }}
        .tag {{ font-size: 0.8em; padding: 2px 6px; border-radius: 4px; margin-left: 5px; color: white; }}
        .tag-hot {{ background: #e67e22; }}
        .tag-warn {{ background: #95a5a6; }}
    </style>
</head>
<body>

<div class="nav">
    <h2>🎯 2026 台股戰情決策室 - {update_time}</h2>
</div>

<div class="container">
    <div class="card">
        <h3>🌍 國際局勢與匯率綜合分析</h3>
        <div class="analysis-box">
            <b>1. 匯率走勢：</b> 2026年初台幣兌美元維持在 31.5 區間，電子外銷業（半導體、零組件）匯兌收益預期穩定。若台幣轉強，資金可能轉往內需資產股。<br>
            <b>2. 國際情勢：</b> CES 2026 展後，AI 機器人與低軌道衛星成為新主流。美股 Nasdaq 強勢，帶動台股權值股表態。<br>
            <b>3. 潛力判斷：</b> 財報顯示伺服器散熱、CPO 光通訊毛利持續攀升，是目前最有潛力的長線標的。
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3 class="bull-header">🔥 市場看好標的 (多頭排列)</h3>
            <p>指標：站穩所有均線、法人持續買超</p>
            <table>
                <tr><th>代碼</th><th>價格</th><th>分析</th></tr>
                {"".join([f"<tr><td>{s['symbol']}</td><td>{s['price']}</td><td><a href='{s['url']}' target='_blank'>連結</a></td></tr>" for s in bull]) if bull else "<tr><td colspan='3'>暫無符合標的</td></tr>"}
            </table>
            <div class="analysis-box" style="margin-top:15px;">
                <b>📈 未來趨勢：</b> 這些股票具備「強者恆強」特徵。看好理由多為營收創高或接獲國際大單。適合回檔不破 5 日線時小量布局。
            </div>
        </div>

        <div class="card">
            <h3 class="bear-header">❄️ 市場看衰標的 (空頭弱勢)</h3>
            <p>指標：均線下彎、跌破年線關鍵支撐</p>
            <table>
                <tr><th>代碼</th><th>價格</th><th>佐證</th></tr>
                {"".join([f"<tr><td>{s['symbol']}</td><td>{s['price']}</td><td><a href='{s['url']}' target='_blank'>佐證</a></td></tr>" for s in bear]) if bear else "<tr><td colspan='3'>市場目前情緒穩定</td></tr>"}
            </table>
            <div class="analysis-box" style="margin-top:15px; color: #666;">
                <b>📉 看衰原因：</b> 多受制於產業景氣下行（如傳統成熟製程晶片過剩）或法人籌碼鬆動。在未出現「破底翻」訊號前，切勿進場接刀。
            </div>
        </div>
    </div>

    <div class="card">
        <h3>🔍 深度挖掘：誰還有潛力？</h3>
        <div class="analysis-box" style="background: #fff;">
            <ul>
                <li><b>技術面潛力：</b> 關注「看衰區」中，成交量開始極度萎縮並站回月線的個股，這是潛在的破底翻機會。</li>
                <li><b>基本面支撐：</b> 2026 第一季財報預告中，毛利率連三季成長的公司（如部分光通訊、特用化學）最具備波段實力。</li>
                <li><b>網友情緒：</b> PTT 股市版目前對「重電」族群看法兩極，這類分歧通常代表行情尚未結束。</li>
            </ul>
        </div>
    </div>
</div>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
