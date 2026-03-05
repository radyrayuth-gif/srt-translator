import streamlit as st
import whisper
import os
import requests
import json
import time

st.set_page_config(page_title="Gemini Final Fix", page_icon="♊")

with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key៖", type="password")
    st.info("យក Key នៅ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("♊ បកប្រែវីដេអូចិន-ខ្មែរ (ជំនាន់ចុងក្រោយបង្អស់)")
st.markdown("---")

# ១. មុខងារបកប្រែដោយប្រើ REST API (វិធីនេះដើរ ១០០% ទោះ Model ធម្មតារកមិនឃើញ)
def translate_khmer(text, api_key):
    if not api_key: return "Missing API Key"
    
    # ប្រើ URL ជំនាន់ v1beta ដែលគាំទ្រ Gemini 1.5 Flash គ្រប់តំបន់
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Translate this Chinese subtitle text to natural Khmer language. Return only the result: {text}"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        # ទាញយកអត្ថបទបកប្រែចេញពី JSON
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"Error: {data.get('error', {}).get('message', 'Unknown Error')}"
    except Exception as e:
        return f"Request Error: {str(e)}"

# ២. បង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    total = len(segments)
    progress_bar = st.progress(0, text="កំពុងបកប្រែ...")
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែតាមរយៈ REST API
        translated = translate_khmer(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600); m = int((seconds % 3600) // 60)
            s = int(seconds % 60); ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        progress_bar.progress((i + 1) / total)
        time.sleep(1) # បន្ថែម Delay ដើម្បីកុំឱ្យលើស Limit របស់ Free Key
        
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
                    # Transcription
                    result = model_w.transcribe(video_path, fp16=False)
                    # Translation
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ បកប្រែរួចរាល់!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ",
                        data=srt_data,
                        file_name="khmer_subtitle.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path): os.remove(video_path)
