#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QBIT-5 intraday snapshot
- 統一基準: 当日始値比（Change vs Open, %）
- 出力:
  docs/outputs/qbit_5_levels.csv        … 当日分の時系列(level, chg_open_pct)
  docs/outputs/qbit_5_stats.json        … 最終時点の%など
  docs/outputs/qbit_5_post_intraday.txt … X投稿用の1行テキスト
  docs/outputs/last_run.txt             … 心拍（サイトのキャッシュバスター用）
"""

import os, json, io, math, time
from datetime import datetime, timedelta, timezone

import pandas as pd

# yfinanceはActionsで pip install yfinance==0.2.* 済み想定
import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(__file__))  # repo root
OUTD = os.path.join(ROOT, "docs", "outputs")
os.makedirs(OUTD, exist_ok=True)

# ===== 指数定義 =====
INDEX_KEY = "QBIT-5"
TICKERS   = ["IONQ", "QBTS", "RGTI", "ARQQ", "QUBT"]
BASE_DATE = "2024-01-02"  # 長期系の基準は参照値として残しておく

# ===== ツール =====
JST = timezone(timedelta(hours=9))
ET  = timezone(timedelta(hours=-5))  # 米国東部（ざっくり）※夏時間ズレは実用上このままでOK

def now_jst_str():
    return datetime.now(JST).strftime("%Y/%m/%d %H:%M (JST)")

def today_et_window():
    """米国当日00:00～翌日00:00(ET)でフィルタするためのUTC時間帯を返す。"""
    now_et = datetime.now(ET)
    start = now_et.replace(hour=0, minute=0, second=0, microsecond=0)
    end   = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

def _download_intraday(tickers):
    """
    できるだけ細かい足を取る（1分がダメなら5分）。
    yfinanceは複数銘柄同時DL → 'Adj Close' wide表 を返す。
    """
    for interval in ("1m", "5m"):
        try:
            df = yf.download(
                tickers=" ".join(tickers),
                period="5d",           # 当日分は必ず含まれるように広め
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=True,
            )
            if isinstance(df, pd.DataFrame) and "Adj Close" in df.columns:
                return df["Adj Close"].copy(), interval
        except Exception:
            pass
    raise RuntimeError("yfinance: intraday download failed")

def build_intraday_series():
    # 取得
    wide, interval = _download_intraday(TICKERS)  # index=UTC Timestamp, columns=tickers
    wide = wide.dropna(how="all")
    if wide.empty:
        raise RuntimeError("no price rows")

    # 当日(ET)だけに限定
    start_utc, end_utc = today_et_window()
    mask = (wide.index >= start_utc) & (wide.index < end_utc)
    wide = wide.loc[mask].dropna(how="all")
    if wide.empty:
        raise RuntimeError("no prices for today (ET)")

    # 各銘柄の「当日最初の有効値」で正規化
    norm = pd.DataFrame(index=wide.index)
    opens = {}
    for t in TICKERS:
        s = wide[t].dropna()
        if s.empty:
            continue
        open_px = s.iloc[0]
        opens[t] = float(open_px)
        norm[t] = s / open_px  # 始値=1.0 基準

    if norm.shape[1] == 0:
        raise RuntimeError("no usable series after normalization")

    # 等加重平均＝指数（始値=1.0）
    idx_norm = norm.mean(axis=1)

    # ％化（Change vs Open）
    chg_open_pct = (idx_norm - 1.0) * 100.0

    # 便利に1行で使えるテーブル
    out = pd.DataFrame({
        "level": idx_norm * 100.0,        # 任意のレベル。100=始値
        "chg_open_pct": chg_open_pct
    }, index=idx_norm.index)

    return out, interval

def save_outputs(df_today: pd.DataFrame):
    # 中間CSV（サイト/デバッグ用）
    csv_path = os.path.join(OUTD, "qbit_5_levels.csv")
    tmp = df_today.copy()
    tmp.index = tmp.index.tz_convert(JST)  # 表示上JSTにしておく
    tmp.index.name = "datetime_jst"
    tmp.to_csv(csv_path, float_format="%.6f")

    last_pct = float(tmp["chg_open_pct"].iloc[-1])

    # stats.json（サイトが読む想定のフィールドに寄せる）
    stats = {
        "key": INDEX_KEY,
        "pct_intraday": round(last_pct, 2),    # ←チャート最終点と一致
        "updated_at": datetime.now(JST).strftime("%Y/%m/%d %H:%M"),
        "unit": "pct",
        "last_level": round(float(tmp["level"].iloc[-1]), 2),
        "base_date": BASE_DATE,
        "tickers": TICKERS,
    }
    with open(os.path.join(OUTD, "qbit_5_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # X投稿テキスト（1行）
    sign = "+" if last_pct >= 0 else ""
    with open(os.path.join(OUTD, "qbit_5_post_intraday.txt"), "w", encoding="utf-8") as f:
        f.write(f"QBIT-5 {sign}{last_pct:.2f}% ({datetime.now(JST).strftime('%Y/%m/%d %H:%M')})\n")

    # 心拍
    with open(os.path.join(OUTD, "last_run.txt"), "w") as f:
        f.write(datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S"))

def main():
    df, interval = build_intraday_series()
    save_outputs(df)

if __name__ == "__main__":
    main()
