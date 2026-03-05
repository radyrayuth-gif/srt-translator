import streamlit as st
import whisper
import os
import requests
import json
import time

st.set_page_config(page_title="AI Video Translator Pro", page_icon="⚡")

with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")
    st.info("យក Key នៅទីនេះ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("⚡ AI Video Translator (Gemini 1.5 Flash)")
st.write("បកប្រែវីដេអូចិនមកខ្មែរ ដោយប្រើបច្ចេកវិទ្យា AI ចុងក្រោយបង្អស់របស់ Google។")
st.markdown("---")

# ១. មុខងារបកប្រែជាមួយ Gemini 1.5 Flash តាមរយៈ REST API (v1beta)
def translate_khmer_pro(text, api_key):
    if not api_key: return "Missing API Key"
    
    # ប្រើ Endpoint ផ្លូវការដែលធានាថាស្គាល់ 1.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are a professional movie subtitle translator. Translate this Chinese text into natural, smooth, and conversational Khmer language. Don't translate word-for-word, focus on the meaning. Text: {text}"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        # ដកស្រង់អត្ថបទបកប្រែ
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"Error: {data.get('error', {}).get('message', 'Model not ready')}"
    except Exception as e:
        return f"Request Error: {str(e)}"

# ២. មុខងារបង្កើត SRT
def create_srt(segments, api_key):
    srt_content = ""
    total = len(segments)
    progress_bar = st.progress(0, text="AI កំពុងវិភាគ និងបកប្រែន័យ...")
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែ
        translated = translate_khmer_pro(text, api_key)
        
        def format_time(seconds):
            h = int(seconds // 3600); m = int((seconds % 3600) // 60)
            s = int(seconds % 60); ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        
        progress_bar.progress((i + 1) / total)
        time.sleep(1) # Delay សម្រាប់ Free Tier របស់ Google
        
    return srt_content

# ៣. ដំណើរការ Whisper
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model_w = load_whisper()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិនរបស់អ្នក (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])

if uploaded_file:
    st.video(uploaded_file)
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែដោយ Gemini 1.5 Flash"):
        if not gemini_key:
            st.warning("⚠️ សូមបញ្ចូល API Key ក្នុងប្រអប់ខាងឆ្វេងជាមុនសិន!")
        else:
            with st.spinner('កំពុងដំណើរការ... សូមកុំបិទផ្ទាំងវេបសាយនេះ'):
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # Transcription
                    result = model_w.transcribe(video_path, fp16=False)
                    # Translation
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    st.success("✅ ការបកប្រែដោយ AI បានសម្រេច!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ (Gemini Quality)",
                        data=srt_data,
                        file_name="gemini_subtitle_kh.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path): os.remove(video_path)
