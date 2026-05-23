import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인 (바둑판 스타일)
st.set_page_config(layout="wide", page_title="PHOENIX 생산 스케줄러 3.0")

st.markdown("""
    <style>
    /* 바둑판 스타일 CSS */
    .grid-cell {
        border: 1px solid #e0e0e0;
        min-height: 80px;
        padding: 5px;
        background-color: white;
    }
    .header-cell {
        border: 1px solid #d0d0d0;
        background-color: #f0f2f6;
        font-weight: bold;
        text-align: center;
        padding: 10px;
    }
    .date-col { 
        border: 1px solid #d0d0d0;
        background-color: #f8f9fa; 
        font-weight: bold; 
        text-align: center;
        padding: 10px;
    }
    .block-tag {
        display: block;
        background-color: #e1f5fe;
        color: #01579b;
        border-radius: 4px;
        padding: 4px 8px;
        margin: 3px 0;
        font-size: 0.8rem;
        border: 1px solid #b3e5fc;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase 연결
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# 3. 제품 리스트 불러오기
@st.cache_data(ttl=60)
def get_products():
    try:
        res = supabase.table("product_master").select("제품명").execute()
        return [item["제품명"] for item in res.data]
    except: return ["제품 정보 없음"]

product_list = get_products()
equipment_list = ["P100", "SM100", "P400", "GS400"]

# 4. 생산 계획 편집 다이얼로그
@st.dialog("📋 계획 편집")
def edit_plan(date, resource):
    st.write(f"📅 {date} | ⚙️ {resource}")
    res = supabase.table("production_schedule").select("*").eq("start", date).eq("resourceId", resource).execute()
    
    if res.data:
        for item in res.data:
            c1, c2 = st.columns([4, 1])
            c1.info(f"📦 {item['title']}")
            if c2.button("❌", key=f"del_{item['id']}"):
                supabase.table("production_schedule").delete().eq("id", item['id']).execute()
                st.rerun()
    
    with st.form("add_form", clear_on_submit=True):
        new_prod = st.selectbox("제품", product_list)
        new_lot = st.text_input("제조번호")
        if st.form_submit_button("➕ 추가"):
            supabase.table("production_schedule").insert({"start": date, "resourceId": resource, "title": f"{new_prod}({new_lot})"}).execute()
            st.rerun()

# 5. 메인 그리드 렌더링
st.title("🏭 PHOENIX 생산 스케줄러 3.0")

# 날짜 범위 설정
base_date = datetime.now().date()
date_range = [(base_date + timedelta(days=i)) for i in range(15)]
all_plans = supabase.table("production_schedule").select("*").execute().data

# 헤더 그리기
header_cols = st.columns([1] + [2]*len(equipment_list))
header_cols[0].markdown("<div class='header-cell'>날짜</div>", unsafe_allow_html=True)
for i, eq in enumerate(equipment_list):
    header_cols[i+1].markdown(f"<div class='header-cell'>{eq}</div>", unsafe_allow_html=True)

# 행 그리기
for d in date_range:
    d_str = d.strftime("%Y-%m-%d")
    row = st.columns([1] + [2]*len(equipment_list))
    
    row[0].markdown(f"<div class='date-col'>{d_str}</div>", unsafe_allow_html=True)
    
    for i, eq in enumerate(equipment_list):
        cell_plans = [p for p in all_plans if p['start'] == d_str and p['resourceId'] == eq]
        
        with row[i+1]:
            st.markdown("<div class='grid-cell'>", unsafe_allow_html=True)
            if st.button("편집", key=f"btn_{d_str}_{eq}"):
                edit_plan(d_str, eq)
            for p in cell_plans:
                st.markdown(f"<span class='block-tag'>{p['title']}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
