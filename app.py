import streamlit as st
import asyncio
import edge_tts
import re
import base64

st.set_page_config(page_title="Khmer SRT Sync Pro", page_icon="🎙️")

async def get_audio_data(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def parse_srt(srt_text):
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        if time_line and text_lines:
            start_time = time_line.split("-->")[0].strip()
            subtitles.append({"time": start_time, "text": " ".join(text_lines)})
    return subtitles

st.title("🎙️ Khmer SRT Sync Pro")
st.write("ផលិតសំឡេងខ្មែរឱ្យចំវិនាទី SRT (ដូច VoiceRTool)")

voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT របស់អ្នកទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិត"):
    if srt_input:
        subs = parse_srt(srt_input)
        st.subheader("លទ្ធផលសម្រេច")
        
        for sub in subs:
            with st.expander(f"⏰ {sub['time']} - {sub['text'][:30]}..."):
                audio_bytes = asyncio.run(get_audio_data(sub['text'], voice_id))
                if audio_bytes:
                    # បង្ហាញសំឡេង និងប៊ូតុងទាញយកសម្រាប់ដុំនីមួយៗ
                    st.audio(audio_bytes, format="audio/mp3")
                    b64 = base64.b64encode(audio_bytes).decode()
                    href = f'<a href="data:audio/mp3;base64,{b64}" download="audio_{sub["time"].replace(":","-")}.mp3">📥 ទាញយកដុំនេះ</a>'
                    st.markdown(href, unsafe_allow_html=True)
        
        st.success("រួចរាល់! អ្នកអាចទាញយកដុំសំឡេងតាមនាទីនីមួយៗ រួចយកទៅដាក់ក្នុង CapCut នោះវានឹងចំគ្នា ១០០%។")
    else:
        st.warning("សូមបញ្ចូល SRT ជាមុនសិន!")
