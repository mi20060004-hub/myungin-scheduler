import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="생산 계획 스케줄러")

# 2. Supabase 연결
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏭 생산 계획 스케줄러")

# 3. 설비 리소스 설정
resources = [
    {"id": "P100", "title": "P100"}, {"id": "SM100", "title": "SM100"}, {"id": "P400", "title": "P400"},
    {"id": "GS400", "title": "GS400"}, {"id": "SM600", "title": "SM600"}, {"id": "KM10", "title": "KM10"},
    {"id": "글라트유동층", "title": "글라트유동층"}, {"id": "GPCG2", "title": "GPCG2"}, {"id": "구형과립기", "title": "구형과립기"},
    {"id": "롤러컴팩터", "title": "롤러컴팩터"}, {"id": "트레이1호", "title": "트레이1호"}, {"id": "트레이2호", "title": "트레이2호"},
    {"id": "트레이3호", "title": "트레이3호"}, {"id": "트레이4호", "title": "트레이4호"}, {"id": "트레이5호", "title": "트레이5호"},
    {"id": "트레이6호", "title": "트레이6호"}, {"id": "트레이7호", "title": "트레이7호"}, {"id": "다산유동층", "title": "다산유동층"},
    {"id": "D600", "title": "D600"}, {"id": "Comil0112", "title": "Comil0112"}, {"id": "Comil0212", "title": "Comil0212"},
    {"id": "Comil0312", "title": "Comil0312"}, {"id": "파워밀", "title": "파워밀"}, {"id": "PM1000", "title": "PM1000"},
    {"id": "PM2000", "title": "PM2000"}, {"id": "드럼혼합기", "title": "드럼혼합기"}
]

# 4. 캘린더 옵션
calendar_options = {
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "resourceTimelineMonth"},
    "initialView": "resourceTimelineMonth",
    "resources": resources,
    "locale": "ko",
    "schedulerLicenseKey": "CC-Attribution-NonCommercial-NoDerivs",
    "height": "auto",
    "resourceAreaWidth": "20%",
    "slotMinWidth": 100,
    "editable": True,
    "selectable": True,
}

# 5. 데이터 로드 및 ID 처리
response = supabase.table("production_schedule").select("*").execute()
events = []
for item in response.data:
    events.append({
        "id": str(item["id"]), # 캘린더는 id를 문자열로 처리하는 것이 안전
        "resourceId": item["resourceId"],
        "title": item["title"],
        "start": item["start"],
        "end": item["end"]
    })

# 6. 캘린더 출력
state = calendar(events=events, options=calendar_options, key="final_calendar_v3")

# 7. 드래그 앤 드롭 업데이트 로직 (함수 분리)
if state.get("eventDrop"):
    event = state["eventDrop"]["event"]
    event_id = event.get("id")
    new_start = event.get("start")
    new_res = event.get("resourceId")
    
    if event_id and new_start:
        clean_date = new_start.split('T')[0]
        try:
            # DB 업데이트 시 ID를 int로 명시적 변환
            supabase.table("production_schedule").update({
                "start": clean_date,
                "end": clean_date,
                "resourceId": new_res
            }).eq("id", int(event_id)).execute()
            st.rerun()
        except Exception as e:
            st.error(f"업데이트 오류: {e}")

# 8. 직접 등록 폼
st.markdown("---")
st.subheader("📝 생산 계획 직접 등록")

product_names = []
p_res = supabase.table("product_master").select("제품명").execute()
if p_res.data:
    product_names = [item["제품명"] for item in p_res.data]

with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1: t_date = st.date_input("날짜")
    with col2: t_res = st.selectbox("설비", [r['title'] for r in resources])
    with col3: 
        s_prod = st.selectbox("제품", product_names)
        lot = st.text_input("제조번호")
    
    if st.form_submit_button("일정 등록"):
        r_id = next(r['id'] for r in resources if r['title'] == t_res)
        supabase.table("production_schedule").insert({
            "resourceId": r_id,
            "title": f"{s_prod} ({lot})",
            "start": str(t_date),
            "end": str(t_date)
        }).execute()
        st.rerun()
