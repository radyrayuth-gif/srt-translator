import streamlit as st
import whisper
import os
import google.generativeai as genai
import time

st.set_page_config(page_title="Gemini Pro Video Translator", page_icon="💎")

# Sidebar សម្រាប់ API Key
with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key៖", type="password")
    st.info("យក Key នៅ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("💎 បកប្រែវីដេអូកម្រិត Gemini Pro")
st.write("ប្រើប្រាស់ Model ខ្លាំងបំផុតដើម្បីគុណភាពបកប្រែខ្ពស់។")
st.markdown("---")

# ១. មុខងារបកប្រែដោយប្រើ Gemini Pro
def translate_with_gemini_pro(text, api_key):
    if not api_key: return "Missing API Key"
    
    try:
        genai.configure(api_key=api_key)
        
        # ប្រើ gemini-1.5-pro ដើម្បីគុណភាពខ្ពស់បំផុត
        # ប្រសិនបើចង់បានល្បឿនលឿន អាចដូរទៅ 'gemini-1.5-flash'
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        តួនាទី៖ អ្នកគឺជាអ្នកបកប្រែខ្សែភាពយន្តអាជីព ចិន-ខ្មែរ។
        ភារកិច្ច៖ បកប្រែអត្ថបទខាងក្រោមឱ្យមានន័យសមរម្យ ស្មោះត្រង់នឹងសាច់រឿង និងប្រើប្រាស់ភាសាខ្មែរឱ្យរលូន។
        អត្ថបទចិន៖ {text}
        លទ្ធផល៖ សូមផ្ដល់មកតែអត្ថបទបកប្រែខ្មែរប៉ុណ្ណោះ។
        """
        
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "បកប្រែមិនចេញ"
        
    except Exception as e:
        # បើ Pro មានបញ្ហា វានឹងព្យាយាមប្រើ Flash ជាជម្រើសបម្រុង
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            return f"Error: {str(e)}"

# ២. មុខងារបង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    total = len(segments)
    progress_bar = st.progress(0, text="Gemini កំពុងវិភាគសាច់រឿង...")
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែជាមួយ Gemini Pro
        translated = translate_with_gemini_pro(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600); m = int((seconds % 3600) // 60)
            s = int(seconds % 60); ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        
        # Update progress
        pct = (i + 1) / total
        progress_bar.progress(pct, text=f"បកប្រែបាន {int(pct*100)}% ({i+1}/{total})")
        
        # បន្ថែម Delay បន្តិចដើម្បីកុំឱ្យជាប់ Rate Limit របស់ Free Tier
        time.sleep(1.0) 
        
    return srt_content

# ៣. ដំណើរការ Whisper
@st.cache_resource
def load_model():
    return whisper.load_model("base")

whisper_model = load_model()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិន...", type=["mp4", "mov", "avi"])

if uploaded_file:
    st.video(uploaded_file)
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែជាមួយ Gemini Pro"):
        if not gemini_key:
            st.warning("⚠️ សូមបញ្ចូល API Key ជាមុនសិន!")
        else:
            with st.spinner('កំពុងដំណើរការ... អាចប្រើពេលយូរតាមប្រវែងវីដេអូ'):
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # ជំហាន ១៖ ស្ដាប់សំឡេង
                    st.info("🔄 កំពុងបម្លែងសំឡេងទៅជាអក្សរ...")
                    result = whisper_model.transcribe(video_path, fp16=False)
                    
                    # ជំហាន ២៖ បកប្រែខ្មែរ
                    st.info("🔄 Gemini Pro កំពុងបកប្រែ (គុណភាពខ្ពស់)...")
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ ការបកប្រែបានសម្រេច!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ (Gemini Quality)",
                        data=srt_data,
                        file_name="gemini_pro_khmer.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"បញ្ហា៖ {e}")
                finally:
                    if os.path.exists(video_path):
                        os.remove(video_path)
