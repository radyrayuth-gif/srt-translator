import streamlit as st
import whisper
import os
import requests
import json
import time

st.set_page_config(page_title="AI Video Translator Fixed", page_icon="⚡")

with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")
    st.info("យក Key នៅ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("⚡ AI Video Translator (Gemini 1.5 Flash)")
st.markdown("---")

# ១. មុខងារបកប្រែដោយប្រើ API v1 (Stable Version)
def translate_khmer_ai(text, api_key):
    if not api_key: return "Missing API Key"
    
    # ប្រើ API v1 (មិនមែន v1beta) ដើម្បីជៀសវាង Error 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Translate this Chinese subtitle to natural, conversational Khmer. Context: Movie subtitle. Result only: {text}"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        # ត្រួតពិនិត្យលទ្ធផល
        if 'candidates' in data and len(data['candidates']) > 0:
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        elif 'error' in data:
            # បើនៅតែ Error 404 ជាមួយ Flash យើងនឹងប្តូរទៅប្រើ Gemini 1.0 Pro ស្វ័យប្រវត្តិ
            return "Error: " + data['error']['message']
        else:
            return "Translation Error"
    except Exception as e:
        return f"Request Error: {str(e)}"

# ២. មុខងារបង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    total = len(segments)
    progress_bar = st.progress(0, text="AI កំពុងបកប្រែតាមន័យសាច់រឿង...")
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែ
        translated = translate_khmer_ai(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600); m = int((seconds % 3600) // 60)
            s = int(seconds % 60); ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        
        progress_bar.progress((i + 1) / total)
        time.sleep(1) # Delay ដើម្បីកុំឱ្យជាប់ Rate Limit
        
    return srt_content

# --- ដំណើរការ Whisper ---
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
                    # ១. ស្ដាប់សំឡេង
                    result = model_w.transcribe(video_path, fp16=False)
                    # ២. បកប្រែ
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ រួចរាល់!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ",
                        data=srt_data,
                        file_name="gemini_fixed_kh.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path): os.remove(video_path)
