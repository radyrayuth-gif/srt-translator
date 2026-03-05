import streamlit as st
import whisper
import os
import google.generativeai as genai
import time

# កំណត់ទម្រង់ទំព័រ
st.set_page_config(page_title="Gemini AI Video Translator", page_icon="♊")

# Sidebar សម្រាប់ API Key
with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")
    st.info("យក Key នៅទីនេះ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("♊ បកប្រែវីដេអូចិន-ខ្មែរ ដោយប្រើ Gemini AI")
st.markdown("---")

# ១. មុខងារបកប្រែ (កែសម្រួលដើម្បីជៀសវាង Error 404)
def translate_with_gemini(text, api_key):
    if not api_key: return "Missing API Key"
    try:
        genai.configure(api_key=api_key)
        
        # ប្រើឈ្មោះពេញ models/gemini-1.5-flash
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
        
        prompt = f"You are a professional translator. Translate this Chinese text into natural Khmer: {text}. Return ONLY the translated text."
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        return "បកប្រែមិនចេញ"
    except Exception as e:
        # បើនៅតែ 404 សាកប្រើ model ជំនាន់មុន (gemini-1.0-pro) ជាជម្រើសចុងក្រោយ
        try:
            model = genai.GenerativeModel(model_name='models/gemini-1.0-pro')
            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            return f"Error: {str(e)}"

# ២. មុខងារបង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    total = len(segments)
    progress_bar = st.progress(0, text="កំពុងបកប្រែឃ្លានីមួយៗ...")
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែ
        translated = translate_with_gemini(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        
        # បង្ហាញការរីកចម្រើន
        pct = (i + 1) / total
        progress_bar.progress(pct, text=f"បកប្រែបាន {int(pct*100)}% ({i+1}/{total})")
        time.sleep(0.5) # ការពារ Rate Limit
        
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
            st.warning("⚠️ សូមបញ្ចូល API Key ក្នុង Sidebar!")
        else:
            with st.spinner('កំពុងដំណើរការ...'):
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # ជំហាន ១៖ ស្ដាប់សំឡេង
                    st.info("🔄 កំពុងបម្លែងសំឡេងជាអក្សរ...")
                    result = model_w.transcribe(video_path, fp16=False)
                    
                    # ជំហាន ២៖ បកប្រែ និងបង្កើត SRT
                    st.info("🔄 Gemini AI កំពុងបកប្រែជាភាសាខ្មែរ...")
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ រួចរាល់! សូមទាញយកឯកសារខាងក្រោម៖")
                    st.download_button(
                        label="📥 ទាញយកឯកសារ Subtitle ខ្មែរ (.srt)",
                        data=srt_data,
                        file_name="gemini_khmer_fixed.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path): os.remove(video_path)
