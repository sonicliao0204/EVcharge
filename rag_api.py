import json
import os
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

# 1. 建立一個自動抓取費率的函數
def auto_fetch_cpo_prices():
    print("🔄 [系統排程] 啟動自動抓取各家 CPO 最新費率...")
    
    # 這裡存放解析後的最新價格
    updated_pricing = {}
    
    try:
        # =========================================
        # 🤖 模擬爬蟲邏輯：自動去 EVOASIS 等網站抓取
        # =========================================
        # 實務上這裡會用 requests 或 Playwright 去解析官網 DOM 或隱藏 API
        # res = requests.get("https://www.evoasis.com.tw/pricing")
        # soup = BeautifulSoup(res.text, "html.parser")
        # peak_price = soup.find("div", id="peak-price").text ... 
        
        # 假設我們爬蟲抓到了最新數據：
        updated_pricing = {
            "FET": {"type": "TOU", "peak": 10.9, "offPeak": 6.8, "holiday": 7.9, "peakStart": 16, "peakEnd": 21},
            "EVALUE": {"type": "TOU", "peak": 13.5, "offPeak": 6.9, "holiday": 8.5, "peakStart": 16, "peakEnd": 21},
            "EVOASIS": {"type": "TOU", "peak": 11.5, "offPeak": 7.5, "holiday": 7.5, "peakStart": 16, "peakEnd": 21}, # 🆕 自動抓到的 EVOASIS
            "U-POWER": {"type": "FLAT", "price": 9.9}
        }

        # 2. 自動覆寫到戰情室前端在讀取的 pricing.json
        os.makedirs("data", exist_ok=True)
        with open("data/pricing.json", "w", encoding="utf-8") as f:
            json.dump(updated_pricing, f, ensure_ascii=False, indent=2)
            
        print("✅ [系統排程] 最新費率已更新至資料庫！戰情室將自動顯示最新價格。")
        
    except Exception as e:
        print(f"❌ [系統排程] 抓取失敗: {e}")

# 3. 設定 FastAPI 啟動時，連帶啟動定時爬蟲
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 伺服器啟動時執行
    scheduler = BackgroundScheduler()
    # 設定每天凌晨 02:00 自動去抓一次價格
    scheduler.add_job(auto_fetch_cpo_prices, 'cron', hour=2, minute=0)
    scheduler.start()
    
    # 啟動時先強制跑一次，確保資料是最新的
    auto_fetch_cpo_prices()
    
    yield
    # 伺服器關閉時執行
    scheduler.shutdown()

# 將 lifespan 綁定到您的 FastAPI APP
app = FastAPI(title="充電樁戰情室 Backend", lifespan=lifespan)

# ... (下方保留您原本的路由設定) ...
