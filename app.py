import streamlit as st
import asyncio
import edge_tts

st.title("🎙️ កម្មវិធីបំប្លែងអត្ថបទទៅជាសំឡេង")

# កន្លែងដាក់អត្ថបទ
text_input = st.text_area("បិទភ្ជាប់អត្ថបទរបស់អ្នកនៅទីនេះ (អាចជា SRT ឬអត្ថបទធម្មតា):", height=300)

async def convert_text(text):
    # ជ្រើសរើសសំឡេងស្រី
    communicate = edge_tts.Communicate(text, "km-KH-SreymomNeural")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

if st.button("🔊 បំប្លែងជាសំឡេង"):
    if text_input:
        # លុបលេខ និងម៉ោងចេញ (ទុកតែអត្ថបទខ្មែរ)
        clean_text = ""
        for line in text_input.split('\n'):
            if "-->" not in line and not line.strip().isdigit():
                clean_text += line + " "
        
        with st.spinner("កំពុងផលិតសំឡេង..."):
            audio_bytes = asyncio.run(convert_text(clean_text))
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button("📥 ទាញយកឯកសារសំឡេង", audio_bytes, file_name="voice.mp3")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
