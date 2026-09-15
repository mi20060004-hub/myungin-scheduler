import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# Streamlit 페이지 설정
st.set_page_config(page_title="명인제약 생산 일정 관리", layout="wide")

st.title("🏭 생산 일정 자동 배정 시스템")
st.markdown("월~목(10시간), 금(8시간), 토(5시간) 근무 시간 규칙에 맞춰 제품 생산 블록을 자동으로 할당합니다.")

# 1. Supabase 연동 설정 (Streamlit Secrets 활용 또는 직접 입력)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.sidebar.warning("⚠️ Streamlit secrets에 Supabase 설정이 없습니다. 테스트용 입력을 사용하세요.")
    SUPABASE_URL = st.sidebar.text_input("Supabase URL")
    SUPABASE_KEY = st.sidebar.text_input("Supabase Anon Key", type="password")
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None

# 2. 요일별 가용 시간 정의
WORK_HOURS = {
    0: 10,  # 월
    1: 10,  # 화
    2: 10,  # 수
    3: 10,  # 목
    4: 8,   # 금
    5: 5,   # 토
    6: 0    # 일 (휴무)
}

# 3. 입력 폼 구성
with st.form("schedule_form"):
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("제품명", placeholder="예: 둘록세틴 장용정")
        batch_no = st.text_input("제조번호", placeholder="예: 26013")
    with col2:
        total_hours = st.number_input("총 소요 시간 (시간)", min_value=1.0, max_value=200.0, value=15.0, step=1.0)
        start_date = st.date_input("시작 예정일", value=datetime.today())
        
    submitted = st.form_submit_button("🚀 일정 자동 계산 및 DB 저장")

if submitted:
    if not product_name or not batch_no:
        st.error("제품명과 제조번호를 모두 입력해주세요.")
    elif not supabase:
        st.error("Supabase 연결 정보를 확인해주세요.")
    else:
        # 기존 DB에 등록된 전체 일정 불러오기 (날짜별 잔여 시간 계산용)
        response = supabase.table("production_schedule").select("*").execute()
        existing_data = response.data
        existing_df = pd.DataFrame(existing_data) if existing_data else pd.DataFrame(columns=['target_date', 'allocated_hours'])

        # 자동 할당 알고리즘 로직
        remaining_hours = total_hours
        current_date = pd.to_datetime(start_date)
        allocations = []
        
        while remaining_hours > 0:
            weekday = current_date.weekday()
            daily_capacity = WORK_HOURS.get(weekday, 0)
            
            if daily_capacity == 0:
                # 휴무일(일요일 등)은 건너뜀
                current_date += timedelta(days=1)
                continue
                
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 해당 날짜에 이미 배정된 총 시간 계산
            used_on_day = 0
            if not existing_df.empty and 'target_date' in existing_df.columns:
                day_rows = existing_df[existing_df['target_date'] == date_str]
                used_on_day = day_rows['allocated_hours'].sum()
                
            available_on_day = daily_capacity - used_on_day
            
            if available_on_day <= 0:
                # 당일 가용 시간이 꽉 찼으면 다음 날로 이동
                current_date += timedelta(days=1)
                continue
                
            # 금일 배정할 수 있는 시간 산정
            assign_hours = min(remaining_hours, available_on_day)
            
            allocations.append({
                'product_name': product_name,
                'batch_no': batch_no,
                'target_date': date_str,
                'weekday': ['월','화','수','목','금','토','일'][weekday],
                'allocated_hours': float(assign_hours)
            })
            
            remaining_hours -= assign_hours
            if remaining_hours > 0:
                current_date += timedelta(days=1)

        # Supabase에 일괄 Insert
        if allocations:
            insert_res = supabase.table("production_schedule").insert(allocations).execute()
            st.success(f"✨ [{product_name} / 제조번호: {batch_no}] 일정이 성공적으로 계산되어 Supabase에 저장되었습니다!")
            
            # 결과 표시
            st.dataframe(pd.DataFrame(allocations), use_container_width=True)

st.markdown("---")
st.subheader("📅 전체 생산 일정 현황 (DB 연동)")

# Supabase에서 전체 일정 조회 및 표시
if supabase:
    try:
        all_data_res = supabase.table("production_schedule").select("*").order("target_date").execute()
        if all_data_res.data:
            df_all = pd.DataFrame(all_data_res.data)
            st.dataframe(df_all[['target_date', 'weekday', 'product_name', 'batch_no', 'allocated_hours']], use_container_width=True)
            
            if st.button("🗑️ 전체 일정 초기화 (DB 비우기)"):
                # 주의: 전체 삭제용 예시 쿼리
                supabase.table("production_schedule").delete().neq("id", 0).execute()
                st.rerun()
        else:
            info_msg = "등록된 생산 일정이 없습니다. 위에서 제품을 추가해 보세요."
            st.info(info_msg)
    except Exception as e:
        err_msg = f"데이터를 불러오는 중 오류가 발생했습니다: {e}"
        st.warning(err_msg)
