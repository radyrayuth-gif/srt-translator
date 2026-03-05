import streamlit as st
import whisper
import os
from deep_translator import GoogleTranslator

st.set_page_config(page_title="បកប្រែវីដេអូចិន-ខ្មែរ", page_icon="🎥")

st.title("🎥 កម្មវិធីបកប្រែវីដេអូចិន មកជាភាសាខ្មែរ")

# ១. មុខងារបង្កើតទម្រង់ឯកសារ SRT
def create_srt(segments):
    srt_content = ""
    translator = GoogleTranslator(source='zh-CN', target='km')
    
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # បកប្រែអក្សរក្នុងចំណែកនីមួយៗ
        try:
            translated_text = translator.translate(text)
        except:
            translated_text = text # បើបកប្រែមិនចេញ ឱ្យបង្ហាញអក្សរដើម
            
        # រៀបចំទម្រង់ពេលវេលា (00:00:00,000)
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated_text}\n\n"
    return srt_content

# ២. Load Model Whisper
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# ៣. ផ្ទៃ Interface សម្រាប់ Upload
uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិនរបស់អ្នកនៅទីនេះ...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    # បង្កើតប៊ូតុងបកប្រែ
    if st.button("ចាប់ផ្ដើមបកប្រែ និងបង្កើត Subtitle"):
        with st.spinner('កំពុងដំណើរការ... សូមរង់ចាំបន្តិច'):
            # រក្សាទុកវីដេអូបណ្ដោះអាសន្ន
            video_path = os.path.join(os.getcwd(), "temp_video.mp4")
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                # ដំណើរការបកប្រែ
                result = model.transcribe(video_path, fp16=False)
                
                # បង្ហាញអក្សរបកប្រែសរុបលើអេក្រង់
                full_text_zh = result['text']
                full_text_km = GoogleTranslator(source='zh-CN', target='km').translate(full_text_zh)
                
                st.success("ការបកប្រែរួចរាល់!")
                st.subheader("អក្សរបកប្រែជាភាសាខ្មែរ៖")
                st.write(full_text_km)
                
                # បង្កើតទិន្នន័យ SRT
                srt_data = create_srt(result['segments'])
                
                # ប៊ូតុងសម្រាប់ទាញយក
                st.download_button(
                    label="📥 ទាញយកឯកសារ Subtitle (.srt)",
                    data=srt_data,
                    file_name="subtitles_khmer.srt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")
            
            finally:
                if os.path.exists(video_path):
                    os.remove(video_path)
