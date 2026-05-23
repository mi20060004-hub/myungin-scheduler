import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인
st.set_page_config(layout="wide", page_title="PHOENIX 생산 스케줄러 3.0")

st.markdown("""
    <style>
    .block-tag {
        display: inline-block;
        background-color: #e1f5fe;
        color: #01579b;
        border-radius: 5px;
        padding: 2px 8px;
        margin: 2px;
        font-size: 0.85rem;
        border: 1px solid #01579b;
        font-weight: bold;
    }
    .date-col { background-color: #f8f9fa; font-weight: bold; text-align: center; }
    .stButton button { width: 100%; border-radius: 5px; height: 100%; min-height: 50px;}
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase 연결
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 3. 제품 리스트 불러오기 (팝업용)
@st.cache_data(ttl=60)
def get_products():
    try:
        res = supabase.table("product_master").select("제품명").execute()
        return [item["제품명"] for item in res.data]
    except:
        return ["제품 정보 없음"]

product_list = get_products()
equipment_list = ["P100", "SM100", "P400", "GS400"]

# 4. 생산 계획 편집 다이얼로그 (팝업창)
@st.dialog("📋 생산 계획 상세 편집")
def edit_plan(date, resource):
    st.write(f"📅 **날짜:** {date}  |  ⚙️ **설비:** {resource}")
    
    # 현재 할당된 항목 표시 및 삭제 기능
    st.subheader("현재 할당된 제품")
    res = supabase.table("production_schedule").select("*").eq("start", date).eq("resourceId", resource).execute()
    
    if res.data:
        for item in res.data:
            col_item, col_del = st.columns([4, 1])
            col_item.info(f"📦 {item['title']}")
            if col_del.button("❌", key=f"del_{item['id']}"):
                supabase.table("production_schedule").delete().eq("id", item['id']).execute()
                st.rerun()
    else:
        st.write("할당된 제품이 없습니다.")

    st.divider()
    
    # 새 제품 추가 폼
    st.subheader("새 제품 추가")
    with st.form("add_form", clear_on_submit=True):
        new_prod = st.selectbox("제품 선택", product_list)
        new_lot = st.text_input("제조번호 입력")
        if st.form_submit_button("➕ 계획 추가"):
            if new_prod and new_lot:
                full_title = f"{new_prod}({new_lot})"
                supabase.table("production_schedule").insert({
                    "start": date, "end": date, "resourceId": resource, "title": full_title
                }).execute()
                st.rerun()
            else:
                st.warning("제품과 제조번호를 모두 입력하세요.")

# 5. 메인 화면 구성
st.title("🏭 PHOENIX 생산 스케줄러 3.0")

# 날짜 범위 설정 (오늘 기준 전후 15일)
base_date = datetime.now().date()
date_range = [(base_date + timedelta(days=i)) for i in range(-5, 25)]

# 데이터 한꺼번에 가져오기
all_plans = supabase.table("production_schedule").select("*").execute().data

# 6. 그리드 렌더링
# 헤더 출력
cols = st.columns([1.5] + [2] * len(equipment_list))
cols[0].markdown("<div style='text-align:center; font-weight:bold;'>날짜</div>", unsafe_allow_html=True)
for i, eq in enumerate(equipment_list):
    cols[i+1].markdown(f"<div style='text-align:center; font-weight:bold;'>{eq}</div>", unsafe_allow_html=True)

st.divider()

# 날짜별 행 출력
for d in date_range:
    d_str = d.strftime("%Y-%m-%d")
    row_cols = st.columns([1.5] + [2] * len(equipment_list))
    
    # 1열: 날짜 표시
    row_cols[0].markdown(f"<div class='date-col'>{d_str}</div>", unsafe_allow_html=True)
    
    # 2~5열: 장비별 칸
    for i, eq in enumerate(equipment_list):
        # 해당 날짜/장비에 해당하는 모든 블록 찾기
        cell_plans = [p for p in all_plans if p['start'] == d_str and p['resourceId'] == eq]
        
        # 칸 내부 표시용 HTML 생성
        content_html = ""
        for p in cell_plans:
            content_html += f"<span class='block-tag'>{p['title']}</span>"
        
        # 버튼 클릭 시 팝업 실행
        with row_cols[i+1]:
            if st.button(f"편집", key=f"btn_{d_str}_{eq}"):
                edit_plan(d_str, eq)
            if content_html:
                st.markdown(content_html, unsafe_allow_html=True)

st.sidebar.markdown("""
### 🧭 사용 가이드
1. **장비명**: 가로 상단에 고정되어 있습니다.
2. **날짜**: 세로로 나열되며 스크롤이 가능합니다.
3. **입력/수정**: 원하는 칸의 **[편집]** 버튼을 누르세요.
4. **멀티 할당**: 팝업창에서 제품을 계속 추가하면 한 칸에 여러 블록이 쌓입니다.
""")
