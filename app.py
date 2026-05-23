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

# 3. 설비 리소스 설정 (기존 리소스 유지)
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

# 4. 캘린더 옵션 설정
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

# 5. 데이터 로드 (Supabase -> Calendar)
try:
    response = supabase.table("production_schedule").select("*").execute()
    db_events = response.data if response.data else []
    
    # 캘린더 인식을 위해 ID를 문자열로 변환하고 데이터 구조 정리
    calendar_events = []
    for e in db_events:
        calendar_events.append({
            "id": str(e["id"]),
            "resourceId": e.get("resourceId"),
            "title": e.get("title"),
            "start": e.get("start"),
            "end": e.get("end"),
            "allDay": True
        })
except Exception as e:
    st.error(f"데이터 조회 중 오류 발생: {e}")
    calendar_events = []

# 6. 캘린더 출력
state = calendar(events=calendar_events, options=calendar_options, key="production_scheduler_v1")

# 7. 드래그 앤 드롭(eventDrop) 처리
if state.get("eventDrop"):
    event_info = state["eventDrop"]["event"]
    eid = event_info.get("id")
    new_start = event_info.get("start")
    new_res = event_info.get("resourceId")
    
    if eid and new_start:
        # 시간 정보가 포함된 경우 날짜만 추출 (예: 2026-05-23T00:00:00 -> 2026-05-23)
        clean_date = new_start.split('T')[0]
        
        try:
            supabase.table("production_schedule").update({
                "start": clean_date,
                "end": clean_date,
                "resourceId": new_res
            }).eq("id", int(eid)).execute()
            
            st.rerun() # DB 업데이트 후 즉시 화면 갱신
        except Exception as e:
            st.error(f"이동 저장 실패: {e}")

# 8. 생산 계획 직접 등록 (기존 기능 완벽 보존)
st.markdown("---")
st.subheader("📝 생산 계획 직접 등록")

# 제품 마스터 로드
product_names = []
try:
    p_response = supabase.table("product_master").select("제품명").execute()
    if p_response.data:
        product_names = [item.get("제품명") for item in p_response.data if item.get("제품명")]
except:
    pass

with st.form("direct_input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        target_date = st.date_input("날짜 선택")
    with col2:
        target_resource = st.selectbox("설비 선택", [r['title'] for r in resources])
    with col3:
        selected_product = st.selectbox("제품 선택", product_names if product_names else ["데이터 없음"])
        lot_number = st.text_input("제조번호")
    
    if st.form_submit_button("일정 등록하기"):
        # 설비 명칭으로 리소스 ID 찾기
        res_id = next(r['id'] for r in resources if r['title'] == target_resource)
        
        new_event = {
            "resourceId": res_id,
            "title": f"{selected_product} ({lot_number})",
            "start": str(target_date),
            "end": str(target_date),
            "created_at": datetime.now().isoformat()
        }
        
        try:
            supabase.table("production_schedule").insert(new_event).execute()
            st.success("새 일정이 등록되었습니다.")
            st.rerun() # 등록 후 즉시 화면 갱신
        except Exception as e:
            st.error(f"일정 등록 실패: {e}")
