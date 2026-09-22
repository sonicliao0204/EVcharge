import json
import datetime
import requests
from bs4 import BeautifulSoup
import re

# 共同的請求標頭，偽裝成真實瀏覽器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
}

def extract_tags(title):
    """
    共用的標籤萃取工具：從標題自動判斷硬體規格與活動類型
    """
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
            if '/latestnews/' in href and href != '/latestnews/list':
                title = a_tag.text.strip()
                if len(title) > 5 and "Read More" not in title:
                    full_url = href if href.startswith('http') else f"https://www.evoasis.com.tw{href}"
                    tag_string = extract_tags(title)
                    news_items.append({
                        'cpo': 'EVOASIS',
                        'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{tag_string}",
                        'url': full_url
                    })
                    
        # 去除重複網址並回傳前 5 筆
        unique_news = list({item['url']: item for item in news_items}.values())
        return unique_news[:5]
    except Exception as e:
        print(f"EVOASIS 爬取失敗: {e}")
        return []

def fetch_upower_news():
    # U-POWER 首頁 (他們通常把最新活動與新聞直接放在首頁或公告區塊)
    url = "https://www.u-power.com.tw/"
    news_items = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找所有連結，並利用關鍵字過濾出「最新消息」或「活動」
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.text.strip()
            
            # 過濾條件：連結包含 news、最新消息、活動，且文字大於 5 個字 (排除導覽列)
            if title and len(title) > 5:
                # 這裡是一個泛用的抓取邏輯，把包含特定關鍵字的連結抓出來
                if 'news' in href.lower() or 'event' in href.lower() or '公告' in title or '啟用' in title or '活動' in title:
                    full_url = href if href.startswith('http') else f"https://www.u-power.com.tw/{href.lstrip('/')}"
                    tag_string = extract_tags(title)
                    
                    news_items.append({
                        'cpo': 'U-POWER',
                        'date': datetime.date.today().strftime('%Y-%m-%d'),
                        'title': f"{title}{tag_string}",
                        'url': full_url
                    })
                    
        # 去除重複網址並回傳前 5 筆
        unique_news = list({item['url']: item for item in news_items}.values())
        return unique_news[:5]
    except Exception as e:
        print(f"U-POWER 爬取失敗: {e}")
        return []

if __name__ == '__main__':
    print("開始抓取各家 CPO 真實資料...")
    
    # 分別執行兩家的爬蟲
    evoasis_data = fetch_evoasis_news()
    upower_data = fetch_upower_news()
    
    # 將兩家的資料合併在同一個陣列中
    all_cpo_data = evoasis_data + upower_data
    
    # 寫入 json 檔案給網頁讀取
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_cpo_data, f, ensure_ascii=False, indent=4)
    
    print(f"成功！已抓取 EVOASIS ({len(evoasis_data)}筆) 與 U-POWER ({len(upower_data)}筆) 資料，並寫入 data.json")
