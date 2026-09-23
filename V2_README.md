# EVcharge V2.0

## 定位
EV Charging Intelligence｜台灣電動車充電產業情報戰情室

V2.0 將原本的「動態情報牆／競品定價／詳細費率」升級為：
- 戰情 Dashboard
- 市場情報
- 價格情報
- Technical Intelligence
- OCPP Log Analyzer（目前為瀏覽器端規則引擎）
- Case Study

## 部署
保留原本 GitHub Actions 與 scraper.py。將本專案內容覆蓋到原 `EVcharge` repository 後即可使用。

## 下一階段
1. 將價格資料移出 index.html，改成 pricing.json。
2. 增加價格歷史資料 price_history.json。
3. 增加 CPO profiles / 站點資料。
4. 接入真正的地圖與站點 API。
5. OCPP Log Analyzer 再接 AI API。
6. 增加 SEO、Open Graph、favicon、網站統計。
