import google.generativeai as genai
import os
import time

class GeminiAdvisor:
    def __init__(self, api_key):
        # Bersihkan API Key dari spasi atau karakter newline yang tidak diinginkan
        self.api_key = api_key.strip() if api_key else None
        self.model_name = 'gemini-1.5-flash' # Mengubah default ke 1.5 flash yang lebih stabil kuotanya
        self.available_models = []
        self.failed_models = set() # Menyimpan model yang terkena quota limit
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._initialize_model()
            except Exception as e:
                print(f"Konfigurasi genai gagal: {e}")
                self.model = None
        else:
            self.model = None

    def _initialize_model(self):
        """Mencoba inisialisasi model dengan fallback."""
        try:
            # Ambil semua model yang mendukung generateContent
            self.available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Prioritas model: 1.5 flash biasanya punya limit lebih lega dibanding 2.0 di free tier
            preferred_models = ['models/gemini-1.5-flash', 'models/gemini-2.0-flash', 'models/gemini-flash-latest']
            
            selected_model = None
            for pm in preferred_models:
                if pm in self.available_models and pm not in self.failed_models:
                    selected_model = pm
                    break
            
            if not selected_model:
                # Ambil model pertama yang belum gagal
                for am in self.available_models:
                    if am not in self.failed_models:
                        selected_model = am
                        break
            
            if selected_model:
                self.model_name = selected_model
                self.model = genai.GenerativeModel(self.model_name)
            else:
                # Jika semua model di list gagal atau tidak ada list, gunakan default
                self.model_name = 'models/gemini-1.5-flash'
                self.model = genai.GenerativeModel(self.model_name)
        except Exception:
            self.model_name = 'models/gemini-1.5-flash'
            self.model = genai.GenerativeModel(self.model_name)

    def _switch_model_on_error(self):
        """Pindah ke model lain jika model saat ini terkena quota limit."""
        self.failed_models.add(self.model_name)
        self._initialize_model()

    def list_available_models(self):
        """Membantu pengguna melihat model apa saja yang bisa mereka akses."""
        if not self.api_key:
            return ["API Key tidak ditemukan."]
        try:
            # Pastikan konfigurasi terbaru digunakan sebelum list_models
            genai.configure(api_key=self.api_key)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return models
        except Exception as e:
            return [f"Gagal mengambil daftar model: {str(e)}"]

    def _ensure_config(self):
        """Memastikan konfigurasi genai selalu menggunakan API key yang benar."""
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def get_ai_advice(self, summary_text):
        if not self.model:
            return "API Key Gemini tidak ditemukan. Silakan masukkan API Key untuk mendapatkan saran AI yang lebih mendalam."
        
        self._ensure_config()
        prompt = f"""
        Anda adalah asisten keberlanjutan (sustainability advisor) bernama EarthBot.
        Berikut adalah data emisi karbon pengguna dalam kg CO2:
        {summary_text}
        
        Berikan analisis singkat dan 3 saran praktis untuk mengurangi emisi tersebut. 
        Gunakan nada bicara yang ramah, memotivasi, dan profesional. 
        Gunakan Bahasa Indonesia.
        """
        
        # Implementasi retry sederhana dengan fallback model
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        max_output_tokens=2048,
                        temperature=0.7
                    )
                )
                return response.text
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    if attempt < max_retries - 1:
                        # Tandai model ini gagal dan coba pindah model
                        self._switch_model_on_error()
                        time.sleep(2) # Tunggu sebentar sebelum retry
                        continue
                    else:
                        return f"Kuota API Terlampaui (429). Google membatasi permintaan Anda. Silakan coba lagi beberapa saat lagi atau gunakan model lain. Detail: {err_msg}"
                elif "404" in err_msg:
                    return f"Error 404: Model '{self.model_name}' tidak ditemukan. Detail: {err_msg}"
                return f"Error saat menghubungi Gemini: {err_msg}"

    def chat_with_earthbot(self, user_message, context=""):
        if not self.model:
            return "Fitur chat memerlukan API Key Gemini."
            
        self._ensure_config()
        prompt = f"""
        Anda adalah EarthBot, asisten ramah lingkungan yang ahli dalam isu perubahan iklim dan gaya hidup berkelanjutan.
        Konteks emisi pengguna saat ini: {context}
        
        Pertanyaan pengguna: {user_message}
        
        Jawablah dengan informatif dan ajak pengguna untuk terus menjaga bumi.
        """
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=2048,
                        temperature=0.7
                    )
                )
                return response.text
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    if attempt < max_retries - 1:
                        self._switch_model_on_error()
                        time.sleep(1)
                        continue
                    else:
                        return f"Maaf, EarthBot sedang sibuk (Quota 429). Silakan coba chat lagi dalam 1 menit."
                if "404" in err_msg:
                    return f"Error 404: Model tidak ditemukan. Detail: {err_msg}"
                return f"Error saat chat dengan Gemini: {err_msg}"
