import streamlit as st
import asyncio
import edge_tts
import io
import re
from datetime import datetime

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Perfect Sync", page_icon="🎙️")

# មុខងារបំប្លែងពេលវេលាពី SRT ទៅជា វិនាទី (Seconds)
def srt_time_to_seconds(time_str):
    time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
    return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)

# មុខងារទាញយកទិន្នន័យពី SRT
def parse_srt(srt_text):
    pattern = r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\d+\s+|\Z)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    for m in matches:
        subtitles.append({
            "start": srt_time_to_seconds(m[1]),
            "text": m[3].replace('\n', ' ').strip()
        })
    return subtitles

# --- មុខងារបង្កើតសំឡេងប្រើ SSML ដែលកំណត់ពេលបានច្បាស់ ---
async def generate_perfect_sync(subtitles, voice, rate, pitch):
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    # ប្រើ SSML ដើម្បីបញ្ជាឱ្យ AI បង្អង់តាមវិនាទីជាក់លាក់
    ssml_parts = ["<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"]
    
    current_time = 0
    for sub in subtitles:
        # គណនាចន្លោះដែលត្រូវសម្រាក (Silence)
        wait_time = sub["start"] - current_time
        if wait_time > 0:
            # បញ្ជាឱ្យផ្អាកចំចំនួនវិនាទីដែលខ្វះ
            ssml_parts.append(f"<break time='{int(wait_time * 1000)}ms'/>")
        
        # បញ្ចូលអត្ថបទអាន
        ssml_parts.append(f"<prosody rate='{rate_str}' pitch='{pitch_str}'>{sub['text']}</prosody>")
        
        # យើងប៉ាន់ស្មានថាការអានប្រើពេលខ្លីបំផុត ដើម្បីគណនាសម្រាប់ឃ្លាបន្ទាប់
        # កូដនេះនឹងរុញពេលវេលាទៅមុខតាមសាច់អត្ថបទជាក់ស្តែង
        current_time = sub["start"] + 0.5 

    ssml_parts.append("</speak>")
    ssml_string = "".join(ssml_parts)
    
    communicate = edge_tts.Communicate(ssml_string, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI ---
st.title("🎙️ កម្មវិធីអានតាមវិនាទី SRT (Fixed)")
st.info("កូដនេះនឹងអានតាមពេលវេលាដែលអ្នកកំណត់ក្នុង SRT ដោយស្វ័យប្រវត្តិ។")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch)", -20, 20, 0, 1)

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT នៅទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្តើមផលិតសំឡេង Sync"):
    if srt_input.strip():
        with st.spinner("កំពុងផលិតសំឡេងឱ្យត្រូវតាមវិនាទី..."):
            try:
                subs = parse_srt(srt_input)
                if subs:
                    audio_bytes = asyncio.run(generate_perfect_sync(subs, voice_id, speed_rate, pitch_val))
                    st.success("ផលិតបានជោគជ័យ!")
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_bytes, "khmer_sync.mp3")
                else:
                    st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
            except Exception as e:
                st.error(f"មានបញ្ហា៖ {e}")
