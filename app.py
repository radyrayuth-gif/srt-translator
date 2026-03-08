import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - លោកពូប៉ាវ", page_icon="🎙️")

def parse_srt(srt_text):
    # កែសម្រួល Regex ឱ្យកាន់តែច្បាស់លាស់
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000
    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "text": match[3].strip()
        })
    return subtitles

async def fetch_audio_chunk(text, voice, rate_str, pitch_str):
    """មុខងារជំនួយសម្រាប់ទាញយកសំឡេងម្ដងមួយដុំៗ"""
    communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs:
        return None
        
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    # ១. ទាញយកសំឡេងទាំងអស់ក្នុងពេលតែមួយ (Turbo Mode)
    tasks = [fetch_audio_chunk(sub['text'], voice, rate_str, pitch_str) for sub in subs]
    audio_chunks = await asyncio.gather(*tasks)
    
    # ២. បង្កើត Timeline ឱ្យវែងល្មម (Buffer 10 វិនាទីបន្ថែម)
    max_duration = subs[-1]['start_ms'] + 10000 
    final_combined = AudioSegment.silent(duration=max_duration)
    
    last_end_point = 0
    for i, sub in enumerate(subs):
        segment = AudioSegment.from_file(io.BytesIO(audio_chunks[i]), format="mp3")
        # ដាក់សំឡេងចូលក្នុង Timeline តាមម៉ោង Start Time
        final_combined = final_combined.overlay(segment, position=sub['start_ms'])
        
        # រក្សាទុកម៉ោងដែលសំឡេងចុងក្រោយបញ្ចប់
        current_end = sub['start_ms'] + len(segment)
        if current_end > last_end_point:
            last_end_point = current_end

    # ៣. កាត់ផ្នែក Silence ដែលនៅសល់ខាងចុងចោល
    final_combined = final_combined[:last_end_point + 500]

    buffer = io.BytesIO()
    final_combined.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer SRT Audio Sync")
st.info("ជំនាន់កែសម្រួល៖ ដំណើរការលឿនជាងមុន និងស៊ីម៉ោងច្បាស់លាស់")

col1, col2 = st.columns(2)
with col1:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed = st.slider("ល្បឿន (%):", -50, 50, 0, 5)
with col2:
    pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)

srt_input = st.text_area("បញ្ចូល SRT របស់អ្នកនៅទីនេះ:", height=300, placeholder="1\n00:00:01,000 --> 00:00:03,000\nសួស្ដីបងប្អូនទាំងអស់គ្នា...")

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងដំណើរការ... សូមរង់ចាំមួយភ្លែត"):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_choice, speed, pitch))
                if final_audio:
                    st.audio(final_audio)
                    st.download_button("📥 ទាញយក MP3", final_audio, "khmer_audio_sync.mp3")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")
