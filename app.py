import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client

st.set_page_config(layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.dialog("생산 계획 등록")
def add_schedule_dialog(date, resource_id):
    products = supabase.table("product_master").select("product_name").execute().data
    product_list = [p["product_name"] for p in products]

    with st.form("schedule_form"):
        selected_product = st.selectbox("제품명 선택", product_list)
        lot_number = st.text_input("제조번호 입력")
        submitted = st.form_submit_button("저장")
        
        if submitted:
            new_event = {
                "resourceId": resource_id,
                "title": f"{selected_product} ({lot_number})",
                "start": date,
                "end": date
            }
            supabase.table("production_schedule").insert(new_event).execute()
            st.success("등록 완료!")
            st.rerun()

st.title("🏭 생산 계획 스케줄러")

resources = [
    {"id": "P100", "title": "P100"}, {"id": "SM100", "title": "SM100"},
    {"id": "P400", "title": "P400"}, {"id": "GS400", "title": "GS400"},
    {"id": "SM600", "title": "SM600"}, {"id": "KM10", "title": "KM10"},
    {"id": "글라트유동층", "title": "글라트유동층"}, {"id": "GPCG2", "title": "GPCG2"},
    {"id": "구형과립기", "title": "구형과립기"}, {"id": "롤러컴팩터", "title": "롤러컴팩터"},
    {"id": "트레이1호", "title": "트레이1호"}, {"id": "트레이2호", "title": "트레이2호"},
    {"id": "트레이3호", "title": "트레이3호"}, {"id": "트레이4호", "title": "트레이4호"},
    {"id": "트레이5호", "title": "트레이5호"}, {"id": "트레이6호", "title": "트레이6호"},
    {"id": "트레이7호", "title": "트레이7호"}, {"id": "다산유동층", "title": "다산유동층"},
    {"id": "D600", "title": "D600"}, {"id": "Comil0112", "title": "Comil0112"},
    {"id": "Comil0212", "title": "Comil0212"}, {"id": "Comil0312", "title": "Comil0312"},
    {"id": "파워밀", "title": "파워밀"}, {"id": "PM1000", "title": "PM1000"},
    {"id": "PM2000", "title": "PM2000"}, {"id": "드럼혼합기", "title": "드럼혼합기"}
]

calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "resourceTimelineMonth"},
    "initialView": "resourceTimelineMonth",
    "resources": resources,
    "locale": "ko",
    "schedulerLicenseKey": "CC-Attribution-NonCommercial-NoDerivs",
    "height": "auto",
}

events = supabase.table("production_schedule").select("*").execute().data

# 캘린더 표시
state = calendar(events=events, options=calendar_options)

# 에러 방지: state에 키가 있는지 안전하게 확인
if state.get("select"):
    selection = state["select"]
    clicked_date = selection.get("startStr")
    clicked_resource = selection.get("resourceId")
    
    if clicked_date and clicked_resource:
        add_schedule_dialog(clicked_date, clicked_resource)
