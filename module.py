import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import time
import json  # 댓글 파싱을 위해 추가됨
from datetime import date, timedelta

# 봇 탐지 방지용 헤더
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    )
}

# ==========================================================
# [PART 1] 기사 링크 수집
# ==========================================================
def extract_oid_aid_key(url: str):
    """네이버 뉴스 URL에서 oid와 aid를 추출해 고유 기사 key 생성"""
    m = re.search(r"/article/(\d+)/(\d+)", url)
    if not m:
        return None
    return f"{m.group(1)}_{m.group(2)}"

def collect_links_day(keyword: str, target_date: date, sleep_sec: float):
    """
    특정 날짜(target_date)와 키워드에 대해 네이버 뉴스 기사 링크 목록 수집
    """
    q = quote(keyword)
    ds = target_date.strftime("%Y.%m.%d")

    # 모바일 검색 URL
    url = (
        f"https://m.search.naver.com/search.naver"
        f"?where=m_news&query={q}&pd=3&ds={ds}&de={ds}&sort=1" 
    )

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"Request Error on {ds}: {e}")
        return []

    rows = []
    # 모바일 뉴스 검색결과 파싱
    for a in soup.select("a[href*='n.news.naver.com/article']"):
        title = a.get("title") or a.text.strip()
        href = a.get("href", "")
        
        key = extract_oid_aid_key(href)
        if not key:
            continue

        rows.append({
            "key": key,            
            "date": ds,            
            "title": title,        
            "url": href,           
            "keyword": keyword     
        })

    time.sleep(sleep_sec)
    return rows


# ==========================================================
# [PART 2] 댓글 수집 (개수 필터링 기능 포함)
# ==========================================================
def parse_oid_aid(article_url):
    m = re.search(r"/article/(\d+)/(\d+)", article_url)
    if not m:
        return None, None
    return m.group(1), m.group(2)

def to_legacy_url(article_url):
    oid, aid = parse_oid_aid(article_url)
    if not oid:
        return None
    return f"https://news.naver.com/main/read.nhn?oid={oid}&aid={aid}"

def safe_jsonp_load(text):
    try:
        start = text.find("(") + 1
        end = text.rfind(")")
        if start > 0 and end > 0:
            return json.loads(text[start:end])
        else:
            return None 
    except:
        return None

def collect_comments_from_url(article_url, min_count=10, sleep_sec=0.3):
    """
    [수정됨] 커서(cursor) 기반 페이지네이션으로 중복 없이 댓글 수집
    """
    oid, aid = parse_oid_aid(article_url)
    if not oid:
        return []
    
    # 기본 URL 및 헤더
    base_url = "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json"
    headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Referer": to_legacy_url(article_url) 
    }
    
    all_comments = []
    
    # 커서 관련 변수
    next_cursor = ""  # 다음 페이지를 가리키는 암호키
    page_count = 0
    
    while True:
        # 요청 파라미터 (page 방식 -> moreParam.next 방식 변경)
        params = {
            'ticket': 'news',
            'templateId': 'view_politics',
            'pool': 'cbox5',
            'lang': 'ko',
            'country': 'KR',
            'objectId': f'news{oid},{aid}',
            'pageSize': 100,
            'sort': 'favorite',
            'includeAllStatus': 'true',
            'pageType': 'more',        # 더보기 모드
            'moreParam.next': next_cursor  # 여기가 핵심!
        }
        
        # 첫 페이지일 때만 초기화 파라미터 추가
        if page_count == 0:
            params['initialize'] = 'true'
            params['pageType'] = '' # 첫 페이지는 pageType 없음
        
        try:
            res = requests.get(base_url, headers=headers, params=params, timeout=5)
            data = safe_jsonp_load(res.text)
        except:
            break
            
        if not data or not data.get('success'):
            break
        
        # 1. 댓글 개수 체크 (첫 턴에만)
        if page_count == 0:
            total_count = data.get('result', {}).get('count', {}).get('total', 0)
            if total_count < min_count:
                return []
        
        # 2. 댓글 리스트 추출
        comment_list = data.get('result', {}).get('commentList', [])
        if not comment_list:
            break 
            
        for c in comment_list:
            if not c.get('contents'): continue
            all_comments.append({
                'article_url': article_url,
                'comment_id': c.get('commentNo'),
                'author': c.get('userName'), 
                'contents': c.get('contents').replace('\n', ' '), 
                'sympathy': c.get('sympathyCount'),
                'antipathy': c.get('antipathyCount'), 
                'date': c.get('regTime')[:10] 
            })
            
        # 3. 다음 페이지 커서 찾기
        more_page = data.get('result', {}).get('morePage', {})
        new_cursor = more_page.get('next')
        
        # 커서가 없거나, 이전과 같으면 종료 (더 이상 댓글 없음)
        if not new_cursor or new_cursor == next_cursor:
            break
            
        next_cursor = new_cursor
        page_count += 1
        time.sleep(sleep_sec)
        
        # 안전장치 (최대 100페이지)
        if page_count > 100: 
            break
            
    return all_comments