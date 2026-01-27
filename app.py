import streamlit as st
import asyncio
import edge_tts
import io
import re

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro", page_icon="🎙️")

# មុខងារទាញយកអត្ថបទពី SRT (សម្រួលឱ្យសាមញ្ញ)
def parse_srt(srt_text):
    # Regex ស្វែងរកតែអត្ថបទ (មិនគិតពេលវេលា ដើម្បីកុំឱ្យជួបបញ្ហា Runtime Error)
    lines = srt_text.split('\n')
    cleaned_text = []
    for line in lines:
        # បោះចោលជួរដែលមានលេខរៀង និងពេលវេលា
        if not re.match(r'^(\d+|\d{2}:\d{2}.*)$', line.strip()) and line.strip():
            cleaned_text.append(line.strip())
    return " ".join(cleaned_text)

# --- មុខងារបង្កើតសំឡេង ---
async def generate_audio(text, voice, rate, pitch):
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI ---
st.title("🎙️ កម្មវិធីអានអត្ថបទជាភាសាខ្មែរ")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch)", -20, 20, 0, 1)

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT នៅទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងបង្កើតសំឡេង..."):
            try:
                # បំប្លែង SRT ទៅជាអត្ថបទធម្មតាដើម្បីឱ្យអានបានរលូន
                pure_text = parse_srt(srt_input)
                audio_bytes = asyncio.run(generate_audio(pure_text, voice_id, speed_rate, pitch_val))
                
                st.success("សម្រេច!")
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button("📥 ទាញយក MP3", audio_bytes, "khmer_audio.mp3")
            except Exception as e:
                st.error(f"កំហុស៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
