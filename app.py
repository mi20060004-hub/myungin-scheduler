import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="PHOENIX 생산 스케줄러 3.0")

st.markdown("""
    <style>
    /* 상단 헤더 고정 */
    .sticky-header {
        position: fixed; top: 60px; left: 0; width: 100%;
        background-color: #f0f2f6; z-index: 999;
        display: flex; padding: 10px 0; border-bottom: 3px solid #d0d0d0;
    }
    .header-item { flex: 2; font-weight: bold; text-align: center; }
    .header-item.date-width { flex: 1; }
    .content-container { margin-top: 80px; }

    /* 핵심 변경: 박스 내부에 버튼을 고정 */
    .grid-cell {
        border: 1px solid #e0e0e0;
        min-height: 120px;
        padding: 10px;
        background-color: white;
        position: relative; /* 자식 요소(버튼)를 이 박스 안에 가둠 */
        display: flex;
        flex-direction: column;
    }
    .product-list { margin-bottom: 30px; } /* 버튼 영역 확보 */
    
    .btn-wrapper {
        position: absolute;
        bottom: 5px;
        right: 5px;
    }
    
    .block-tag {
        display: block;
        background-color: #e1f5fe;
        color: #01579b;
        border-radius: 4px;
        padding: 3px 6px;
        font-size: 0.75rem;
        border: 1px solid #b3e5fc;
        font-weight: 600;
        margin-bottom: 4px;
        width: fit-content;
    }
    </style>
    """, unsafe_allow_html=True)

# (중략: Supabase 및 다이얼로그 함수는 이전과 동일하게 유지)
# ... (앞의 edit_plan, get_products, get_products 함수 코드 그대로 사용)

# 5. 메인 그리드 렌더링 수정부
# ... (헤더 렌더링 코드 동일)

for d in date_range:
    d_str = d.strftime("%Y-%m-%d")
    row = st.columns([1] + [2]*len(equipment_list))
    row[0].markdown(f"<div class='date-col'>{d_str}</div>", unsafe_allow_html=True)
    
    for i, eq in enumerate(equipment_list):
        cell_plans = [p for p in all_plans if p['start'] == d_str and p['resourceId'] == eq]
        
        with row[i+1]:
            # HTML 박스 시작
            st.markdown(f"<div class='grid-cell'><div class='product-list'>", unsafe_allow_html=True)
            for p in cell_plans:
                st.markdown(f"<span class='block-tag'>{p['title']}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True) # 리스트 닫기
            
            # 버튼 영역을 별도 컨테이너로 감싸서 absolute 위치 적용
            with st.container():
                st.markdown("<div class='btn-wrapper'>", unsafe_allow_html=True)
                if st.button("✎ 편집", key=f"btn_{d_str}_{eq}"):
                    edit_plan(d_str, eq)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True) # grid-cell 닫기
