import streamlit as st
import plotly.express as px
import pandas as pd
import os
import time
from tracker import CarbonTracker
from gemini_integration import GeminiAdvisor

st.set_page_config(page_title="GreenQuest AI", page_icon="🌱", layout="wide")

# Inisialisasi State
if 'tracker' not in st.session_state:
    st.session_state.tracker = CarbonTracker()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("🌱 GreenQuest: AI-Powered Carbon Tracker")
st.markdown("Monitor emisi karbon harianmu dan dapatkan saran cerdas dari EarthBot AI.")

# Sidebar untuk API Key dan Info
with st.sidebar:
    st.header("Konfigurasi")
    
    # Coba ambil API Key dari Secrets atau Env Var sebagai fallback (tidak ditampilkan di UI)
    secret_api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    
    user_api_key = st.text_input(
        "Gemini API Key (Opsional)", 
        type="password", 
        placeholder="Kosongkan untuk menggunakan kunci default pengembang",
        help="Masukkan API Key pribadi Anda jika ingin. Jika kosong, aplikasi akan menggunakan kunci default yang sudah diatur pengembang secara aman."
    )
    
    # Logika penentuan API Key yang digunakan
    active_api_key = user_api_key if user_api_key else secret_api_key
    
    if active_api_key:
        if user_api_key:
            st.success("Menggunakan API Key Pribadi")
        else:
            st.success("Menggunakan API Key Default (Aman)")
    else:
        st.warning("API Key tidak ditemukan. Fitur AI tidak akan berfungsi.")
    
    st.divider()
    st.header("Manajemen Data")
    if st.button("Reset Semua Data", help="Hapus semua riwayat emisi"):
        st.session_state.tracker.clear_data()
        st.success("Data berhasil dikosongkan!")
        st.rerun()
    
    st.divider()
    st.info("GreenQuest membantu Anda menjaga bumi dengan melacak emisi dari aktivitas harian.")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Tambah Data", "💬 Chat with EarthBot"])

# Logic Tracker
tracker = st.session_state.tracker
summary = tracker.get_summary()

with tab1:
    st.subheader("Ringkasan Emisi Anda")
    total_emissions = tracker.get_total_emissions()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.metric("Total Emisi", f"{total_emissions:.2f} kg CO2")
        if summary:
            df = pd.DataFrame(list(summary.items()), columns=['Aktivitas', 'Emisi'])
            fig = px.pie(df, values='Emisi', names='Aktivitas', title='Distribusi Emisi', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Belum ada data untuk ditampilkan.")

    with col2:
        st.write("### 💡 Analisis EarthBot AI")
        if active_api_key:
            if st.button("Generate AI Analysis"):
                advisor = GeminiAdvisor(active_api_key)
                summary_text = "\n".join([f"{k}: {v:.2f} kg CO2" for k, v in summary.items()])
                with st.spinner("EarthBot sedang berpikir..."):
                    advice = advisor.get_ai_advice(summary_text)
                    st.markdown(advice)
        else:
            st.info("API Key diperlukan untuk analisis AI.")

with tab2:
    st.subheader("Catat Aktivitas Baru")
    
    # Inisialisasi daftar sementara untuk batch upload
    if 'temp_activities' not in st.session_state:
        st.session_state.temp_activities = []
    
    with st.form("activity_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            act_type = st.selectbox("Tipe Aktivitas", 
                                   ["electricity", "gas", "petrol", "meat", "flight_short", "public_transport"],
                                   format_func=lambda x: x.capitalize())
        with col_b:
            amount = st.number_input("Jumlah (kWh/liter/kg/km)", min_value=0.0, step=0.1)
        
        add_to_list = st.form_submit_button("Tambah ke Daftar Sementara")
        if add_to_list:
            if amount > 0:
                emission = amount * tracker.factors[act_type]
                st.session_state.temp_activities.append({
                    "type": act_type,
                    "amount": amount,
                    "emission": emission
                })
                st.toast(f"✅ {act_type.capitalize()} ditambahkan ke daftar!", icon="➕")
            else:
                st.error("Jumlah harus lebih dari 0.")

    # Tampilkan daftar sementara jika ada
    if st.session_state.temp_activities:
        st.write("### 📋 Daftar Aktivitas Sementara")
        df_temp = pd.DataFrame(st.session_state.temp_activities)
        # Format kolom agar lebih rapi
        df_temp.columns = ["Tipe", "Jumlah", "Emisi (kg CO2)"]
        st.table(df_temp)
        
        col_submit, col_cancel = st.columns([1, 4])
        with col_submit:
            if st.button("Submit Semua Data", type="primary"):
                count = 0
                for act in st.session_state.temp_activities:
                    success, result = tracker.add_activity(act["type"], act["amount"])
                    if success:
                        count += 1
                
                st.session_state.temp_activities = []
                st.success(f"Berhasil menyimpan {count} aktivitas ke riwayat!")
                st.balloons()
                time.sleep(2)
                st.rerun()
        
        with col_cancel:
            if st.button("Kosongkan Daftar"):
                st.session_state.temp_activities = []
                st.rerun()
    else:
        st.info("Belum ada aktivitas di daftar sementara. Masukkan data di atas dan klik 'Tambah ke Daftar Sementara'.")

with tab3:
    st.subheader("Chat dengan EarthBot AI")
    if not active_api_key:
        st.error("API Key tidak ditemukan. Fitur chat dinonaktifkan.")
    else:
        advisor = GeminiAdvisor(active_api_key)
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Tanyakan sesuatu tentang cara hidup hemat energi..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                summary_text = ", ".join([f"{k}: {v:.2f}" for k, v in summary.items()])
                context = f"Emisi saat ini: {summary_text} kg CO2."
                with st.spinner("Mengetik..."):
                    response = advisor.chat_with_earthbot(prompt, context)
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

st.divider()
st.caption("Final Project: GreenQuest AI - Solusi Cerdas untuk Bumi Lebih Hijau.")
