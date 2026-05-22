import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
import pandas as pd

# Supabase 연결
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(layout="wide")
st.title("🏭 생산 계획 스케줄러")

# 1. 설비 정보 가져오기 (리소스)
# product_master에서 설비 데이터를 추출하는 로직입니다.
# 일단 테스트로 고정 리소스를 먼저 설정합니다.
resources = [
    {"id": "P100", "title": "과립공정 P100"},
    {"id": "트레이1호", "title": "건조공정 트레이1호"},
    {"id": "PM1000", "title": "혼합공정 PM1000"}
]

# 2. 캘린더 설정
calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "resourceTimelineDay,resourceTimelineWeek"
    },
    "initialView": "resourceTimelineDay",
    "resources": resources,
}

# 3. 캘린더 표시
state = calendar(events=[], options=calendar_options)

st.write("블록을 드래그해서 일정을 변경해 보세요!")
