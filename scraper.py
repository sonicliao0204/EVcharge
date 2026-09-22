import json
import datetime

# 1. 建立一個模擬的爬蟲函式 (先用測試資料確保網頁能跑)
def fetch_cpo_news():
    today = datetime.date.today().strftime('%Y-%m-%d')
    # 這裡放兩筆模擬資料，之後您可以換成真實的 requests/BeautifulSoup 爬蟲
    data = [
        {
            'cpo': 'EVOASIS',
            'date': today,
            'title': '竹科新站上線，限時每度 6.5 元',
            'url': 'https://example.com/evoasis'
        },
        {
            'cpo': 'U-POWER',
            'date': today,
            'title': '中秋連假全台站點 8 折優惠',
            'url': 'https://example.com/upower'
        }
    ]
    return data

if __name__ == '__main__':
    print("開始抓取資料...")
    scraped_data = fetch_cpo_news()
    
    # 2. 將抓到的資料寫入 data.json 檔案
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=4)
    
    print("成功！資料已寫入 data.json")
