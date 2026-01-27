import streamlit as st
import asyncio
import edge_tts
import io
import re
from datetime import datetime

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS SRT-Sync", page_icon="🎙️")

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

# --- មុខងារបង្កើតសំឡេង (កែសម្រួល SSML) ---
async def generate_synced_audio(subtitles, voice, rate, pitch):
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    # បង្កើត SSML String
    ssml_parts = [f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"]
    current_time_ms = 0
    
    for sub in subtitles:
        wait_time_ms = sub["start"] - current_time_ms
        if wait_time_ms > 0:
            ssml_parts.append(f"<break time='{wait_time_ms}ms'/>")
        
        ssml_parts.append(f"<prosody rate='{rate_str}' pitch='{pitch_str}'>{sub['text']}</prosody>")
        # ប៉ាន់ស្មានថាអត្ថបទខ្លីៗប្រើពេល ១ វិនាទី ដើម្បីគណនា Break បន្ទាប់
        current_time_ms = sub["start"] + 1000 

    ssml_parts.append("</speak>")
    ssml_string = "".join(ssml_parts)
    
    # កែសម្រួលត្រង់នេះ៖ ប្រើ Communicate ជាមួយ SSML ផ្ទាល់
    communicate = edge_tts.Communicate(ssml_string, voice) 
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI ---
st.title("🎙️ កម្មវិធីអានតាមពេលវេលា (Fixed)")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch)", -20, 20, 0, 1)

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT នៅទីនេះ:", height=300)

if st.button("🚀 បង្កើតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងបង្កើត..."):
            try:
                subs = parse_srt(srt_input)
                if subs:
                    # ហៅប្រើមុខងារដែលបានកែសម្រួល
                    audio_bytes = asyncio.run(generate_synced_audio(subs, voice_id, speed_rate, pitch_val))
                    st.success("រួចរាល់!")
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_bytes, "synced_audio.mp3")
                else:
                    st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
            except Exception as e:
                st.error(f"កំហុស៖ {e}")
