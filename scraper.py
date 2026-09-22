import json
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

HEADERS = {
    # 換一組更新的 User-Agent，避免被當成機器人擋下來
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

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
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # 💡 終極解法：使用 response.content 取得最原始資料，讓 BeautifulSoup 自己判斷編碼
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # 加入 lower() 避免網址大小寫改變導致抓不到
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
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # 💡 終極解法：同樣使用 response.content
        soup = BeautifulSoup(response.content, 'html.parser')
        
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
    print("開始抓取各家 CPO 真實資料...")
    evoasis_data = fetch_evoasis_news()
    upower_data = fetch_upower_news()
    
    all_cpo_data = evoasis_data + upower_data
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_cpo_data, f, ensure_ascii=False, indent=4)
    
    print("成功！已輸出防呆版資料。")
