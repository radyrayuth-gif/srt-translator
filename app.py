import streamlit as st
import whisper
import os
import google.generativeai as genai
import time

st.set_page_config(page_title="បកប្រែវីដេអូ Gemini AI", page_icon="♊")

# Sidebar សម្រាប់ API Key
with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")
    st.info("យក Key នៅទីនេះ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("♊ បកប្រែវីដេអូចិន-ខ្មែរ ដោយប្រើ Gemini AI")
st.markdown("---")

# ១. មុខងារបកប្រែ (កែសម្រួលឈ្មោះ model ឱ្យត្រូវតាមស្តង់ដារថ្មី)
def translate_with_gemini(text, api_key):
    if not api_key: return "Missing API Key"
    try:
        genai.configure(api_key=api_key)
        # ប្រើឈ្មោះពេញលេញដើម្បីការពារ Error 404
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = f"Translate this Chinese subtitle to natural Khmer. Return only the translated text: {text}"
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        return "Translation Empty"
    except Exception as e:
        return f"Error: {str(e)}"

# ២. មុខងារបង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    total = len(segments)
    progress_bar = st.progress(0, text="កំពុងបកប្រែ...")
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        translated = translate_with_gemini(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        progress_bar.progress((i + 1) / total, text=f"បកប្រែបាន {int(((i+1)/total)*100)}%")
        time.sleep(0.1) # ការពារកុំឱ្យលើស Rate Limit របស់ Free Key
        
    return srt_content

# ៣. ដំណើរការ Whisper
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិនរបស់អ្នក...", type=["mp4", "mov", "avi"])

if uploaded_file:
    st.video(uploaded_file)
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែ"):
        if not gemini_key:
            st.warning("⚠️ សូមបញ្ចូល API Key ក្នុង Sidebar!")
        else:
            with st.spinner('កំពុងដំណើរការ...'):
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # Transcription
                    result = model.transcribe(video_path, fp16=False)
                    # Translation & SRT
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ រួចរាល់!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ",
                        data=srt_data,
                        file_name="gemini_khmer.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path): os.remove(video_path)
