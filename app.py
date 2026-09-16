import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="명인제약 생산 일정 관리", layout="wide")

st.title("🏭 생산 일정 자동 배정 시스템 (휴무일 예외 처리 포함)")
st.markdown("월~목(10시간), 금(8시간), 토(5시간) 근무 규칙 및 **지정된 예외 휴무일(명절, 회사 휴가 등)**을 반영하여 일정을 자동 배정합니다.")

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

# --- [탭 분리] 1. 일정 등록 / 2. 예외 휴무일 관리 ---
tab1, tab2 = st.tabs(["📅 생산 일정 등록 및 조회", "🏖️ 예외 휴무일(명절/휴가) 관리"])

with tab1:
    with st.form("schedule_form"):
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("제품명", placeholder="예: 둘록세틴 장용정")
            batch_no = st.text_input("제조번호", placeholder="예: 26001")
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
                
                # [핵심] 예외 휴무일이거나 주간 가용 시간이 0인 경우(일요일 등) 건너뜀
                daily_capacity = WORK_HOURS.get(weekday, 0)
                if date_str in holiday_dates or daily_capacity == 0:
                    current_date += timedelta(days=1)
                    continue
                    
                # 해당 날짜 당일 배정된 시간 계산
                used_on_day = 0
                if not existing_schedule.empty and 'target_date' in existing_schedule.columns:
                    day_rows = existing_schedule[existing_schedule['target_date'] == date_str]
                    used_on_day = day_rows['allocated_hours'].sum()
                    
                available_on_day = daily_capacity - used_on_day
                
                if available_on_day <= 0:
                    current_date += timedelta(days=1)
                    continue
                    
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

            if allocations:
                supabase.table("production_schedule").insert(allocations).execute()
                st.success(f"✨ [{product_name} / 제조번호: {batch_no}] 일정이 휴무일을 피해 성공적으로 배정되었습니다!")
                st.dataframe(pd.DataFrame(allocations), use_container_width=True)

    st.markdown("---")
    st.subheader("📅 전체 생산 일정 현황")
    if supabase:
        try:
            all_data_res = supabase.table("production_schedule").select("*").order("target_date").execute()
            if all_data_res.data:
                st.dataframe(pd.DataFrame(all_data_res.data)[['target_date', 'weekday', 'product_name', 'batch_no', 'allocated_hours']], use_container_width=True)
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
            df_holidays = pd.DataFrame(holidays_res.data)
            st.dataframe(df_holidays, use_container_width=True)
            
            # 개별 삭제 기능 등 추가 가능
        else:
            st.info("등록된 예외 휴무일이 없습니다.")
