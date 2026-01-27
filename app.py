import streamlit as st
import asyncio
import edge_tts
import io
import re
from pydub import AudioSegment
from datetime import datetime

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer Perfect Sync TTS", page_icon="🎙️")

def srt_time_to_ms(time_str):
    time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
    return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)

def parse_srt(srt_text):
    # Regex ដើម្បីទាញយកតែ ពេលវេលា និង អត្ថបទ (លុបលេខរៀងចេញ)
    pattern = r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\d{2}:\d{2}:\d{2},\d{3}|\n\n\d+|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    
    subtitles = []
    for m in matches:
        text_only = m[2].strip()
        if text_only:
            subtitles.append({
                "start": srt_time_to_ms(m[0]),
                "text": text_only
            })
    return subtitles

async def generate_perfect_audio(subtitles, voice, rate, pitch):
    # បង្កើត Audio ទទេជាមូលដ្ឋាន
    combined = AudioSegment.silent(duration=0)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    progress_bar = st.progress(0)
    
    for i, sub in enumerate(subtitles):
        # ១. បង្កើតសំឡេងអាន (អានតែអត្ថបទ មិនអានលេខ ឬ Tag)
        communicate = edge_tts.Communicate(sub["text"], voice, rate=rate_str, pitch=pitch_str)
        temp_buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                temp_buf.write(chunk["data"])
        
        temp_buf.seek(0)
        segment = AudioSegment.from_file(temp_buf, format="mp3")

        # ២. គណនាចន្លោះស្ងាត់ដើម្បីឱ្យត្រូវនឹងវិនាទីចាប់ផ្ដើម
        current_len = len(combined)
        silence_needed = sub["start"] - current_len
        
        if silence_needed > 0:
            combined += AudioSegment.silent(duration=silence_needed)
        
        # ៣. បន្ថែមសំឡេងអានចូលចំទីតាំង (ប្រើ Overlay ដើម្បីធានាភាពសុក្រឹត)
        combined = combined.overlay(segment, position=sub["start"])
        
        # ពង្រីកប្រវែង Audio សរុបប្រសិនបើសំឡេងអានវែងជាង
        if len(combined) < sub["start"] + len(segment):
            combined += AudioSegment.silent(duration=(sub["start"] + len(segment)) - len(combined))
            
        progress_bar.progress((i + 1) / len(subtitles))

    out_buf = io.BytesIO()
    combined.export(out_buf, format="mp3")
    return out_buf.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS Perfect Sync (No Tags)")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch)", -20, 20, 0, 1)

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT នៅទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input.strip():
        try:
            subs = parse_srt(srt_input)
            if not subs:
                st.error("រកមិនឃើញទម្រង់ SRT ត្រឹមត្រូវទេ!")
            else:
                with st.spinner("កំពុងរៀបចំសំឡេងតាមវិនាទី..."):
                    audio_data = asyncio.run(generate_perfect_audio(subs, voice_id, speed_rate, pitch_val))
                    st.success("រួចរាល់! សំឡេងនឹងអានចំពេល និងមិនអានលេខរៀងឡើយ។")
                    st.audio(audio_data, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_data, "khmer_subtitle_sync.mp3")
        except Exception as e:
            st.error(f"កំហុស៖ {e}")
