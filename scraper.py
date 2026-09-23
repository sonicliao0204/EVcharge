import json
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKET_FILE = ROOT / 'data' / 'market.json'
HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'}

def classify(title):
    if any(k in title for k in ['優惠','回饋','免費','折扣','點數']): return '優惠'
    if any(k in title for k in ['上線','啟用','營運','新站']): return '新站'
    if any(k in title for k in ['價格','費率','調整','每度']): return '價格'
    return '情報'

def extract_tags(title):
    tags=[]
    if re.search(r'360\s*kW|360k|500\s*kW|480\s*kW', title, re.I): tags.append('超高速')
    if re.search(r'CCS1', title, re.I): tags.append('CCS1')
    if re.search(r'CCS2', title, re.I): tags.append('CCS2')
    tags.append(classify(title))
    return list(dict.fromkeys(tags))

def fetch_cpo_news(base_url, cpo_name, extra_keywords=None):
    news_items=[]; keywords=['news','event','活動','公告','啟用','上線']+(extra_keywords or [])
    try:
        res=requests.get(base_url,headers=HEADERS,timeout=15);res.encoding=res.apparent_encoding or 'utf-8'
        soup=BeautifulSoup(res.text,'html.parser')
        for a in soup.find_all('a',href=True):
            title=' '.join(a.get_text(' ',strip=True).split()); href=a['href']
            if len(title)<=4 or 'more' in title.lower(): continue
            if any(kw in href.lower() or kw in title for kw in keywords):
                news_items.append({'cpo':cpo_name,'date':datetime.date.today().isoformat(),'title':title,'url':urllib.parse.urljoin(base_url,href),'tags':extract_tags(title)})
        return list({x['url']:x for x in news_items}.values())[:5]
    except Exception as e:
        print(f'[{cpo_name}] 爬取失敗: {e}'); return []

def load_existing():
    try:return json.loads(MARKET_FILE.read_text(encoding='utf-8'))
    except Exception:return []

if __name__=='__main__':
    print('🚀 EVcharge V2.1 市場情報爬蟲啟動...')
    new=[]
    new += fetch_cpo_news('https://www.evalue.com.tw/news/','EVALUE',['detail'])
    new += fetch_cpo_news('https://www.cblok.biz/news','iCharging')
    new += fetch_cpo_news('https://www.u-power.com.tw/','U-POWER')
    new += fetch_cpo_news('https://www.tail.com.tw/','TAIL 特爾電力')
    new += fetch_cpo_news('https://www.yes-energy.com.tw/','YES!來電')
    # 保留舊資料，避免爬蟲一次失敗造成網站情報清空；同 URL 以最新內容覆蓋。
    merged={x.get('url'):x for x in load_existing() if x.get('url')}
    for x in new: merged[x['url']]=x
    result=list(merged.values())
    result=sorted(result,key=lambda x:x.get('date',''),reverse=True)[:100]
    MARKET_FILE.parent.mkdir(exist_ok=True)
    MARKET_FILE.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # 保持舊 GitHub Actions 相容：root data.json 同步成一份 market snapshot。
    (ROOT/'data.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'✅ 完成：{len(result)} 筆市場情報；舊資料保留策略已啟用。')
