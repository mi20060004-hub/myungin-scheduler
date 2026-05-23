import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
from datetime import datetime

st.set_page_config(layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏭 생산 계획 스케줄러")

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
    "droppable": True,
    "selectable": True,
}

try:
    response = supabase.table("production_schedule").select("*").execute()
    events = response.data if response.data else []
except Exception as e:
    events = []

state = calendar(events=events, options=calendar_options, key="final_calendar")

# 드래그 앤 드롭 디버깅 및 업데이트
if state.get("eventDrop"):
    event_info = state["eventDrop"]["event"]
    st.write("--- 드래그 감지됨! 전달된 데이터 ---")
    st.write(event_info) # 무엇이 넘어오는지 눈으로 확인
    
    eid = event_info.get("id")
    new_start = event_info.get("start")
    new_res = event_info.get("resourceId")
    
    if eid and new_start:
        clean_date = new_start.split('T')[0]
        try:
            res = supabase.table("production_schedule").update({
                "start": clean_date,
                "end": clean_date,
                "resourceId": new_res
            }).eq("id", eid).execute()
            
            st.success("DB 업데이트 성공!")
            st.rerun()
        except Exception as e:
            st.error(f"DB 업데이트 에러: {e}")

st.markdown("---")
st.subheader("📝 생산 계획 직접 등록")
product_names = []
try:
    p_response = supabase.table("product_master").select("제품명").execute()
    if p_response.data:
        product_names = [item.get("제품명") for item in p_response.data if item.get("제품명")]
except: pass

with st.form("direct_input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1: target_date = st.date_input("날짜 선택")
    with col2: target_resource = st.selectbox("설비 선택", [r['title'] for r in resources])
    with col3: 
        selected_product = st.selectbox("제품 선택", product_names if product_names else ["데이터 없음"])
        lot_number = st.text_input("제조번호")
    if st.form_submit_button("일정 등록하기"):
        res_id = next(r['id'] for r in resources if r['title'] == target_resource)
        new_event = {"resourceId": res_id, "title": f"{selected_product} ({lot_number})", "start": str(target_date), "end": str(target_date), "created_at": datetime.now().isoformat()}
        supabase.table("production_schedule").insert(new_event).execute()
        st.rerun()
