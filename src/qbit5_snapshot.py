#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import datetime as dt
import json
import pandas as pd
import yfinance as yf

JST = dt.timezone(dt.timedelta(hours=9))
TICKERS = ["IONQ", "QBTS", "RGTI", "ARQQ", "QUBT"]
BASE_DATE = "2024-01-02"
OUT_DIR = Path("docs/outputs")

def jst_now_str() -> str:
    return dt.datetime.now(JST).strftime("%Y/%m/%d %H:%M")

def download_prices(start: str = "2023-09-01") -> pd.DataFrame:
    df = yf.download(" ".join(TICKERS), start=start, interval="1d",
                     auto_adjust=True, progress=False, group_by="column", threads=True)
    if isinstance(df.columns, pd.MultiIndex):
        df = df["Close"].copy()
    else:
        if "Close" in df.columns:
            df = df[["Close"]].copy()
            df.columns = [TICKERS[0]]
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().ffill().dropna(how="all")
    cols = [c for c in TICKERS if c in df.columns]
    return df[cols].copy()

def calc_level(df: pd.DataFrame, base_date: str) -> pd.Series:
    base_dt = pd.to_datetime(base_date)
    base_row = df.loc[:base_dt].iloc[-1]
    return df.divide(base_row).mean(axis=1) * 100.0

def intraday_pct(level: pd.Series) -> float:
    if len(level) < 2: return 0.0
    prev, cur = level.iloc[-2], level.iloc[-1]
    return float((cur / prev - 1.0) * 100.0)

def write_json(fp: Path, obj: dict):
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def write_text(fp: Path, text: str):
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(text, encoding="utf-8")

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = download_prices(start="2023-09-01")
    level = calc_level(prices, BASE_DATE)

    pct_id = round(intraday_pct(level), 2)
    updated = jst_now_str()

    # ✅ 確実にヘッダ付きで保存
    lv = level.reset_index()
    lv.columns = ["date", "level"]
    lv.to_csv(OUT_DIR / "qbit_5_levels.csv", index=False)

    stats = {
        "key": "QBIT-5",
        "pct_intraday": pct_id,
        "updated_at": updated,
        "unit": "pct",
        "last_level": round(float(level.iloc[-1]), 2),
        "base_date": BASE_DATE,
        "tickers": [c for c in TICKERS if c in prices.columns],
    }
    write_json(OUT_DIR / "qbit_5_stats.json", stats)
    write_text(OUT_DIR / "qbit_5_post_intraday.txt", f"QBIT-5 {pct_id:+.2f}% ({updated})")
    write_text(OUT_DIR / "last_run.txt", updated)
    print("snapshot done:", updated)

if __name__ == "__main__":
    main()
