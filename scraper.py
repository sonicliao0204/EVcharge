import json
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

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
    if extra_keywords:
        keywords.extend(extra_keywords)
        
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

if __name__ == '__main__':
    print("🚀 啟動 5 大 CPO 聯合爬蟲任務...")
    
    all_data = []
    all_data += fetch_cpo_news("https://www.evalue.com.tw/news/", "EVALUE", ['detail'])
    all_data += fetch_cpo_news("https://www.cblok.biz/news", "iCharging")
    all_data += fetch_cpo_news("https://www.u-power.com.tw/", "U-POWER")
    all_data += fetch_cpo_news("https://www.tail.com.tw/", "TAIL 特爾電力")
    all_data += fetch_cpo_news("https://www.yes-energy.com.tw/", "YES!來電")
    
    # 確保資料直接寫入最外層，不使用任何資料夾
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 成功！共抓取 {len(all_data)} 筆最新資料。")
