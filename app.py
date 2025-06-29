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

# --- Khởi tạo Session State cho dữ liệu (Giữ nguyên cho các phần khác) ---
if 'df_tba_thang' not in st.session_state:
    st.session_state.df_tba_thang = None
if 'df_tba_luyke' not in st.session_state:
    st.session_state.df_tba_luyke = None
if 'df_tba_ck' not in st.session_state:
    st.session_state.df_tba_ck = None
if 'df_ha_thang' not in st.session_state:
    st.session_state.df_ha_thang = None
if 'df_ha_luyke' not in st.session_state:
    st.session_state.df_ha_luyke = None
if 'df_ha_ck' not in st.session_state:
    st.session_state.df_ha_ck = None
if 'df_trung_thang_tt' not in st.session_state:
    st.session_state.df_trung_thang_tt = None
if 'df_trung_luyke_tt' not in st.session_state:
    st.session_state.df_trung_ck_tt = None
if 'df_trung_thang_dy' not in st.session_state:
    st.session_state.df_trung_thang_dy = None
if 'df_trung_luyke_dy' not in st.session_state:
    st.session_state.df_trung_luyke_dy = None
if 'df_trung_ck_dy' not in st.session_state:
    st.session_state.df_trung_ck_dy = None
if 'df_dv_thang' not in st.session_state:
    st.session_state.df_dv_thang = None
if 'df_dv_luyke' not in st.session_state:
    st.session_state.df_dv_luyke = None
if 'df_dv_ck' not in st.session_state:
    st.session_state.df_dv_ck = None


# --- Biến và Hàm hỗ trợ tải dữ liệu từ Google Drive (từ app moi.py) ---
FOLDER_ID = '165Txi8IyqG50uFSFHzWidSZSG9qpsbaq' # ID thư mục Google Drive chứa file Excel

@st.cache_data
def get_drive_service():
    """Khởi tạo và trả về đối tượng dịch vụ Google Drive."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["google"],
            scopes=["https://www.googleapis.com/auth/drive.readonly"] # Chỉ cần quyền đọc
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"Lỗi khi xác thực Google Drive: {e}. Vui lòng kiểm tra cấu hình `secrets.toml`.")
        return None

@st.cache_data
def list_excel_files():
    """Liệt kê các file Excel trong thư mục Google Drive đã cho."""
    service = get_drive_service()
    if not service:
        return {}
    query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
        return {f['name']: f['id'] for f in results.get('files', [])}
    except Exception as e:
        st.error(f"Lỗi khi liệt kê file từ Google Drive: {e}. Vui lòng kiểm tra ID thư mục và quyền truy cập.")
        return {}

@st.cache_data
def download_excel(file_id):
    """Tải xuống file Excel từ Google Drive bằng ID file."""
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
            # st.progress(status.progress()) # Có thể thêm thanh tiến trình
        fh.seek(0)
        return pd.read_excel(fh, sheet_name=0)
    except Exception as e:
        st.warning(f"Không thể tải xuống hoặc đọc file với ID {file_id}. Lỗi: {e}. Có thể file không tồn tại hoặc không đúng định dạng sheet 'dữ liệu'.")
        return pd.DataFrame()

def generate_filenames(year, start_month, end_month):
    """Tạo danh sách tên file dự kiến dựa trên năm và tháng."""
    return [f"TBA_{year}_{str(m).zfill(2)}.xlsx" for m in range(start_month, end_month + 1)]

def load_data(file_list, all_files, nhan="Thực hiện"):
    """Tải và nối các DataFrame từ danh sách file."""
    dfs = []
    for fname in file_list:
        file_id = all_files.get(fname)
        if file_id:
            df = download_excel(file_id)
            if not df.empty:
                df["Kỳ"] = nhan
                dfs.append(df)
        else:
            st.info(f"Không tìm thấy file: {fname}")
    return pd.concat(dfs) if dfs else pd.DataFrame()

def classify_nguong(x):
    """Phân loại tỷ lệ tổn thất vào các ngưỡng."""
    try:
        # Chuyển đổi sang số nếu cần, xử lý dấu phẩy thành dấu chấm
        x = float(str(x).replace(",", "."))
    except (ValueError, TypeError):
        return "Không rõ" # Xử lý các giá trị không phải số

    if x < 2: return "<2%"
    elif 2 <= x < 3: return ">=2 và <3%"
    elif 3 <= x < 4: return ">=3 và <4%"
    elif 4 <= x < 5: return ">=4 và <5%"
    elif 5 <= x < 7: return ">=5 và <7%"
    else: return ">=7%"


# --- Các nút điều hướng chính (Expander) ---

with st.expander("🔌 Tổn thất các TBA công cộng"):
    st.header("Phân tích dữ liệu TBA công cộng")

    # Toàn bộ nội dung từ app moi.py được chèn vào đây
    col1, col2, col3 = st.columns(3)
    with col1:
        mode = st.radio("Chế độ phân tích", ["Theo tháng", "Lũy kế", "So sánh cùng kỳ", "Lũy kế cùng kỳ"], key="tba_mode")
    with col2:
        thang_from = st.selectbox("Từ tháng", list(range(1, 13)), index=0, key="tba_thang_from")
        # Đảm bảo thang_to không nhỏ hơn thang_from
        thang_to_options = list(range(thang_from, 13))
        # Đặt index mặc định để tránh lỗi khi thang_to_options rỗng
        default_index_thang_to = 0 if thang_to_options else None
        if "Lũy kế" in mode:
            # Chọn index sao cho nó không vượt quá kích thước của list options
            # Nếu tháng 5 là index 4 trong list 1-12, khi range bắt đầu từ 5, index 4 có thể là tháng 9
            # Cố gắng giữ tháng 5 làm tháng cuối mặc định nếu có thể
            if 5 in thang_to_options:
                default_index_thang_to = thang_to_options.index(5)
            elif len(thang_to_options) > 4: # Fallback nếu 5 không có, chọn tháng thứ 5 trong list mới
                 default_index_thang_to = 4
            else: # Nếu ít hơn 5 tháng, chọn tháng cuối cùng
                 default_index_thang_to = len(thang_to_options) - 1 if thang_to_options else None

            thang_to = st.selectbox("Đến tháng", thang_to_options, index=default_index_thang_to, key="tba_thang_to")
        else:
            thang_to = thang_from # Nếu không phải lũy kế, tháng đến bằng tháng từ

    with col3:
        nam = st.selectbox("Chọn năm", list(range(2020, datetime.now().year + 1))[::-1], index=0, key="tba_nam")
        nam_cungkỳ = nam - 1 if "cùng kỳ" in mode.lower() else None

    nguong_display = st.selectbox("Ngưỡng tổn thất", ["(All)", "<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"], key="tba_nguong_display")

    # Tải dữ liệu từ Google Drive
    all_files = list_excel_files()

    files = generate_filenames(nam, thang_from, thang_to if "Lũy kế" in mode or "cùng kỳ" in mode.lower() else thang_from)
    df = load_data(files, all_files, "Thực hiện")

    if "cùng kỳ" in mode.lower() and nam_cungkỳ:
        files_ck = generate_filenames(nam_cungkỳ, thang_from, thang_to if "Lũy kế" in mode or "cùng kỳ" in mode.lower() else thang_from)
        df_ck = load_data(files_ck, all_files, "Cùng kỳ")
        if not df_ck.empty:
            # Đảm bảo cột "Kỳ" là string để có thể concat
            df_ck["Kỳ"] = "Cùng kỳ"
            df = pd.concat([df, df_ck])

    if not df.empty and "Tỷ lệ tổn thất" in df.columns:
        # Đảm bảo cột Tỷ lệ tổn thất là số để apply classify_nguong
        df["Tỷ lệ tổn thất"] = pd.to_numeric(df["Tỷ lệ tổn thất"].astype(str).str.replace(',', '.'), errors='coerce')
        df["Ngưỡng tổn thất"] = df["Tỷ lệ tổn thất"].apply(classify_nguong)

        # Drop duplicates based on 'Tên TBA' and 'Kỳ' to count unique TBAs per period
        df_unique = df.drop_duplicates(subset=["Tên TBA", "Kỳ"])

        # Create count_df and pivot_df for plotting
        count_df = df_unique.groupby(["Ngưỡng tổn thất", "Kỳ"]).size().reset_index(name="Số lượng")
        pivot_df = count_df.pivot(index="Ngưỡng tổn thất", columns="Kỳ", values="Số lượng").fillna(0).astype(int)
        # Sắp xếp lại thứ tự các ngưỡng
        pivot_df = pivot_df.reindex(["<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"])

        # --- Vẽ biểu đồ ---
        fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(10, 3), dpi=300)

        # Biểu đồ cột
        x = range(len(pivot_df))
        width = 0.35
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # Màu sắc cho các cột
        for i, col in enumerate(pivot_df.columns):
            offset = (i - (len(pivot_df.columns)-1)/2) * width
            bars = ax_bar.bar([xi + offset for xi in x], pivot_df[col], width, label=col, color=colors[i % len(colors)])
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax_bar.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{int(height)}', ha='center', va='bottom', fontsize=5, fontweight='bold', color='black')

        ax_bar.set_ylabel("Số lượng", fontsize=5)
        ax_bar.set_title("Số lượng TBA theo ngưỡng tổn thất", fontsize=6, weight='bold')
        ax_bar.set_xticks(list(x))
        ax_bar.set_xticklabels(pivot_df.index, fontsize=5)
        ax_bar.tick_params(axis='y', labelsize=5)
        ax_bar.legend(title="Kỳ", fontsize=5)
        ax_bar.grid(axis='y', linestyle='--', linewidth=0.5)

        # Biểu đồ tròn (Tỷ trọng) - Ưu tiên dữ liệu 'Thực hiện' hoặc kỳ đầu tiên nếu không có
        pie_data = pd.Series(0, index=pivot_df.index) # Default empty
        if 'Thực hiện' in df_unique['Kỳ'].unique():
            df_latest = df_unique[df_unique['Kỳ'] == 'Thực hiện']
            pie_data = df_latest["Ngưỡng tổn thất"].value_counts().reindex(pivot_df.index, fill_value=0)
        elif not df_unique.empty and not pivot_df.empty:
            # Fallback to the first available period if 'Thực hiện' is not present
            first_col_data = pivot_df.iloc[:, 0]
            if first_col_data.sum() > 0:
                pie_data = first_col_data

        if pie_data.sum() > 0:
            wedges, texts, autotexts = ax_pie.pie(
                pie_data,
                labels=pivot_df.index,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                pctdistance=0.75,
                wedgeprops={'width': 0.3, 'edgecolor': 'w'}
            )

            for text in texts:
                text.set_fontsize(4)
                text.set_fontweight('bold')
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontsize(4)
                autotext.set_fontweight('bold')

            ax_pie.text(0, 0, f"Tổng số TBA\\n{pie_data.sum()}", ha='center', va='center', fontsize=5, fontweight='bold', color='black')
            ax_pie.set_title("Tỷ trọng TBA theo ngưỡng tổn thất", fontsize=6, weight='bold')
        else:
            ax_pie.text(0.5, 0.5, "Không có dữ liệu tỷ trọng phù hợp", horizontalalignment='center', verticalalignment='center', transform=ax_pie.transAxes, fontsize=6)
            ax_pie.set_title("Tỷ trọng TBA theo ngưỡng tổn thất", fontsize=6, weight='bold')


        st.pyplot(fig)

        # --- Danh sách chi tiết TBA ---
        nguong_filter = st.selectbox("Chọn ngưỡng để lọc danh sách TBA", ["(All)", "<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"], key="tba_detail_filter")
        if nguong_filter != "(All)":
            df_filtered = df[df["Ngưỡng tổn thất"] == nguong_filter]
        else:
            df_filtered = df

        st.markdown("### 📋 Danh sách chi tiết TBA")
        st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

    else:
        st.warning("Không có dữ liệu phù hợp để hiển thị biểu đồ. Vui lòng kiểm tra các file Excel trên Google Drive và định dạng của chúng (cần cột 'Tỷ lệ tổn thất').")



with st.expander("⚡ Tổn thất hạ thế"):
    st.header("Phân tích dữ liệu tổn thất hạ thế")

    FOLDER_ID_HA = '1_rAY5T-unRyw20YwMgKuG1C0y7oq6GkK'

    @st.cache_data
    def list_excel_files_ha():
        service = get_drive_service()
        if not service:
            return {}
        query = f"'{FOLDER_ID_HA}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
        try:
            results = service.files().list(q=query, fields="files(id, name)").execute()
            return {f['name']: f['id'] for f in results.get('files', [])}
        except Exception as e:
            st.error(f"Lỗi liệt kê file hạ thế: {e}")
            return {}

    all_files_ha = list_excel_files_ha()
    nam = st.selectbox("Chọn năm", list(range(2020, datetime.now().year + 1))[::-1], index=0, key="ha_nam")
    thang = st.selectbox("Chọn tháng", list(range(1, 13)), index=0, key="ha_thang")

    df_list = []
    df_list_ck = []
    df_list_kh = []

    for i in range(1, thang + 1):
        fname = f"HA_{nam}_{i:02}.xlsx"
        fname_ck = f"HA_{nam - 1}_{i:02}.xlsx"
        file_id = all_files_ha.get(fname)
        file_id_ck = all_files_ha.get(fname_ck)

        if file_id:
            df = download_excel(file_id)
            if not df.empty and df.shape[0] >= 1:
                try:
                    ty_le_th = float(str(df.iloc[0, 4]).replace(",", "."))  # Thực hiện (cột E)
                    ty_le_ck = float(str(df.iloc[0, 5]).replace(",", ".")) if df.shape[1] >= 6 else None  # Cùng kỳ (cột F nếu có)
                    ty_le_kh = float(str(df.iloc[0, 6]).replace(",", ".")) if df.shape[1] >= 7 else None  # Kế hoạch (cột G nếu có)

                    df_list.append({"Tháng": i, "Tỷ lệ": ty_le_th})
                    if ty_le_ck is not None:
                        df_list_ck.append({"Tháng": i, "Tỷ lệ": ty_le_ck})
                    if ty_le_kh is not None:
                        df_list_kh.append({"Tháng": i, "Tỷ lệ": ty_le_kh})
                except:
                    st.warning(f"Lỗi đọc dữ liệu file: {fname}")

    df_th = pd.DataFrame(df_list).sort_values("Tháng")
    df_ck = pd.DataFrame(df_list_ck).sort_values("Tháng") if df_list_ck else pd.DataFrame()
    df_kh = pd.DataFrame(df_list_kh).sort_values("Tháng") if df_list_kh else pd.DataFrame()

    if not df_th.empty:
        fig, ax = plt.subplots(figsize=(6, 3), dpi=150)

        ax.plot(df_th["Tháng"], df_th["Tỷ lệ"], marker='o', color='blue', label='Thực hiện', linewidth=1)
        if not df_ck.empty:
            ax.plot(df_ck["Tháng"], df_ck["Tỷ lệ"], marker='o', color='orange', label='Cùng kỳ', linewidth=1)
        if not df_kh.empty:
            ax.plot(df_kh["Tháng"], df_kh["Tỷ lệ"], marker='o', color='gray', label='Kế hoạch', linewidth=1)

        for i, v in enumerate(df_th["Tỷ lệ"]):
            ax.text(df_th["Tháng"].iloc[i], v + 0.05, f"{v:.2f}", ha='center', fontsize=6, color='black')

        ax.set_ylabel("Tỷ lệ (%)", fontsize=8, color='black')
        ax.set_xlabel("Tháng", fontsize=8, color='black')
        ax.tick_params(axis='both', colors='black', labelsize=6)
        ax.grid(True, linestyle='--', linewidth=0.5)
        ax.set_title("Biểu đồ tỷ lệ tổn thất hạ thế", fontsize=10, color='black')
        ax.legend(fontsize=6)

        st.pyplot(fig)
        st.dataframe(df_th)

    else:
        st.warning("Không có dữ liệu phù hợp để hiển thị.")
with st.expander("⚡ Tổn thất trung thế (TBA Trung thế)"):
    st.header("Phân tích dữ liệu TBA Trung áp (Trung thế)")
    st.info("Nội dung phân tích mới cho TBA Trung thế sẽ được viết tại đây.")
    if st.session_state.df_trung_thang_tt is not None:
        st.dataframe(st.session_state.df_trung_thang_tt)
    else:
        st.warning("Chưa có dữ liệu TBA Trung áp (Trung thế) để hiển thị.")


with st.expander("⚡ Tổn thất các đường dây trung thế"):
    st.header("Phân tích dữ liệu tổn thất Đường dây Trung thế")
    st.info("Nội dung phân tích mới cho đường dây trung thế sẽ được viết tại đây.")
    if st.session_state.df_trung_thang_dy is not None:
        st.dataframe(st.session_state.df_trung_thang_dy)
    else:
        st.warning("Chưa có dữ liệu tổn thất Đường dây Trung thế để hiển thị.")


with st.expander("🏢 Tổn thất toàn đơn vị"):
    st.header("Phân tích dữ liệu tổn thất Toàn đơn vị")
    st.info("Nội dung phân tích mới cho toàn đơn vị sẽ được viết tại đây.")
    if st.session_state.df_dv_thang is not None:
        st.dataframe(st.session_state.df_dv_thang)
    else:
        st.warning("Chưa có dữ liệu tổn thất Toàn đơn vị để hiển thị.")