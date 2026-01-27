import streamlit as st
import asyncio
import edge_tts
import io
import re
from datetime import datetime

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS SRT-Sync", page_icon="🎙️")

# មុខងារបំប្លែងពេលវេលាពី SRT ទៅជា Milliseconds
def srt_time_to_ms(time_str):
    time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
    return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)

# មុខងារទាញយកទិន្នន័យពី SRT
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

# --- មុខងារបង្កើតសំឡេងប្រើ SSML ---
async def generate_synced_audio(subtitles, voice, rate, pitch):
    # កំណត់ល្បឿន និង Pitch
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    # ចាប់ផ្ដើមបង្កើត SSML
    ssml_parts = [f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"]
    
    current_time_ms = 0
    for sub in subtitles:
        # គណនាចន្លោះដែលត្រូវស្ងាត់ (Break)
        wait_time_ms = sub["start"] - current_time_ms
        if wait_time_ms > 0:
            ssml_parts.append(f"<break time='{wait_time_ms}ms'/>")
        
        # បន្ថែមអត្ថបទអាន
        ssml_parts.append(f"<prosody rate='{rate_str}' pitch='{pitch_str}'>{sub['text']}</prosody>")
        
        # ចំណាំ៖ ការប្រើ SSML បែបនេះ វានឹងព្យាយាមចាប់ផ្ដើមអានចំពេលដែលកំណត់
        # ប៉ុន្តែយើងមិនអាចដឹងច្បាស់ថាអានចប់ពេលណានោះទេ ដូច្នេះយើងដាក់ចន្លោះស្មើៗគ្នា
        current_time_ms = sub["start"] + 1000 # បន្ថែមប៉ាន់ស្មាន ១ វិនាទីសម្រាប់ឃ្លានីមួយៗ

    ssml_parts.append("</speak>")
    ssml_string = "".join(ssml_parts)
    
    communicate = edge_tts.Communicate(ssml_string, voice, is_ssml=True)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI ---
st.title("🎙️ កម្មវិធីអានតាមពេលវេលា (SSML)")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch)", -20, 20, 0, 1)

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT នៅទីនេះ:", height=300, 
                         placeholder="1\n00:00:02,000 --> 00:00:04,000\nសួស្តីប្អូនស្រី!")

if st.button("🚀 បង្កើតសំឡេងតាមពេលវេលា"):
    if srt_input.strip():
        with st.spinner("កំពុងគណនាពេលវេលា និងបង្កើតសំឡេង..."):
            try:
                subs = parse_srt(srt_input)
                if subs:
                    audio_bytes = asyncio.run(generate_synced_audio(subs, voice_id, speed_rate, pitch_val))
                    st.success("ការបំប្លែងជោគជ័យ!")
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_bytes, "synced_khmer_audio.mp3")
                else:
                    st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
            except Exception as e:
                st.error(f"កំហុស៖ {e}")
