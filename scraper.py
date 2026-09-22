import json
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse # 💡 新增這個官方套件，專門用來完美組合相對/絕對網址

# 共同的請求標頭，偽裝成真實瀏覽器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
}

def extract_tags(title):
    """從標題自動判斷硬體規格與活動類型"""
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
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # 篩選出真實的新聞內頁連結
            if '/latestnews/' in href and href != '/latestnews/list':
                title = a_tag.text.strip()
                if len(title) > 5 and "Read More" not in title:
                    # 💡 使用 urljoin 自動且完美地組合出網址
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
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.text.strip()
            
            if title and len(title) > 5:
                if 'news' in href.lower() or 'event' in href.lower() or '公告' in title or '啟用' in title or '活動' in title:
                    # 💡 同樣使用 urljoin 處理 U-POWER 的相對網址
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
    
    print("成功！請查看 data.json 中的網址是否已修復為正確的絕對路徑。")
