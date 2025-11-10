#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QBIT-5 (Quantum Computing 5 Index)
等加重指数の算出とスナップショット出力

出力: docs/outputs/
- qbit_5_stats.json
- qbit_5_post_intraday.txt
- qbit_5_levels.csv
- last_run.txt
"""

from pathlib import Path
import datetime as dt
import json
import pandas as pd
import yfinance as yf

JST = dt.timezone(dt.timedelta(hours=9))

# ===== 構成銘柄（等加重） =====
TICKERS = ["IONQ", "QBTS", "RGTI", "ARQQ", "QUBT"]

# ===== 基準日（指数=100） =====
BASE_DATE = "2024-01-02"  # 必要に応じて変更

OUT_DIR = Path("docs/outputs")


def jst_now_str() -> str:
    return dt.datetime.now(JST).strftime("%Y/%m/%d %H:%M")


def download_prices(start: str = "2023-09-01") -> pd.DataFrame:
    """
    yfinance から日次の調整後終値を取得。
    auto_adjust=True なので 'Close' が調整済み価格。
    """
    df = yf.download(
        " ".join(TICKERS),
        start=start,
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )

    # 返り値の形は2通り:
    #  1) columns が MultiIndex（例: ('Close', 'IONQ'), ...）
    #  2) columns が単層（単一ティッカー時など）
    if isinstance(df.columns, pd.MultiIndex):
        # 調整後終値は 'Close'
        df = df["Close"].copy()
    else:
        # 単一ティッカーのとき
        if "Close" in df.columns:
            df = df[["Close"]].copy()
            df.columns = [TICKERS[0]]

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.ffill().dropna(how="all")
    # 列順を揃える（存在しない銘柄は除外）
    cols = [c for c in TICKERS if c in df.columns]
    df = df[cols].copy()
    return df


def calc_level(df: pd.DataFrame, base_date: str) -> pd.Series:
    """等加重指数（基準日=100）"""
    base_dt = pd.to_datetime(base_date)
    # 基準日に最も近い過去営業日の価格を採用
    base_row = df.loc[:base_dt].iloc[-1]
    norm = df.divide(base_row)
    level = norm.mean(axis=1) * 100.0
    return level


def intraday_pct(level: pd.Series) -> float:
    """前営業日終値→最新の %"""
    if len(level) < 2:
        return 0.0
    prev = level.iloc[-2]
    cur = level.iloc[-1]
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

    # 保存: levels.csv（長期/日内チャート用のベース）
    lv = level.reset_index()
    lv.columns = ["date", "level"]
    (OUT_DIR / "qbit_5_levels.csv").write_text(lv.to_csv(index=False), encoding="utf-8")

    # 統計(JSON)
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

    # X用テキスト（簡易）
    write_text(OUT_DIR / "qbit_5_post_intraday.txt", f"QBIT-5 {pct_id:+.2f}% ({updated})")

    # last_run（サイトのキャッシュバスター用）
    write_text(OUT_DIR / "last_run.txt", updated)

    print("snapshot done:", updated)


if __name__ == "__main__":
    main()
