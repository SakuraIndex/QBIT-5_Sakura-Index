#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import yfinance as yf

OUT_DIR = Path("docs/outputs")
TICKERS = ["IONQ", "QBTS", "RGTI", "ARQQ", "QUBT"]
BASE_DATE = "2024-01-02"

def _recalc_and_save():
    df = yf.download(" ".join(TICKERS), start="2023-09-01",
                     interval="1d", auto_adjust=True, progress=False, group_by="column")
    if isinstance(df.columns, pd.MultiIndex):
        df = df["Close"].copy()
    else:
        if "Close" in df.columns:
            df = df[["Close"]].copy()
            df.columns = [TICKERS[0]]
    df = df.ffill().dropna(how="all")
    base_row = df.loc[:pd.to_datetime(BASE_DATE)].iloc[-1]
    level = (df.divide(base_row).mean(axis=1) * 100.0)
    lv = level.reset_index()
    lv.columns = ["date", "level"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lv.to_csv(OUT_DIR / "qbit_5_levels.csv", index=False)
    return level

def load_levels():
    csv = OUT_DIR / "qbit_5_levels.csv"
    if csv.exists():
        try:
            df = pd.read_csv(csv)
            # 必須カラム検証＋空チェック
            if set(["date", "level"]).issubset(df.columns) and len(df) > 0:
                df["date"] = pd.to_datetime(df["date"])
                return df.set_index("date")["level"]
        except Exception:
            pass
    # 壊れている/無い → 再計算して保存
    return _recalc_and_save()

def _save(s: pd.Series, name: str, title: str):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(s.index, s.values)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / f"qbit_5_{name}.png", dpi=160)
    plt.close(fig)

def main():
    s = load_levels()
    _save(s.last("7D"),  "7d", "QBIT-5 (7D)")
    _save(s.last("35D"), "1m", "QBIT-5 (1M)")
    _save(s.last("400D"),"1y", "QBIT-5 (1Y)")

if __name__ == "__main__":
    main()
