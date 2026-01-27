import streamlit as st
from gtts import gTTS
import asyncio
import edge_tts
from edge_tts import submaker
import io

st.set_page_config(page_title="Khmer Multi-TTS", layout="centered")
st.title("🎙️ កម្មវិធីបម្លែងសំឡេងខ្មែរ (Standard & Backup)")

# ១. បញ្ចូលអត្ថបទ
text = st.text_area("បញ្ចូលអត្ថបទរបស់អ្នក៖", height=150)

# ២. ជ្រើសរើសម៉ាស៊ីនសំឡេង
engine = st.radio("ជ្រើសរើសបច្ចេកវិទ្យាសំឡេង៖", ("Edge-TTS (ពិរោះខ្លាំង ប៉ុន្តែជួនកាល Error 403)", "Google-TTS (ដើររហូត ១០០%)"))

col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសតួអង្គ (សម្រាប់ Edge):", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអាន៖", 0.5, 2.0, 1.0, step=0.1)

async def generate_edge(text_input, voice_name, rate_val):
    rate_str = f"{'+' if rate_val >= 1.0 else ''}{int((rate_val - 1) * 100)}%"
    communicate = edge_tts.Communicate(text_input, voice_name, rate=rate_str)
    sub_maker = submaker.SubMaker()
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            sub_maker.feed(chunk)
    return audio_data, sub_maker.generate_subs()

if st.button("🚀 ចាប់ផ្ដើមដំណើរការ"):
    if text.strip():
        try:
            with st.spinner('កំពុងផលិតសំឡេង...'):
                if engine == "Edge-TTS (ពិរោះខ្លាំង ប៉ុន្តែជួនកាល Error 403)":
                    audio_content, srt_content = asyncio.run(generate_edge(text, voice, speed))
                    st.audio(audio_content, format='audio/mp3')
                    st.download_button("📥 ទាញយក MP3", audio_content, "edge_voice.mp3")
                    st.download_button("📄 ទាញយក SRT", srt_content, "subtitle.srt")
                else:
                    # បច្ចេកវិទ្យា Google (Backup)
                    tts = gTTS(text=text, lang='km', slow=(speed < 1.0))
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp.getvalue(), format='audio/mp3')
                    st.download_button("📥 ទាញយក MP3 (Google)", fp.getvalue(), "google_voice.mp3")
                    st.info("ចំណាំ៖ Google TTS មិនគាំទ្រការបង្កើត SRT តាមរយៈកូដសាមញ្ញនេះទេ។")
                
                st.success("រួចរាល់!")
        except Exception as e:
            st.error(f"កំហុស៖ {e}")
            st.warning("ដំបូន្មាន៖ បើ Edge-TTS ជាប់ Error 403 សូមប្តូរទៅប្រើ Google-TTS វិញ។")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
