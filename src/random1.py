import random
import pandas as pd
import streamlit as st

def minutes_to_time(minutes):
    hours, mins = divmod(minutes, 60)
    return f"{8 + hours:02}:{mins:02}"  # Asumsikan mulai dari pukul 08:00

def generate_random_numbers(z0, a, c, m, n):
    numbers = []
    zi = z0
    for _ in range(n):
        zi = (zi * a + c) % m
        numbers.append(zi / m)  # Normalize to [0, 1]
    return numbers

def create_distribution_table(values, frequencies, intervals):
    freq_cum = [sum(frequencies[:i+1]) for i in range(len(frequencies))]
    iaa = [(intervals[i][0], intervals[i][1]) for i in range(len(intervals))]
    return pd.DataFrame({
        'Values': values,
        'Frequency': frequencies,
        'Cumulative Frequency': freq_cum,
        'Interval': iaa
    })

def get_simulation_table(random_numbers, distribution_table, column_name):
    intervals = distribution_table['Interval']
    values = distribution_table['Values']
    results = []
    for rnd in random_numbers:
        for i, (low, high) in enumerate(intervals):
            if low / 100 <= rnd < high / 100:
                results.append(values[i])
                break
    return pd.DataFrame({column_name: results})

def calculate_queue_simulation(kedatangan, pelayanan):
    n = len(kedatangan)
    AT = [sum(kedatangan[:i+1]) for i in range(n)]  # Arrival Time (cumulative kedatangan)
    SST = [0] * n  # Service Start Time
    SET = [0] * n  # Service End Time
    TIQ = [0] * n  # Time in Queue
    TIS = [0] * n  # Time in System

    for i in range(n):
        if i == 0:
            SST[i] = AT[i]
        else:
            SST[i] = max(AT[i], SET[i-1])

        SET[i] = SST[i] + pelayanan[i]
        TIQ[i] = SST[i] - AT[i] if SST[i] > AT[i] else 0
        TIS[i] = SET[i] - AT[i]

    # Convert times to HH:MM format
    AT_time = [minutes_to_time(at) for at in AT]
    SST_time = [minutes_to_time(sst) for sst in SST]
    SET_time = [minutes_to_time(set_) for set_ in SET]

    return pd.DataFrame({
        'AT (Arrival Time)': AT_time,
        'SST (Service Start Time)': SST_time,
        'SET (Service End Time)': SET_time,
        'ST (Service Time)': pelayanan,
        'TIQ (Time in Queue)': TIQ,
        'TIS (Time in System)': TIS
    })


def main():
    st.title("Simulasi Antrian dengan Streamlit")

    st.sidebar.header("Parameter Random Number")
    z0_col1 = st.sidebar.number_input("Nilai awal (z0) untuk Kolom 1", value=5)
    a_col1 = st.sidebar.number_input("Nilai pengali (a) untuk Kolom 1", value=3)
    c_col1 = st.sidebar.number_input("Nilai penambah (c) untuk Kolom 1", value=7)
    m_col1 = st.sidebar.number_input("Nilai modulus (m) untuk Kolom 1", value=100)

    z0_col2 = st.sidebar.number_input("Nilai awal (z0) untuk Kolom 2", value=10)
    a_col2 = st.sidebar.number_input("Nilai pengali (a) untuk Kolom 2", value=5)
    c_col2 = st.sidebar.number_input("Nilai penambah (c) untuk Kolom 2", value=11)
    m_col2 = st.sidebar.number_input("Nilai modulus (m) untuk Kolom 2", value=100)

    n = 32  # Number of random numbers

    # Input custom numbers for kedatangan and pelayanan
    kedatangan_input = st.text_area("Masukkan angka acak untuk Kedatangan (pisahkan dengan koma)", "15, 12, 13, 46")
    pelayanan_input = st.text_area("Masukkan angka acak untuk Pelayanan (pisahkan dengan koma)", "5, 10, 15, 20")

    # Parse the custom inputs into lists of integers
    kedatangan_custom = list(map(int, kedatangan_input.split(',')))
    pelayanan_custom = list(map(int, pelayanan_input.split(',')))

    # Define distributions
    kedatangan_values = list(range(1, 6))
    kedatangan_frequencies = [0.2] * 5
    kedatangan_intervals = [(1, 20), (21, 40), (41, 60), (61, 80), (81, 100)]

    pelayanan_values = list(range(5, 25))
    pelayanan_frequencies = [0.5] * 20
    pelayanan_intervals = [(i, i + 4) for i in range(1, 100, 5)]

    kedatangan_table = create_distribution_table(kedatangan_values, kedatangan_frequencies, kedatangan_intervals)
    pelayanan_table = create_distribution_table(pelayanan_values, pelayanan_frequencies, pelayanan_intervals)

    # Simulation tables for custom inputs
    kedatangan_simulation = get_simulation_table(kedatangan_custom, kedatangan_table, "Waktu Kedatangan")
    pelayanan_simulation = get_simulation_table(pelayanan_custom, pelayanan_table, "Lama Pelayanan")

    # Calculate queue simulation
    queue_simulation = calculate_queue_simulation(kedatangan_simulation["Waktu Kedatangan"].tolist(), pelayanan_simulation["Lama Pelayanan"].tolist())

    # Display tables
    st.header("Distribusi Kedatangan")
    st.write(kedatangan_table)

    st.header("Distribusi Pelayanan")
    st.write(pelayanan_table)

    st.header("Angka Acak untuk Kedatangan")
    st.write(pd.DataFrame({"Angka Acak": kedatangan_custom}))

    st.header("Angka Acak untuk Pelayanan")
    st.write(pd.DataFrame({"Angka Acak": pelayanan_custom}))

    st.header("Tabel Simulasi Antrian")
    st.write(queue_simulation)

if __name__ == "__main__":
    main()