import streamlit as st
import asyncio
import edge_tts
from edge_tts import submaker
import os

st.set_page_config(page_title="Khmer TTS & SRT", layout="centered")
st.title("🎙️ Khmer MP3 & SRT Generator")

# ១. បញ្បញ្ចូលអត្ថបទ
text = st.text_area("បញ្ចូលអត្ថបទខ្មែរ (កុំវែងពេកក្នុងម្ដងៗ):", height=150)

col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសតួអង្គ:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអាន:", 0.5, 2.0, 1.0, step=0.1)

async def generate_assets(text_input, voice_name, rate_val):
    # បំលែងល្បឿនជា %
    speed_str = f"{'+' if rate_val >= 1.0 else ''}{int((rate_val - 1) * 100)}%"
    
    # បង្កើតការតភ្ជាប់ជាមួយ Error Handling
    try:
        communicate = edge_tts.Communicate(text_input, voice_name, rate=speed_str)
        sub_maker = submaker.SubMaker()
        audio_data = b""
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                sub_maker.feed(chunk)
        
        srt_content = sub_maker.generate_subs()
        return audio_data, srt_content
    except Exception as e:
        raise e

if st.button("🚀 ចាប់ផ្ដើមដំណើរការ"):
    if text.strip():
        try:
            with st.spinner('កំពុងទាក់ទងទៅកាន់ Cloud...'):
                audio_content, srt_content = asyncio.run(generate_assets(text, voice, speed))
                
                st.audio(audio_content, format='audio/mp3')
                
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📥 ទាញយក MP3", audio_content, "voice.mp3")
                with c2:
                    st.download_button("📄 ទាញយក SRT", srt_content, "subtitle.srt")
                
                st.success("រួចរាល់ជោគជ័យ!")
        except Exception as e:
            st.error(f"កំហុស 403 ឬបញ្ហា Cloud: {e}")
            st.info("💡 ដំបូន្មាន: សាកល្បងចុចប៊ូតុងម្ដងទៀត ឬកាត់បន្ថយអត្ថបទឱ្យខ្លីជាងនេះបន្តិច។")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
