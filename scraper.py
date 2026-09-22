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

def fetch_evalue_news():
    url = "https://www.evalue.com.tw/"
    news_items = []
    try:
        # EVALUE 通常將新聞放在 /news/ 路徑下
        res = requests.get(urllib.parse.urljoin(url, "news/"), headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.text.strip()
            
            # 確保抓取的是新聞內頁
            if title and len(title) > 4 and 'news' in href.lower():
                full_url = urllib.parse.urljoin(url, href)
                tag_string = extract_tags(title)
                news_items.append({
                    'cpo': 'EVALUE',
                    'date': datetime.date.today().strftime('%Y-%m-%d'),
                    'title': f"{title}{tag_string}",
                    'url': full_url
                })
        return list({item['url']: item for item in news_items}.values())[:5]
    except Exception as e:
        print(f"EVALUE 爬取失敗: {e}")
        return []

def fetch_cblok_news():
    url = "https://www.cblok.biz/news"
    news_items = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.text.strip()
            
            if title and len(title) > 4:
                # 篩選公告或新聞關鍵字
                if 'news' in href.lower() or 'article' in href.lower() or '公告' in title or '活動' in title:
                    full_url = urllib.parse.urljoin(url, href)
                    tag_string = extract_tags(title)
                    news_items.append({
                        'cpo': 'iCharging',
                        'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{tag_string}",
                        'url': full_url
                    })
        return list({item['url']: item for item in news_items}.values())[:5]
    except Exception as e:
        print(f"CBLOK 爬取失敗: {e}")
        return []

def fetch_upower_news():
    url = "https://www.u-power.com.tw/"
    news_items = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.text.strip()
            
            if title and len(title) > 5:
                if 'news' in href.lower() or 'event' in href.lower() or '公告' in title or '啟用' in title or '活動' in title:
                    full_url = urllib.parse.urljoin(url, href)
                    tag_string = extract_tags(title)
                    news_items.append({
                        'cpo': 'U-POWER',
                        'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{tag_string}",
                        'url': full_url
                    })
        return list({item['url']: item for item in news_items}.values())[:5]
    except Exception as e:
        print(f"U-POWER 爬取失敗: {e}")
        return []

if __name__ == '__main__':
    print("開始執行最新 CPO 陣列爬蟲任務...")
    # 將三家資料合併
    all_cpo_data = fetch_evalue_news() + fetch_cblok_news() + fetch_upower_news()
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_cpo_data, f, ensure_ascii=False, indent=4)
    
    print(f"成功！共抓取 {len(all_cpo_data)} 筆最新資料。")
