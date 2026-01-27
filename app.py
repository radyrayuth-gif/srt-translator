import streamlit as st
import asyncio
import edge_tts
import re
import io
import base64
from datetime import datetime
from pydub import AudioSegment

st.set_page_config(page_title="Khmer Perfect Sync", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)
    except:
        return 0

def parse_srt_to_list(srt_text):
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        if time_line and text_lines:
            start_sec = srt_time_to_seconds(time_line.split("-->")[0].strip())
            subtitles.append({"start": start_sec, "text": " ".join(text_lines)})
    return subtitles

async def generate_audio_segment(text, voice, rate):
    rate_str = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")

st.title("🎙️ Khmer TTS: Perfect Sync")

st.sidebar.header("ការកំណត់")
voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
speed = st.sidebar.slider("ល្បឿននិយាយ (%)", min_value=-50, max_value=50, value=0, step=5)
srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT ទីនេះ:", height=250)

if st.button("🚀 ផលិត និងទាញយកសំឡេង"):
    if srt_input:
        subs = parse_srt_to_list(srt_input)
        if subs:
            with st.spinner("កំពុងផលិតសំឡេង..."):
                final_audio = AudioSegment.silent(duration=0)
                for sub in subs:
                    segment = asyncio.run(generate_audio_segment(sub["text"], voice_id, speed))
                    start_ms = int(sub["start"] * 1000)
                    if len(final_audio) < start_ms:
                        final_audio += AudioSegment.silent(duration=start_ms - len(final_audio))
                    final_audio = final_audio.overlay(segment, position=start_ms)
                
                buffer = io.BytesIO()
                final_audio.export(buffer, format="mp3")
                buffer.seek(0)
                audio_bytes = buffer.read()
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="📥 ទាញយកឯកសារសំឡេង (.mp3)",
                        data=audio_bytes,
                        file_name=f"khmer_audio.mp3",
                        mime="audio/mp3"
                    )
                    st.success("រួចរាល់! សូមចុចប៊ូតុងខាងលើដើម្បីដោនឡូត។")
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន។")
