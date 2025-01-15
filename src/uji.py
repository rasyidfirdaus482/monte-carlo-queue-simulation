import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st

# Data dengan penyesuaian panjang array
# raw_data = {
#     "Jarak Kedatangan (menit)": [1, 2, 3, 4, 5] * 4,  # Mengulang data agar panjangnya sesuai
#     "Frekuensi Kedatangan Konsumen": [0.20] * 20,  # Menyesuaikan panjang array
#     "Lama Pelayanan (menit)": list(range(5, 25)),  # 5 hingga 24
#     "Frekuensi Pelayanan Konsumen": [0.05] * 20,  # Menyesuaikan panjang array
# }
raw_data = {
    "Jarak Kedatangan (menit)": [0, 1, 2, 3, 4, 5] * 2 + [0, 1],  
    "Frekuensi Kedatangan Konsumen": [0.20] * 14,  # Probabilitas
    "Lama Pelayanan (menit)": list(range(11, 25)),
    "Frekuensi Pelayanan Konsumen": [0.05] * 14,  # Probabilitas
}

# Membuat DataFrame
df = pd.DataFrame(raw_data)

# Streamlit Layout
st.title("Analisis Distribusi Antrian")

# Menampilkan data yang telah diolah
st.subheader("Tabel Data")
st.write(df)

# 1. Visualisasi Histogram - Waktu Kedatangan
st.subheader("Distribusi Waktu Kedatangan")
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.hist(df["Jarak Kedatangan (menit)"], bins=5, alpha=0.7, color='b', edgecolor='black')
ax1.set_title('Distribusi Jarak Kedatangan')
ax1.set_xlabel('Jarak Kedatangan (menit)')
ax1.set_ylabel('Frekuensi')
st.pyplot(fig1)

# 2. Visualisasi Histogram - Waktu Pelayanan
st.subheader("Distribusi Waktu Pelayanan")
fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.hist(df["Lama Pelayanan (menit)"], bins=10, alpha=0.7, color='g', edgecolor='black')
ax2.set_title('Distribusi Lama Pelayanan')
ax2.set_xlabel('Lama Pelayanan (menit)')
ax2.set_ylabel('Frekuensi')
st.pyplot(fig2)

# 3. Uji Kolmogorov-Smirnov (KS) dan Shapiro-Wilk untuk kesesuaian distribusi
from scipy.stats import kstest, shapiro

# Uji Kolmogorov-Smirnov untuk Waktu Kedatangan (menggunakan distribusi eksponensial)
ks_stat_1, ks_p_1 = kstest(df["Jarak Kedatangan (menit)"], 'expon')
st.subheader("Hasil Uji Kolmogorov-Smirnov untuk Waktu Kedatangan")
st.write(f"Statistik = {ks_stat_1:.4f}, p-value = {ks_p_1:.4f}")

# Uji Kolmogorov-Smirnov untuk Waktu Pelayanan (menggunakan distribusi gamma)
ks_stat_2, ks_p_2 = kstest(df["Lama Pelayanan (menit)"], 'gamma', args=(2,))
st.subheader("Hasil Uji Kolmogorov-Smirnov untuk Waktu Pelayanan")
st.write(f"Statistik = {ks_stat_2:.4f}, p-value = {ks_p_2:.4f}")

# Uji Shapiro-Wilk untuk Waktu Kedatangan
shapiro_stat_1, shapiro_p_1 = shapiro(df["Jarak Kedatangan (menit)"])
st.subheader("Hasil Uji Shapiro-Wilk untuk Waktu Kedatangan")
st.write(f"Statistik = {shapiro_stat_1:.4f}, p-value = {shapiro_p_1:.4f}")

# Uji Shapiro-Wilk untuk Waktu Pelayanan
shapiro_stat_2, shapiro_p_2 = shapiro(df["Lama Pelayanan (menit)"])
st.subheader("Hasil Uji Shapiro-Wilk untuk Waktu Pelayanan")
st.write(f"Statistik = {shapiro_stat_2:.4f}, p-value = {shapiro_p_2:.4f}")
