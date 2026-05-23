import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
from datetime import datetime

st.set_page_config(layout="wide", page_title="생산 계획 스케줄러")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏭 생산 계획 스케줄러")

# 설비 리소스 설정
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
    "selectable": True,
}

# 1. 상태 변수를 통해 오류 메시지 유지
if "error_msg" not in st.session_state:
    st.session_state.error_msg = ""

# 데이터 로드
response = supabase.table("production_schedule").select("*").execute()
events = [{"id": str(i["id"]), "resourceId": i["resourceId"], "title": i["title"], "start": i["start"], "end": i["end"]} for i in response.data]

# 캘린더 출력
state = calendar(events=events, options=calendar_options, key="final_calendar_v4")

# 2. 드래그 감지 및 처리
if state.get("eventDrop"):
    event = state["eventDrop"]["event"]
    eid = event.get("id")
    new_start = event.get("start")
    new_res = event.get("resourceId")
    
    if eid and new_start:
        clean_date = new_start.split('T')[0]
        try:
            # 시도 전 상태 초기화
            st.session_state.error_msg = ""
            supabase.table("production_schedule").update({
                "start": clean_date,
                "end": clean_date,
                "resourceId": new_res
            }).eq("id", int(eid)).execute()
            st.rerun()
        except Exception as e:
            # 오류 발생 시 세션 상태에 저장하여 사라지지 않게 함
            st.session_state.error_msg = str(e)
            st.rerun()

# 3. 오류 메시지가 있다면 화면에 계속 표시
if st.session_state.error_msg:
    st.error(f"⚠️ DB 업데이트 오류: {st.session_state.error_msg}")

st.markdown("---")
st.subheader("📝 생산 계획 직접 등록")
# ... (이하 등록 폼 코드 동일)
