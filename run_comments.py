import pandas as pd
import os
import time
import module  # 위에서 만든 module.py를 사용

# ---------------------------------------------------------
# [설정] 
# ---------------------------------------------------------
# 1. 기사 목록 파일 (아까 수집한 파일명으로 바꿔주세요)
INPUT_FILE = r'C:\\Users\\philh\\OneDrive\\바탕 화면\\시계열 연구자료\\2월1일_3일_코스피_기사.csv'  

# 2. 저장 경로
SAVE_DIR = r'C:\\Users\\philh\\OneDrive\\바탕 화면\\시계열 연구자료'
OUTPUT_FILENAME = '코스피_댓글수집_최종.csv'

# 3. 최소 댓글 수 설정 (이것보다 적으면 수집 안 함!)
MIN_COMMENT_COUNT = 5 

def main():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        
    full_output_path = os.path.join(SAVE_DIR, OUTPUT_FILENAME)

    print(f"📂 입력 파일 로드: {INPUT_FILE}")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print("❌ 파일을 찾을 수 없습니다.")
        return

    print(f"📊 총 {len(df)}개 기사 중 댓글 {MIN_COMMENT_COUNT}개 이상인 기사만 수집합니다.")
    print("-" * 60)

    # 저장 모드 설정 (파일이 없으면 헤더 포함, 있으면 이어쓰기)
    if not os.path.exists(full_output_path):
        header_mode = True
    else:
        header_mode = False

    total_saved = 0

    for idx, row in df.iterrows():
        url = row['url']
        # 제목이 너무 길면 자르기 (화면 출력용)
        title = str(row.get('title', ''))[:20] + "..."
        
        print(f"[{idx+1}/{len(df)}] 검색: {title}", end="")
        
        # [핵심] min_count를 설정하여 호출
        comments = module.collect_comments_from_url(url, min_count=MIN_COMMENT_COUNT)
        
        if comments:
            # 수집된 댓글이 있으면 저장
            cmt_df = pd.DataFrame(comments)
            cmt_df.to_csv(full_output_path, mode='a', index=False, header=header_mode, encoding='utf-8-sig')
            header_mode = False # 이후부터는 헤더 없이 데이터만 추가
            
            count = len(comments)
            total_saved += count
            print(f" -> ✅ {count}개 수집됨")
        else:
            # min_count 미만이거나 댓글이 없는 경우
            print(f" -> [Pass] 기준 미달")
            
        time.sleep(0.5) # 차단 방지 딜레이

    print("-" * 60)
    print(f"🎉 작업 완료! 총 {total_saved}개의 댓글이 저장되었습니다.")
    print(f"파일 위치: {full_output_path}")

if __name__ == "__main__":
    main()