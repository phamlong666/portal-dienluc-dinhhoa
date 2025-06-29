import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.title("Ứng dụng Phân tích Tổn thất Điện năng")

menu = ["Trang chính", "⚡ Tổn thất hạ thế"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Trang chính":
    st.subheader("Trang chính - Chào mừng anh Long")

elif choice == "⚡ Tổn thất hạ thế":
    st.subheader("Báo cáo Tổn thất Hạ thế")

    mode = st.radio("Chọn chế độ báo cáo", ["Tháng", "Lũy kế"], horizontal=True)

    if mode == "Tháng":
        month = st.selectbox("Chọn tháng", list(range(1, 13)))
        year = st.selectbox("Chọn năm", list(range(2020, 2026)))
        st.write(f"Hiển thị dữ liệu Tháng {month}/{year}")
    else:
        year = st.selectbox("Chọn năm", list(range(2020, 2026)))
        st.write(f"Hiển thị dữ liệu Lũy kế năm {year}")

    # Load dữ liệu từ file trong folder "Tổn thất hạ thế" (ví dụ đã tải về server)
    file_path = 'TonThat_HaThe.xlsx'  # File tên ví dụ, thực tế lấy từ Drive
    df = pd.read_excel(file_path)

    if mode == "Tháng":
        df_filtered = df[(df['Tháng'] == month) & (df['Năm'] == year)]
    else:
        df_filtered = df[df['Năm'] == year]

    x = df_filtered['Tháng'] if mode == "Lũy kế" else [month]
    y_plan = df_filtered['KeHoach']
    y_actual = df_filtered['ThucHien']
    y_last = df_filtered['CungKy']

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(x, y_plan, marker='o', label='Kế hoạch', color='grey')
    ax.plot(x, y_actual, marker='o', label='Thực hiện', color='blue')
    ax.plot(x, y_last, marker='o', label='Cùng kỳ', color='orange')

    for i in range(len(x)):
        ax.text(x.iloc[i], y_plan.iloc[i]+0.02, f"{y_plan.iloc[i]:.2f}", fontsize=7, ha='center')
        ax.text(x.iloc[i], y_actual.iloc[i]-0.05, f"{y_actual.iloc[i]:.2f}", fontsize=7, ha='center')
        ax.text(x.iloc[i], y_last.iloc[i]+0.05, f"{y_last.iloc[i]:.2f}", fontsize=7, ha='center')

    ax.set_xlabel("Tháng")
    ax.set_ylabel("% Tổn thất")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    if not df_filtered.empty:
        last_val = y_actual.iloc[-1]
        last_val_last = y_last.iloc[-1]
        delta = last_val - last_val_last
        st.metric(label="Tỷ lệ tổn thất", value=f"{last_val:.2f}%", delta=f"{delta:+.2f}% so với cùng kỳ")
    else:
        st.warning("Không có dữ liệu cho lựa chọn này.")

# Kết thúc
