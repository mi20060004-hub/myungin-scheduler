import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client
import pandas as pd

# 페이지 레이아웃 설정
st.set_page_config(layout="wide")

# Supabase 연결 (깃허브 Secrets에서 불러옴)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏭 생산 계획 스케줄러")

# 1. 설비 리소스 설정 (캘린더 가로축에 표시될 항목)
resources = [
    {"id": "P100", "title": "과립공정 P100"},
    {"id": "트레이1호", "title": "건조공정 트레이1호"},
    {"id": "PM1000", "title": "혼합공정 PM1000"}
]

# 2. 캘린더 옵션 설정 (날짜 단위 타임라인 뷰)
calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "resourceTimelineMonth"  # 월 단위 타임라인 뷰
    },
    "initialView": "resourceTimelineMonth",
    "resources": resources,
    "resourceAreaHeaderContent": "설비명",
    "slotLabelFormat": { 
        "month": "long", 
        "day": "numeric", 
        "weekday": "short" 
    },
    "height": "auto",
    "schedulerLicenseKey": "CC-Attribution-NonCommercial-NoDerivs",
}

# 3. 데이터 불러오기 (production_schedule 테이블)
try:
    response = supabase.table("production_schedule").select("*").execute()
    events = response.data
except Exception as e:
    events = []
    st.error(f"데이터를 불러오는 중 오류 발생: {e}")

# 4. 캘린더 표시
state = calendar(events=events, options=calendar_options)

st.write("---")
st.write("💡 블록을 드래그해서 일정을 변경해 보세요!")

# (참고) 드래그 이벤트가 발생했을 때 state에 변경 내용이 담깁니다.
# 추후 이 state를 이용해 Supabase DB에 업데이트하는 로직을 추가할 수 있습니다.
