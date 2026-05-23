import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta

# 1. 페이지 설정 및 스타일
st.set_page_config(layout="wide", page_title="생산 계획 관리 시트")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stDataEditor { border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase 연결
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("📊 생산 계획 관리 시트 (엑셀형)")
st.info("💡 칸에 제품명이나 계획을 입력하고 엔터를 누르면 자동 저장됩니다. 내용을 지우면 DB에서도 삭제됩니다.")

# 3. 데이터 준비 (날짜 범위 및 장비 리스트)
# 날짜: 오늘 기준 전후 30일 (총 60일치)
start_date = datetime.now().date() - timedelta(days=5)
date_range = [ (start_date + timedelta(days=i)) for i in range(60) ]
date_strings = [d.strftime("%Y-%m-%d") for d in date_range]

# 장비명 (사용자 요청 4개)
equipment_list = ["P100", "SM100", "P400", "GS400"]

# 4. DB에서 데이터 불러와서 엑셀 형태로 변환
def load_grid_data():
    # 빈 데이터프레임 생성 (인덱스: 날짜, 컬럼: 장비명)
    df = pd.DataFrame("", index=date_strings, columns=equipment_list)
    
    try:
        response = supabase.table("production_schedule").select("*").execute()
        if response.data:
            for row in response.data:
                d = row.get("start")
                res = row.get("resourceId")
                title = row.get("title")
                # 해당 날짜와 장비가 우리 그리드에 있다면 값 채우기
                if d in df.index and res in df.columns:
                    df.at[d, res] = title
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
    
    return df

# 5. 데이터 그리드 표시 및 편집
df_current = load_grid_data()

# 엑셀 형식의 데이터 에디터 출력
edited_df = st.data_editor(
    df_current,
    use_container_width=True,
    height=600, # 스크롤이 생기도록 높이 조절
    key="plan_editor",
    num_rows="fixed"
)

# 6. 변경된 내용 DB에 반영 (중요: 자동 저장 로직)
if st.button("💾 변경사항 최종 확인 및 강제 저장"):
    st.rerun()

# 실시간 변경 감지 및 업데이트
# st.data_editor는 수정한 즉시 내부 state에 저장되므로, 
# 데이터프레임의 차이를 분석하여 DB를 업데이트합니다.

def sync_to_db(old_df, new_df):
    for date in old_df.index:
        for res in old_df.columns:
            old_val = old_df.at[date, res]
            new_val = new_df.at[date, res]
            
            if old_val != new_val:
                # 1. 내용이 지워진 경우 -> DB에서 삭제
                if new_val == "" or new_val is None:
                    supabase.table("production_schedule").delete().eq("start", date).eq("resourceId", res).execute()
                
                # 2. 내용이 새로 입력되거나 수정된 경우
                else:
                    # 기존 데이터가 있는지 확인
                    check = supabase.table("production_schedule").select("id").eq("start", date).eq("resourceId", res).execute()
                    
                    if check.data:
                        # 업데이트
                        supabase.table("production_schedule").update({"title": new_val}).eq("start", date).eq("resourceId", res).execute()
                    else:
                        # 신규 입력
                        supabase.table("production_schedule").insert({
                            "start": date,
                            "end": date,
                            "resourceId": res,
                            "title": new_val
                        }).execute()

# 변경 사항이 있을 때만 실행
if not df_current.equals(edited_df):
    sync_to_db(df_current, edited_df)
    st.toast("✅ DB에 저장되었습니다!", icon="💾")
