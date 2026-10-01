import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def fetch_evoasis_pricing():
    print("🔄 [爬蟲啟動] 正在前往 EVOASIS 官網抓取最新費率...")
    
    # EVOASIS 的電價公告頁面 (星晴電價/尖離峰)
    url = "https://www.evoasis.com.tw/post/activity-day_night"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 抓取頁面中所有的文字內容進行解析
        page_text = soup.get_text(separator="\n", strip=True)
        
        # 預設 EVOASIS 費率模板
        evoasis_pricing = {
            "type": "TOU",
            "peak": 10.0,
            "offPeak": 6.5,
            "holiday": 8.4,
            "peakStart": 16,
            "peakEnd": 21
        }
        
        # 🤖 透過正則表達式 (Regex) 自動捕捉最新數字
        # 1. 抓取尖峰費率 (例如：每度14.9元 或 每度12.5元)
        peak_match = re.search(r'尖峰費率.*?每度([\d\.]+)元', page_text)
        if peak_match:
            evoasis_pricing["peak"] = float(peak_match.group(1))
            
        # 2. 抓取離峰/星晴電價 (例如：每度6.5元)
        offpeak_match = re.search(r'星晴電價.*?每度([\d\.]+)元', page_text)
        if offpeak_match:
            evoasis_pricing["offPeak"] = float(offpeak_match.group(1))
            
        # 3. 抓取假日費率 (例如：每度8.4元)
        holiday_match = re.search(r'假日費率.*?每度([\d\.]+)元', page_text)
        if holiday_match:
            evoasis_pricing["holiday"] = float(holiday_match.group(1))
            
        # 4. 判斷當前是否為夏月 (6月~9月)，自動切換尖峰時間 (夏月16~22 / 非夏月15~21)
        current_month = datetime.now().month
        if 6 <= current_month <= 9:
            evoasis_pricing["peakStart"] = 16
            evoasis_pricing["peakEnd"] = 21
        else:
            evoasis_pricing["peakStart"] = 15
            evoasis_pricing["peakEnd"] = 20

        print(f"✅ [爬蟲成功] 取得 EVOASIS 最新費率: {evoasis_pricing}")
        return evoasis_pricing

    except Exception as e:
        print(f"❌ [爬蟲失敗] 無法解析 EVOASIS 網站: {e}")
        return None

# ==========================================
# 整合到您的定時任務中
# ==========================================
def update_cpo_pricing_db():
    print("正在更新 pricing.json 資料庫...")
    
    # 預設的其他 CPO 費率 (若有其他家爬蟲也可以寫在這邊組合)
    pricing_db = {
        "FET": {"type": "TOU", "peak": 10.9, "offPeak": 6.8, "holiday": 7.9, "peakStart": 16, "peakEnd": 21},
        "EVALUE": {"type": "TOU", "peak": 13.5, "offPeak": 6.9, "holiday": 8.5, "peakStart": 16, "peakEnd": 21},
        "TAIL": {"type": "TOU", "peak": 11.9, "offPeak": 8.9, "holiday": 8.9, "peakStart": 16, "peakEnd": 21},
        "U-POWER": {"type": "FLAT", "price": 9.9},
        "YES": {"type": "FLAT", "price": 9.5}
    }
    
    # 執行 EVOASIS 爬蟲
    evoasis_data = fetch_evoasis_pricing()
    if evoasis_data:
        pricing_db["EVOASIS"] = evoasis_data
        
    # 存入戰情室前端正在讀取的 json
    import os
    os.makedirs("data", exist_ok=True)
    with open("data/pricing.json", "w", encoding="utf-8") as f:
        json.dump(pricing_db, f, ensure_ascii=False, indent=2)
        
    print("🎉 資料庫更新完成，戰情室將顯示最新競品價格！")

# 單獨測試執行
if __name__ == "__main__":
    update_cpo_pricing_db()
