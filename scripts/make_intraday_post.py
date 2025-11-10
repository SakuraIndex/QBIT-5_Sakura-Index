#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path("docs/outputs")

def load_series():
    csv = OUT_DIR / "qbit_5_levels.csv"
    s = pd.read_csv(csv, parse_dates=["date"]).set_index("date")["level"]
    return s

def plot_intraday():
    s = load_series().last("14D")  # 直近約2週間
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
