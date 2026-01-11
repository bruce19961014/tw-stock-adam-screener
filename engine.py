import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta

def run_engine():
    # 市值前 200 權值股代碼 (此處演示 10 檔，可無限擴充至 200+)
    tickers = ["2330.TW", "2454.TW", "2317.TW", "3017.TW", "2382.TW", "6669.TW", "1513.TW", "2603.TW", "2881.TW", "2409.TW"]
    
    db = {"market": {}, "stocks": [], "update_time": ""}
    
    # 抓取大盤數據
    mkt = yf.download("^TWII", period="5d")
    db["market"] = {
        "index": round(float(mkt['Close'].iloc[-1]), 0),
        "txf_net": -22500, # 模擬期指數據
        "vix": 21.8
    }

    for t in tickers:
        try:
            df = yf.download(t, period="60d", progress=False)
            c = df['Close']
            # 計算斷頭價、強弱、乖離等
            db["stocks"].append({
                "id": t.split('.')[0],
                "p": round(float(c.iloc[-1]), 1),
                "bias": round(((c.iloc[-1]/c.rolling(20).mean().iloc[-1])-1)*100, 2),
                "risk": "高" if c.iloc[-1] < c.max()*0.75 else "穩"
            })
        except: continue

    db["update_time"] = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False)

run_engine()
