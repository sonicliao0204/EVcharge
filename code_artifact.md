# 台灣充電站情報自動化系統

## 專案簡介
這是一個自動爬取台灣各大充電營運商 (CPO) 網站最新消息的爬蟲系統。系統會定期抓取各家業者的最新站點、電價異動與優惠活動資訊，並將結構化的資料轉換為直覺的靜態網頁，最後透過 GitHub Actions 達成每天自動排程執行與網頁更新。

## 檔案結構說明
專案包含以下核心檔案：

* **`scraper.py`**：Python 爬蟲主程式。負責執行網頁抓取邏輯，處理資料後輸出成 JSON 格式。
* **`data.json`**：爬蟲產生的資料儲存檔，也是前端網頁讀取的輕量級資料庫。
* **`index.html`**：網頁前端介面。透過 JavaScript 自動讀取 `data.json` 並將情報以表格形式呈現。
* **`requirements.txt`**：Python 相依套件清單，記錄本專案需要的外部函式庫（如 `requests`, `beautifulsoup4`）。

## 如何在本地端執行

若要在本地端測試或開發此專案，請依照以下步驟進行：

### 1. 建立虛擬環境 (建議)
為了保持開發環境乾淨，建議先建立 Python 虛擬環境：
```bash
python -m venv venv
```

啟動虛擬環境：
* **Windows**:
  ```bash
  venv\Scripts\activate
  ```
* **Mac / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 2. 安裝相依套件
請確保終端機路徑位於專案資料夾下，執行以下指令安裝所需套件：
```bash
pip install -r requirements.txt
```

### 3. 執行爬蟲更新資料
執行爬蟲程式以抓取最新資訊並生成（或覆蓋）`data.json`：
```bash
python scraper.py
```

### 4. 啟動本地測試伺服器
為了正常預覽帶有本地 JSON 讀取功能的靜態網頁，請啟動 Python 內建的微型伺服器：
```bash
python -m http.server
```
啟動後，請打開瀏覽器並前往 `http://localhost:8000` 即可查看最新的充電情報網頁。

---

**開發者**：Sonic 廖繼文