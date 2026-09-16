import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="명인제약 생산 일정 관리", layout="wide")

st.title("🏭 생산 일정 자동 배정 시스템 (다중 장비 통합 관리)")
st.markdown("장비별(보쉬충전기, 세종20홀충전기, 세종6홀충전기)로 근무 시간 규칙 및 예외 휴무일을 반영하여 일정을 자동 배정합니다.")

# Supabase 연동 설정
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None

WORK_HOURS = {
    0: 10,  # 월
    1: 10,  # 화
    2: 10,  # 수
    3: 10,  # 목
    4: 8,   # 금
    5: 5,   # 토
    6: 0    # 일 (휴무)
}

tab1, tab2 = st.tabs(["📅 생산 일정 등록 및 통합 현황", "🏖️ 예외 휴무일(명절/휴가) 관리"])

with tab1:
    with st.form("schedule_form"):
        col_eq, col_prd = st.columns(2)
        with col_eq:
            equipment = st.selectbox("장비 선택", ["보쉬충전기", "세종20홀충전기", "세종6홀충전기"])
            product_name = st.text_input("제품명", placeholder="예: 둘록세틴 장용정")
        with col_prd:
            batch_no = st.text_input("제조번호", placeholder="예: 26001")
            total_hours = st.number_input("총 소요 시간 (시간)", min_value=1.0, max_value=200.0, value=15.0, step=1.0)
            
        start_date = st.date_input("시작 예정일", value=datetime.today())
        submitted = st.form_submit_button("🚀 일정 자동 계산 및 DB 저장")

    if submitted:
        if not product_name or not batch_no:
            st.error("제품명과 제조번호를 모두 입력해주세요.")
        elif not supabase:
            st.error("Supabase 연결 정보를 확인해주세요.")
        else:
            # 1. 기존 생산 일정 불러오기
            schedule_res = supabase.table("production_schedule").select("*").execute()
            existing_schedule = pd.DataFrame(schedule_res.data) if schedule_res.data else pd.DataFrame(columns=['target_date', 'allocated_hours'])

            # 2. 등록된 예외 휴무일 불러오기
            holiday_res = supabase.table("production_holidays").select("*").execute()
            holiday_dates = set(item['holiday_date'] for item in holiday_res.data) if holiday_res.data else set()

            # 자동 할당 알고리즘
            remaining_hours = total_hours
            current_date = pd.to_datetime(start_date)
            allocations = []
            
            while remaining_hours > 0:
                date_str = current_date.strftime('%Y-%m-%d')
                weekday = current_date.weekday()
                
                daily_capacity = WORK_HOURS.get(weekday, 0)
                if date_str in holiday_dates or daily_capacity == 0:
                    current_date += timedelta(days=1)
                    continue
                    
                # 해당 날짜에 선택한 장비에 이미 배정된 시간 계산 (장비별로 슬롯 관리)
                used_on_day = 0
                if not existing_schedule.empty and 'target_date' in existing_schedule.columns and 'equipment' in existing_schedule.columns:
                    day_eq_rows = existing_schedule[(existing_schedule['target_date'] == date_str) & (existing_schedule['equipment'] == equipment)]
                    used_on_day = day_eq_rows['allocated_hours'].sum()
                    
                available_on_day = daily_capacity - used_on_day
                
                if available_on_day <= 0:
                    current_date += timedelta(days=1)
                    continue
                    
                assign_hours = min(remaining_hours, available_on_day)
                
                allocations.append({
                    'equipment': equipment,
                    'product_name': product_name,
                    'batch_no': batch_no,
                    'target_date': date_str,
                    'weekday': ['월','화','수','목','금','토','일'][weekday],
                    'allocated_hours': float(assign_hours)
                })
                
                remaining_hours -= assign_hours
                if remaining_hours > 0:
                    current_date += timedelta(days=1)

            if allocations:
                supabase.table("production_schedule").insert(allocations).execute()
                st.success(f"✨ [{equipment}] [{product_name} / 제조번호: {batch_no}] 일정이 성공적으로 배정되었습니다!")
                st.dataframe(pd.DataFrame(allocations), use_container_width=True)

    st.markdown("---")
    st.subheader("📅 전체 장비 통합 생산 일정 현황")
    if supabase:
        try:
            all_data_res = supabase.table("production_schedule").select("*").order("target_date").execute()
            if all_data_res.data:
                df_all = pd.DataFrame(all_data_res.data)
                # 컬럼 순서 보기 쉽게 정렬
                display_cols = ['equipment', 'target_date', 'weekday', 'product_name', 'batch_no', 'allocated_hours']
                st.dataframe(df_all[[c for c in display_cols if c in df_all.columns]], use_container_width=True)
                
                if st.button("🗑️ 전체 일정 초기화"):
                    supabase.table("production_schedule").delete().neq("id", 0).execute()
                    st.rerun()
            else:
                st.info("등록된 일정이 없습니다.")
        except Exception as e:
            st.warning(f"데이터를 불러오는 중 오류 발생: {e}")

with tab2:
    st.subheader("🏖️ 회사 휴무일 (명절, 창립기념일, 하계휴가 등) 등록")
    with st.form("holiday_form"):
        holiday_date = st.date_input("휴무 지정일")
        reason = st.text_input("휴무 사유", placeholder="예: 추석 연휴, 하계 휴가 등")
        submitted_holiday = st.form_submit_button("➕ 휴무일 추가하기")
        
    if submitted_holiday and supabase:
        try:
            supabase.table("production_holidays").insert({
                "holiday_date": holiday_date.strftime('%Y-%m-%d'),
                "reason": reason
            }).execute()
            st.success(f"✨ {holiday_date} ({reason}) 휴무일이 정상 등록되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"등록 실패 (이미 등록된 날짜일 수 있습니다): {e}")
            
    st.markdown("---")
    st.subheader("📋 등록된 예외 휴무일 목록")
    if supabase:
        holidays_res = supabase.table("production_holidays").select("*").order("holiday_date").execute()
        if holidays_res.data:
            st.dataframe(pd.DataFrame(holidays_res.data), use_container_width=True)
        else:
            st.info("등록된 예외 휴무일이 없습니다.")
