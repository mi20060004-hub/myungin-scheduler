import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="PHOENIX 생산 스케줄러 3.0")

st.markdown("""
    <style>
    /* 상단 헤더 고정 (가장 중요) */
    .sticky-header {
        position: fixed;
        top: 60px; /* Streamlit 기본 상단 메뉴 높이 고려 */
        left: 0;
        width: 100%;
        background-color: #f0f2f6;
        z-index: 999;
        display: flex;
        padding: 10px 0;
        border-bottom: 3px solid #d0d0d0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .header-item { flex: 2; font-weight: bold; text-align: center; }
    .header-item.date-width { flex: 1; }
    
    /* 본문 영역 - 상단 헤더에 가리지 않게 상단 여백 확보 */
    .content-container { margin-top: 100px; }
    
    .grid-cell {
        border: 1px solid #e0e0e0;
        min-height: 100px;
        padding: 8px;
        background-color: white;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    .date-col { 
        border: 1px solid #d0d0d0;
        background-color: #f8f9fa; 
        font-weight: bold; 
        text-align: center;
        padding: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .block-tag {
        display: block;
        background-color: #e1f5fe;
        color: #01579b;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 0.8rem;
        border: 1px solid #b3e5fc;
        font-weight: 600;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase 연결 및 함수들
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=60)
def get_products():
    try:
        res = supabase.table("product_master").select("제품명").execute()
        return [item["제품명"] for item in res.data]
    except: return ["제품 정보 없음"]

product_list = get_products()
equipment_list = ["P100", "SM100", "P400", "GS400"]

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

# 3. UI 렌더링
st.title("🏭 PHOENIX 생산 스케줄러 3.0")

# 고정 헤더 영역 (HTML로 직접 고정)
header_html = f"""
<div class='sticky-header'>
    <div class='header-item date-width'>날짜</div>
    {''.join([f"<div class='header-item'>{eq}</div>" for eq in equipment_list])}
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# 본문 영역 시작
st.markdown("<div class='content-container'>", unsafe_allow_html=True)

all_plans = supabase.table("production_schedule").select("*").execute().data
date_range = [(datetime.now().date() + timedelta(days=i)) for i in range(20)]

for d in date_range:
    d_str = d.strftime("%Y-%m-%d")
    row = st.columns([1] + [2]*len(equipment_list))
    row[0].markdown(f"<div class='date-col'>{d_str}</div>", unsafe_allow_html=True)
    
    for i, eq in enumerate(equipment_list):
        cell_plans = [p for p in all_plans if p['start'] == d_str and p['resourceId'] == eq]
        with row[i+1]:
            st.markdown("<div class='grid-cell'>", unsafe_allow_html=True)
            if st.button("✎ 편집", key=f"btn_{d_str}_{eq}"):
                edit_plan(d_str, eq)
            for p in cell_plans:
                st.markdown(f"<span class='block-tag'>{p['title']}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # content-container 종료
