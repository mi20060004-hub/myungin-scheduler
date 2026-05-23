import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client

# 1. 설정
st.set_page_config(layout="wide")
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏭 생산 계획 스케줄러")

# 2. 에러 메시지 고정용 세션 관리
if "sticky_error" not in st.session_state:
    st.session_state.sticky_error = None

# 3. 데이터 로드
try:
    response = supabase.table("production_schedule").select("*").execute()
    # 테이블이 비어있으면 빈 리스트 반환
    events = [{"id": str(i["id"]), "resourceId": i["resourceId"], "title": i["title"], "start": i["start"], "end": i["end"]} for i in response.data] if response.data else []
except Exception as e:
    events = []
    st.session_state.sticky_error = f"데이터 로드 실패: {e}"

# 4. 캘린더 출력
resources = [{"id": "P100", "title": "P100"}, {"id": "SM100", "title": "SM100"}, {"id": "P400", "title": "P400"}, {"id": "GS400", "title": "GS400"}, {"id": "SM600", "title": "SM600"}, {"id": "KM10", "title": "KM10"}, {"id": "글라트유동층", "title": "글라트유동층"}, {"id": "GPCG2", "title": "GPCG2"}, {"id": "구형과립기", "title": "구형과립기"}, {"id": "롤러컴팩터", "title": "롤러컴팩터"}, {"id": "트레이1호", "title": "트레이1호"}, {"id": "트레이2호", "title": "트레이2호"}, {"id": "트레이3호", "title": "트레이3호"}, {"id": "트레이4호", "title": "트레이4호"}, {"id": "트레이5호", "title": "트레이5호"}, {"id": "트레이6호", "title": "트레이6호"}, {"id": "트레이7호", "title": "트레이7호"}, {"id": "다산유동층", "title": "다산유동층"}, {"id": "D600", "title": "D600"}, {"id": "Comil0112", "title": "Comil0112"}, {"id": "Comil0212", "title": "Comil0212"}, {"id": "Comil0312", "title": "Comil0312"}, {"id": "파워밀", "title": "파워밀"}, {"id": "PM1000", "title": "PM1000"}, {"id": "PM2000", "title": "PM2000"}, {"id": "드럼혼합기", "title": "드럼혼합기"}]

state = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "resourceTimelineMonth"}, "initialView": "resourceTimelineMonth", "resources": resources, "editable": True, "selectable": True, "height": "auto"}, key="calendar_final_attempt")

# 5. 드래그 업데이트 (에러 발생 시 st.rerun() 없이 상태 저장)
if state.get("eventDrop"):
    event = state["eventDrop"]["event"]
    try:
        supabase.table("production_schedule").update({
            "start": event["start"].split('T')[0],
            "end": event["start"].split('T')[0],
            "resourceId": event["resourceId"]
        }).eq("id", int(event["id"])).execute()
        st.session_state.sticky_error = None
        st.rerun()
    except Exception as e:
        st.session_state.sticky_error = f"업데이트 실패! 원인: {str(e)}"
        st.rerun()

# 6. 에러 고정 출력 (삭제 버튼 누르기 전까지 절대 안 사라짐)
if st.session_state.sticky_error:
    st.error(st.session_state.sticky_error)
    if st.button("에러 메시지 닫기"):
        st.session_state.sticky_error = None
        st.rerun()

# 7. 직접 등록 폼 (절대 안 사라짐)
st.markdown("---")
st.subheader("📝 생산 계획 직접 등록")
with st.form("direct_input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    t_date = col1.date_input("날짜 선택")
    t_res = col2.selectbox("설비 선택", [r['title'] for r in resources])
    p_name = col3.text_input("제품명 및 제조번호")
    if st.form_submit_button("일정 등록하기"):
        res_id = next(r['id'] for r in resources if r['title'] == t_res)
        supabase.table("production_schedule").insert({"resourceId": res_id, "title": p_name, "start": str(t_date), "end": str(t_date)}).execute()
        st.rerun()
