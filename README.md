# QBIT-5 — Quantum Computing 5 Index

- **構成**: IONQ, QBTS, RGTI, ARQQ, QUBT（等加重）
- **基準日**: 2024-01-02 (=100)
- **出力**: `docs/outputs/`
  - `qbit_5_stats.json` … `pct_intraday`, `updated_at`, `last_level`
  - `qbit_5_post_intraday.txt` … 「QBIT-5 +1.23% (YYYY/MM/DD HH:MM)」
  - `qbit_5_intraday.png`, `qbit_5_7d.png`, `qbit_5_1m.png`, `qbit_5_1y.png`
  - `last_run.txt`
  - `qbit_5_levels.csv`

### 初回手動実行
1. Actions > **QBIT-5 Intraday** → Run workflow  
2. その後 **QBIT-5 Long Charts** → Run workflow  
3. `docs/outputs/*` が生成され、サイトが画像・数値を拾える状態になります
