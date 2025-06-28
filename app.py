import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

st.set_page_config(layout="wide", page_title="Phân tích tổn thất TBA công cộng")
st.title("📊 Phân tích tổn thất các TBA công cộng")

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

all_files = list_excel_files()

files = generate_filenames(nam, thang_from, thang_to if "Lũy kế" in mode else thang_from)
df = load_data(files, all_files, "Thực hiện")
if "cùng kỳ" in mode.lower() and nam_cungkỳ:
    files_ck = generate_filenames(nam_cungkỳ, thang_from, thang_to if "Lũy kế" in mode else thang_from)
    df_ck = load_data(files_ck, all_files, "Cùng kỳ")
    df = pd.concat([df, df_ck])

if not df.empty and "Tỷ lệ tổn thất" in df.columns:
    def classify_nguong(x):
        if x < 2: return "<2%"
        elif 2 <= x < 3: return ">=2 và <3%"
        elif 3 <= x < 4: return ">=3 và <4%"
        elif 4 <= x < 5: return ">=4 và <5%"
        elif 5 <= x < 7: return ">=5 và <7%"
        else: return ">=7%"
    df["Ngưỡng tổn thất"] = df["Tỷ lệ tổn thất"].apply(classify_nguong)

    st.subheader(f"🔍 Biểu đồ tổn thất - Tháng {thang_from} / {nam}")
    count_df = df.groupby(["Ngưỡng tổn thất", "Kỳ"]).size().reset_index(name="Số lượng")
    pivot_df = count_df.pivot(index="Ngưỡng tổn thất", columns="Kỳ", values="Số lượng").fillna(0).astype(int)
    pivot_df = pivot_df.reindex(["<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"])
    pivot_df = pivot_df.loc[~pivot_df.index.isnull()]

    fig, ax = plt.subplots(figsize=(10, 4))
    width = 0.35
    x = range(len(pivot_df))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    for i, col in enumerate(pivot_df.columns):
        offset = (i - (len(pivot_df.columns)-1)/2) * width
        bars = ax.bar([xi + offset for xi in x], pivot_df[col], width, label=col, color=colors[i % len(colors)])
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 1, f'{int(height)}', ha='center', fontsize=8, color='black')

    ax.set_xticks(list(x))
    ax.set_xticklabels(pivot_df.index, fontsize=9)
    ax.set_ylabel("Số lượng", fontsize=9)
    ax.set_title("Số lượng TBA theo ngưỡng tổn thất", fontsize=11, weight='bold')
    ax.legend(title="Kỳ", fontsize=8)
    ax.grid(axis='y', linestyle='--', linewidth=0.5)
    st.pyplot(fig)

    # BIỂU ĐỒ DONUT
    st.markdown("### 🎯 Tỷ trọng TBA theo ngưỡng tổn thất")
    df_unique = df.drop_duplicates(subset="Tên TBA")  # Chỉnh: loại trùng TBA
    pie_data = df_unique["Ngưỡng tổn thất"].value_counts().reindex(
        ["<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"],
        fill_value=0
    )
    fig2, ax2 = plt.subplots(figsize=(2.5, 2.5))  # Chỉnh nhỏ biểu đồ
    wedges, _, autotexts = ax2.pie(
        pie_data,
        labels=None,
        autopct=lambda p: f'{p:.2f}%' if p > 0 else '',
        startangle=90,
        colors=["#1f77b4", "#ff7f0e", "#c7c7c7", "#bcbd22", "#2ca02c", "#d62728"],
        wedgeprops={'width': 0.35}
    )
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_fontweight("bold")
    ax2.text(0, 0, f"Tổng số TBA\n{pie_data.sum()}", ha='center', va='center', fontsize=10, fontweight='bold')
    ax2.set_title("Tỷ trọng TBA theo ngưỡng tổn thất", fontsize=10)
    st.pyplot(fig2)

    st.markdown("### 📋 Danh sách chi tiết TBA")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

else:
    st.warning("Không có dữ liệu phù hợp để hiển thị biểu đồ.")
