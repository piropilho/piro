import os
import pandas as pd
from datetime import datetime, timedelta
import module  # 위에서 만든 module.py를 호출

# ---------------------------------------------------------
# [설정] 사용자 지정 경로 및 옵션
# ---------------------------------------------------------
SAVE_DIR = r'C:\\Users\\philh\\OneDrive\\바탕 화면\\시계열 연구자료'
SLEEP_SEC = 0.5  # 크롤링 딜레이 (초)

def get_date_range(start_str, end_str):
    """시작일~종료일 사이의 모든 날짜를 리스트로 반환"""
    start = datetime.strptime(start_str, "%Y.%m.%d").date()
    end = datetime.strptime(end_str, "%Y.%m.%d").date()
    
    days = []
    curr = start
    while curr <= end:
        days.append(curr)
        curr += timedelta(days=1)
    return days

def main():
    # 1. 경로 확인 및 생성
    if not os.path.exists(SAVE_DIR):
        try:
            os.makedirs(SAVE_DIR)
            print(f"폴더 생성 완료: {SAVE_DIR}")
        except Exception as e:
            print(f"폴더 생성 실패: {e}")
            return

    # 2. 사용자 입력
    keyword = input("수집할 키워드를 입력하세요 (예: 금리): ")
    start_date = input("시작 날짜 (YYYY.MM.DD): ")
    end_date = input("종료 날짜 (YYYY.MM.DD): ")
    file_name = input("저장할 파일명 (확장자 제외): ")

    # 3. 날짜 리스트 생성
    target_days = get_date_range(start_date, end_date)
    print(f"\n총 {len(target_days)}일간의 데이터를 수집합니다...")

    all_data = []
    unique_keys = set() # 중복 방지용 집합

    # 4. 수집 루프 (module의 로직 활용)
    for d in target_days:
        print(f"[{d}] '{keyword}' 검색 중...", end="\r")
        
        # module.py에 있는 함수 호출
        items = module.collect_links_day(keyword, d, SLEEP_SEC)
        
        for item in items:
            # [요청사항] 제목에 키워드가 포함된 것만 필터링
            if keyword not in item['title']:
                continue
                
            # 중복 제거 (oid_aid 키 기준)
            if item['key'] not in unique_keys:
                unique_keys.add(item['key'])
                all_data.append(item)

    print(f"\n\n수집 완료! 총 {len(all_data)}개의 기사를 찾았습니다.")

    # 5. CSV 저장
    if all_data:
        df = pd.DataFrame(all_data)
        
        # 컬럼 순서 보기 좋게 정렬
        df = df[['date', 'keyword', 'title', 'url', 'key']]
        
        full_path = os.path.join(SAVE_DIR, f"{file_name}.csv")
        df.to_csv(full_path, index=False, encoding='utf-8-sig')
        print(f"파일 저장 완료: {full_path}")
    else:
        print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()