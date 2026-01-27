import streamlit as st
import asyncio
import edge_tts
import io
import re
from pydub import AudioSegment
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync", page_icon="🎙️")

def srt_time_to_ms(time_str):
    time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
    return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)

def parse_srt(srt_text):
    # Regex នេះជួយលុបលេខរៀងចេញ ដើម្បីកុំឱ្យ AI អានលេខ ១, ២, ៣
    pattern = r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\d{2}:\d{2}:\d{2},\d{3}|\n\n\d+|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    for m in matches:
        text_only = m[2].strip()
        if text_only:
            subtitles.append({"start": srt_time_to_ms(m[0]), "text": text_only})
    return subtitles

async def generate_audio(subtitles, voice, rate, pitch):
    combined = AudioSegment.silent(duration=0)
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    for sub in subtitles:
        # បង្កើតសំឡេងអាន (មិនប្រើ SSML ដើម្បីកុំឱ្យអាន Tag ចេញមកក្រៅ)
        communicate = edge_tts.Communicate(sub["text"], voice, rate=rate_str, pitch=pitch_str)
        temp_buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                temp_buf.write(chunk["data"])
        
        temp_buf.seek(0)
        segment = AudioSegment.from_file(temp_buf, format="mp3")
        
        # បញ្ចូលភាពស្ងាត់ឱ្យត្រូវតាមវិនាទីចាប់ផ្ដើមក្នុង SRT
        silence_needed = sub["start"] - len(combined)
        if silence_needed > 0:
            combined += AudioSegment.silent(duration=silence_needed)
        
        combined = combined.overlay(segment, position=sub["start"])
        if len(combined) < sub["start"] + len(segment):
            combined += AudioSegment.silent(duration=(sub["start"] + len(segment)) - len(combined))
            
    out_buf = io.BytesIO()
    combined.export(out_buf, format="mp3")
    return out_buf.getvalue()

st.title("🎙️ កម្មវិធីអានតាមវិនាទី (Fixed)")
voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង"):
    if srt_input:
        subs = parse_srt(srt_input)
        audio_data = asyncio.run(generate_audio(subs, voice_id, 0, 0))
        st.audio(audio_data, format="audio/mp3")
