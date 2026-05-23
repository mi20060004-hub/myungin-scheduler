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

# 1. 설비 리소스 설정 (가로축에 표시됨)
resources = [
    {"id": "P100", "title": "과립공정 P100"},
    {"id": "트레이1호", "title": "건조공정 트레이1호"},
    {"id": "PM1000", "title": "혼합공정 PM1000"},
]

# 2. 캘린더 옵션 설정 (한글 적용 및 타임라인 뷰)
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
    "locale": "ko",  # 한글 적용
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
st.write("💡 이제 가로축이 설비명입니다. 추가할 설비명들을 알려주세요!")
