import streamlit as st
import asyncio
import edge_tts
import io
import re
from pydub import AudioSegment
from datetime import datetime

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Perfect Sync", page_icon="🎙️")

def srt_time_to_ms(time_str):
    time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
    return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)

def parse_srt(srt_text):
    pattern = r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\d+\s+|\Z)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    for m in matches:
        subtitles.append({
            "start": srt_time_to_ms(m[1]),
            "text": m[3].replace('\n', ' ').strip()
        })
    return subtitles

async def generate_perfect_sync_audio(subtitles, voice, rate, pitch):
    # បង្កើត Audio ទទេសម្រាប់ចាប់ផ្ដើម
    combined = AudioSegment.silent(duration=0)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    progress_bar = st.progress(0)
    
    for i, sub in enumerate(subtitles):
        # ១. បង្កើតសំឡេងអានសម្រាប់តែមួយឃ្លានេះ
        communicate = edge_tts.Communicate(sub["text"], voice, rate=rate_str, pitch=pitch_str)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        
        # បំប្លែង Bytes ទៅជា AudioSegment
        segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        
        # ២. គណនា៖ តើត្រូវថែមភាពស្ងាត់ប៉ុន្មាន ដើម្បីឱ្យចំវិនាទីក្នុង SRT?
        current_len = len(combined)
        needed_silence = sub["start"] - current_len
        
        if needed_silence > 0:
            # បើមិនទាន់ដល់ពេលអាន ថែមភាពស្ងាត់ចូល
            combined += AudioSegment.silent(duration=needed_silence)
        
        # ៣. ដាក់សំឡេងអានចូល (Overlays ឬ Append)
        # ប្រសិនបើកន្លែងខ្លះអានយឺតពេក វាអាចនឹងជាន់គ្នាបន្តិច ប៉ុន្តែវិនាទីចាប់ផ្ដើមគឺត្រូវជានិច្ច
        combined = combined.overlay(segment, position=sub["start"])
        
        # ប្រសិនបើចង់ឱ្យវាវែងទៅតាមសំឡេងអាន (ក្នុងករណីសំឡេងអានវែងជាង SRT)
        if sub["start"] + len(segment) > len(combined):
            # បន្ថែមចន្លោះឱ្យត្រូវនឹងប្រវែងសំឡេង
            combined += AudioSegment.silent(duration=(sub["start"] + len(segment)) - len(combined))

        progress_bar.progress((i + 1) / len(subtitles))

    # រក្សាទុកជា Bytes
    out_buf = io.BytesIO()
    combined.export(out_buf, format="mp3")
    return out_buf.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS: Sync តាមវិនាទី SRT")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch)", -20, 20, 0, 1)

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT នៅទីនេះ:", height=300)

if st.button("🚀 បង្កើតសំឡេង Sync វិនាទី"):
    if srt_input.strip():
        try:
            subs = parse_srt(srt_input)
            with st.spinner("កំពុងរៀបចំតាមវិនាទី..."):
                audio_data = asyncio.run(generate_perfect_sync_audio(subs, voice_id, speed_rate, pitch_val))
                st.success("រួចរាល់! សំឡេងនឹងអានចំពេលដែលអ្នកកំណត់ក្នុង SRT។")
                st.audio(audio_data, format="audio/mp3")
                st.download_button("📥 ទាញយក MP3", audio_data, "sync_perfect.mp3")
        except Exception as e:
            st.error(f"កំហុសបច្ចេកទេស៖ {e}")
