#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QBIT-5 (Quantum Computing 5 Index)
等加重指数の算出とスナップショット出力

出力先: docs/outputs/
- qbit_5_stats.json            … intraday用の統計（pct_intraday / updated_at）
- qbit_5_post_intraday.txt     … 「QBIT-5 +1.23% (YYYY/MM/DD HH:MM)」
- last_run.txt                 … タイムスタンプ（サイトのキャッシュバスター用）

チャート画像は scripts 側で生成（matplotlib）。
"""

import json, os, sys, math, datetime as dt
from pathlib import Path

import pandas as pd
import yfinance as yf

JST = dt.timezone(dt.timedelta(hours=9))
UTC = dt.timezone.utc

# ===== 構成銘柄（等加重） =====
TICKERS = ["IONQ", "QBTS", "RGTI", "ARQQ", "QUBT"]

# ===== 基準日（指数=100） =====
BASE_DATE = "2024-01-02"   # 必要に応じて変更

# ===== 出力先 =====
OUT_DIR = Path("docs/outputs")

def jst_now():
    return dt.datetime.now(JST).strftime("%Y/%m/%d %H:%M")

def _download_prices(start="2023-01-01"):
    """
    調整後終値(Adj Close)を日次で取得。前後補間と前日持越しで欠損を埋める。
    """
    df = yf.download(
        tickers=TICKERS,
        start=start,
        auto_adjust=True,
        progress=False,
        group_by='ticker',
        interval='1d',
        threads=True
    )
    # yfinance の multi-index を単純化
    if isinstance(df.columns, pd.MultiIndex):
        df = df.stack(0)  # (Date, Ticker, Field)
        df = df.reset_index()
        df = df.pivot_table(index="Date", columns="level_1", values="Adj Close")  # level_1 = Ticker
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    # 欠損処理
    df = df.ffill().dropna(how="all")
    return df

def _calc_index_level(df: pd.DataFrame, base_date=BASE_DATE) -> pd.Series:
    """
    等加重： 各銘柄 P(t)/P(t0) の平均 × 100
    """
    base_date = pd.to_datetime(base_date)
    # 基準日の株価（最も近い営業日を採用）
    base_row = df.loc[:base_date].iloc[-1]
    norm = df.divide(base_row)
    level = norm.mean(axis=1) * 100.0
    return level

def _intraday_pct(level: pd.Series) -> float:
    """
    当日リターン（前営業日終値→最新）
    """
    if len(level) < 2:
        return 0.0
    prev = level.iloc[-2]
    cur  = level.iloc[-1]
    return float((cur / prev - 1.0) * 100.0)

def write_text(fp: Path, text: str):
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(text, encoding="utf-8")

def write_json(fp: Path, obj: dict):
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # データ取得（BASE_DATE より少し前から）
    df = _download_prices(start="2023-09-01")
    level = _calc_index_level(df, BASE_DATE)

    pct_id = round(_intraday_pct(level), 2)
    updated = jst_now()

    # 統計(JSON)
    stats = {
        "key": "QBIT-5",
        "pct_intraday": pct_id,
        "updated_at": updated,
        "unit": "pct",
        "last_level": round(float(level.iloc[-1]), 2),
        "base_date": BASE_DATE,
        "tickers": TICKERS,
    }
    write_json(OUT_DIR / "qbit_5_stats.json", stats)

    # X用テキスト
    post = f"QBIT-5 {pct_id:+.2f}% ({updated})"
    write_text(OUT_DIR / "qbit_5_post_intraday.txt", post)

    # last_run
    write_text(OUT_DIR / "last_run.txt", updated)

    print("done:", updated)

if __name__ == "__main__":
    main()
