#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json

OUT_DIR = Path("docs/outputs")

def load_levels():
    # src で作ったスナップ時に生成済みのベースを再計算してもOKだが、
    # スナップスクリプトと同じロジックを再利用するのが安全。
    # ここでは stats.json から base_date を読むだけにし、実データは yfinance 再取得でも良い。
    # シンプルに、既に保存した levels.csv を優先利用する。
    csv = OUT_DIR / "qbit_5_levels.csv"
    if csv.exists():
        s = pd.read_csv(csv, parse_dates=["date"]).set_index("date")["level"]
        return s

    # CSVが無い場合のfallback：最小限の線を描くため、stats.jsonだけで描けないのでスキップ
    raise FileNotFoundError("qbit_5_levels.csv missing. Please run a snapshot that writes CSV first.")

def _save(s: pd.Series, name: str, title: str):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(s.index, s.values)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"qbit_5_{name}.png", dpi=160)
    plt.close(fig)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # levels.csv は src側のスナップ時に作るようにしても良いが、
    # 既存系と似せるなら src でCSVを出力する実装に寄せる方がシンプル。
    # ここでは既にある前提で画像だけ更新する。
    s = load_levels()
    _save(s.last("7D"),  "7d", "QBIT-5 (7D)")
    _save(s.last("35D"), "1m", "QBIT-5 (1M)")
    _save(s.last("400D"),"1y", "QBIT-5 (1Y)")

if __name__ == "__main__":
    main()
