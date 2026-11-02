# EVcharge

> 狀態：開發中（WIP）。本檔為根目錄統一入口 README，細節請見 `V2.1_README.md`。

## 這是什麼（推測）
依現有程式碼與 `V2.1_README.md` 判讀，這是一個**台灣充電樁資訊 / 費率**相關的網站：
- 前端為靜態頁面（`index.html` + `js/`），可直接用 GitHub Pages 部署，不需後端。
- 後端工具為 Python：爬取市場情報、串接 TDX 交通資料、更新站點，並以 RAG API 對接 AI。

（以上「用途」為依檔名與說明推斷，非官方定位，歡迎修正。）

## 目錄結構（現狀）
- `index.html`、`js/` — 前端介面
- `data/`、`data.json` — 資料（依 `V2.1_README` 描述含 `market.json` / `pricing.json` / `operators.json` / `price_history.json` 等）
- `rag_api.py` — RAG / AI 介接
- `scraper.py` — 市場情報爬蟲（保留舊資料、只更新新資料）
- `tdx_pipeline.py` — TDX 資料管線
- `update_stations.py` — 站點更新
- `requirements.txt` — Python 依賴：`requests`、`beautifulsoup4`、`playwright`
- `CCS/`、`scripts/`、`code_artifact.md` — 其他資源
- `V2_README.md`、`V2.1_README.md` — 版本開發筆記

## ⚠️ 資料真實性警示（重要）
`pricing.json` 與 `price_history.json` 目前**仍延續 V2 Prototype 的「示範數值」**，並非來自各 CPO 官方費率、站點條件或可驗證日期的已驗證市場歷史。
**正式對外使用前，請以官方來源建立真實 snapshot（如 `pricing_snapshots.json`），切勿把 prototype 數據當成已驗證市場資料。**

## 開發路線（摘自 V2.1_README）
1. 以官方來源建立 `pricing_snapshots.json`
2. 增加站點資料與地圖
3. 建立 CPO 個別情報頁
4. 將 OCPP Log Analyzer 接 AI API
5. 增加搜尋、SEO、Open Graph、favicon 與網站分析

## 部署
靜態 GitHub Pages 即可，不需要後端。
