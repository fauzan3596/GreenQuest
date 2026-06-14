import streamlit as st
import plotly.express as px
import pandas as pd
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
    api_key = st.text_input("Gemini API Key", type="password", help="Dapatkan di Google AI Studio")
    if api_key:
        st.success("API Key Terpasang")
    else:
        st.warning("Gunakan API Key untuk fitur ChatBot AI")
    
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
        if api_key:
            if st.button("Generate AI Analysis"):
                advisor = GeminiAdvisor(api_key)
                summary_text = "\n".join([f"{k}: {v:.2f} kg CO2" for k, v in summary.items()])
                with st.spinner("EarthBot sedang berpikir..."):
                    advice = advisor.get_ai_advice(summary_text)
                    st.markdown(advice)
        else:
            st.info("Masukkan API Key di sidebar untuk mendapatkan analisis AI yang dipersonalisasi.")

with tab2:
    st.subheader("Catat Aktivitas Baru")
    with st.form("activity_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            act_type = st.selectbox("Tipe Aktivitas", 
                                   ["electricity", "gas", "petrol", "meat", "flight_short", "public_transport"],
                                   format_func=lambda x: x.capitalize())
        with col_b:
            amount = st.number_input("Jumlah (kWh/liter/kg/km)", min_value=0.0, step=0.1)
        
        submitted = st.form_submit_button("Simpan Aktivitas")
        if submitted:
            success, result = tracker.add_activity(act_type, amount)
            if success:
                st.success(f"Tersimpan! Emisi baru: {result:.2f} kg CO2")
                st.rerun()
            else:
                st.error(result)

with tab3:
    st.subheader("Chat dengan EarthBot AI")
    if not api_key:
        st.error("Silakan masukkan API Key Gemini di sidebar untuk mulai mengobrol.")
    else:
        advisor = GeminiAdvisor(api_key)
        
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
