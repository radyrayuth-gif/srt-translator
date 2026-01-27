import streamlit as st
import asyncio
import edge_tts
import io
import re
from pydub import AudioSegment
from datetime import datetime

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro", page_icon="🎙️")

# មុខងារបំប្លែងពេលវេលាពី SRT ទៅជា ms
def srt_time_to_ms(time_str):
    time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
    return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)

# មុខងារទាញយកអត្ថបទពី SRT
def parse_srt(srt_text):
    pattern = r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\d+\s+|\Z)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    for m in matches:
        subtitles.append({
            "start": srt_time_to_ms(m[1]),
            "text": m[3].strip()
        })
    return subtitles

# --- មុខងារបង្កើតសំឡេង ---
async def generate_srt_audio(subtitles, voice, rate, pitch):
    combined_audio = AudioSegment.silent(duration=0)
    current_time = 0

    # បន្ថែម Rate និង Pitch ទៅក្នុងទម្រង់ edge-tts (+10%, -5%, etc.)
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    progress_bar = st.progress(0)
    for i, sub in enumerate(subtitles):
        # បង្កើតសំឡេងដោយមានកំណត់ល្បឿន
        communicate = edge_tts.Communicate(sub["text"], voice, rate=rate_str, pitch=pitch_str)
        temp_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                temp_buffer.write(chunk["data"])
        
        temp_buffer.seek(0)
        segment = AudioSegment.from_file(temp_buffer, format="mp3")

        # គណនាចន្លោះស្ងាត់
        wait_time = sub["start"] - current_time
        if wait_time > 0:
            combined_audio += AudioSegment.silent(duration=wait_time)
        
        combined_audio += segment
        current_time = sub["start"] + len(segment)
        progress_bar.progress((i + 1) / len(subtitles))

    out_buffer = io.BytesIO()
    combined_audio.export(out_buffer, format="mp3")
    return out_buffer.getvalue()

# --- UI Layout ---
st.title("🎙️ កម្មវិធីអាន SRT កម្រិតខ្ពស់")

with st.sidebar:
    st.header("⚙️ ការកំណត់សំឡេង")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    
    # បន្ថែម Slider សម្រាប់ល្បឿន
    speed_rate = st.slider("ល្បឿនអាន (%)", min_value=-50, max_value=50, value=0, step=5)
    pitch_val = st.slider("កម្រិតសំឡេង Pitch (Hz)", min_value=-20, max_value=20, value=0, step=1)
    
    st.info("💡 ល្បឿន (+) លឿន, (-) យឺត")

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT នៅទីនេះ:", height=250, placeholder="1\n00:00:01,000 --> 00:00:02,000\nសួស្តី...")

if st.button("🚀 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input.strip():
        try:
            subs = parse_srt(srt_input)
            if subs:
                with st.spinner("កំពុងបំប្លែង..."):
                    audio_data = asyncio.run(generate_srt_audio(subs, voice_id, speed_rate, pitch_val))
                    st.success("សម្រេច! អ្នកអាចស្តាប់ និងទាញយកខាងក្រោម៖")
                    st.audio(audio_data, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_data, "khmer_subtitle_audio.mp3")
        except Exception as e:
            st.error(f"កំហុសបច្ចេកទេស៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទជាមុនសិន!")
