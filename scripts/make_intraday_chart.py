# -*- coding: utf-8 -*-
"""
QBIT-5 intraday chart builder (reads docs/outputs/qbit_5_intraday.csv)
- CSVは snapshot スクリプトが出力（index: timestamp_utc, col: pct_vs_open）
- 休場/データ薄い場合でもエラーにせず静かに終了
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, AutoMinorLocator

OUTPUT_DIR = "docs/outputs"
CSV_PATH   = os.path.join(OUTPUT_DIR, "qbit_5_intraday.csv")
IMG_PATH   = os.path.join(OUTPUT_DIR, "qbit_5_intraday.png")

JST = timezone(timedelta(hours=9))

def load():
    if not os.path.exists(CSV_PATH):
        print("intraday csv not found; skip chart")
        sys.exit(0)

    # 読み込み（index: timestamp_utc）
    df = pd.read_csv(CSV_PATH)
    if "timestamp_utc" in df.columns:
        dt = pd.to_datetime(df["timestamp_utc"], utc=True)
        df.index = dt
        df = df.drop(columns=["timestamp_utc"])
    else:
        # 古い形式への後方互換（index列が残ってくるケース）
        df.index = pd.to_datetime(df.index, utc=True)

    # 欠損・重複整理
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")].copy()

    # JSTへ（表示を日本時間に揃える）
    df.index = df.index.tz_convert(JST)

    # 列名を保証
    if "pct_vs_open" not in df.columns:
        # 旧: change_pct などがあれば拾っておく
        for c in ["change_pct", "pct", "value"]:
            if c in df.columns:
                df = df.rename(columns={c: "pct_vs_open"})
                break
    if "pct_vs_open" not in df.columns:
        print("no pct_vs_open column; skip chart")
        sys.exit(0)

    # データが薄いときは描画スキップ
    if len(df) < 10:
        print("intraday points < 10; skip chart")
        sys.exit(0)

    return df[["pct_vs_open"]].astype(float)


def style_dark():
    plt.rcParams.update({
        "figure.facecolor": "#0b1420",
        "axes.facecolor":   "#0b1420",
        "savefig.facecolor":"#0b1420",
        "axes.edgecolor":   "#1c2a3a",
        "axes.labelcolor":  "#cfe6f3",
        "xtick.color":      "#9fb6c7",
        "ytick.color":      "#9fb6c7",
        "grid.color":       "#1f2d3d",
        "font.size":        12,
        "axes.titleweight": "bold",
    })


def pct_formatter(x, pos):
    return f"{x:.1f}%"


def main():
    style_dark()
    df = load()

    last = float(df["pct_vs_open"].iloc[-1])
    up_color   = "#10b981"  # 緑
    down_color = "#fb7185"  # 赤
    line_color = up_color if last >= 0 else down_color
    fill_color = line_color

    # 滑らかさ向上（3分移動平均）
    s = df["pct_vs_open"].rolling(3, min_periods=1).mean()

    fig = plt.figure(figsize=(15, 8.5), dpi=150)
    ax  = fig.add_subplot(111)

    # グリッドを細かく
    ax.grid(True, which="major", linestyle="-", linewidth=0.8, alpha=0.6)
    ax.grid(True, which="minor", linestyle=":", linewidth=0.5, alpha=0.35)
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    # 0% ライン
    ax.axhline(0.0, color="#284056", linewidth=1.0)

    # ライン＆面
    ax.plot(s.index, s.values, linewidth=2.2, color=line_color)
    ax.fill_between(s.index, s.values, 0, where=None, alpha=0.16, color=fill_color)

    # 軸ラベル
    ax.set_ylabel("Change vs Open (%)")
    ax.yaxis.set_major_formatter(FuncFormatter(pct_formatter))

    # 余白
    ax.margins(x=0.01)

    # タイトル（JST）
    updated_jst = df.index[-1].astimezone(JST).strftime("%Y/%m/%d %H:%M (JST)")
    ax.set_title(f"QBIT-5 Intraday Snapshot ({updated_jst})", color="#e6f2fb", pad=14)

    # 上下に少し余裕
    ypad = max(1.0, (s.max() - s.min()) * 0.1)
    ax.set_ylim(s.min() - ypad, s.max() + ypad)

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.tight_layout()
    plt.savefig(IMG_PATH, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {IMG_PATH} (last={last:+.2f}%)")


if __name__ == "__main__":
    main()
