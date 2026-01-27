import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

st.set_page_config(page_title="Khmer Voice Sync Pro", page_icon="🎙️")

# ១. មុខងារបំប្លែងម៉ោង SRT ទៅជាមីលីវិនាទី (ms)
def time_to_ms(time_str):
    h, m, s = time_str.replace(',', '.').split(':')
    return int((int(h) * 3600 + int(m) * 60 + float(s)) * 1000)

# ២. មុខងារផលិតសំឡេងដុំៗ
async def get_audio_segment(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")

st.title("🎙️ Khmer Voice Sync (ដូច VoiceRTool)")
st.write("បិទភ្ជាប់ SRT រួចទាញយក File MP3 ដែល Sync រួចជាស្រេច")

voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT ទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិត File រួមគ្នា"):
    if srt_input:
        with st.spinner("កំពុងផលិត និងបញ្ចូលសំឡេងតាមនាទី..."):
            # ច្រោះយកម៉ោង និងអត្ថបទ
            blocks = re.split(r'\n\s*\n', srt_input.strip())
            final_audio = AudioSegment.silent(duration=0)
            
            for block in blocks:
                lines = block.strip().split('\n')
                time_line = next((l for l in lines if "-->" in l), None)
                text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
                
                if time_line and text_lines:
                    start_time_str = time_line.split("-->")[0].strip()
                    start_ms = time_to_ms(start_time_str)
                    text = " ".join(text_lines)
                    
                    # ផលិតសំឡេងដុំ
                    segment = asyncio.run(get_audio_segment(text, voice_id))
                    
                    # បន្ថែមភាពស្ងាត់បើមិនទាន់ដល់ម៉ោងអាន
                    if len(final_audio) < start_ms:
                        final_audio += AudioSegment.silent(duration=start_ms - len(final_audio))
                    
                    # ដាក់សំឡេងចូលក្នុង Timeline
                    final_audio = final_audio.overlay(segment, position=start_ms)

            # Export ជា File តែមួយ
            out_buffer = io.BytesIO()
            final_audio.export(out_buffer, format="mp3")
            out_buffer.seek(0)
            audio_bytes = out_buffer.read()

            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button("📥 ទាញយក File MP3 ដែល Sync រួច", audio_bytes, "khmer_sync_audio.mp3")
                st.success("ជោគជ័យ! សំឡេងអានត្រូវតាមនាទី SRT ទាំងអស់។")
    else:
        st.warning("សូមបញ្ចូល SRT!")
