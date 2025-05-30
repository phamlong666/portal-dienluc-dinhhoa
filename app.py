import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cổng điều hành EVNNPC - Định Hóa", layout="wide")
st.title("🟧 Trung tâm điều hành số - EVNNPC Điện lực Định Hóa")

st.sidebar.title("📚 Danh mục hệ thống")

# Đọc menu từ Google Sheet công khai
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuo5p3L_PeUYlKJcEkLf8AeQZnnjVWlTZ0pyTCI_2MgLPiFUPSRafFLJPkVY59YZFzLUwklqKUtbJR/pub?gid=0&single=true&output=csv"
try:
    df = pd.read_csv(sheet_url)
    for section in df['Nhóm chức năng'].unique():
        st.sidebar.markdown(f"### {section}")
        for _, row in df[df['Nhóm chức năng'] == section].iterrows():
            st.sidebar.markdown(f"- [{row['Tên ứng dụng']}]({row['Liên kết']})")
except:
    st.sidebar.error("Không thể tải menu từ Google Sheet. Kiểm tra đường dẫn hoặc quyền chia sẻ.")

st.info("""
Chào mừng anh Long đến với cổng điều hành số tổng hợp của Điện lực Định Hóa. 

Tại đây, anh có thể truy cập nhanh vào toàn bộ hệ thống EVNNPC, 
kết hợp các công cụ do Mắt Nâu hỗ trợ như nhập liệu, phân tích tổn thất, 
báo cáo kỹ thuật, và ghi nhớ lịch sử GPT.

✔️ Toàn bộ menu sidebar được tự động sinh từ Google Sheet. 
Anh chỉ cần cập nhật bảng là hệ thống sẽ hiển thị ngay menu mới.
""")
