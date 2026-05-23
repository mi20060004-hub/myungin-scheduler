import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
from datetime import datetime

st.set_page_config(layout="wide", page_title="생산 계획 스케줄러")

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

# 데이터 로드
try:
    response = supabase.table("production_schedule").select("*").execute()
    events = response.data if response.data else []
except Exception as e:
    events = []

# 캘린더 컴포넌트
state = calendar(events=events, options=calendar_options, key="calendar_final")

# 이벤트 수정(드래그) 감지
if state.get("eventDrop"):
    event_info = state["eventDrop"]["event"]
    # 캘린더에서 넘어오는 데이터 구조에 맞춰 id 추출
    event_id = event_info.get("id")
    new_start = event_info.get("start")
    new_resource = event_info.get("resourceId")
    
    if event_id and new_start:
        clean_date = new_start.split('T')[0]
        try:
            # DB 업데이트
            supabase.table("production_schedule").update({
                "start": clean_date,
                "end": clean_date,
                "resourceId": new_resource
            }).eq("id", event_id).execute()
            
            # 성공 시 브라우저에서 바로 새로고침
            st.rerun()
        except Exception as e:
            st.error(f"DB 오류: {e}")

st.markdown("---")
st.subheader("📝 생산 계획 직접 등록")
# (하단 등록 폼 생략 - 기존 코드와 동일)
