import streamlit as st
import whisper
import os
from deep_translator import GoogleTranslator
from moviepy.editor import VideoFileClip

st.set_page_config(page_title="បកប្រែវីដេអូ ចិន-ខ្មែរ", page_icon="🎥")

st.title("🎥 កម្មវិធីបកប្រែវីដេអូចិន មកជាភាសាខ្មែរ")

@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិននៅទីនេះ...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("ចាប់ផ្ដើមបកប្រែ"):
        with st.spinner('កំពុងដំណើរការ...'):
            # រក្សាទុកឯកសារ
            with open("video.mp4", "wb") as f:
                f.write(uploaded_file.getbuffer())

            # ១. បម្លែងសំឡេងជាអក្សរ
            result = model.transcribe("video.mp4")
            chinese_text = result['text']

            # ២. បកប្រែជាខ្មែរ (ប្រើ Deep Translator)
            translated_text = GoogleTranslator(source='zh-CN', target='km').translate(chinese_text)

            # ៣. បង្ហាញលទ្ធផល
            st.success("រួចរាល់!")
            st.subheader("អក្សរបកប្រែជាភាសាខ្មែរ៖")
            st.write(translated_text)
            
            os.remove("video.mp4")
