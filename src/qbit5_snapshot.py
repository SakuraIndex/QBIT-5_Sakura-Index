# -*- coding: utf-8 -*-
"""
QBIT-5 snapshot generator (intraday-safe)
- 直近5営業日の1分足を取り、最新の取引日を自動判定
- 当日データが無い/薄い場合は前営業日にフォールバック
- Intraday系列を CSV 出力（scripts/make_intraday_chart.py が使用）
- stats.json（pct_intraday, updated_at, last_level）を更新
"""

import os
import sys
import json
import math
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import numpy as np
import yfinance as yf

JST = timezone(timedelta(hours=9))
ET = timezone(timedelta(hours=-5))  # ※米国夏時間でも yfinance Index がUTCのため日付判定は後段で安全にやる

# === 設定 ===
OUTPUT_DIR = "docs/outputs"
INTRADAY_CSV = os.path.join(OUTPUT_DIR, "qbit_5_intraday.csv")
LEVELS_CSV = os.path.join(OUTPUT_DIR, "qbit_5_levels.csv")
STATS_JSON = os.path.join(OUTPUT_DIR, "qbit_5_stats.json")

TICKERS = ["IONQ", "QBTS", "RGTI", "ARQQ", "QUBT"]

# 最低限「当日データがある」とみなすサンプル数（1分足）
MIN_SAMPLES_TODAY = 30  # 30分ぶん


def _ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def _now_jst_str():
    return datetime.now(JST).strftime("%Y/%m/%d %H:%M")


def _download_1m_last_days(tickers, days=5):
    frames = []
    for t in tickers:
        # period=5d, interval=1m を推奨。auto_adjust=True で分割調整後の価格を取得
        df = yf.download(
            t, period=f"{days}d", interval="1m",
            auto_adjust=True, prepost=False, progress=False, threads=False
        )
        if df is None or df.empty:
            continue
        # yfinanceはUTC index。Localize → ETに変換して日付判定に使う
        if df.index.tz is None:
            df.index = df.index.tz_localize(timezone.utc)
        df_et = df.copy()
        df_et.index = df_et.index.tz_convert(ET)
        df_et["DateET"] = df_et.index.date
        df_et["Ticker"] = t
        frames.append(df_et[["Close", "DateET", "Ticker"]])

        # API叩き過ぎ防止
        time.sleep(0.2)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, axis=0).sort_index()


def _select_latest_trading_date(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    直近の取引日（ET）のうち、サンプル数が MIN_SAMPLES_TODAY 以上の最新日を返す。
    見つからなければ空の DataFrame。
    """
    if df_all.empty:
        return df_all

    # 取引日ごとにサンプル数を計算
    counts = df_all.groupby("DateET").size().sort_index()
    # サンプルが十分な日だけ残す
    valid_days = [d for d, c in counts.items() if c >= MIN_SAMPLES_TODAY]
    if not valid_days:
        return pd.DataFrame()

    latest_day = valid_days[-1]
    return df_all[df_all["DateET"] == latest_day].copy()


def _make_equal_weight_intraday(df_day: pd.DataFrame) -> pd.DataFrame:
    """
    当日1分足（複数ティッカー）の DataFrame から
    等加重のインデックス「始値比（%）」の時系列を作る。
    """
    if df_day.empty:
        return df_day

    out = []
    # 同一 Timestamp（UTCだがET日付で揃っている）の各ティッカー終値をピボット
    pivot = df_day.pivot_table(
        index=df_day.index, columns="Ticker", values="Close", aggfunc="last"
    ).sort_index()

    # 各ティッカーの「当日オープン（最初のレコード）」で正規化 → 等加重平均
    open_vals = pivot.ffill().bfill().iloc[0]
    rel = pivot.div(open_vals) - 1.0  # ratio-1
    eq = rel.mean(axis=1) * 100.0     # %へ

    s = pd.Series(eq, name="pct_vs_open")
    s.index.name = "timestamp_utc"
    return s.to_frame()


def _load_last_level() -> float | None:
    if not os.path.exists(LEVELS_CSV):
        return None
    try:
        df = pd.read_csv(LEVELS_CSV)
        # level/close など列名のゆらぎを吸収
        for col in ["level", "Level", "close", "Close", "index_level"]:
            if col in df.columns:
                val = df[col].dropna().iloc[-1]
                return float(val)
    except Exception:
        pass
    return None


def main():
    _ensure_dir(OUTPUT_DIR)

    # 1) 直近5営業日の1分足を取得（空なら休場/エラー）
    df_all = _download_1m_last_days(TICKERS, days=5)
    if df_all.empty:
        print("no intraday data for last 5 days; market likely closed or API empty")
        # 休場などは正常終了（チャートは前回のままにする）
        sys.exit(0)

    # 2) サンプル数のある**最新取引日**を特定（当日が無ければ前日）
    df_day = _select_latest_trading_date(df_all)
    if df_day.empty:
        print("no sufficiently-sampled trading day found; skipping without error")
        sys.exit(0)

    # 3) 当日インデックスの「始値比(%)」時系列を作成
    intraday = _make_equal_weight_intraday(df_day)
    if intraday.empty:
        print("intraday series empty; skipping without error")
        sys.exit(0)

    # 4) CSVとして保存（チャート生成スクリプトが読み込む）
    intraday.to_csv(INTRADAY_CSV, index=True)

    # 5) stats.json を更新（pct_intraday / updated_at / last_level）
    pct_intraday = float(intraday["pct_vs_open"].iloc[-1])
    updated_at = _now_jst_str()
    last_level = _load_last_level()

    stats = {
        "key": "QBIT-5",
        "pct_intraday": round(pct_intraday, 2),
        "updated_at": updated_at,
        "unit": "pct",
        "last_level": None if (last_level is None or math.isnan(last_level)) else round(last_level, 2),
        "tickers": TICKERS,
    }

    with open(STATS_JSON, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # 6) 走行記録
    with open(os.path.join(OUTPUT_DIR, "last_run.txt"), "w", encoding="utf-8") as f:
        f.write(f"intraday snapshot OK @ {updated_at}\n")

    print("snapshot done; intraday.csv + stats.json written.")


if __name__ == "__main__":
    main()
