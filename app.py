import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import seaborn as sns

st.set_page_config(layout="wide", page_title="Phân tích tổn thất TBA công cộng")
st.title("📊 Phân tích tổn thất các TBA công cộng")

# ============ CẤU HÌNH ============
col1, col2, col3 = st.columns(3)
with col1:
    mode = st.radio("Chế độ phân tích", ["Theo tháng", "Lũy kế", "So sánh cùng kỳ", "Lũy kế cùng kỳ"])
with col2:
    thang_from = st.selectbox("Từ tháng", list(range(1, 13)), index=0)
    thang_to = st.selectbox("Đến tháng", list(range(thang_from, 13)), index=4) if "Lũy kế" in mode else thang_from
with col3:
    nam = st.selectbox("Chọn năm", list(range(2020, datetime.now().year + 1))[::-1], index=0)
    nam_cungkỳ = nam - 1 if "cùng kỳ" in mode.lower() else None

nguong = st.selectbox("Ngưỡng tổn thất", ["(All)", "<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"])

FOLDER_ID = '165Txi8IyqG50uFSFHzWidSZSG9qpsbaq'

@st.cache_data
def get_drive_service():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["google"],
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build('drive', 'v3', credentials=credentials)

@st.cache_data
def list_excel_files():
    service = get_drive_service()
    query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return {f['name']: f['id'] for f in results.get('files', [])}

def download_excel(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    try:
        return pd.read_excel(fh, sheet_name="dữ liệu")
    except:
        return pd.DataFrame()

def generate_filenames(year, start_month, end_month):
    return [f"TBA_{year}_{str(m).zfill(2)}.xlsx" for m in range(start_month, end_month + 1)]

def load_data(file_list, all_files, nhan="Thực hiện"):
    dfs = []
    for fname in file_list:
        file_id = all_files.get(fname)
        if file_id:
            df = download_excel(file_id)
            if not df.empty:
                df["Kỳ"] = nhan
                dfs.append(df)
    return pd.concat(dfs) if dfs else pd.DataFrame()

# ============ PHÂN TÍCH ============
all_files = list_excel_files()

files = generate_filenames(nam, thang_from, thang_to if "Lũy kế" in mode else thang_from)
df = load_data(files, all_files, "Thực hiện")
if "cùng kỳ" in mode.lower() and nam_cungkỳ:
    files_ck = generate_filenames(nam_cungkỳ, thang_from, thang_to if "Lũy kế" in mode else thang_from)
    df_ck = load_data(files_ck, all_files, "Cùng kỳ")
    df = pd.concat([df, df_ck])

if not df.empty and all(col in df.columns for col in ["Tổn thất (KWh)", "ĐN nhận đầu nguồn"]):
    df = df.copy()
    for col in ["Tỷ lệ tổn thất", "So sánh"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: round(x, 2))

    def classify_nguong(x):
        if x < 2: return "<2%"
        elif 2 <= x < 3: return ">=2 và <3%"
        elif 3 <= x < 4: return ">=3 và <4%"
        elif 4 <= x < 5: return ">=4 và <5%"
        elif 5 <= x < 7: return ">=5 và <7%"
        else: return ">=7%"

    if "Tỷ lệ tổn thất" in df.columns:
        df["Ngưỡng tổn thất"] = df["Tỷ lệ tổn thất"].apply(classify_nguong)

    if nguong != "(All)":
        df = df[df["Ngưỡng tổn thất"] == nguong]

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        count_df = df.groupby(["Ngưỡng tổn thất", "Kỳ"]).size().unstack(fill_value=0).reset_index()
        fig, ax = plt.subplots(figsize=(6, 3.2))
        width = 0.35
        x = range(len(count_df))
        cols = list(count_df.columns)
        cols.remove("Ngưỡng tổn thất")
        palette = sns.color_palette("Set2", len(cols))
        for i, col in enumerate(cols):
            offset = (i - (len(cols) - 1)/2) * width
            bars = ax.bar([xi + offset for xi in x], count_df[col], width, label=col, color=palette[i])
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, height + 1, f'{int(height)}', ha='center', fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(count_df["Ngưỡng tổn thất"], fontsize=9)
        ax.set_title("Số lượng TBA theo ngưỡng tổn thất", fontsize=11)
        ax.set_ylabel("Số lượng", fontsize=9)
        ax.legend(fontsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        st.pyplot(fig)

    with col2:
        count_pie = df["Ngưỡng tổn thất"].value_counts().reindex([
            "<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"
        ], fill_value=0)
        fig2, ax2 = plt.subplots(figsize=(3.2, 3.2))
        colors_pie = sns.color_palette("Set2", len(count_pie))
        wedges, texts, autotexts = ax2.pie(
            count_pie,
            labels=None,
            autopct=lambda p: f'{p:.1f}%' if p > 0 else '',
            startangle=90,
            colors=colors_pie,
            wedgeprops={'width': 0.35}
        )
        for autotext in autotexts:
            autotext.set_fontsize(7)
        ax2.text(0, 0, f"Tổng số TBA\n{count_pie.sum()}", ha='center', va='center', fontsize=9, fontweight='bold')
        ax2.set_title("Tỷ trọng theo ngưỡng", fontsize=10)
        st.pyplot(fig2)

    st.markdown("---")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Không có dữ liệu phù hợp hoặc thiếu file Excel trong thư mục Drive.")
