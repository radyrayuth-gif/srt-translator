import streamlit as st
import whisper
import os
import openai

# កំណត់ទម្រង់ទំព័រ
st.set_page_config(page_title="AI Video Translator Pro", page_icon="🤖")

# --- ផ្នែក Sidebar សម្រាប់បញ្ចូល API Key ---
with st.sidebar:
    st.title("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល OpenAI API Key របស់អ្នក៖", type="password")
    st.info("អ្នកអាចបង្កើត Key បាននៅ៖ [platform.openai.com](https://platform.openai.com/)")

st.title("🤖 បកប្រែវីដេអូចិន-ខ្មែរ ដោយប្រើ AI (GPT-4)")
st.markdown("---")

# ១. មុខងារបកប្រែដោយប្រើ GPT (បកតាមន័យ)
def translate_with_gpt(text, user_key):
    if not user_key:
        return None
    
    client = openai.OpenAI(api_key=user_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a pro Chinese-to-Khmer translator. Translate the meaning naturally for movie subtitles. Don't be robotic."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except:
        return "បកប្រែមានបញ្ហា (សូមពិនិត្យ Key របស់អ្នក)"

# ២. មុខងារបង្កើត SRT
def create_srt(segments, user_key):
    srt_content = ""
    progress_bar = st.progress(0)
    total = len(segments)
    
    for i, segment in enumerate(segments):
        start, end, text = segment['start'], segment['end'], segment['text']
        
        # បកប្រែ
        translated = translate_with_gpt(text, user_key)
        
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        progress_bar.progress((i + 1) / total)
        
    return srt_content

# ៣. ដំណើរការសំខាន់
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិនរបស់អ្នក...", type=["mp4", "mov", "avi"])

if uploaded_file:
    st.video(uploaded_file)
    
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែដោយ AI"):
        if not api_key:
            st.warning("⚠️ សូមបញ្ចូល API Key ក្នុងប្រអប់ខាងឆ្វេងជាមុនសិន!")
        else:
            with st.spinner('AI កំពុងវិភាគ និងបកប្រែន័យ...'):
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # ស្ដាប់សំឡេង
                    result = model.transcribe(video_path, fp16=False)
                    
                    # បកប្រែ និងបង្កើត SRT
                    srt_data = create_srt(result['segments'], api_key)
                    
                    st.success("✅ ការបកប្រែដោយ AI រួចរាល់!")
                    st.download_button(
                        label="📥 ទាញយក Subtitle ខ្មែរ (ន័យត្រឹមត្រូវខ្ពស់)",
                        data=srt_data,
                        file_name="ai_subtitle_kh.srt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(video_path):
                        os.remove(video_path)
