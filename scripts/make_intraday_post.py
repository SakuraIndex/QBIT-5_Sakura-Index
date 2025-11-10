#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QBIT-5 intraday.png を高品位なダークテーマで描画するスクリプト。
- 背景: #0b1420（サイトに合わせる）
- ライン色: 最終騰落率 >= 0 -> ティール, < 0 -> サーモン
- ゼロライン/グリッド/スパイン/凡例: ダーク向け調整
- DPI高め、アンチエイリアス、余白最適化
- 微小スムージング(3点移動平均, center=True)

入力:  docs/outputs/qbit_5_levels.csv   （Date/Level を想定。列名の揺らぎに耐性）
出力:  docs/outputs/qbit_5_intraday.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import timezone, timedelta

BASE = "docs/outputs"
LEVEL_CSV = os.path.join(BASE, "qbit_5_levels.csv")
OUT_PNG   = os.path.join(BASE, "qbit_5_intraday.png")

# サイト配色
BG       = "#0b1420"
PANEL    = "#0f1b28"
BORDER   = "#1c2a3a"
TEXT     = "#d4e9f7"
SUBTEXT  = "#9fb6c7"
UP       = "#22d3ee"   # ティール系（サイトのシアン寄せ）
DOWN     = "#fb7185"   # サーモン
ZERO     = "#334155"   # 0% 補助線

JST = timezone(timedelta(hours=9))


def _pick_col(df, keywords):
    ks = [k.lower() for k in keywords]
    for c in df.columns:
        cl = c.lower()
        if any(k in cl for k in ks):
            return c
    raise KeyError(f"column not found for keywords: {keywords} in {list(df.columns)}")


def load_series():
    df = pd.read_csv(LEVEL_CSV)
    dt_col = _pick_col(df, ["date", "time"])
    lv_col = _pick_col(df, ["level"])
    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
    df = df.dropna(subset=[dt_col, lv_col]).sort_values(dt_col)
    df = df.reset_index(drop=True)

    # 当日の変化率に準拠（先頭点基準）
    base = df[lv_col].iloc[0]
    pct = (df[lv_col] / base - 1.0) * 100.0

    # 見やすさのため 3点移動平均（形状は保持）
    pct_sm = pct.rolling(window=3, min_periods=1, center=True).mean()
    return df[dt_col], pct, pct_sm


def dark_axes(ax):
    # 背景・枠線・目盛のカラー
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.0)
    ax.tick_params(colors=TEXT, labelsize=10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=1))
    # グリッド（控えめ）
    ax.grid(True, which="major", color="#1f2b3a", alpha=0.55, linewidth=0.6)
    ax.grid(True, which="minor", color="#1f2b3a", alpha=0.35, linewidth=0.4)
    ax.minorticks_on()


def main():
    # データ読込
    x, pct_raw, pct = load_series()
    last = float(pct.iloc[-1])
    color = UP if last >= 0 else DOWN

    # 図の作成（高DPI＋広めアスペクト）
    plt.rcParams["figure.facecolor"] = BG
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    dark_axes(ax)

    # 0%ライン
    ax.axhline(0, color=ZERO, linewidth=1.1, alpha=0.9, zorder=1)

    # ライン本体
    line, = ax.plot(
        x, pct,
        color=color,
        linewidth=2.2,
        solid_capstyle="round",
        antialiased=True,
        zorder=3,
    )

    # 面を薄く塗る（視認性を少し補助）
    ax.fill_between(x, pct, 0, where=None, color=color, alpha=0.08, zorder=2)

    # 軸ラベル・タイトル
    ts_jst = x.iloc[-1].tz_localize("UTC").astimezone(JST) if x.iloc[-1].tzinfo is None else x.iloc[-1].astimezone(JST)
    ax.set_title(
        f"QBIT-5 Intraday Snapshot ({ts_jst:%Y/%m/%d %H:%M JST})",
        color=TEXT, fontsize=14, pad=10, weight="bold"
    )
    ax.set_xlabel("", color=SUBTEXT)
    ax.set_ylabel("Change vs Open (%)", color=SUBTEXT)

    # 余白を最適化
    plt.tight_layout()
    fig.savefig(OUT_PNG, facecolor=BG, bbox_inches="tight")
    plt.close(fig)

    print(f"saved: {OUT_PNG}  last={last:+.2f}% color={'UP' if last>=0 else 'DOWN'}")


if __name__ == "__main__":
    main()
