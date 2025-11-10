#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import json

OUT_DIR = Path("docs/outputs")

TEMPLATE = """【QBIT-5｜量子コンピューター指数】
本日: {pct:+.2f}%
状況: {level:.1f}
構成: IONQ/QBTS/RGTI/ARQQ/QUBT
#桜Index #QBIT5"""

def main():
    js = json.loads((OUT_DIR / "qbit_5_stats.json").read_text())
    text = TEMPLATE.format(pct=js["pct_intraday"], level=js["last_level"])
    (OUT_DIR / "post_intraday.txt").write_text(text, encoding="utf-8")
    print(text)

if __name__ == "__main__":
    main()
