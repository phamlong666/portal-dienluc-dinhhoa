import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

st.set_page_config(layout="wide", page_title="Báo cáo tổn thất TBA")
st.title("📥 AI_Trợ lý tổn thất")

FOLDER_ID = '165Txi8IyqG50uFSFHzWidSZSG9qpsbaq'

@st.cache_data
def get_drive_service():
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["google"],
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"Lỗi xác thực Google Drive: {e}")
        return None

@st.cache_data
def download_excel(file_id, sheet_name="Sheet1"):
    service = get_drive_service()
    if not service:
        return pd.DataFrame()
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return pd.read_excel(fh, sheet_name=sheet_name)
    except Exception as e:
        st.warning(f"Không thể tải hoặc đọc file: {e}")
        return pd.DataFrame()

# --- 🔌 Tổn thất các TBA công cộng ---
with st.expander("🔌 Tổn thất các TBA công cộng"):
    st.header("Phân tích dữ liệu TBA công cộng")
    st.write("(Đưa lại toàn bộ code TBA công cộng gốc của anh Long tại đây)")

# --- ⚡ Tổn thất hạ thế ---
with st.expander("⚡ Tổn thất hạ thế"):
    st.header("Phân tích dữ liệu tổn thất hạ thế")

    FOLDER_ID_HA = '1_rAY5T-unRyw20YwMgKuG1C0y7oq6GkK'

    def list_excel_files_ha():
        service = get_drive_service()
        if not service:
            return {}
        query = f"'{FOLDER_ID_HA}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
        try:
            results = service.files().list(q=query, fields="files(id, name)").execute()
            return {f['name']: f['id'] for f in results.get('files', [])}
        except Exception as e:
            st.error(f"Lỗi liệt kê file: {e}")
            return {}

    all_files_ha = list_excel_files_ha()

    nam = st.selectbox("Chọn năm", list(range(2020, datetime.now().year + 1))[::-1], index=0)
    thang = st.selectbox("Chọn tháng", list(range(1, 13)), index=0)
    loai_bc = st.radio("Loại báo cáo", ["Tháng", "Lũy kế"], index=0)

    selected_file = st.selectbox("Chọn file dữ liệu hạ thế", list(all_files_ha.keys()))

    if selected_file:
        # Chú ý: kiểm tra tên sheet thật sự trong file, có thể không phải 'dữ liệu'
        df_ha = download_excel(all_files_ha[selected_file], sheet_name=0)

        if not df_ha.empty:
            if 'Tháng' in df_ha.columns and 'Thực hiện' in df_ha.columns and 'Cùng kỳ' in df_ha.columns and 'Kế hoạch' in df_ha.columns:
                x = df_ha['Tháng']
                y_th = df_ha['Thực hiện']
                y_ck = df_ha['Cùng kỳ']
                y_kh = df_ha['Kế hoạch']

                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(x, y_th, marker='o', label='Thực hiện', color='blue')
                ax.plot(x, y_ck, marker='o', label='Cùng kỳ', color='orange')
                ax.plot(x, y_kh, marker='o', label='Kế hoạch', color='gray')

                for i, v in enumerate(y_th):
                    ax.text(x[i], v + 0.02, f"{v:.2f}", ha='center', fontsize=8)

                ax.set_ylabel("Tỷ lệ (%)")
                ax.set_xlabel("Tháng")
                ax.legend()
                ax.grid(True, linestyle='--', linewidth=0.5)
                ax.set_title("Biểu đồ tỷ lệ tổn thất hạ thế")

                st.pyplot(fig)

                tile = f"### Tỷ lệ tổn thất: {y_th.iloc[-1]:.2f}%"
                st.markdown(tile)

                diff_ck = y_th.iloc[-1] - y_ck.iloc[-1]
                diff_kh = y_th.iloc[-1] - y_kh.iloc[-1]

                st.write(f"So với cùng kỳ: {y_ck.iloc[-1]:.2f}% (chênh {diff_ck:+.2f}%)")
                st.write(f"So với kế hoạch: {y_kh.iloc[-1]:.2f}% (chênh {diff_kh:+.2f}%)")

                st.dataframe(df_ha)
            else:
                st.warning("File không chứa đủ cột cần thiết (Tháng, Thực hiện, Cùng kỳ, Kế hoạch).")
        else:
            st.warning("File trống hoặc không đúng định dạng.")
    else:
        st.warning("Chưa chọn file dữ liệu.")

# --- ⚡ Tổn thất trung thế (TBA Trung thế) ---
with st.expander("⚡ Tổn thất trung thế (TBA Trung thế)"):
    st.header("Phân tích dữ liệu TBA Trung áp (Trung thế)")
    st.write("(Đưa code gốc TBA Trung thế vào đây)")

# --- ⚡ Tổn thất các đường dây trung thế ---
with st.expander("⚡ Tổn thất các đường dây trung thế"):
    st.header("Phân tích dữ liệu tổn thất Đường dây Trung thế")
    st.write("(Đưa code gốc đường dây trung thế vào đây)")

# --- 🏢 Tổn thất toàn đơn vị ---
with st.expander("🏢 Tổn thất toàn đơn vị"):
    st.header("Phân tích dữ liệu tổn thất Toàn đơn vị")
    st.write("(Đưa code gốc toàn đơn vị vào đây)")
