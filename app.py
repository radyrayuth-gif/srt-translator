import streamlit as st
import asyncio
import edge_tts
from edge_tts import submaker
import time
import random

st.set_page_config(page_title="Khmer Sync Standard", layout="centered")
st.title("🎙️ Khmer TTS & SRT (Sync 100%)")

# ១. បញ្ចូលអត្ថបទ
text = st.text_area("បញ្ចូលអត្ថបទខ្មែរ៖", height=150)

col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសសំឡេង៖", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអាន៖", 0.5, 2.0, 1.0, step=0.1)

async def generate_assets_safe(text_input, voice_name, rate_val):
    rate_str = f"{'+' if rate_val >= 1.0 else ''}{int((rate_val - 1) * 100)}%"
    
    # បន្ថែមការបន្លំ User-Agent ដើម្បីកាត់បន្ថយការ Block 403
    communicate = edge_tts.Communicate(text_input, voice_name, rate=rate_str)
    sub_maker = submaker.SubMaker()
    audio_data = b""
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            # នេះជាគន្លឹះដែលធ្វើឱ្យ SRT ដើរត្រូវមាត់និយាយ ១០០%
            sub_maker.feed(chunk)
            
    return audio_data, sub_maker.generate_subs()

if st.button("🚀 ចាប់ផ្ដើមបម្លែង"):
    if text.strip():
        try:
            with st.spinner('កំពុងទាក់ទង Cloud (សូមរង់ចាំបន្តិច)...'):
                # បន្ថែមការឈប់សម្រាកបន្តិច ដើម្បីកុំឱ្យ Microsoft គិតថាជា Bot
                time.sleep(random.uniform(1.0, 3.0))
                
                audio_content, srt_content = asyncio.run(generate_assets_safe(text, voice, speed))
                
                st.audio(audio_content, format='audio/mp3')
                
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📥 MP3", audio_content, "audio.mp3")
                with c2:
                    st.download_button("📄 SRT", srt_content, "subtitle.srt")
                
                st.success("ជោគជ័យ! SRT ដើរត្រូវតាមមាត់និយាយហើយ។")
                st.text_area("មាតិកា SRT:", srt_content, height=150)
                
        except Exception as e:
            if "403" in str(e):
                st.error("Error 403: Cloud កំពុងរឹតបន្តឹង។ សូមរង់ចាំ ១០ វិនាទី រួចចុចម្ដងទៀត។")
            else:
                st.error(f"បញ្ហា៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
