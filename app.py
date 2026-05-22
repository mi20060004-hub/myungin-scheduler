import streamlit as st
from supabase import create_client

# 깃허브 Secrets에서 값을 불러옵니다.
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

# 연결 테스트
try:
    supabase = create_client(url, key)
    st.title("연결 테스트 성공! 🎉")
    st.write("Supabase 프로젝트와 성공적으로 연결되었습니다.")
    
    # 데이터가 있는지 확인
    response = supabase.table("product_master").select("*").limit(5).execute()
    st.write("product_master 테이블 샘플 데이터:")
    st.dataframe(response.data)
except Exception as e:
    st.error(f"연결 실패: {e}")
