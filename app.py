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

# ... Các phần đọc file và xử lý dữ liệu giữ nguyên như trước ...

if not df.empty and "Tỷ lệ tổn thất" in df.columns:
    # Phân loại ngưỡng
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

    df_latest = df_unique[df_unique['Kỳ'] == 'Thực hiện']
    pie_data = df_latest["Ngưỡng tổn thất"].value_counts().reindex(pivot_df.index, fill_value=0)

    fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # Vẽ biểu đồ cột
    x = range(len(pivot_df))
    width = 0.35
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    for i, col in enumerate(pivot_df.columns):
        offset = (i - (len(pivot_df.columns)-1)/2) * width
        ax_bar.bar([xi + offset for xi in x], pivot_df[col], width, label=col, color=colors[i % len(colors)])

    ax_bar.set_ylabel("Số lượng", fontsize=8)
    ax_bar.set_title("Số lượng TBA theo ngưỡng tổn thất", fontsize=10, weight='bold')
    ax_bar.set_xticks(list(x))
    ax_bar.set_xticklabels(pivot_df.index, fontsize=7)
    ax_bar.legend(title="Kỳ", fontsize=6)
    ax_bar.grid(axis='y', linestyle='--', linewidth=0.5)

    # Vẽ biểu đồ donut
    wedges, texts, autotexts = ax_pie.pie(
        pie_data,
        labels=pivot_df.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        pctdistance=0.75,
        wedgeprops={'width': 0.3, 'edgecolor': 'w'}
    )
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontsize(6)

    ax_pie.text(0, 0, f"Tổng số TBA\n{pie_data.sum()}", ha='center', va='center', fontsize=8, fontweight='bold', color='black')
    ax_pie.set_title("Tỷ trọng TBA theo ngưỡng tổn thất", fontsize=10, weight='bold')

    st.pyplot(fig)

    # Lọc và hiển thị bảng
    nguong_options = ["(All)", "<2%", ">=2 và <3%", ">=3 và <4%", ">=4 và <5%", ">=5 và <7%", ">=7%"]
    nguong_filter = st.selectbox("Chọn ngưỡng để lọc danh sách TBA", nguong_options)
    if nguong_filter != "(All)":
        df_filtered = df[df["Ngưỡng tổn thất"] == nguong_filter]
    else:
        df_filtered = df

    st.markdown("### 📋 Danh sách chi tiết TBA")
    st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)
else:
    st.warning("Không có dữ liệu phù hợp để hiển thị biểu đồ.")
