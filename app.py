import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="명인제약 생산 일정 관리", layout="wide")

st.title("🏭 캡슐제품 생산계획")
st.markdown("등록된 제품명을 선택하면 기준 소요시간 자동 입력 및 2027년 4월까지의 캘린더 틀 제공")

# Supabase 연동 설정
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None

# 자주 사용하는 제품별 표준 소요시간 사전 정의
DEFAULT_PRODUCT_HOURS = {
    "드록틴캡슐30": 28.0,
    "드록틴캡슐60": 14.0,
    "이가탄에프캡슐": 15.0,
    "트라조돈캡슐25": 30.0,
    "디스그렌캡슐150": 6.0,
    "디스그렌캡슐300": 35.0,
    "리셀톤캡슐1.5": 33.0,
    "리셀톤캡슐3": 33.0,
    "리셀톤캡슐4.5": 16.0,
    "리셀톤캡슐6": 8.0,
    "프레갈캡슐25": 5.0,
    "프레갈캡슐50": 3.0,
    "프레갈캡슐75": 10.0,
    "프레갈캡슐100": 2.0,
    "프레갈캡슐150": 5.0,
    "프레갈캡슐300": 1.0,
    "가펜틴캡슐300": 5.0,
    "그로민캡슐10": 16.0,
    "그로민캡슐25": 16.0,
    "푸록틴캡슐10": 24.0,
    "푸록틴캡슐20": 22.0,
    "아토목신캡슐10": 10.0,
    "아토목신캡슐18": 10.0,
    "아토목신캡슐25": 12.0,
    "아토목신캡슐40": 12.0,
    "아토목신캡슐60": 16.0,
    "아토목신캡슐80": 3.0,
    "슈퍼피린캡슐75-100": 10.0,
    "슈퍼피린캡슐75-75": 13.0,
    "갈란타민서방캡슐8": 6.0,
    "갈란타민서방캡슐16": 3.0,
    "갈란타민서방캡슐24": 2.0,
    "코팩사XR서방캡슐75": 11.0,
    "코팩사XR서방캡슐37.5": 20.0,
    "직접 입력 (신규 품목)": 10.0
}

# 사이드바: 장비별 요일 가용 시간 동적 설정
st.sidebar.header("⚙️요일별 근무시간설정")
equipments = ["보쉬충전기", "세종20홀충전기", "세종6홀충전기"]
days = ['월', '화', '수', '목', '금', '토', '일']

EQUIPMENT_WORK_HOURS = {}
default_presets = {
    "보쉬충전기": [10, 10, 10, 10, 8, 5, 0],
    "세종20홀충전기": [10, 10, 10, 10, 8, 0, 0],
    "세종6홀충전기": [10, 10, 10, 10, 8, 0, 0]
}

for eq in equipments:
    with st.sidebar.expander(f"{eq} 근무 시간 설정"):
        eq_hours = {}
        defaults = default_presets[eq]
        for idx, day in enumerate(days):
            label_text = day + "요일 가용 시간 (h)"
            hours = st.number_input(label_text, min_value=0.0, max_value=24.0, value=float(defaults[idx]), step=1.0, key=f"{eq}_{day}")
            eq_hours[idx] = hours
        EQUIPMENT_WORK_HOURS[eq] = eq_hours

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📅 생산 일정 등록 및 현황", "✂️ 특정 제품/로트 이후 일정 삭제 관리", "🏖️ 예외 휴무일(명절/휴가) 관리"])

with tab1:
    with st.form("schedule_form"):
        col_eq, col_prd = st.columns(2)
        with col_eq:
            equipment = st.selectbox("장비 선택", equipments, key="reg_eq")
            selected_product_option = st.selectbox("제품명 선택", list(DEFAULT_PRODUCT_HOURS.keys()))
            
            if selected_product_option == "직접 입력 (신규 품목)":
                product_name = st.text_input("신규 제품명 직접 입력", placeholder="예: 신규약품")
            else:
                product_name = selected_product_option

        with col_prd:
            batch_no = st.text_input("제조번호", placeholder="예: 26001")
            preset_hours = DEFAULT_PRODUCT_HOURS.get(selected_product_option, 15.0)
            total_hours = st.number_input("총 생산 소요 시간 (시간)", min_value=1.0, max_value=200.0, value=float(preset_hours), step=1.0)
            
        col_time1, _ = st.columns(2)
        with col_time1:
            setup_hours = st.number_input("장비 세팅 시간 (시간)", min_value=0.0, max_value=24.0, value=1.0, step=0.5, help="품목 변경 시 필요한 준비/세팅 시간")
            
        start_date = st.date_input("시작 예정일", value=datetime.today())
        submitted = st.form_submit_button("🚀 일정 자동 계산 및 DB 저장")

    if submitted:
        if selected_product_option == "직접 입력 (신규 품목)" and not product_name:
            st.error("신규 제품명을 입력해주세요.")
        elif not batch_no:
            st.error("제조번호를 입력해주세요.")
        elif not supabase:
            st.error("Supabase 연결 정보를 확인해주세요.")
        else:
            schedule_res = supabase.table("production_schedule").select("*").execute()
            existing_schedule = pd.DataFrame(schedule_res.data) if schedule_res.data else pd.DataFrame(columns=['target_date', 'allocated_hours'])

            holiday_res = supabase.table("production_holidays").select("*").execute()
            holiday_dates = set(item['holiday_date'] for item in holiday_res.data) if holiday_res.data else set()

            work_hours_rule = EQUIPMENT_WORK_HOURS.get(equipment, {})

            remaining_hours = total_hours
            current_date = pd.to_datetime(start_date)
            allocations = []
            
            # 1. 세팅 시간 배정 로직
            remaining_setup = setup_hours
            while remaining_setup > 0:
                date_str = current_date.strftime('%Y-%m-%d')
                weekday = current_date.weekday()
                
                daily_capacity = work_hours_rule.get(weekday, 0)
                if date_str in holiday_dates or daily_capacity == 0:
                    current_date += timedelta(days=1)
                    continue
                    
                used_on_day = 0
                if not existing_schedule.empty and 'target_date' in existing_schedule.columns and 'equipment' in existing_schedule.columns:
                    day_eq_rows = existing_schedule[(existing_schedule['target_date'] == date_str) & (existing_schedule['equipment'] == equipment)]
                    used_on_day = day_eq_rows['allocated_hours'].sum()
                    
                available_on_day = daily_capacity - used_on_day
                if available_on_day <= 0:
                    current_date += timedelta(days=1)
                    continue
                    
                assign_setup = min(remaining_setup, available_on_day)
                allocations.append({
                    'equipment': equipment,
                    'product_name': f"[세팅] {product_name}",
                    'batch_no': f"{batch_no}(세팅)",
                    'target_date': date_str,
                    'weekday': days[weekday],
                    'allocated_hours': float(assign_setup)
                })
                
                remaining_setup -= assign_setup
                if remaining_setup > 0:
                    current_date += timedelta(days=1)
            
            # 2. 본 생산 소요 시간 배정 로직
            while remaining_hours > 0:
                date_str = current_date.strftime('%Y-%m-%d')
                weekday = current_date.weekday()
                
                daily_capacity = work_hours_rule.get(weekday, 0)
                if date_str in holiday_dates or daily_capacity == 0:
                    current_date += timedelta(days=1)
                    continue
                    
                used_on_day = 0
                if not existing_schedule.empty and 'target_date' in existing_schedule.columns and 'equipment' in existing_schedule.columns:
                    day_eq_rows = existing_schedule[(existing_schedule['target_date'] == date_str) & (existing_schedule['equipment'] == equipment)]
                    used_on_day = day_eq_rows['allocated_hours'].sum()
                
                temp_df = pd.DataFrame(allocations)
                if not temp_df.empty:
                    used_on_day += temp_df[temp_df['target_date'] == date_str]['allocated_hours'].sum()
                    
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
                    'weekday': days[weekday],
                    'allocated_hours': float(assign_hours)
                })
                
                remaining_hours -= assign_hours
                if remaining_hours > 0:
                    current_date += timedelta(days=1)

            if allocations:
                supabase.table("production_schedule").insert(allocations).execute()
                st.success(f"✨ [{equipment}] 세팅 시간 및 본 생산 일정이 성공적으로 배정되었습니다!")
                st.rerun()

    st.markdown("---")
    st.subheader("📅 날짜별 장비 통합 생산 현황표 (2027년 4월까지 표시)")
    
    if supabase:
        try:
            # 1. 예외 휴무일 불러오기
            holiday_res = supabase.table("production_holidays").select("*").execute()
            holiday_dict = {item['holiday_date']: item['reason'] for item in holiday_res.data} if holiday_res.data else {}
            holiday_dates = set(holiday_dict.keys())

            # 2. 등록된 생산 일정 불러오기
            all_data_res = supabase.table("production_schedule").select("*").order("target_date").order("created_at").execute()
            raw_data = all_data_res.data if all_data_res.data else []
            df_raw = pd.DataFrame(raw_data)

            # 3. 캘린더 전체 날짜 범위 설정 (오늘부터 2027년 4월 30일까지, 단 기존 일정이 더 이른 날짜부터 시작하면 그 날짜부터 포함)
            min_date = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
            if not df_raw.empty:
                data_min_date = pd.to_datetime(df_raw['target_date'].min())
                if data_min_date < min_date:
                    min_date = data_min_date
            
            # 종료일은 2027년 4월 30일로 고정 (또는 등록된 일정의 최대일이 그보다 뒤라면 최대일 기준)
            max_date = pd.to_datetime('2027-04-30')
            if not df_raw.empty:
                data_max_date = pd.to_datetime(df_raw['target_date'].max())
                if data_max_date > max_date:
                    max_date = data_max_date

            date_range = pd.date_range(start=min_date, end=max_date)
            
            pivot_rows = []
            for single_date in date_range:
                d_str = single_date.strftime('%Y-%m-%d')
                w_idx = single_date.weekday() # 0:월 ~ 6:일
                w_str = days[w_idx]
                
                # 휴무일 여부 판정 (일요일이거나 휴무일 테이블에 등록된 날짜)
                is_off = (w_idx == 6) or (d_str in holiday_dates)
                off_reason = holiday_dict.get(d_str, "일요일 휴무" if w_idx == 6 else "")

                # 스타일 적용을 위한 HTML 태그 (휴무일이면 빨간색)
                if is_off:
                    display_date = f"<span style='color:red; font-weight:bold;'>{d_str}</span>"
                    display_weekday = f"<span style='color:red; font-weight:bold;'>{w_str}</span>"
                else:
                    display_date = d_str
                    display_weekday = w_str

                row_data = {
                    '날짜': display_date,
                    '요일': display_weekday
                }

                # 해당 날짜의 장비별 데이터 매핑
                for eq in equipments:
                    if not df_raw.empty:
                        df_eq = df_raw[(df_raw['target_date'] == d_str) & (df_raw['equipment'] == eq)]
                    else:
                        df_eq = pd.DataFrame()

                    if not df_eq.empty:
                        if 'created_at' in df_eq.columns:
                            df_eq = df_eq.sort_values(by='created_at')
                        
                        pure_prods = []
                        for p in df_eq['product_name'].astype(str).tolist():
                            clean_p = p.replace("[세팅] ", "").replace("[세팅]", "").strip()
                            if clean_p not in pure_prods:
                                pure_prods.append(clean_p)
                                
                        batch_list = []
                        for b in df_eq['batch_no'].astype(str).tolist():
                            if "(세팅)" not in b:
                                clean_b = b.strip()
                                batch_list.append(clean_b)

                        row_data[f"{eq}_제품명"] = ", ".join(pure_prods) if pure_prods else "-"
                        row_data[f"{eq}_제조번호"] = ", ".join(batch_list) if batch_list else "-"
                        row_data[f"{eq}_소요시간(h)"] = df_eq['allocated_hours'].sum()
                    else:
                        if is_off and off_reason:
                            row_data[f"{eq}_제품명"] = f"<span style='color:gray;'>[{off_reason}]</span>"
                        else:
                            row_data[f"{eq}_제품명"] = "-"
                        row_data[f"{eq}_제조번호"] = "-"
                        row_data[f"{eq}_소요시간(h)"] = 0

                pivot_rows.append(row_data)

            df_matrix = pd.DataFrame(pivot_rows)

            ordered_cols = ['날짜', '요일', 
                            '보쉬충전기_제품명', '보쉬충전기_제조번호', '보쉬충전기_소요시간(h)',
                            '세종20홀충전기_제품명', '세종20홀충전기_제조번호', '세종20홀충전기_소요시간(h)',
                            '세종6홀충전기_제품명', '세종6홀충전기_제조번호', '세종6홀충전기_소요시간(h)']

            final_display_cols = [c for c in ordered_cols if c in df_matrix.columns]

            table_height = max(300, len(df_matrix) * 35 + 40)
            st.markdown(df_matrix[final_display_cols].to_html(escape=False, index=False), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ 전체 일정 초기화"):
                supabase.table("production_schedule").delete().neq("id", 0).execute()
                st.rerun()
        except Exception as e:
            st.warning(f"데이터를 불러오는 중 오류 발생: {e}")

with tab2:
    st.subheader("✂️ 특정 제품명 및 제조번호(로트) 이후 일정 일괄 삭제")
    st.markdown("일정 변경 시, 특정 장비에서 **지정하고자 하는 제품명과 제조번호**가 시작되는 시점을 찾아 그 이후의 모든 일정을 한 번에 삭제합니다.")
    
    with st.form("delete_form"):
        del_equipment = st.selectbox("대상 장비 선택", equipments, key="del_eq")
        target_product = st.text_input("삭제 기준 제품명 입력", placeholder="예: 드록틴캡슐30")
        target_batch = st.text_input("삭제 기준 제조번호 입력", placeholder="예: 26005")
        
        submitted_del = st.form_submit_button("🔥 해당 제품/로트 이후 일정 삭제 실행", type="primary")
        
    if submitted_del and supabase:
        if not target_product or not target_batch:
            st.error("삭제 기준이 될 제품명과 제조번호를 모두 입력해주세요.")
        else:
            try:
                res = supabase.table("production_schedule").select("*").eq("equipment", del_equipment).order("target_date").execute()
                if res.data:
                    df_eq_sched = pd.DataFrame(res.data)
                    
                    matched = df_eq_sched[
                        (df_eq_sched['product_name'].str.contains(target_product, na=False)) & 
                        (df_eq_sched['batch_no'] == target_batch)
                    ]
                    
                    if not matched.empty:
                        start_del_date = matched['target_date'].min()
                        target_rows = df_eq_sched[df_eq_sched['target_date'] >= start_del_date]
                        ids_to_delete = target_rows['id'].tolist()
                        
                        if ids_to_delete:
                            for item_id in ids_to_delete:
                                supabase.table("production_schedule").delete().eq("id", item_id).execute()
                            st.success(f"✨ [{del_equipment}] [{target_product} / {target_batch}] 이후의 일정이 성공적으로 삭제되었습니다! (총 {len(ids_to_delete)}개 블록 삭제됨)")
                            st.rerun()
                    else:
                        st.error(f"입력하신 조건([{del_equipment}] 제품명: {target_product}, 제조번호: {target_batch})에 해당하는 일정을 찾을 수 없습니다.")
                else:
                    st.info("해당 장비에 등록된 일정이 없습니다.")
            except Exception as e:
                st.error(f"삭제 처리 중 오류 발생: {e}")

with tab3:
    st.subheader("🏖️ 회사 휴무일 (명절, 창립기념일, 하계휴가 등) 등록")
    with st.form("holiday_form"):
        holiday_date = st.date_input("휴무 지정일", key="hol_date")
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
