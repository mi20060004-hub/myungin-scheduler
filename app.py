import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 생산 계획 다중 할당 시트")

# 2. 제품 리스트 가져오기 (Supabase product_master 테이블)
def get_product_list():
    try:
        res = supabase.table("product_master").select("제품명").execute()
        return [item["제품명"] for item in res.data]
    except:
        return ["데이터 없음"]

product_options = get_product_list()

# 3. 그리드 데이터 구성
equipment_list = ["P100", "SM100", "P400", "GS400"]
start_date = datetime.now().date() - timedelta(days=5)
date_strings = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]

# 4. 데이터 로드 및 다중 선택형 에디터
df = pd.DataFrame("", index=date_strings, columns=equipment_list)
# 데이터 채우기 (생략, 기존과 동일)

# 여기서 핵심: 각 셀을 '다중 선택'이 가능한 텍스트 필드로 처리
st.info("💡 셀을 클릭하고 내용을 입력하세요. 여러 제품을 넣으려면 쉼표(,)로 구분해서 입력하세요.")
edited_df = st.data_editor(
    df, 
    column_config={
        col: st.column_config.TextColumn(col, help="제품명(제조번호)를 쉼표로 구분하여 입력") 
        for col in equipment_list
    },
    use_container_width=True
)

# 5. 저장 로직 (동일)
if st.button("💾 변경사항 저장"):
    # sync_to_db 함수 호출...
    st.success("저장 완료!")
