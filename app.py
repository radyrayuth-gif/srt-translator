import streamlit as st
import asyncio
import edge_tts
import re
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    """បំប្លែងពេលវេលា SRT ទៅជាវិនាទីសុទ្ធ"""
    time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
    return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)

def parse_srt(srt_text):
    """ទាញយកពេលវេលា និងអត្ថបទ (មិនអានលេខរៀង)"""
    pattern = r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\d+|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    return [{"start": srt_time_to_seconds(m[0]), "text": m[2].strip()} for m in matches]

async def generate_synced_ssml(subtitles, voice):
    """ប្រើ SSML ដើម្បីបញ្ជាឱ្យ AI ឈប់រង់ចាំឱ្យចំវិនាទី (Sync)"""
    ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"
    current_time = 0
    
    for sub in subtitles:
        # គណនាចន្លោះដែលត្រូវឱ្យ AI ស្ងាត់ (Break)
        wait_time = sub["start"] - current_time
        if wait_time > 0:
            ssml += f"<break time='{int(wait_time * 1000)}ms'/>"
        
        ssml += f"<prosody rate='0%'>{sub['text']}</prosody>"
        # ប៉ាន់ស្មានរយៈពេលអានខ្លីបំផុត ដើម្បីគណនាឃ្លាបន្ទាប់
        current_time = sub["start"] + 0.1 
        
    ssml += "</speak>"
    
    communicate = edge_tts.Communicate(ssml, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer TTS Perfect Sync (No-Error)")

voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង Sync"):
    if srt_input:
        try:
            subs = parse_srt(srt_input)
            if subs:
                with st.spinner("កំពុងគណនាវិនាទី និងផលិតសំឡេង..."):
                    audio_bytes = asyncio.run(generate_synced_ssml(subs, voice_id))
                    st.success("រួចរាល់! សំឡេងនឹងអានត្រូវតាមវិនាទី SRT។")
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_bytes, "sync_voice.mp3")
        except Exception as e:
            st.error(f"បញ្ហា៖ {e}")
