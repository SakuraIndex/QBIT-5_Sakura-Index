#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json

# 注: 指定があるため seaborn は使わない

OUT_DIR = Path("docs/outputs")

def load_series():
    js = json.loads((OUT_DIR / "qbit_5_stats.json").read_text())
    # 画像生成は level の時系列が必要なので、long_charts.py 側で生成したCSVを使う
    csv = OUT_DIR / "qbit_5_levels.csv"
    if not csv.exists():
        raise FileNotFoundError("qbit_5_levels.csv not found. Run long_charts.py first.")
    s = pd.read_csv(csv, parse_dates=["date"]).set_index("date")["level"]
    return s

def plot_intraday():
    s = load_series().last("14D")  # 直近14日相当
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(s.index, s.values)
    ax.set_title("QBIT-5 Intraday Snapshot")
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "qbit_5_intraday.png", dpi=160)
    plt.close(fig)

if __name__ == "__main__":
    plot_intraday()
