from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime

app = FastAPI(title="充電樁戰情室 Backend (PlugShare 企業版)")

# 允許跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 data 資料夾
os.makedirs("data", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")

# CPO 名稱標準化處理
def standardize_cpo_name(raw_name):
    name = str(raw_name).upper()
    if "EVOASIS" in name or "源點" in name: return "EVOASIS"
    if "U-POWER" in name or "旭電馳" in name: return "U-POWER"
    if "EVALUE" in name or "華城" in name: return "EVALUE"
    if "TAIL" in name or "特爾" in name: return "TAIL"
    if "ICHARGING" in name or "中興" in name: return "iCharging"
    if "YES" in name or "裕電" in name: return "YES"
    if "FET" in name or "遠傳" in name: return "FET"
    return raw_name

# 🔌 全新 PlugShare 抓取引擎
@app.post("/sync_plugshare")
async def sync_plugshare():
    url = "https://api.plugshare.com/v3/locations/region"
    params = {
        "latitude": 23.8,  # 台灣中心點
        "longitude": 120.9,
        "spanLat": 4.0,    # 涵蓋全台
        "spanLng": 3.0,
        "count": 2500      # 提高上限以容納全台站點
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": "Basic d2ViX3YyOkVOanNuUE54NHhXeHVkODU="
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        res.raise_for_status()
        locations = res.json()
        
        clean_dataset = []
        for loc in locations:
            name = loc.get("name", "未命名站點")
            raw_cpo = loc.get("network", {}).get("name", "未知") if loc.get("network") else "未知"
            cpo = standardize_cpo_name(raw_cpo)
            
            lat = loc.get("latitude", 0)
            lng = loc.get("longitude", 0)
            
            max_kw = 0
            total_plugs = 0
            is_available = False
            is_charging = False
            is_faulted = False
            
            for st in loc.get("stations", []):
                for out in st.get("outlets", []):
                    total_plugs += 1
                    kw = out.get("kilowatts")
                    if kw is not None and kw > max_kw:
                        max_kw = kw
                        
                    status_code = out.get("status")
                    if status_code == 1: is_available = True
                    elif status_code == 2: is_charging = True
                    elif status_code == 3: is_faulted = True
            
            if is_faulted and not is_available and not is_charging:
                final_status = "Faulted"
            elif is_available:
                final_status = "Available"
            elif is_charging:
                final_status = "Charging"
            else:
                final_status = "Offline"
                
            clean_dataset.append({
                "id": str(loc.get("id", "")),
                "name": name,
                "cpo": cpo,
                "lat": float(lat),
                "lng": float(lng),
                "total_kw": max_kw,
                "total_plugs": total_plugs,
                "status": final_status,
                "updated_at": datetime.now().isoformat()
            })
        
        with open("data/stations_live.json", "w", encoding="utf-8") as f:
            json.dump(clean_dataset, f, ensure_ascii=False, indent=2)
            
        return {"status": "success", "message": "PlugShare 資料同步完成", "count": len(clean_dataset)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LogData(BaseModel):
    log_content: str

@app.post("/analyze_log")
async def analyze_log(data: LogData):
    return {"diagnosis_html": f"<strong>✅ 後端接收成功</strong><br><br>系統分析內容：{data.log_content[:20]}..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
