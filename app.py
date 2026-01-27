import streamlit as st
import asyncio
import edge_tts
from edge_tts import submaker
import os

# កំណត់ទម្រង់ទំព័រ
st.set_page_config(page_title="Khmer MP3 & SRT Generator", page_icon="🎙️")
st.title("🎙️ Khmer MP3 & SRT Generator")

# ១. បញ្ចូលអត្ថបទ
text = st.text_area("បញ្ចូលអត្ថបទខ្មែរសម្រាប់បង្កើត SRT:", height=150)

# ២. ជ្រើសរើសសំឡេង និងល្បឿន
col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសតួអង្គ:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអាន:", 0.5, 2.0, 1.0, step=0.1)

# បង្កើត Function សម្រាប់បម្លែង (ត្រូវប្រាកដថាឈ្មោះនេះត្រូវគ្នាជាមួយកន្លែងហៅប្រើ)
async def generate_assets(text_input, voice_name, rate_val):
    rate_str = f"{'+' if rate_val >= 1 else ''}{int((rate_val-1)*100)}%"
    communicate = edge_tts.Communicate(text_input, voice_name, rate=rate_str)
    
    sub_maker = submaker.SubMaker()
    audio_data = b""
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            sub_maker.feed(chunk)
            
    srt_content = sub_maker.generate_subs()
    return audio_data, srt_content

# ៣. នៅពេលចុចប៊ូតុង
if st.button("🚀 ចាប់ផ្ដើមដំណើរការ"):
    if text.strip():
        try:
            with st.spinner('កំពុងដំណើរការ... សូមរង់ចាំ'):
                # ហៅប្រើមុខងារ generate_assets
                audio_content, srt_content = asyncio.run(generate_assets(text, voice, speed))
                
                # បង្ហាញ Audio Player
                st.audio(audio_content, format='audio/mp3')
                
                # ប៊ូតុង Download
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📥 ទាញយក MP3", audio_content, "voice.mp3", "audio/mp3")
                with c2:
                    st.download_button("📄 ទាញយក SRT", srt_content, "subtitle.srt", "text/plain")
                
                st.success("រួចរាល់ជោគជ័យ!")
                st.text_area("ខ្លឹមសារ SRT ដែលបានបង្កើត:", srt_content, height=150)
        except Exception as e:
            st.error(f"បញ្ហាបច្ចេកទេស៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទជាមុនសិន!")
