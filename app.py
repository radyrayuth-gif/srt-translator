import streamlit as st
import asyncio
import edge_tts
import io
import re

st.set_page_config(page_title="Khmer TTS Stable", page_icon="🎙️")

def parse_srt(srt_text):
    # Regex នេះនឹងយកតែអត្ថបទ មិនយកលេខរៀង 1, 2, 3 មកអានទេ
    pattern = r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\s+(.*?)(?=\n\d+|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    return [m.strip() for m in matches if m.strip()]

async def generate_audio(texts, voice):
    combined_audio = b""
    for text in texts:
        # បង្កើតសំឡេងម្ដងមួយឃ្លា រួចបូកបញ្ចូលគ្នាជា Bytes
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                combined_audio += chunk["data"]
    return combined_audio

st.title("🎙️ កម្មវិធីអានខ្មែរ (ជំនាន់គ្មាន Error)")

voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT របស់អ្នកនៅទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិត"):
    if srt_input:
        try:
            texts = parse_srt(srt_input)
            if texts:
                with st.spinner("កំពុងផលិត..."):
                    audio_data = asyncio.run(generate_audio(texts, voice_id))
                    st.audio(audio_data, format="audio/mp3")
                    st.download_button("📥 ទាញយក", audio_data, "khmer_voice.mp3")
            else:
                st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
        except Exception as e:
            st.error(f"កំហុស៖ {e}")
