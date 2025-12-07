import pandas as pd
import streamlit as st

# Fungsi untuk menghitung TIQ, ST, dan TIS
def calculate_metrics(df):
    # Fungsi untuk mengkonversi waktu dengan format HH.MM (misalnya 08.05) menjadi format waktu yang bisa diproses
    def convert_time_format(time_str):
        try:
            # Mengganti titik dengan titik dua
            time_str = str(time_str).replace('.', ':')
            return pd.to_datetime(time_str, format='%H:%M')
        except ValueError:
            return pd.NaT  # Mengembalikan NaT (Not a Time) jika format salah

    # Mengonversi waktu di kolom AT, SST, SET
    df['AT'] = df['AT'].apply(convert_time_format)
    df['SST'] = df['SST'].apply(convert_time_format)
    df['SET'] = df['SET'].apply(convert_time_format)

    # Menghapus baris dengan nilai NaT (waktu yang tidak valid)
    df = df.dropna(subset=['AT', 'SST', 'SET'])

    # Menghitung TIQ (Time in Queue) = SST - AT
    df['TIQ'] = (df['SST'] - df['AT']).dt.total_seconds() / 60  # Mengkonversi ke menit
    
    # Menghitung ST (Service Time) = SET - SST
    df['ST'] = (df['SET'] - df['SST']).dt.total_seconds() / 60  # Mengkonversi ke menit
    
    # Menghitung TIS (Time in System) = SET - AT
    df['TIS'] = (df['SET'] - df['AT']).dt.total_seconds() / 60  # Mengkonversi ke menit
    
    # Menghitung Idle Time antara pelayanan
    df['Idle Time'] = 0.0
    for i in range(1, len(df)):
        prev_set = df.iloc[i-1]['SET']
        current_sst = df.iloc[i]['SST']
        idle_time = (current_sst - prev_set).total_seconds() / 60
        if idle_time > 0:
            df.at[i, 'Idle Time'] = idle_time

    # Mengubah waktu menjadi string dengan format HH:MM sebelum menampilkan
    df['AT'] = df['AT'].dt.strftime('%H:%M')
    df['SST'] = df['SST'].dt.strftime('%H:%M')
    df['SET'] = df['SET'].dt.strftime('%H:%M')

    return df

# Aplikasi Streamlit
def app():
    st.title("Analisis Data Antrian")

    # Upload file CSV
    uploaded_file = st.file_uploader("Unggah file CSV", type=["csv"])
    
    if uploaded_file is not None:
        # Membaca file CSV
        df = pd.read_csv(uploaded_file)
        
        # Menampilkan data pertama
        st.subheader("Data yang Diunggah")
        st.write(df.head())

        try:
            # Menganalisis data
            df = calculate_metrics(df)

            # Menampilkan hasil analisis
            st.subheader("Hasil Analisis")
            st.write(df)
            col1, col2 = st.columns(2)
            with col1:
            # Menghitung rata-rata TIQ, ST, TIS, dan Idle Time
                avg_tiq = df['TIQ'].mean()
                avg_st = df['ST'].mean()
                avg_tis = df['TIS'].mean()
                avg_idle_time = df['Idle Time'].mean()

            # Menampilkan metrik rata-rata
                st.subheader("Hasil Perhitungan Data Real")
                st.metric("Rata-rata TIQ (Time in Queue)", f"{avg_tiq:.2f} menit")
                st.metric("Rata-rata ST (Service Time)", f"{avg_st:.2f} menit")
                st.metric("Rata-rata TIS (Time in System)", f"{avg_tis:.2f} menit")
                st.metric("Rata-rata Idle Time", f"{avg_idle_time:.2f} menit")
            with col2:
                if 'total_idle_time' in st.session_state:
                    st.subheader("Hasil Perhitungan Data Simulasi")
                    
                    server_utilization = st.session_state.server_utilization
                    st.metric("server_utilization", f"{server_utilization:.1f} %")

                    rata_rata_pelayanan = st.session_state.rata_rata_pelayanan
                    st.metric("Rata-rata pelayanan", f"{rata_rata_pelayanan:.1f} menit")

                    rata_rata_tis = st.session_state.rata_rata_tis
                    st.metric("Rata-rata TIS", f"{rata_rata_tis:.1f} menit")

                    avg_wait_time = st.session_state.avg_wait_time
                    st.metric("TIQ (Waktu Tunggu)", f"{avg_wait_time:.1f} Menit")

                    total_idle_time = st.session_state.total_idle_time
                    st.metric("Total Idle Time", f"{total_idle_time:.1f} min")

                else:
                    st.write("Data tidak ditemukan!")
        
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    app()
