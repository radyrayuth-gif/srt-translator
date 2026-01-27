import streamlit as st
import asyncio
import edge_tts
import io
from datetime import datetime

st.set_page_config(page_title="Khmer TTS Sync", page_icon="🎙️")

async def generate_voice(text, voice, rate):
    rate_str = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer TTS: Simple & Sync")

voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
speed = st.sidebar.slider("ល្បឿន (%):", -50, 50, 0)
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=200)

if st.button("🚀 ផលិតសំឡេង"):
    if srt_input:
        # ច្រោះយកតែអត្ថបទខ្មែរចេញពី SRT
        lines = srt_input.split('\n')
        clean_text = ""
        for line in lines:
            if not any(c in line for c in ['>', ':', '-']) and not line.strip().isdigit():
                clean_text += line + " "

        if clean_text.strip():
            with st.spinner("កំពុងផលិត..."):
                audio_bytes = asyncio.run(generate_voice(clean_text, voice_id, speed))
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="📥 ទាញយក MP3",
                        data=audio_bytes,
                        file_name="khmer_voice.mp3",
                        mime="audio/mp3"
                    )
                    st.success("រួចរាល់! បើចាក់មិនឮ សូមឆែកមើល Speaker ទូរសព្ទ។")
