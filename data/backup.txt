import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tes
# Set page config
st.set_page_config(
    page_title="Simulasi Antrian Interaktif",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding: 2rem;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .dataframe {
        font-size: 0.9rem !important;
    }
    .css-1d391kg {
        padding: 1rem;
    }
    div.stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi untuk konversi waktu
def time_to_minutes(time_str):
    time_obj = datetime.strptime(time_str, "%H:%M")
    return time_obj.hour * 60 + time_obj.minute

def minutes_to_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{int(hours):02d}:{int(mins):02d}"

# Fungsi untuk menghasilkan bilangan acak dengan formula
def lcm_random(n, a, c, m, x0):
    numbers = []
    formulas = []
    x = x0
    for i in range(n):
        x_new = (a * x + c) % m
        numbers.append(x_new)
        formulas.append(f"({a} × {x} + {c}) mod {m} = {x_new}")
        x = x_new
    return np.array([num % 100 for num in numbers]), formulas

def lcg_random(n, a, c, m, x0):
    numbers = []
    formulas = []
    x = x0
    for i in range(n):
        x_new = (a * x + c) % m
        numbers.append(x_new)
        z_value = x_new % 100
        formulas.append(f"{z_value}Z_{i+1} = ({a} × {x} + {c}) mod {m} = {x_new} = {z_value}")
        x = x_new
    return np.array([num % 100 for num in numbers]), formulas

# Fungsi untuk menghitung interval angka acak
def calculate_intervals(df, column):
    df["Probabilitas"] = df["Frekuensi"] / df["Frekuensi"].sum()
    df["Frekuensi Kumulatif"] = df["Probabilitas"].cumsum()
    df["Interval Angka Acak"] = [
        f"[{int(fc * 100)}-{int(fc_next * 100) - 1}]"
        for fc, fc_next in zip([0] + df["Frekuensi Kumulatif"].tolist()[:-1], df["Frekuensi Kumulatif"])
    ]
    return df

# Fungsi untuk menghasilkan bilangan acak
def generate_random_numbers(method, size, seed=None):
    if method == "Random Default":
        if seed is not None:
            np.random.seed(seed)
        return np.random.random(size)
    elif method == "LCM":
        a = 1664525
        c = 1013904223
        m = 2**32
        numbers = []
        x = seed if seed is not None else int(datetime.now().timestamp())
        for _ in range(size):
            x = (a * x + c) % m
            numbers.append(x / m)
        return np.array(numbers)
    else:  # LCG
        a = 16807
        m = 2**31 - 1
        numbers = []
        x = seed if seed is not None else int(datetime.now().timestamp())
        for _ in range(size):
            x = (a * x) % m
            numbers.append(x / m)
        return np.array(numbers)

# Fungsi simulasi antrian
def simulate_queue(
    n_customers,
    start_time,
    random_method,
    arrival_distribution,
    service_times,
    service_probabilities,
    lcm_params=None
):
    # Generate random numbers based on method
    if random_method == "LCM" and lcm_params:
        random_arrival, arrival_formulas = lcm_random(
            n_customers, 
            lcm_params['a'], 
            lcm_params['c'], 
            lcm_params['m'], 
            lcm_params['x0']
        )
        random_service, service_formulas = lcm_random(
            n_customers, 
            lcm_params['a'], 
            lcm_params['c'], 
            lcm_params['m'], 
            lcm_params['x0'] + 1
        )
    elif random_method == "LCG":
        random_arrival = generate_random_numbers("LCG", n_customers)
        random_service = generate_random_numbers("LCG", n_customers)
        arrival_formulas = ["LCG generated" for _ in range(n_customers)]
        service_formulas = ["LCG generated" for _ in range(n_customers)]
    else:
        random_arrival = generate_random_numbers("Random Default", n_customers)
        random_service = generate_random_numbers("Random Default", n_customers)
        arrival_formulas = ["numpy.random" for _ in range(n_customers)]
        service_formulas = ["numpy.random" for _ in range(n_customers)]

    # Create arrival and service dataframes
    arrival_df = pd.DataFrame({
        "Jarak Kedatangan": raw_data["Jarak Kedatangan (menit)"],
        "Frekuensi": raw_data["Frekuensi Kedatangan Konsumen"]
    })
    
    service_df = pd.DataFrame({
        "Lama Pelayanan": raw_data["Lama Pelayanan (menit)"],
        "Frekuensi": raw_data["Frekuensi Pelayanan Konsumen"]
    })

   
    # Calculate intervals
    arrival_df = calculate_intervals(arrival_df, "Jarak Kedatangan")
    service_df = calculate_intervals(service_df, "Lama Pelayanan")

    # Map random numbers to values
    def map_random_to_value(random_numbers, df, column_name):
        mapped_values = []
        intervals = [
            tuple(map(int, interval.strip("[]").split('-')))
            for interval in df["Interval Angka Acak"]
        ]
        for num in (random_numbers * 100).astype(int):
            for i, (low, high) in enumerate(intervals):
                if low <= num <= high:
                    mapped_values.append(df.iloc[i][column_name])
                    break
        return mapped_values

    arrival_times = map_random_to_value(random_arrival, arrival_df, "Jarak Kedatangan")
    service_times = map_random_to_value(random_service, service_df, "Lama Pelayanan")

    # Initialize simulation DataFrame with new columns
    simulation_data = []
    arrival_time_cumulative = 0
    end_service_time = 0
    start_minutes = time_to_minutes(start_time.strftime("%H:%M"))

    for i in range(n_customers):
        # Calculate arrival and service times
        arrival_time_cumulative += arrival_times[i]
        prev_end_service = end_service_time if i > 0 else 0
        start_service_time = max(arrival_time_cumulative, end_service_time)
        idle_time = max(0, arrival_time_cumulative - end_service_time) if i > 0 else 0
        end_service_time = start_service_time + service_times[i]
        wait_time = start_service_time - arrival_time_cumulative
        time_in_system = end_service_time - arrival_time_cumulative

        # Create detailed record with formulas
        customer_data = {
            "Konsumen": i + 1,
            "angka acak": int(random_arrival[i] * 100),
            "Jarak Kedatangan (menit)": arrival_times[i],
            "Waktu Kedatangan": minutes_to_time(start_minutes + arrival_time_cumulative),
           # "Rumus Waktu Kedatangan": f"Kedatangan_{i+1} = Kedatangan_{i} + {arrival_times[i]}" if i > 0 else f"Kedatangan_1 = {arrival_times[i]}",
            "Lama Pelayanan (menit)": service_times[i],
            "Mulai Pelayanan": minutes_to_time(start_minutes + start_service_time),
            #"Rumus Mulai Pelayanan": f"Max(Waktu Kedatangan {arrival_time_cumulative}, Selesai Pelayanan Sebelumnya {prev_end_service}) = {start_service_time}",
            "Selesai Pelayanan": minutes_to_time(start_minutes + end_service_time),
            #"Rumus Selesai Pelayanan": f"Mulai Pelayanan {start_service_time} + Lama Pelayanan {service_times[i]} = {end_service_time}",
            "Waktu Tunggu (menit)": wait_time,
            #"Rumus Waktu Tunggu": f"Mulai Pelayanan {start_service_time} - Waktu Kedatangan {arrival_time_cumulative} = {wait_time}",
            "Waktu dalam Sistem (menit)": time_in_system,
            #"Rumus Waktu Sistem": f"Selesai Pelayanan {end_service_time} - Waktu Kedatangan {arrival_time_cumulative} = {time_in_system}",
            "Idle Time Kasir (menit)": idle_time,
            #"Rumus Idle Time": f"Max(0, Waktu Kedatangan {arrival_time_cumulative} - Selesai Pelayanan Sebelumnya {prev_end_service}) = {idle_time}"
        }
        
        simulation_data.append(customer_data)

    simulation_df = pd.DataFrame(simulation_data)
    
    # Create random number tables
    arrival_random_df = pd.DataFrame({
        "Bilangan Acak": (random_arrival * 100).astype(int),
        "Rumus": arrival_formulas
    })

    service_random_df = pd.DataFrame({
        "Bilangan Acak": (random_service * 100).astype(int),
        "Rumus": service_formulas
    })

    return simulation_df, arrival_df, service_df, arrival_random_df, service_random_df

# Data Awal (Raw Data)
raw_data = {
    "Jarak Kedatangan (menit)": [1, 2, 3, 4, 5],
    "Frekuensi Kedatangan Konsumen": [0.20] * 5,  # Probabilitas
    "Lama Pelayanan (menit)": list(range(5, 25)),
    "Frekuensi Pelayanan Konsumen": [0.05] * 20,  # Probabilitas
}


# Sidebar dengan tema
st.sidebar.image("https://docs.streamlit.io/logo.svg", width=100)

st.sidebar.title("🎯 Kontrol Simulasi")

# st.sidebar.button("Edit Data", key="edit_data")
# Tab untuk pengaturan berbeda
tabs = st.sidebar.tabs(["⚙️ Parameter", "📊 Visual", "💡 Tips", "🙎‍♂️ Profile"])

with tabs[0]:
    # Parameter Simulasi
    st.header("Parameter Dasar")
    random_method = st.selectbox("Metode Bilangan Acak", ["Random Default", "LCM", "LCG"])
    
    # LCM/LCG Parameters jika dipilih
    lcm_params = None
    if random_method in ["LCM", "LCG"]:
        if random_method == "LCM":
            a = st.number_input("Konstanta Perkalian (a)", value=1597)
            c = st.number_input("Kenaikan (c)", value=51749)
            m = st.number_input("Bilangan Tetap (m)", value=244944)
        else:  # LCG
            a = st.number_input("Multiplier (a)", value=1664525)
            c = st.number_input("Increment (c)", value=1013904223)
            m = st.number_input("Modulus (m)", value=2**32)
        x0 = st.number_input("Nilai Awal (x0)", value=1234)
        lcm_params = {'a': a, 'c': c, 'm': m, 'x0': x0}
    
    start_time = st.time_input("Waktu Mulai Operasi", datetime.strptime("08:00", "%H:%M").time())
    
    # Pengaturan jumlah pelanggan
    customer_setting = st.radio("Pengaturan Pelanggan", ["Default (32)", "Custom"])
    if customer_setting == "Custom":
        n_customers = st.number_input("Jumlah Pelanggan", min_value=1, value=32)
    else:
        n_customers = 32

    # Parameter distribusi
    st.header("Distribusi Waktu")
    arrival_distribution = st.selectbox("Distribusi Kedatangan", ["Custom", "Poisson", "Normal"])
    
    if arrival_distribution == "Custom":
        service_times = [2, 3, 4, 5]
        service_probabilities = [0.2, 0.3, 0.3, 0.2]
    else:
        mean_arrival = st.slider("Rata-rata Waktu Kedatangan (menit)", 1, 10, 3)
        service_times = [2, 3, 4, 5]
        service_probabilities = [0.2, 0.3, 0.3, 0.2]

with tabs[1]:
    # Pengaturan Visual
    st.header("Pengaturan Grafik")
    show_charts = st.multiselect(
        "Pilih Grafik yang Ditampilkan",
        ["Waktu Tunggu", "Utilisasi Server", "Distribusi Kedatangan", "Gantt Chart"],
        default=["Waktu Tunggu", "Utilisasi Server"]
    )
    chart_theme = st.selectbox("Tema Grafik", ["plotly", "plotly_white", "plotly_dark"])

    
with tabs[2]:
    st.info("""
    💡 Tips Penggunaan:
    1. Mulai dengan parameter default
    2. Sesuaikan jumlah pelanggan
    3. Eksperimen dengan distribusi
    4. Analisis hasil melalui grafik
    """)

# Tab Profile
with tabs[3]:

    # Profil Developer dengan Tabs
    st.title("👤 Profile Developer")

    # Menggunakan Tabs
    tab1, tab2, tab3 = st.tabs(["Informasi", "Deskripsi", "Foto"])

    with tab1:
        st.subheader("📋 Informasi Profil")
        st.write("**Nama:** Rasyid Firdaus Harmaini")
        st.write("**Email:** Rasyidfirdaus53@gmail.com")
        st.write("**Keahlian:** Data Science, Machine Learning, Web Development")

    with tab2:
        st.subheader("💼 Deskripsi")
        st.write(
            """
            Saya adalah developer yang berpengalaman dalam pengembangan aplikasi berbasis data. 
            Saya menyukai tantangan teknologi dan kolaborasi tim untuk menciptakan solusi inovatif.
            """
        )

    with tab3:
        st.subheader("📸 Foto Profil")  
        st.image("https://media.licdn.com/dms/image/v2/D5603AQEGRZfHEzlcsQ/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1709377374178?e=1741824000&v=beta&t=8Oy6AjFF-V5BlbymvbXVwDdgtQRY3bBaZxSkRbdBASE", caption="Rasyid Firdaus", width=150,)

# # Edit Data Main Tab
# with tabs[4]:
#     st.header("Edit Data")
    
#     # Excel File Upload Section
#     # uploaded_file = st.file_uploader("Pilih file Excel", type=["xlsx", "xls"])
    
#     if uploaded_file is not None:
#         # Read the Excel file into a DataFrame
#         df = pd.read_excel(uploaded_file)
#         st.write("Data yang di-upload:")
#         st.dataframe(df)
        
#         # Add functionality to edit data - example: edit row values
#         st.subheader("Edit Data")
#         index_to_edit = st.number_input("Pilih index yang ingin diedit", min_value=0, max_value=len(df)-1)
        
#         st.write("Kolom Data:")
#         columns = df.columns.tolist()
#         col_to_edit = st.selectbox("Pilih kolom yang ingin diedit", columns)
#         new_value = st.text_input(f"Nilai baru untuk {col_to_edit}")
        
#         if st.button("Update Data"):
#             if new_value:
#                 df.at[index_to_edit, col_to_edit] = new_value
#                 st.write("Data telah diperbarui:")
#                 st.dataframe(df)
#             else:
#                 st.warning("Harap masukkan nilai baru.")

#     else:
#         st.write("Tidak ada file yang di-upload. Harap upload file Excel.")

# # Add Data Export Option to Excel after editing
# if uploaded_file is not None:
#     st.download_button(
#         label="Unduh Data sebagai Excel",
#         data=df.to_excel(index=False),
#         file_name="updated_data.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )

# Main content
st.title("📊 Simulasi Antrian Interaktif")

# Simulasi antrian ketika tombol ditekan
if 'simulation_df' not in st.session_state:
    st.session_state.simulation_df = None
    st.session_state.simulation_results = None

if st.sidebar.button("Jalankan Simulasi"):
    simulation_results = simulate_queue(
        n_customers,
        start_time,
        random_method,
        arrival_distribution,
        service_times,
        service_probabilities,
        lcm_params
    )
    st.session_state.simulation_df = simulation_results[0]
    st.session_state.simulation_results = simulation_results

# Create tabs for different views
main_tabs = st.tabs(["📈 Dashboard", "📋 Data Detail", "📊 Analisis Lanjutan", "Analisis data real"])

if st.session_state.simulation_df is not None:
    simulation_df = st.session_state.simulation_df
    
    with main_tabs[0]:  # "📈 Dashboard" tab
        # Dashboard layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Statistik Real-time")

            # Metrics in cards
            col1_1, col2_1, col3_1 = st.columns(3)
            with col1_1:
                avg_wait_time = simulation_df["Waktu Tunggu (menit)"].mean()
                st.metric("Rata-rata Waktu Tunggu", f"{avg_wait_time:.1f} min")
                st.session_state.avg_wait_time = avg_wait_time
            with col2_1:
                total_time = (
                    time_to_minutes(simulation_df["Selesai Pelayanan"].iloc[-1]) - 
                    time_to_minutes("08:00")
                )
                server_utilization = (
                    simulation_df["Lama Pelayanan (menit)"].sum() / total_time
                ) * 100
                st.metric("Utilisasi Server", f"{server_utilization:.1f}%")
                st.session_state.server_utilization = server_utilization
            with col3_1:
                total_idle_time = simulation_df["Idle Time Kasir (menit)"].sum()
                st.metric("Total Idle Time", f"{total_idle_time:.1f} min")
                st.session_state.total_idle_time = total_idle_time

            # Second row for m4
            col4 = st.columns(1)
            with col4[0]:
                rata_rata_tis = simulation_df["Waktu dalam Sistem (menit)"].mean()
                st.metric("Rata-rata TIS", f"{rata_rata_tis:.1f} menit")

        with col2:
            st.subheader("Grafik Waktu Tunggu")
            fig = px.line(simulation_df, 
                          x="Konsumen", 
                          y="Waktu Tunggu (menit)",
                          template="plotly_dark")  # Ensure chart_theme variable is defined if needed
            st.plotly_chart(fig, use_container_width=True)

            # Additional visualizations (Gantt Chart)
            if "Gantt Chart" in show_charts:  # Ensure 'show_charts' is properly defined
                st.subheader("Gantt Chart Pelayanan")
                fig = px.timeline(simulation_df,
                                   x_start="Mulai Pelayanan",
                                   x_end="Selesai Pelayanan",
                                   y="Konsumen",
                                   template="plotly_dark")  # Use template if needed
                st.plotly_chart(fig, use_container_width=True)

    with main_tabs[1]:
        st.header("Data Detail")
        st.header("📋 Semua Data Interaktif")
        st.subheader("Simulasi Antrian")
        selected_columns = st.multiselect(
            "Pilih Kolom yang Ditampilkan",
            simulation_df.columns.tolist(),
            default=["Konsumen", "Waktu Kedatangan", "Mulai Pelayanan", "Selesai Pelayanan"]
        )
        st.dataframe(simulation_df[selected_columns], use_container_width=True)

        # Tabel Distribusi Kedatangan
        st.subheader("Distribusi Kedatangan")
        st.dataframe(st.session_state.simulation_results[1])

        # Tabel Distribusi Pelayanan
        st.subheader("Distribusi Pelayanan")
        st.dataframe(st.session_state.simulation_results[2])

        # Bilangan Acak Kedatangan
        st.subheader("Bilangan Acak Kedatangan")
        st.dataframe(st.session_state.simulation_results[3])

        # Bilangan Acak Pelayanan
        st.subheader("Bilangan Acak Pelayanan")
        st.dataframe(st.session_state.simulation_results[4])


    with main_tabs[2]:
        st.header("Analisis Lanjutan")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribusi Waktu Tunggu")
            fig = px.histogram(simulation_df, 
                             x="Waktu Tunggu (menit)",
                             nbins=20,
                             template=chart_theme)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Korelasi Waktu")
            correlation = simulation_df[["Waktu Tunggu (menit)", 
                                      "Lama Pelayanan (menit)",
                                      "Waktu dalam Sistem (menit)"]].corr()
            fig = px.imshow(correlation,
                          template=chart_theme)
            st.plotly_chart(fig, use_container_width=True)

        # Tambahan analisis
        st.subheader("Performa Sistem")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Maksimum Waktu Tunggu", 
                     f"{simulation_df['Waktu Tunggu (menit)'].max():.1f} min")
        with col2:
            st.metric("Standar Deviasi Waktu Tunggu",
                     f"{simulation_df['Waktu Tunggu (menit)'].std():.1f} min")
        with col3:
            efficiency = (simulation_df["Lama Pelayanan (menit)"].sum() / total_time) * 100
            st.metric("Efisiensi Sistem", f"{efficiency:.1f}%")
    with main_tabs[3]:
        st.header("📊 Analisis Data Real")
        st.write("Mengintegrasikan analisis data real-time.")
        tes.app()
# Download Section
st.sidebar.header("💾 Ekspor Data")
if st.session_state.simulation_df is not None:
    csv = simulation_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Unduh Hasil Simulasi (CSV)",
        data=csv,
        file_name="simulasi_antrian.csv",
        mime="text/csv"
    )

# Penjelasan dan Footer
st.markdown("---")
st.subheader("Penjelasan Perhitungan")
st.write("""
1. **Probabilitas dan Interval:**
   - Probabilitas = Frekuensi / Total Frekuensi
   - Frekuensi Kumulatif = Jumlah probabilitas sampai baris tersebut
   - Interval = [Frekuensi Kumulatif sebelumnya * 100 - Frekuensi Kumulatif saat ini * 100]

2. **Penentuan Waktu:**
   - Waktu Kedatangan = Waktu mulai + Jumlah jarak kedatangan sebelumnya
   - Mulai Pelayanan = Max(Waktu Kedatangan, Waktu Selesai Pelayanan Sebelumnya)
   - Selesai Pelayanan = Waktu Mulai Pelayanan + Lama Pelayanan
   - Waktu Tunggu = Waktu Mulai Pelayanan - Waktu Kedatangan
   - Waktu dalam Sistem = Selesai Pelayanan - Waktu Kedatangan
   - Idle Time Kasir = Max(0, Waktu Kedatangan - Waktu Selesai Pelayanan Sebelumnya)
""")

if random_method in ["LCM", "LCG"]:
    st.latex(r"X_{i+1} = (aX_i + c) \bmod m")
    st.write("""
    Dimana:
    - a = Konstanta perkalian
    - Xi = Nilai awal/sebelumnya
    - c = Kenaikan
    - m = Bilangan tetap (modulus)
    """)

# Garis pemisah untuk estetika
st.markdown("---")

# Ambil tahun saat ini
current_year = datetime.now().year

# Footer dengan logo GitHub, LinkedIn, dan Instagram
footer = f"""
    <div style='text-align: center; margin-top: 20px; font-family: Arial, sans-serif;'>
        <p style='font-size: 14px; color: #6c757d;'>
            © {current_year} Created with ❤️ by 
            <a href='https://github.com/rasyidfirdaus482' target='_blank' 
               style='text-decoration: none; color: #0d6efd; font-weight: bold;'>
                Rasyid Firdaus
            </a>
        </p>
        <div style='margin-top: 10px;'>
            <!-- GitHub -->
            <a href='https://github.com/rasyidfirdaus482' target='_blank' style='text-decoration: none;'>
                <img src='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png' 
                     alt='GitHub Logo' width='25' style='margin-right: 15px;' />
            </a>
            <!-- LinkedIn -->
            <a href='https://www.linkedin.com/in/rasyidfirdaus482' target='_blank' style='text-decoration: none;'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' 
                     alt='LinkedIn Logo' width='25' style='margin-right: 15px;' />
            </a>
            <!-- Instagram -->
            <a href='https://www.instagram.com/rasyidfirdaus482' target='_blank' style='text-decoration: none;'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174855.png' 
                     alt='Instagram Logo' width='25' />
            </a>
        </div>
    </div>
"""

# Tampilkan footer menggunakan HTML
st.markdown(footer, unsafe_allow_html=True)