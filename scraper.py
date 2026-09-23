import json, datetime, requests, re, urllib.parse, os
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'}

def extract_tags(title):
    specs = []
    if re.search(r'360\s*kW|360k|500\s*kW|480\s*kW', title, re.IGNORECASE): specs.append('⚡超高速')
    if re.search(r'CCS1', title, re.IGNORECASE): specs.append('CCS1')
    if re.search(r'CCS2', title, re.IGNORECASE): specs.append('CCS2')
    if any(k in title for k in ['免費','回饋','優惠','折扣','點數']): specs.append('💰優惠活動')
    if any(k in title for k in ['上線','啟用','營運','新站']): specs.append('🎉新站情報')
    if any(k in title for k in ['電價','補助','法規','政策','規範','費率','綠能','電網']): specs.append('🏛️政策法規')
    return f" [{' | '.join(specs)}]" if specs else ""

def fetch_cpo_news(base_url, cpo_name, extra_keywords=None):
    news_items, keywords = [], ['news', 'event', '活動', '公告', '啟用', '上線']
    if extra_keywords: keywords.extend(extra_keywords)
    try:
        res = requests.get(base_url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        for a_tag in BeautifulSoup(res.text, 'html.parser').find_all('a', href=True):
            href, title = a_tag.get('href', ''), a_tag.text.strip()
            if title and len(title) > 4 and 'more' not in title.lower():
                if any(kw in href.lower() or kw in title for kw in keywords):
                    news_items.append({
                        'cpo': cpo_name, 'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{extract_tags(title)}", 'url': urllib.parse.urljoin(base_url, href)
                    })
        return list({item['url']: item for item in news_items}.values())[:5]
    except Exception as e:
        print(f"[{cpo_name}] 爬取失敗: {e}")
        return []

def fetch_policy_news():
    news_items = []
    policy_sources = [
        {"name": "台電", "url": "https://www.taipower.com.tw/tc/news.aspx?mid=17", "kws": ['電價', '電網', '供電', '費率']},
        {"name": "經濟部", "url": "https://www.moeaea.gov.tw/ECW/populace/news/NewsList.aspx?kind=1", "kws": ['補助', '綠能', '電動車', '充電', '能源']}
    ]
    for source in policy_sources:
        try:
            res = requests.get(source['url'], headers=HEADERS, timeout=15)
            res.encoding = 'utf-8'
            for a_tag in BeautifulSoup(res.text, 'html.parser').find_all('a', href=True):
                title = a_tag.text.strip()
                if len(title) > 5 and any(kw in title for kw in source['kws']):
                    href = a_tag.get('href', '')
                    news_items.append({
                        'cpo': source['name'], 'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{extract_tags(title)}", 'url': urllib.parse.urljoin(source['url'], href)
                    })
        except Exception as e:
            print(f"[{source['name']}] 政策爬取失敗: {e}")
    return list({item['url']: item for item in news_items}.values())[:4]

def generate_operational_data(pricing_data):
    """模擬串接遠傳充電樁作業管理平台，生成內部營運數據"""
    # 從費率設定自動計算全市場最低尖峰費率
    cpo_names = ['FET', 'EVALUE', 'iCharging', 'TAIL', 'U-POWER', 'YES']
    peak_prices = {cpo: (pricing_data[cpo]['peak'] if 'peak' in pricing_data[cpo] else pricing_data[cpo]['price']) for cpo in cpo_names}
    lowest_cpo = min(peak_prices, key=peak_prices.get)
    lowest_price = peak_prices[lowest_cpo]
    
    op_data = {
        "fet_stations": 68,
        "fet_growth_rate": "較上月成長 +12.5%",
        "lowest_peak_rate": lowest_price,
        "lowest_peak_cpo": "遠傳具備競爭優勢" if lowest_cpo == 'FET' else f"需注意 {lowest_cpo} 定價策略",
        "ocpp_availability": 99.6
    }
    with open('data/stations.json', 'w', encoding='utf-8') as f:
        json.dump(op_data, f, ensure_ascii=False, indent=4)

def init_v2_2_structure():
    os.makedirs('data', exist_ok=True)
    
    # 1. market.json
    all_data = fetch_policy_news()
    all_data += fetch_cpo_news("https://www.evalue.com.tw/news/", "EVALUE", ['detail'])
    all_data += fetch_cpo_news("https://www.cblok.biz/news", "iCharging")
    all_data += fetch_cpo_news("https://www.u-power.com.tw/", "U-POWER")
    all_data += fetch_cpo_news("https://www.tail.com.tw/", "TAIL 特爾電力")
    all_data += fetch_cpo_news("https://www.yes-energy.com.tw/", "YES!來電")
    with open('data/market.json', 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    # 2. pricing.json
    pricing = {
        'FET': {'type': 'TOU', 'peak': 10.9, 'offPeak': 6.8, 'holiday': 7.9, 'peakStart': 16, 'peakEnd': 21, 'color': '#ef4444'},
        'EVALUE': {'type': 'TOU', 'peak': 13.5, 'offPeak': 6.9, 'holiday': 8.5, 'peakStart': 16, 'peakEnd': 21, 'color': '#4CAF50'},
        'iCharging': {'type': 'TOU', 'peak': 12.0, 'offPeak': 6.5, 'holiday': 6.5, 'peakStart': 18, 'peakEnd': 21, 'color': '#ea580c'},
        'TAIL': {'type': 'TOU', 'peak': 11.9, 'offPeak': 8.9, 'holiday': 8.9, 'peakStart': 16, 'peakEnd': 21, 'color': '#0891b2'},
        'U-POWER': {'type': 'FLAT', 'price': 9.9, 'color': '#0369a1'},
        'YES': {'type': 'FLAT', 'price': 9.5, 'color': '#ca8a04'}
    }
    with open('data/pricing.json', 'w', encoding='utf-8') as f: json.dump(pricing, f, ensure_ascii=False, indent=4)
    
    # 3. price_history.json
    history = {
        "labels": ['2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08'],
        "datasets": { "FET": [12, 18, 25, 38, 52, 65], "U-POWER": [45, 48, 52, 55, 60, 68], "EVALUE": [80, 82, 85, 87, 89, 92], "TAIL": [35, 40, 48, 55, 58, 62] }
    }
    with open('data/price_history.json', 'w', encoding='utf-8') as f: json.dump(history, f, ensure_ascii=False, indent=4)
    
    # 4. stations.json (動態營運指標)
    generate_operational_data(pricing)
    
    # 5. 其他佔位檔
    for sf in ['operators.json', 'price_history_verified.json', 'cpo_profiles.json']:
        if not os.path.exists(os.path.join('data', sf)):
            with open(os.path.join('data', sf), 'w', encoding='utf-8') as f: json.dump([], f)

if __name__ == '__main__':
    print("🚀 啟動情報與營運資料聯合爬蟲...")
    init_v2_2_structure()
    print("✅ 內部營運資料庫 (stations.json) 更新完畢！")
