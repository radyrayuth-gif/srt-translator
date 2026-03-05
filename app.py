import streamlit as st
import whisper
import os
import google.generativeai as genai

st.set_page_config(page_title="Gemini Video Translator", page_icon="♊")

# --- ផ្នែក Sidebar សម្រាប់បញ្ចូល Gemini API Key ---
with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")
    st.info("យក Key នៅទីនេះ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("♊ បកប្រែវីដេអូចិន-ខ្មែរ ដោយប្រើ Gemini AI")
st.markdown("---")

# ១. មុខងារបកប្រែដោយប្រើ Gemini
def translate_with_gemini(text, api_key):
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') # ប្រើ model flash ដើម្បីល្បឿនលឿន
        prompt = f"You are a professional translator. Translate this Chinese text into natural Khmer language for video subtitles: {text}"
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# ២. មុខងារបង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    progress_bar = st.progress(0)
    total = len(segments)
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែដោយប្រើ Gemini
        translated = translate_with_gemini(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        progress_bar.progress((i + 1) / total)
        
    return srt_content

# ៣. ផ្នែកដំណើរការ Whisper
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

whisper_model = load_whisper()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិន...", type=["mp4", "mov", "avi"])

if uploaded_file:
    st.video(uploaded_file)
    
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែជាមួយ Gemini"):
        if not gemini_key:
            st.warning("⚠️ សូមបញ្ចូល Gemini API Key ក្នុង Sidebar ជាមុនសិន!")
        else:
            with st.spinner('Gemini កំពុងវិភាគន័យសាច់រឿង...'):
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # ស្ដាប់សំឡេង
                    result = whisper_model.transcribe(video_path, fp16=False)
                    
                    # បកប្រែ និងបង្កើត SRT
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ ការបកប្រែដោយ Gemini រួចរាល់!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ",
                        data=srt_data,
                        file_name="gemini_subtitle_kh.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path):
                        os.remove(video_path)
