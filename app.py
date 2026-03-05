import streamlit as st
import whisper
import os
from deep_translator import GoogleTranslator

# កំណត់ទម្រង់ទំព័រវេបសាយ
st.set_page_config(page_title="បកប្រែវីដេអូ ចិន-ខ្មែរ Pro", page_icon="🇰🇭")

st.title("🇰🇭 កម្មវិធីបកប្រែវីដេអូចិនមកជាភាសាខ្មែរ (គុណភាពខ្ពស់)")
st.markdown("---")

# ១. មុខងារបកប្រែពី ចិន -> អង់គ្លេស -> ខ្មែរ (Pivot Translation)
def improved_translate(text):
    try:
        # បកពី ចិន ទៅ អង់គ្លេស សិន (ដើម្បីរក្សាន័យឱ្យចំល្អ)
        english_text = GoogleTranslator(source='zh-CN', target='en').translate(text)
        # បកពី អង់គ្លេស បន្តមក ខ្មែរ (ដើម្បីឱ្យវេយ្យាករណ៍ខ្មែររលូនជាងមុន)
        khmer_text = GoogleTranslator(source='en', target='km').translate(english_text)
        return khmer_text
    except:
        return text

# ២. មុខងារបង្កើតឯកសារ SRT
def create_srt(segments):
    srt_content = ""
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # ប្រើមុខងារបកប្រែដែលបានកែលម្អ
        translated_text = improved_translate(text)
        
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated_text}\n\n"
    return srt_content

# ៣. Load Model Whisper
@st.cache_resource
def load_model():
    # ប្រសិនបើមាន Error ដើរយឺត អ្នកអាចប្តូរ "small" មក "base" វិញបាន
    return whisper.load_model("small") 

model = load_model()

# ៤. ផ្ទៃ Interface
uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិនរបស់អ្នក (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែគុណភាពខ្ពស់"):
        with st.spinner('កំពុងស្ដាប់សំឡេង និងបកប្រែជាភាសាខ្មែរ...'):
            video_path = os.path.join(os.getcwd(), "temp_video.mp4")
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                # ដំណើរការបម្លែងសំឡេងជាអក្សរ
                result = model.transcribe(video_path, fp16=False)
                
                # បង្ហាញអក្សរបកប្រែសរុប
                st.success("ការបកប្រែជោគជ័យ!")
                
                full_text_zh = result['text']
                full_text_km = improved_translate(full_text_zh)
                
                with st.expander("មើលអត្ថបទដែលបានបកប្រែ"):
                    st.subheader("អត្ថបទភាសាខ្មែរ៖")
                    st.write(full_text_km)
                
                # បង្កើតឯកសារ SRT
                srt_data = create_srt(result['segments'])
                
                st.markdown("---")
                st.subheader("📥 ទាញយកលទ្ធផល")
                st.download_button(
                    label="📥 ទាញយកឯកសារ Subtitle (.srt) ភាសាខ្មែរ",
                    data=srt_data,
                    file_name="translated_khmer.srt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error: {e}")
            
            finally:
                if os.path.exists(video_path):
                    os.remove(video_path)

st.markdown("---")
st.caption("ចំណាំ៖ ការបកប្រែនេះប្រើបច្ចេកទេសបកប្រែពី ចិន-អង់គ្លេស-ខ្មែរ ដើម្បីឱ្យអត្ថន័យកាន់តែច្បាស់។")
