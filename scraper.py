import json
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import cloudscraper # 💡 秘密武器：專門突破網站防火牆

# 共用標籤萃取
def extract_tags(title):
    specs = []
    if re.search(r'360\s*kW|360k|500\s*kW', title, re.IGNORECASE): specs.append('⚡超高速')
    if re.search(r'CCS1', title, re.IGNORECASE): specs.append('CCS1')
    if re.search(r'CCS2', title, re.IGNORECASE): specs.append('CCS2')
    if '免費' in title or '回饋' in title or '優惠' in title or '折扣' in title or '點數' in title: specs.append('💰優惠活動')
    if '上線' in title or '啟用' in title or '營運' in title or '新站' in title: specs.append('🎉新站情報')
    return f" [{' | '.join(specs)}]" if specs else ""

def fetch_evoasis_news():
    url = "https://www.evoasis.com.tw/latestnews/list"
    news_items = []
    try:
        # 💡 建立高階偽裝器，嘗試突破防火牆
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=15)
        response.encoding = 'utf-8'
        
        # 👇 抓蟲專用：印出狀態碼，看看是不是依然被擋
        print(f"EVOASIS 伺服器回傳狀態碼: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        print(f"EVOASIS 網頁解析到 {len(links)} 個連結") 
        
        for a_tag in links:
            href = a_tag['href']
            # 確保涵蓋所有大小寫情況
            if '/latestnews/' in href.lower() and not href.lower().endswith('/list'):
                title = a_tag.text.strip()
                if len(title) > 5 and "read" not in title.lower():
                    full_url = urllib.parse.urljoin(url, href)
                    tag_string = extract_tags(title)
                    news_items.append({
                        'cpo': 'EVOASIS',
                        'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{tag_string}",
                        'url': full_url
                    })
                    
        unique_news = list({item['url']: item for item in news_items}.values())
        return unique_news[:5]
    except Exception as e:
        print(f"EVOASIS 爬取失敗: {e}")
        return []

def fetch_upower_news():
    url = "https://www.u-power.com.tw/"
    news_items = []
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
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
                    
        unique_news = list({item['url']: item for item in news_items}.values())
        return unique_news[:5]
    except Exception as e:
        print(f"U-POWER 爬取失敗: {e}")
        return []

if __name__ == '__main__':
    print("開始執行雙重爬蟲任務...")
    evoasis_data = fetch_evoasis_news()
    upower_data = fetch_upower_news()
    
    all_cpo_data = evoasis_data + upower_data
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_cpo_data, f, ensure_ascii=False, indent=4)
    
    print(f"成功！寫入 EVOASIS ({len(evoasis_data)}筆), U-POWER ({len(upower_data)}筆)")
