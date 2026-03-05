import streamlit as st
import whisper
import os
import openai

st.set_page_config(page_title="បកប្រែវីដេអូ AI Pro", page_icon="🤖")

# --- កន្លែងដាក់ API KEY របស់អ្នក ---
# ណែនាំ៖ គួរដាក់ក្នុង Streamlit Secrets ដើម្បីសុវត្ថិភាព
OPENAI_API_KEY = "ដាក់_API_KEY_របស់អ្នកនៅទីនេះ" 

st.title("🤖 ជំនួយការបកប្រែវីដេអូដោយប្រើ GPT-4o")
st.markdown("កម្មវិធីនេះប្រើប្រាស់ AI ជំនាន់ចុងក្រោយដើម្បីបកប្រែឱ្យមានន័យសមស្របតាមបរិបទខ្មែរ។")

# ១. មុខងារបកប្រែដោយប្រើ GPT-4o
def translate_with_gpt(text):
    if not OPENAI_API_KEY or "ដាក់" in OPENAI_API_KEY:
        st.error("សូមបញ្ចូល OpenAI API Key ជាមុនសិន!")
        return text
        
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # ប្រើ mini ដើម្បីសន្សំលុយ និងដើរលឿន
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate Chinese video subtitles to Khmer. Ensure the tone is natural, conversational, and easy for Cambodians to understand. Don't translate word-for-word, translate the meaning."},
                {"role": "user", "content": f"Translate this: {text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ២. មុខងារបង្កើត SRT
def create_srt(segments):
    srt_content = ""
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # បកប្រែដោយប្រើ GPT
        translated_text = translate_with_gpt(text)
        
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated_text}\n\n"
    return srt_content

# ៣. ផ្នែកដំណើរការកម្មវិធី
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិន...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែដោយ AI"):
        with st.spinner('GPT កំពុងវិភាគន័យសាច់រឿង...'):
            video_path = os.path.join(os.getcwd(), "temp_video.mp4")
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                result = model.transcribe(video_path, fp16=False)
                
                # បង្កើត SRT (វានឹងបកប្រែម្ដងមួយឃ្លាៗដោយប្រើ GPT)
                srt_data = create_srt(result['segments'])
                
                st.success("ការបកប្រែដោយ AI រួចរាល់!")
                
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
