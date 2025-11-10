#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intraday chart for QBIT-5
- 入力: docs/outputs/qbit_5_levels.csv（snapshotが作成）
- 出力: docs/outputs/qbit_5_intraday.png
- 黒ベース / 0%ライン / 最終値の符号で色を変える
"""

import os
from datetime import datetime, timezone, timedelta

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = os.path.dirname(os.path.dirname(__file__))
CSV  = os.path.join(ROOT, "docs", "outputs", "qbit_5_levels.csv")
OUT  = os.path.join(ROOT, "docs", "outputs", "qbit_5_intraday.png")

JST = timezone(timedelta(hours=9))

def load():
    df = pd.read_csv(CSV)
    df["datetime_jst"] = pd.to_datetime(df["datetime_jst"])
    df = df.set_index("datetime_jst").sort_index()
    return df

def style_dark(ax):
    ax.set_facecolor("#0b1420")
    ax.figure.set_facecolor("#0b1420")
    for s in ax.spines.values():
        s.set_color("#1c2a3a")
        s.set_linewidth(1.0)
    ax.tick_params(colors="#9fb6c7", labelsize=9)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
    ax.grid(True, color="#1c2a3a", alpha=0.7, linewidth=0.8)

def run():
    df = load()
    y = df["chg_open_pct"]
    last = float(y.iloc[-1])

    line = "#29c7c7" if last >= 0 else "#fb7185"
    fill = line

    fig = plt.figure(figsize=(13, 6), dpi=140)
    ax = fig.add_subplot(111)
    style_dark(ax)

    ax.plot(y.index, y.values, linewidth=2.1, color=line)
    ax.fill_between(y.index, 0, y.values, alpha=0.08, color=fill)
    ax.axhline(0.0, color="#1c2a3a", linewidth=1.0)

    ax.set_ylabel("Change vs Open (%)", color="#9fb6c7")
    ax.set_xlabel("", color="#9fb6c7")

    ts = datetime.now(JST).strftime("%Y/%m/%d %H:%M (JST)")
    ax.set_title(f"QBIT-5 Intraday Snapshot ({ts})", color="#cfe6f3", fontsize=12, pad=10)

    plt.tight_layout()
    fig.savefig(OUT, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

if __name__ == "__main__":
    run()
