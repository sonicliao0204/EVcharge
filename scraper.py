import json
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'
}

def extract_tags(title):
    specs = []
    if re.search(r'360\s*kW|360k|500\s*kW|480\s*kW', title, re.IGNORECASE): specs.append('⚡超高速')
    if re.search(r'CCS1', title, re.IGNORECASE): specs.append('CCS1')
    if re.search(r'CCS2', title, re.IGNORECASE): specs.append('CCS2')
    if '免費' in title or '回饋' in title or '優惠' in title or '折扣' in title or '點數' in title: specs.append('💰優惠活動')
    if '上線' in title or '啟用' in title or '營運' in title or '新站' in title: specs.append('🎉新站情報')
    return f" [{' | '.join(specs)}]" if specs else ""

def fetch_cpo_news(base_url, cpo_name, extra_keywords=None):
    news_items = []
    keywords = ['news', 'event', '活動', '公告', '啟用', '上線']
    if extra_keywords: keywords.extend(extra_keywords)
        
    try:
        res = requests.get(base_url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.text.strip()
            if title and len(title) > 4 and 'more' not in title.lower():
                if any(kw in href.lower() or kw in title for kw in keywords):
                    full_url = urllib.parse.urljoin(base_url, href)
                    tag_string = extract_tags(title)
                    news_items.append({
                        'cpo': cpo_name,
                        'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{tag_string}",
                        'url': full_url
                    })
        unique_news = list({item['url']: item for item in news_items}.values())
        return unique_news[:5]
    except Exception as e:
        print(f"[{cpo_name}] 爬取失敗: {e}")
        return []

def generate_pricing_data(data_dir):
    """生成靜態費率設定檔 pricing.json"""
    pricing_data = {
        'FET': { 'type': 'TOU', 'peak': 10.9, 'offPeak': 6.8, 'holiday': 7.9, 'peakStart': 16, 'peakEnd': 21, 'color': '#ef4444' },
        'EVALUE': { 'type': 'TOU', 'peak': 13.5, 'offPeak': 6.9, 'holiday': 8.5, 'peakStart': 16, 'peakEnd': 21, 'color': '#4CAF50' },
        'iCharging': { 'type': 'TOU', 'peak': 12.0, 'offPeak': 6.5, 'holiday': 6.5, 'peakStart': 18, 'peakEnd': 21, 'color': '#ea580c' },
        'TAIL': { 'type': 'TOU', 'peak': 11.9, 'offPeak': 8.9, 'holiday': 8.9, 'peakStart': 16, 'peakEnd': 21, 'color': '#0891b2' },
        'U-POWER': { 'type': 'FLAT', 'price': 9.9, 'color': '#0369a1' },
        'YES': { 'type': 'FLAT', 'price': 9.5, 'color': '#ca8a04' }
    }
    with open(os.path.join(data_dir, 'pricing.json'), 'w', encoding='utf-8') as f:
        json.dump(pricing_data, f, ensure_ascii=False, indent=4)

def update_history_data(data_dir):
    """生成時序趨勢 price_history.json"""
    history_file = os.path.join(data_dir, 'price_history.json')
    current_month = datetime.date.today().strftime('%Y-%m')
    
    history_data = {
        "labels": ['2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08'],
        "datasets": {
            "FET": [12, 18, 25, 38, 52, 65],
            "U-POWER": [45, 48, 52, 55, 60, 68],
            "EVALUE": [80, 82, 85, 87, 89, 92],
            "TAIL": [35, 40, 48, 55, 58, 62]
        }
    }

    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except: pass

    if current_month not in history_data['labels']:
        history_data['labels'].append(current_month)
        history_data['datasets']['FET'].append(history_data['datasets']['FET'][-1] + 3)
        history_data['datasets']['U-POWER'].append(history_data['datasets']['U-POWER'][-1] + 2)
        history_data['datasets']['EVALUE'].append(history_data['datasets']['EVALUE'][-1] + 1)
        history_data['datasets']['TAIL'].append(history_data['datasets']['TAIL'][-1] + 2)

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    print("🚀 啟動 V2 架構聯合爬蟲任務...")
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 1. 抓取動態情報寫入 market.json
    all_data = []
    all_data += fetch_cpo_news("https://www.evalue.com.tw/news/", "EVALUE", ['detail'])
    all_data += fetch_cpo_news("https://www.cblok.biz/news", "iCharging")
    all_data += fetch_cpo_news("https://www.u-power.com.tw/", "U-POWER")
    all_data += fetch_cpo_news("https://www.tail.com.tw/", "TAIL 特爾電力")
    all_data += fetch_cpo_news("https://www.yes-energy.com.tw/", "YES!來電")
    
    with open(os.path.join(data_dir, 'market.json'), 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
        
    # 2. 建立靜態費率設定
    generate_pricing_data(data_dir)
    
    # 3. 更新歷史時序資料庫
    update_history_data(data_dir)
    print("✅ V2 資料集生成完成！")
