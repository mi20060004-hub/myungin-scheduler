import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
import pandas as pd

# 페이지 레이아웃 설정
st.set_page_config(layout="wide")

# Supabase 연결
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏭 생산 계획 스케줄러")

# 1. 설비 리소스 설정 (보내주신 설비 목록 반영)
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

# 2. 캘린더 옵션 설정
calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "resourceTimelineMonth"
    },
    "initialView": "resourceTimelineMonth",
    "resources": resources,
    "locale": "ko",
    "resourceAreaHeaderContent": "설비명",
    "schedulerLicenseKey": "CC-Attribution-NonCommercial-NoDerivs",
    "height": "auto",
    "resourceAreaWidth": "20%",
    "slotMinWidth": 100,
}

# 3. 데이터 불러오기
try:
    response = supabase.table("production_schedule").select("*").execute()
    events = response.data
except Exception as e:
    events = []
    st.error(f"데이터를 불러오는 중 오류 발생: {e}")

# 4. 캘린더 표시
state = calendar(events=events, options=calendar_options)

st.write("---")
st.write("💡 모든 설비 리스트가 등록되었습니다!")
