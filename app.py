import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# មុខងារបំប្លែងម៉ោង SRT ទៅជាមីលីវិនាទី
def srt_to_ms(time_str):
    h, m, s = time_str.replace(',', '.').split(':')
    return int((int(h) * 3600 + int(m) * 60 + float(s)) * 1000)

async def generate_voice(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data += chunk["data"]
    return AudioSegment.from_file(io.BytesIO(data), format="mp3")

st.title("🎙️ Khmer SRT Sync (Pro Version)")

srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=250)

if st.button("🚀 ផលិតសំឡេង"):
    if srt_input:
        with st.spinner("កំពុងផលិត..."):
            blocks = re.split(r'\n\s*\n', srt_input.strip())
            final_audio = AudioSegment.silent(duration=0)
            
            for block in blocks:
                lines = block.strip().split('\n')
                time_line = next((l for l in lines if "-->" in l), None)
                text = " ".join([l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()])
                
                if time_line and text:
                    start_ms = srt_to_ms(time_line.split("-->")[0].strip())
                    segment = asyncio.run(generate_voice(text, "km-KH-SreymomNeural"))
                    if len(final_audio) < start_ms:
                        final_audio += AudioSegment.silent(duration=start_ms - len(final_audio))
                    final_audio = final_audio.overlay(segment, position=start_ms)

            # នាំចេញជា MP3
            buffer = io.BytesIO()
            final_audio.export(buffer, format="mp3")
            buffer.seek(0) # ត្រឡប់មកដើមវិញដើម្បីឱ្យឮសំឡេង
            
            st.audio(buffer, format="audio/mp3")
            st.download_button("📥 ទាញយក MP3", buffer, "voice_sync.mp3")
