import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
from datetime import datetime

st.set_page_config(layout="wide", page_title="생산 계획 스케줄러")

# Supabase 연결
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏭 생산 계획 스케줄러")

# 1. 설비 리소스 및 데이터 로드
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

# 2. 에러 메시지 저장을 위한 세션 상태
if 'last_error' not in st.session_state:
    st.session_state.last_error = None

# 3. 데이터 조회
try:
    response = supabase.table("production_schedule").select("*").execute()
    events = [{"id": str(i["id"]), "resourceId": i["resourceId"], "title": i["title"], "start": i["start"], "end": i["end"]} for i in response.data]
except Exception as e:
    events = []
    st.error(f"데이터 로드 실패: {e}")

# 4. 캘린더 출력
state = calendar(events=events, options={
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "resourceTimelineMonth"},
    "initialView": "resourceTimelineMonth",
    "resources": resources,
    "editable": True, "selectable": True, "height": "auto"
}, key="final_calendar_v6")

# 5. 드래그 앤 드롭 업데이트 (에러 고정 로직)
if state.get("eventDrop"):
    event = state["eventDrop"]["event"]
    eid = event.get("id")
    new_start = event.get("start")
    new_res = event.get("resourceId")
    
    if eid and new_start:
        try:
            clean_date = new_start.split('T')[0]
            supabase.table("production_schedule").update({
                "start": clean_date, "end": clean_date, "resourceId": new_res
            }).eq("id", int(eid)).execute()
            st.session_state.last_error = None # 성공 시 에러 초기화
            st.rerun()
        except Exception as e:
            st.session_state.last_error = e # 에러를 세션에 저장하여 사라지지 않게 함

# 에러가 있다면 화면에 표시
if st.session_state.last_error:
    st.error(f"⚠️ 업데이트 오류 발생: {st.session_state.last_error}")
    if st.button("에러 메시지 지우기"):
        st.session_state.last_error = None
        st.rerun()

# 6. 등록 폼
st.markdown("---")
st.subheader("📝 생산 계획 직접 등록")
# ... (등록 폼 코드 동일)
