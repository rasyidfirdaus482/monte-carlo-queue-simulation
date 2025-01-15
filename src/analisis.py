import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime
from scipy import stats
import numpy as np

# Data kedatangan dan pelayanan
data = [
    ["08:05", "08:05", "08:17"],
    ["08:08", "08:17", "08:28"],
    ["08:09", "08:28", "08:36"],
    ["08:11", "08:11", "08:23"],
    ["08:16", "08:36", "08:48"],
    ["08:20", "08:20", "08:36"],
    ["08:22", "08:22", "08:38"],
    ["08:23", "08:23", "08:34"],
    ["08:23", "08:23", "08:37"],
    ["08:25", "08:38", "08:50"],
    ["08:25", "08:48", "09:05"],
    ["08:26", "08:38", "08:51"],
    ["08:27", "08:51", "09:07"],
    ["08:29", "09:07", "09:19"],
    ["08:31", "09:19", "09:27"],
    ["08:34", "09:27", "09:36"],
    ["08:35", "08:36", "08:41"],
    ["08:37", "08:37", "08:50"],
    ["08:39", "08:39", "08:55"],
    ["08:40", "08:40", "08:58"],
    ["08:41", "08:41", "09:00"],
    ["08:44", "08:44", "08:50"],
    ["08:45", "08:46", "08:58"],
    ["08:45", "08:46", "09:01"],
    ["08:47", "09:05", "09:26"],
    ["08:49", "08:55", "09:18"],
    ["08:49", "09:36", "09:50"],
    ["08:50", "08:50", "09:13"],
    ["08:51", "08:51", "09:15"],
    ["08:52", "08:52", "09:14"],
    ["08:53", "08:53", "09:17"],
    ["08:54", "09:01", "09:20"]
]

# Mengubah waktu ke format datetime
def to_datetime(time_str):
    return datetime.strptime(time_str, "%H:%M")

df = pd.DataFrame(data, columns=["AT", "SST", "SET"])

df["AT"] = df["AT"].apply(to_datetime)
df["SST"] = df["SST"].apply(to_datetime)
df["SET"] = df["SET"].apply(to_datetime)

# Menghitung waktu antar kedatangan (Inter-arrival Time)
df["AT_diff"] = df["AT"].diff().apply(lambda x: x.total_seconds() / 60)  # dalam menit

# Menghitung waktu pelayanan
df["Service_Time"] = (df["SET"] - df["SST"]).apply(lambda x: x.total_seconds() / 60)  # dalam menit

# Membuat tampilan Streamlit
st.title("Simulasi Antrian dengan Streamlit")
st.subheader("Distribusi Waktu Antar Kedatangan dan Pelayanan")

# Tampilkan tabel data
st.write("Tabel Data Kedatangan dan Pelayanan:", df)

# Plot untuk waktu antar kedatangan
st.subheader("Distribusi Waktu Antar Kedatangan")
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.hist(df["AT_diff"].dropna(), bins=10, alpha=0.7, label="Inter-arrival Time (menit)")
ax1.set_xlabel("Waktu Antar Kedatangan (menit)")
ax1.set_ylabel("Frekuensi")
ax1.set_title("Distribusi Waktu Antar Kedatangan")
ax1.legend()
st.pyplot(fig1)

# Plot untuk waktu pelayanan
st.subheader("Distribusi Waktu Pelayanan")
fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.hist(df["Service_Time"], bins=10, alpha=0.7, label="Durasi Pelayanan (menit)")
ax2.set_xlabel("Waktu Pelayanan (menit)")
ax2.set_ylabel("Frekuensi")
ax2.set_title("Distribusi Waktu Pelayanan")
ax2.legend()
st.pyplot(fig2)

# Uji distribusi eksponensial menggunakan Kolmogorov-Smirnov Test
def test_exponential(data):
    # Uji distribusi eksponensial
    stat, p_value = stats.kstest(data, 'expon', args=(np.min(data), np.mean(data)-np.min(data)))
    return stat, p_value

# Uji normalitas menggunakan Shapiro-Wilk Test
def test_normal(data):
    # Uji normalitas
    stat, p_value = stats.shapiro(data)
    return stat, p_value

# Uji distribusi eksponensial pada waktu antar kedatangan (AT_diff) dan waktu pelayanan (Service_Time)
st.subheader("Uji Distribusi")

# Uji eksponensial untuk Waktu Antar Kedatangan
ks_stat, ks_p_value = test_exponential(df["AT_diff"].dropna())
st.write(f"Uji Kolmogorov-Smirnov untuk Waktu Antar Kedatangan: Statistik = {ks_stat:.4f}, p-value = {ks_p_value:.4f}")

# Uji normalitas untuk Waktu Antar Kedatangan
normal_stat, normal_p_value = test_normal(df["AT_diff"].dropna())
st.write(f"Uji Shapiro-Wilk untuk Waktu Antar Kedatangan: Statistik = {normal_stat:.4f}, p-value = {normal_p_value:.4f}")

# Uji eksponensial untuk Waktu Pelayanan
ks_stat_service, ks_p_value_service = test_exponential(df["Service_Time"])
st.write(f"Uji Kolmogorov-Smirnov untuk Waktu Pelayanan: Statistik = {ks_stat_service:.4f}, p-value = {ks_p_value_service:.4f}")

# Uji normalitas untuk Waktu Pelayanan
normal_stat_service, normal_p_value_service = test_normal(df["Service_Time"])
st.write(f"Uji Shapiro-Wilk untuk Waktu Pelayanan: Statistik = {normal_stat_service:.4f}, p-value = {normal_p_value_service:.4f}")

# Q-Q Plot untuk Normalitas
st.subheader("Q-Q Plot untuk Waktu Antar Kedatangan")
fig3, ax3 = plt.subplots(figsize=(10, 5))
stats.probplot(df["AT_diff"].dropna(), dist="norm", plot=ax3)
st.pyplot(fig3)

# Q-Q Plot untuk Waktu Pelayanan
st.subheader("Q-Q Plot untuk Waktu Pelayanan")
fig4, ax4 = plt.subplots(figsize=(10, 5))
stats.probplot(df["Service_Time"], dist="norm", plot=ax4)
st.pyplot(fig4)
