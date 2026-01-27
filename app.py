import streamlit as st
import asyncio
import edge_tts
import re
from datetime import datetime

st.set_page_config(page_title="Khmer TTS No-FFmpeg", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return time_str.strip()
    except: return "00:00:00"

def parse_srt(srt_text):
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        if time_line and text_lines:
            subtitles.append({"time": time_line.split("-->")[0].strip(), "text": " ".join(text_lines)})
    return subtitles

async def get_voice_bytes(text, voice, rate):
    communicate = edge_tts.Communicate(text, voice, rate=f"{rate:+d}%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer TTS (វិធីសាស្ត្រងាយស្រួល)")
st.info("វិធីនេះមិនប្រើ FFmpeg ទេ ដូច្នេះវានឹងមិន Error ទៀតឡើយ!")

voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
speed = st.sidebar.slider("ល្បឿន (%):", -50, 50, 0)
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=200)

if st.button("🚀 បំប្លែងសំឡេង"):
    if srt_input:
        subs = parse_srt(srt_input)
        for i, sub in enumerate(subs):
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"⏱️ {sub['time']}")
                with col2:
                    audio_bytes = asyncio.run(get_voice_bytes(sub["text"], voice_id, speed))
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(f"ទាញយកឃ្លាទី {i+1}", audio_bytes, file_name=f"part_{i+1}.mp3")
    else:
        st.warning("សូមបញ្ចូល SRT")
