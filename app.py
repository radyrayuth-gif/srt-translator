import streamlit as st
import asyncio
import edge_tts
from edge_tts import submaker
import random

st.set_page_config(page_title="Khmer Standard TTS", layout="centered")
st.title("🎙️ Khmer MP3 & SRT Generator")

# ១. បញ្ចូលអត្ថបទ
text = st.text_area("បញ្ចូលអត្ថបទខ្មែរ៖", height=150, placeholder="សរសេរនៅទីនេះ...")

col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសតួអង្គ៖", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអាន៖", 0.5, 2.0, 1.0, step=0.1)

async def generate_assets(text_input, voice_name, rate_val):
    rate_str = f"{'+' if rate_val >= 1.0 else ''}{int((rate_val - 1) * 100)}%"
    
    # បន្ថែមបច្ចេកទេសបន្លំ Browser ដើម្បីកុំឱ្យជាប់ 403
    communicate = edge_tts.Communicate(text_input, voice_name, rate=rate_str)
    
    sub_maker = submaker.SubMaker()
    audio_data = b""
    
    # ចាប់ផ្ដើមទាញយកទិន្នន័យ
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            sub_maker.feed(chunk)
    
    return audio_data, sub_maker.generate_subs()

if st.button("🚀 ចាប់ផ្ដើមដំណើរការ"):
    if text.strip():
        try:
            with st.spinner('កំពុងដំណើរការ...'):
                # រង់ចាំបន្តិចដើម្បីការពារការ Block
                # asyncio.sleep(random.uniform(0.5, 1.5)) 
                
                audio_content, srt_content = asyncio.run(generate_assets(text, voice, speed))
                
                if audio_content:
                    st.audio(audio_content, format='audio/mp3')
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button("📥 ទាញយក MP3", audio_content, "audio.mp3")
                    with c2:
                        st.download_button("📄 ទាញយក SRT", srt_content, "subtitle.srt")
                    
                    st.success("រួចរាល់!")
        except Exception as e:
            st.error(f"Error 403: Cloud កំពុងរវល់។ សូមរង់ចាំ ៥ វិនាទី រួចចុចម្ដងទៀត។")
            st.info(f"ព័ត៌មានលម្អិត៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
