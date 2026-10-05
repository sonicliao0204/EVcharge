import os
import json
import requests
import traceback
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import email.utils

# 抓取目前目錄下的 data 資料夾
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def extract_cpo(loc):
    net_name = str((loc.get("network") or {}).get("name") or "").upper()
    name = str(loc.get("name") or "").upper()
    desc = str(loc.get("description") or "").upper()
    addr = str(loc.get("address") or "").upper()
    combined = f"{net_name} {name} {desc} {addr}"

    if any(k in combined for k in ["TESLA", "特斯拉", "SUPERCHARGER"]): return "Tesla"
    if any(k in combined for k in ["EVOASIS", "源點"]): return "EVOASIS"
    if any(k in combined for k in ["U-POWER", "UPOWER", "旭電馳"]): return "U-POWER"
    if any(k in combined for k in ["EVALUE", "華城"]): return "EVALUE"
    if any(k in combined for k in ["TAIL", "特爾"]): return "TAIL"
    if any(k in combined for k in ["ICHARGING", "中興", "嘟嘟房"]): return "iCharging"
    if any(k in combined for k in ["YES", "裕電", "YES!"]): return "YES"
    if any(k in combined for k in ["FET", "遠傳"]): return "FET"
    if any(k in combined for k in ["NOODOE", "拓連"]): return "Noodoe"
    if any(k in combined for k in ["NHOA", "TCC", "台泥"]): return "台泥NHOA"
    if any(k in combined for k in ["星舟", "TITAN", "泓德"]): return "星舟快充"
    if any(k in combined for k in ["中油", "CPC"]): return "台灣中油"
    if any(k in combined for k in ["USPACE", "悠勢"]): return "USPACE"
    if any(k in combined for k in ["LINBROS", "領鹿"]): return "領鹿"
    if any(k in combined for k in ["PORSCHE", "保時捷"]): return "Porsche"
    if any(k in combined for k in ["AUDI", "奧迪"]): return "Audi"
    if any(k in combined for k in ["BMW", "賓士", "MERCEDES", "VOLVO", "HYUNDAI", "KIA"]): return "車廠原廠"
    if any(k in combined for k in ["飯店", "酒店", "HOTEL", "RESORT", "民宿", "莊園", "會館"]): return "飯店民宿自備"
    if any(k in combined for k in ["停車場", "公有", "區公所", "地下室", "立體"]): return "公有及自設"
    return "其他"

def update_stations():
    print("🚀 正在執行全台 5 大地理網格深度掃描...")
    url = "https://api.plugshare.com/v3/locations/region"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Authorization": "Basic d2ViX3YyOkVOanNuUE54NHhXeHVkODU="
    }
    
    regions = [
        {"name": "北部", "latitude": 25.04, "longitude": 121.53, "spanLat": 0.9, "spanLng": 1.2},
        {"name": "中苗", "latitude": 24.30, "longitude": 120.75, "spanLat": 0.9, "spanLng": 1.2},
        {"name": "嘉南", "latitude": 23.35, "longitude": 120.35, "spanLat": 0.9, "spanLng": 1.2},
        {"name": "高屏", "latitude": 22.55, "longitude": 120.45, "spanLat": 0.9, "spanLng": 1.2},
        {"name": "東部", "latitude": 23.90, "longitude": 121.50, "spanLat": 1.8, "spanLng": 1.0}
    ]
    
    collected = {}
    for r in regions:
        try:
            params = {"latitude": r["latitude"], "longitude": r["longitude"], "spanLat": r["spanLat"], "spanLng": r["spanLng"], "count": 500}
            res = requests.get(url, headers=headers, params=params, timeout=15)
            if res.status_code == 200:
                for item in res.json():
                    sid = str(item.get("id"))
                    if sid: collected[sid] = item
        except Exception as e:
            print(f"網格 {r['name']} 採集警告: {e}")

    dataset = []
    for loc in collected.values():
        name = loc.get("name") or "未命名站點"
        cpo = extract_cpo(loc)
        lat = float(loc.get("latitude") or 0.0)
        lng = float(loc.get("longitude") or 0.0)
        
        max_kw = 0.0
        total_plugs = 0
        is_avail, is_chg, is_fault = False, False, False
        
        for st in (loc.get("stations") or []):
            for out in (st.get("outlets") or []):
                total_plugs += 1
                kw = out.get("kilowatts")
                if kw is not None:
                    try:
                        val = float(kw)
                        if val > max_kw: max_kw = val
                    except: pass
                code = out.get("status")
                if code == 1: is_avail = True
                elif code == 2: is_chg = True
                elif code == 3: is_fault = True
                
        status = "Faulted" if (is_fault and not is_avail) else ("Available" if is_avail else ("Charging" if is_chg else "Offline"))

        dataset.append({
            "id": str(loc.get("id", "")),
            "name": name,
            "cpo": cpo,
            "lat": lat,
            "lng": lng,
            "total_kw": max_kw,
            "total_plugs": total_plugs,
            "status": status,
            "updated_at": datetime.now().isoformat()
        })
        
    out_path = os.path.join(DATA_DIR, "stations.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"✅ 站點儲存完成，共 {len(dataset)} 站 -> {out_path}")

def update_news():
    print("📰 正在抓取市場即時情報...")
    try:
        url = "https://news.google.com/rss/search?q=%E9%9B%BB%E5%8B%95%E8%BB%8A+%E5%85%85%E9%9B%BB%E7%AB%99+when:7d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        root = ET.fromstring(req.content)
        
        news_list = []
        for item in root.findall('.//item')[:12]:
            title = item.find('title').text
            link = item.find('link').text
            pub_date_raw = item.find('pubDate').text if item.find('pubDate') is not None else ""
            pub_date_formatted = "近期"
            if pub_date_raw:
                try:
                    dt = email.utils.parsedate_to_datetime(pub_date_raw)
                    dt_tw = dt.astimezone(timezone(timedelta(hours=8)))
                    pub_date_formatted = dt_tw.strftime("%Y-%m-%d %H:%M")
                except:
                    pub_date_formatted = pub_date_raw

            cpo = extract_cpo({"name": title})
            if cpo in ["其他", "公有及自設", "飯店民宿自備"]: cpo = "產業動態"
            news_list.append({"title": title, "url": link, "cpo": cpo, "date": pub_date_formatted})
            
        out_path = os.path.join(DATA_DIR, "news.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        print(f"✅ 情報儲存完成，共 {len(news_list)} 則 -> {out_path}")
    except Exception as e:
        print(f"抓取新聞異常: {e}")

if __name__ == "__main__":
    update_stations()
    update_news()
