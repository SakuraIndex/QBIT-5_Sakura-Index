# scripts/make_intraday_post.py
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "outputs"
STATS = OUT / "qbit_5_stats.json"

def jst_now_str():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y/%m/%d %H:%M (JST)")

def fmt_pct(x: float) -> str:
    # 表示は小数点2桁、符号付き
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.2f}%"

def main():
    if not STATS.exists():
        raise FileNotFoundError(f"stats not found: {STATS}")

    data = json.loads(STATS.read_text(encoding="utf-8"))

    # 互換フィールド名：pct_intraday / rtn_intraday など
    pct = None
    for k in ["pct_intraday", "intraday_pct", "change_pct", "pct", "rtn_pct"]:
        v = data.get(k)
        if isinstance(v, (int, float)):
            pct = float(v)
            break
    if pct is None:
        raise RuntimeError("pct_intraday missing in stats")

    tickers = data.get("tickers", [])
    tickers_str = ",".join(tickers) if tickers else "IONQ,QBTS,RGTI,ARQQ,QUBT"

    # 見出し・本文
    title = "【QBIT-5｜量子コンピューター指数】"
    line1 = f"本日: {fmt_pct(pct)}"
    last_level = data.get("last_level")
    line2 = f"指数: {last_level:.2f}" if isinstance(last_level, (int, float)) else ""
    line3 = f"構成: {tickers_str}"
    ts = data.get("updated_at") or jst_now_str()
    footer = f"更新: {ts}"
    hashtags = "#桜Index #QBIT5"

    body = "\n".join([title, line1, line2, line3, hashtags])

    # 2 か所に同一内容を書き出す（サイト側は post_intraday.txt を見に行く場合があるため）
    targets = [
        OUT / "qbit_5_post_intraday.txt",
        OUT / "post_intraday.txt",
    ]
    for p in targets:
        p.write_text(body, encoding="utf-8")

    print("written:", ", ".join(str(p) for p in targets))

if __name__ == "__main__":
    main()
