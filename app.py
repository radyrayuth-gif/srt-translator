import streamlit as st
import asyncio
import edge_tts
from edge_tts import submaker
import io

st.set_page_config(page_title="Khmer Sync TTS & SRT", layout="centered")
st.title("🎙️ កម្មវិធីបម្លែងសំឡេងខ្មែរ (ត្រូវតាមពេលវេលា)")

text = st.text_area("បញ្ចូលអត្ថបទខ្មែរ៖", height=150)

col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសតួអង្គ៖", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអាន៖", 0.5, 2.0, 1.0, step=0.1)

async def generate_sync_assets(text_input, voice_name, rate_val):
    # កែសម្រួល format ល្បឿនឱ្យត្រូវតាម API
    rate_str = f"{'+' if rate_val >= 1.0 else ''}{int((rate_val - 1) * 100)}%"
    
    communicate = edge_tts.Communicate(text_input, voice_name, rate=rate_str)
    # ប្រើ SubMaker ដើម្បីចាប់យកពេលវេលាពិតប្រាកដ (Offset)
    sub_maker = submaker.SubMaker()
    audio_data = b""
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            # នេះគឺជាចំណុចសំខាន់ដែលធ្វើឱ្យ SRT និងសំឡេងដើរត្រូវគ្នា
            sub_maker.feed(chunk)
            
    # បង្កើត SRT ដែលប្រើប្រាស់ពេលវេលាពិតពី WordBoundary
    srt_content = sub_maker.generate_subs()
    return audio_data, srt_content

if st.button("🚀 ចាប់ផ្ដើមដំណើរការ"):
    if text.strip():
        try:
            with st.spinner('កំពុងផលិតសំឡេង និង SRT...'):
                audio_content, srt_content = asyncio.run(generate_sync_assets(text, voice, speed))
                
                # បង្ហាញ Audio Player
                st.audio(audio_content, format='audio/mp3')
                
                # ប៊ូតុងទាញយក
                col_a, col_b = st.columns(2)
                with col_a:
                    st.download_button("📥 ទាញយក MP3", audio_content, "audio_sync.mp3")
                with col_b:
                    st.download_button("📄 ទាញយក SRT", srt_content, "subtitle_sync.srt")
                
                st.success("រួចរាល់! ឥឡូវនេះ SRT នឹងដើរត្រូវតាមសំឡេង។")
                st.text_area("ពិនិត្យមើលពេលវេលាក្នុង SRT:", srt_content, height=150)
                
        except Exception as e:
            if "403" in str(e):
                st.error("Error 403: Cloud រវល់ពេក។ សូមរង់ចាំ ៥ វិនាទី រួចចុចម្ដងទៀត។")
            else:
                st.error(f"បញ្ហា៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
