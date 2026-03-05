import streamlit as st
import whisper
import os
import google.generativeai as genai
import time

st.set_page_config(page_title="Gemini AI Translator Fixed", page_icon="♊")

# Sidebar settings
with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key៖", type="password")
    st.info("យក Key នៅ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("♊ បកប្រែវីដេអូចិន-ខ្មែរ (ជំនាន់ដោះស្រាយ Error 404)")
st.markdown("---")

# ១. មុខងារបកប្រែដែលធានាថានឹងដើរ (Robust Translation)
def translate_text(text, api_key):
    if not api_key: return "Missing API Key"
    
    genai.configure(api_key=api_key)
    
    # បញ្ជី Model ដែលត្រូវសាកល្បងម្ដងមួយៗ បើមួយណា Error វានឹងប្ដូរទៅមួយទៀត
    models_to_try = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.0-pro']
    
    prompt = f"Translate this Chinese subtitle to natural Khmer. Return only translated text: {text}"
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception:
            continue # បើ Error 404 វានឹងទៅសាក Model បន្ទាប់
            
    return "Error: មិនអាចហៅ Model បកប្រែបានទេ (សូមពិនិត្យ API Key)"

# ២. បង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    total = len(segments)
    progress_bar = st.progress(0, text="កំពុងបកប្រែ...")
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែ
        translated = translate_text(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600); m = int((seconds % 3600) // 60)
            s = int(seconds % 60); ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        progress_bar.progress((i + 1) / total)
        time.sleep(0.6) # ការពារ Rate Limit (Free Tier)
        
    return srt_content

# ៣. ដំណើរការសំខាន់
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model_w = load_whisper()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិន...", type=["mp4", "mov", "avi"])

if uploaded_file:
    st.video(uploaded_file)
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែ"):
        if not gemini_key:
            st.warning("⚠️ សូមបញ្ចូល API Key ជាមុនសិន!")
        else:
            with st.spinner('កំពុងដំណើរការ...'):
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # ជំហាន ១៖ Whisper Transcription
                    st.info("🔄 កំពុងស្ដាប់សំឡេងវីដេអូ...")
                    result = model_w.transcribe(video_path, fp16=False)
                    
                    # ជំហាន ២៖ Gemini Translation
                    st.info("🔄 កំពុងបកប្រែជាភាសាខ្មែរ (Gemini)...")
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ រួចរាល់!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ",
                        data=srt_data,
                        file_name="translated_khmer.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path): os.remove(video_path)
