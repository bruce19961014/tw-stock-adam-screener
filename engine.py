import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta

def run_engine():
    # 這裡可以擴展至 200 檔，先以核心 40 檔演示以確保速度
    tickers = [
        "2330.TW", "2454.TW", "2317.TW", "3017.TW", "2382.TW", "6669.TW", "1513.TW", "2603.TW",
        "2308.TW", "2303.TW", "3711.TW", "2412.TW", "2357.TW", "3231.TW", "2881.TW", "2882.TW",
        "2609.TW", "2615.TW", "2618.TW", "2610.TW", "1605.TW", "1519.TW", "1503.TW", "1514.TW",
        "2376.TW", "2353.TW", "2324.TW", "2352.TW", "2408.TW", "2409.TW", "3481.TW", "6415.TW",
        "3661.TW", "5274.TW", "3533.TW", "3037.TW", "8069.TWO", "3293.TWO", "6488.TWO", "3105.TWO"
    ]
    
    db = {"market": {}, "stocks": [], "sentiment": {}, "update_time": ""}
    
    # 1. 宏觀指標
    twii = yf.download("^TWII", period="5d", progress=False)
    vix = yf.download("^VIX", period="5d", progress=False)
    db["market"] = {
        "index": round(float(twii['Close'].iloc[-1]), 0),
        "change": round(float(twii['Close'].iloc[-1] - twii['Close'].iloc[-2]), 0),
        "txf_net": -22500, # 2026 模擬數據：外資淨空單
        "vix": round(float(vix['Close'].iloc[-1]), 2),
        "margin_bal": 3820 # 模擬融資餘額
    }

    # 2. 個股大數據運算
    for t in tickers:
        try:
            df = yf.download(t, period="120d", progress=False)
            if df.empty: continue
            c = df['Close']
            curr_p = round(float(c.iloc[-1]), 1)
            ma20 = c.rolling(20).mean().iloc[-1]
            high_120 = c.max()
            
            db["stocks"].append({
                "id": t.split('.')[0],
                "p": curr_p,
                "bias": round(((curr_p / ma20) - 1) * 100, 2),
                "drawdown": round(((curr_p / high_120) - 1) * 100, 1),
                "risk": "🚨 高" if curr_p < high_120 * 0.72 else "✅ 穩",
                "vol": "放量" if df['Volume'].iloc[-1] > df['Volume'].rolling(5).mean().iloc[-1] else "量縮"
            })
        except: continue

    db["sentiment"] = {
        "summary": "2026.01.11: 市場處於三萬點高位恐懼期，外資避險情緒濃厚，2nm 供應鏈為唯一護城河。",
        "hot_topics": ["#台積電2nm", "#避險空單", "#融資斷頭潮"]
    }
    
    db["update_time"] = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False)

if __name__ == "__main__":
    run_engine()
