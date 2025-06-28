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

# Dummy dữ liệu demo
data = {
    "Tên TBA": ["TBA 1", "TBA 2", "TBA 3", "TBA 4", "TBA 5", "TBA 6"],
    "Kỳ": ["Thực hiện", "Thực hiện", "Cùng kỳ", "Cùng kỳ", "Thực hiện", "Cùng kỳ"],
    "Tỷ lệ tổn thất": [1.5, 2.8, 3.5, 4.2, 5.1, 6.3]
}
df = pd.DataFrame(data)

if not df.empty and "Tỷ lệ tổn thất" in df.columns:
    def classify_nguong(x):
        if x < 2: return "<2%"
        elif 2 <= x < 3: return ">=2 và <3%"
        elif 3 <= x < 4: return ">=3 và <4%"
        elif 4 <= x < 5: return ">=4 và <5%"
        elif 5 <= x < 7: return ">=5 và <7%"
        else: return ">=7%"
    df["Ngưỡng tổn thất"] = df["Tỷ lệ tổn thất"].apply(classify_nguong)

    df_unique = df.drop_duplicates(subset=["Tên TBA", "Kỳ"])

    count_df = df_unique.groupby(["Ngưỡng tổn thất", "Kỳ"]).size().reset_index(name="Số lượng")
    pivot_df = count_df.pivot(index="Ngưỡng tổn thất", columns="Kỳ", values="Số lượng").fillna(0).astype(int)
    pivot_df = pivot_df.reindex(["<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"])

    fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(10, 3), dpi=400)

    x = range(len(pivot_df))
    width = 0.35
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    for i, col in enumerate(pivot_df.columns):
        offset = (i - (len(pivot_df.columns)-1)/2) * width
        bars = ax_bar.bar([xi + offset for xi in x], pivot_df[col], width, label=col, color=colors[i % len(colors)])
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax_bar.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{int(height)}', ha='center', va='bottom', fontsize=7, fontweight='bold', color='black')

    ax_bar.set_ylabel("Số lượng", fontsize=7)
    ax_bar.set_title("Số lượng TBA theo ngưỡng tổn thất", fontsize=8, weight='bold')
    ax_bar.set_xticks(list(x))
    ax_bar.set_xticklabels(pivot_df.index, fontsize=7, fontweight='bold')
    ax_bar.tick_params(axis='y', labelsize=7)
    ax_bar.legend(title="Kỳ", fontsize=7)
    ax_bar.grid(axis='y', linestyle='--', linewidth=0.5)

    df_latest = df_unique[df_unique['Kỳ'] == 'Thực hiện']
    pie_data = df_latest["Ngưỡng tổn thất"].value_counts().reindex(pivot_df.index, fill_value=0)

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
        text.set_fontsize(6)
        text.set_fontweight('bold')
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontsize(6)
        autotext.set_fontweight('bold')

    ax_pie.text(0, 0, f"Tổng số TBA\n{pie_data.sum()}", ha='center', va='center', fontsize=7, fontweight='bold', color='black')
    ax_pie.set_title("Tỷ trọng TBA theo ngưỡng tổn thất", fontsize=8, weight='bold')

    st.pyplot(fig)

    nguong_filter = st.selectbox("Chọn ngưỡng để lọc danh sách TBA", ["(All)", "<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"])
    if nguong_filter != "(All)":
        df_filtered = df[df["Ngưỡng tổn thất"] == nguong_filter]
    else:
        df_filtered = df

    st.markdown("### 📋 Danh sách chi tiết TBA")
    df_filtered_reset = df_filtered.reset_index(drop=True)
    df_filtered_reset.index += 1
    df_filtered_reset.reset_index(inplace=True)
    df_filtered_reset.rename(columns={'index': 'STT'}, inplace=True)
    st.dataframe(df_filtered_reset, use_container_width=True)
else:
    st.warning("Không có dữ liệu phù hợp để hiển thị biểu đồ.")
