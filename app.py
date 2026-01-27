import streamlit as st
import asyncio
import edge_tts
import os

st.set_page_config(page_title="Khmer Standard TTS", page_icon="🎙️")

st.title("🇰🇭 កម្មវិធីបម្លែងសំឡេងខ្មែរ (ស្តង់ដា)")

# ១. កន្លែងដាក់អត្ថបទ
text = st.text_area("បញ្ចូលអត្ថបទខ្មែរ៖", height=150)

# ២. ជ្រើសរើសតួអង្គ និងល្បឿន
col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសសំឡេង៖", 
                        ["km-KH-SreymomNeural (ស្រី)", "km-KH-PisethNeural (ប្រុស)"])
with col2:
    speed = st.slider("ល្បឿនអាន៖", 0.5, 2.0, 1.0, step=0.1)

# បង្កើត Function សម្រាប់បម្លែងសំឡេង
async def generate_audio(text, voice, rate):
    # កែសម្រួលល្បឿន (Format: +10% ឬ -10%)
    speed_str = f"{'+' if rate >= 1 else ''}{int((rate-1)*100)}%"
    communicate = edge_tts.Communicate(text, voice.split(' ')[0], rate=speed_str)
    await communicate.save("output.mp3")

if st.button("🔊 ចាប់ផ្ដើមបម្លែង"):
    if text:
        with st.spinner('កំពុងបង្កើតសំឡេង...'):
            asyncio.run(generate_audio(text, voice, speed))
            
            # ៣. បង្ហាញ Audio និងប៊ូតុង Download
            st.audio("output.mp3")
            with open("output.mp3", "rb") as f:
                st.download_button("📥 ទាញយក MP3", f, "khmer_audio.mp3")
            st.success("រួចរាល់!")
    else:
        st.error("សូមបញ្ចូលអត្ថបទជាមុនសិន!")
