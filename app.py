import streamlit as st
import asyncio
import edge_tts
import io

st.set_page_config(page_title="Khmer TTS Final", page_icon="🎙️")

async def text_to_speech(text, voice):
    # បង្កើតសំឡេងដោយផ្ទាល់ពីអត្ថបទ (មិនបាច់មាន Regex ស្មុគស្មាញ)
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ កម្មវិធីអានខ្មែរ (Safe Mode)")

voice_id = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
text_input = st.text_area("បញ្ចូលអត្ថបទរបស់អ្នកនៅទីនេះ (អាចជា SRT ឬអត្ថបទធម្មតា):", height=200)

if st.button("🚀 ចាប់ផ្ដើមផលិត"):
    if text_input:
        try:
            # លុបលេខ និង Tag ចេញតាមវិធីសាមញ្ញបំផុត
            clean_text = "".join([line for line in text_input.splitlines() if "-->" not in line and not line.strip().isdigit()])
            
            with st.spinner("កំពុងដំណើរការ..."):
                audio_bytes = asyncio.run(text_to_speech(clean_text, voice_id))
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button("📥 ទាញយក", audio_bytes, "voice.mp3")
        except Exception as e:
            st.error(f"កំហុស៖ {e}")
