#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QBIT-5 intraday chart (equal-weight) for *today's US session*.

- その場で各構成銘柄の 1 分足を yfinance から取得
- 当日（US/Eastern）のデータだけを抽出
- 銘柄ごとの当日始値比を計算 → 等加重平均 → % 表示
- ダークテーマで高DPI描画（サイトと同配色）
- 上昇=ティール、下落=サーモンの自動色分け

Input  : なし（ネットから minute データ取得）
Output : docs/outputs/qbit_5_intraday.png
"""

import os
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import yfinance as yf
import pytz

# ---- config ---------------------------------------------------------------
TICKERS = ["IONQ", "QBTS", "RGTI", "ARQQ", "QUBT"]
BASE_DIR = "docs/outputs"
OUT_PNG = os.path.join(BASE_DIR, "qbit_5_intraday.png")

# dark theme (site palette)
BG      = "#0b1420"
BORDER  = "#1c2a3a"
TEXT    = "#d4e9f7"
SUBTEXT = "#9fb6c7"
UP      = "#22d3ee"
DOWN    = "#fb7185"
ZERO    = "#334155"

US_EAST = pytz.timezone("US/Eastern")
JST     = timezone(timedelta(hours=9))


# ---- helpers --------------------------------------------------------------
def _today_eastern_now():
    """US/Eastern の今日の日付オブジェクトを返す"""
    return datetime.now(tz=US_EAST).date()

def _load_1min_last_session(ticker: str) -> pd.Series:
    """
    指定ティッカーの 1分足 Close を取得し、
    US/Eastern の「直近の営業日」のデータだけを返す (Series[Datetime->float]).
    """
    # 2日分取って、直近営業日を切り出す（場中・場後どちらでも対応）
    df = yf.download(
        ticker, period="2d", interval="1m", auto_adjust=True,
        progress=False, prepost=False, threads=True
    )
    if df.empty:
        raise RuntimeError(f"empty minute data: {ticker}")

    # yfinance の index は tz-naive(UTC) or tz-aware(UTC) のことがある。UTC とみなし Eastern へ。
    idx_utc = pd.to_datetime(df.index, utc=True)
    idx_est = idx_utc.tz_convert(US_EAST)
    df = df.set_index(idx_est)
    df = df.sort_index()

    # 直近の営業日を求める（最終レコードの日付）
    last_est_day = df.index[-1].date()

    # 同日のみ抽出 & RTH(正規時間) でフィルタ（9:30–16:00）
    s = df["Close"].copy()
    s = s[s.index.date == last_est_day]
    s = s.between_time("09:30", "16:00")
    s.name = ticker
    return s.dropna()


def _compose_equal_weight(panels: list[pd.Series]) -> pd.DataFrame:
    """
    複数ティッカーの Series を時間で内部結合。等加重で合成し、
    当日始値比％の DataFrame を返す。
    """
    if not panels:
        raise RuntimeError("no panels")
    df = pd.concat(panels, axis=1, join="inner").sort_index()
    # 当日始値（その日の最初の値）で正規化
    opens = df.iloc[0]
    rel = df / opens  # 各列が 1.00 から始まる比率
    eqw = rel.mean(axis=1)
    pct = (eqw - 1.0) * 100.0
    # 見やすさのため 3点移動平均（形状は保持）
    pct_sm = pct.rolling(window=3, min_periods=1, center=True).mean()
    out = pd.DataFrame({"pct": pct_sm})
    return out


def _style_axes(ax):
    ax.set_facecolor(BG)
    for sp in ax.spines.values():
        sp.set_color(BORDER)
        sp.set_linewidth(1.0)
    ax.tick_params(colors=TEXT, labelsize=10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=1))
    ax.grid(True, which="major", color="#1f2b3a", alpha=0.55, linewidth=0.6)
    ax.grid(True, which="minor", color="#1f2b3a", alpha=0.35, linewidth=0.4)
    ax.minorticks_on()


# ---- main ----------------------------------------------------------------
def main():
    # 1) 各銘柄の 1 分足を取得
    panels = []
    for t in TICKERS:
        try:
            panels.append(_load_1min_last_session(t))
        except Exception as e:
            print(f"[warn] {t}: {e}")
    if len(panels) < 2:
        raise RuntimeError("failed to fetch minute data enough for composition")

    # 2) 等加重インデックス（当日始値比％）
    intraday = _compose_equal_weight(panels)
    last_pct = float(intraday["pct"].iloc[-1])
    color = UP if last_pct >= 0 else DOWN

    # 3) 描画
    plt.rcParams["figure.facecolor"] = BG
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    _style_axes(ax)

    # 0%ライン
    ax.axhline(0, color=ZERO, linewidth=1.1, alpha=0.9, zorder=1)

    # ライン
    ax.plot(
        intraday.index, intraday["pct"],
        color=color, linewidth=2.2, solid_capstyle="round", antialiased=True, zorder=3
    )
    ax.fill_between(intraday.index, intraday["pct"], 0, color=color, alpha=0.08, zorder=2)

    # x 軸を時間だけに（Eastern → JST をタイトルに付記）
    ax.set_xlabel("", color=SUBTEXT)
    ax.set_ylabel("Change vs Open (%)", color=SUBTEXT)
    # 目盛りを 30分刻み程度に
    ax.xaxis.set_major_locator(mticker.MaxNLocator(7))
    ax.tick_params(axis="x", rotation=0)

    ts_jst = intraday.index[-1].tz_convert(JST)
    ax.set_title(
        f"QBIT-5 Intraday Snapshot ({ts_jst:%Y/%m/%d %H:%M JST})",
        color=TEXT, fontsize=14, pad=10, weight="bold"
    )

    plt.tight_layout()
    os.makedirs(BASE_DIR, exist_ok=True)
    fig.savefig(OUT_PNG, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"saved: {OUT_PNG} last={last_pct:+.2f}%")

if __name__ == "__main__":
    main()
