import streamlit as st
import asyncio
import edge_tts
import os

st.set_page_config(page_title="Khmer SRT Generator", page_icon="🎙️")

st.title("🎙️ Khmer SRT & MP3 Generator")

# ១. បញ្ចូលអត្ថបទ
text = st.text_area("បញ្ចូលអត្ថបទខ្មែរសម្រាប់បង្កើត SRT:", height=150)

# ២. កំណត់សំឡេង និងល្បឿន
col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសតួអង្គ:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអាន:", 0.5, 2.0, 1.0, step=0.1)

async def generate_assets(text, voice_name, rate_val):
    # បំលែងល្បឿនទៅជា format (+0%, -10%, etc.)
    speed_str = f"{'+' if rate_val >= 1 else ''}{int((rate_val-1)*100)}%"
    
    communicate = edge_tts.Communicate(text, voice_name, rate=speed_str)
    submaker = edge_tts.SubMaker()
    
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            submaker.feed(chunk)
            
    return audio_data, submaker.generate_subs()

if st.button("🚀 ចាប់ផ្ដើមដំណើរការ"):
    if text.strip():
        try:
            with st.spinner('កំពុងបង្កើតឯកសារ...'):
                audio_content, srt_content = asyncio.run(generate_assets(text, voice, speed))
                
                # បង្ហាញ Audio Player
                st.audio(audio_content, format='audio/mp3')
                
                # ប៊ូតុងទាញយក
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📥 ទាញយក MP3", audio_content, "khmer_voice.mp3", "audio/mp3")
                with c2:
                    st.download_button("📄 ទាញយក SRT", srt_content, "subtitle.srt", "text/plain")
                
                st.success("រួចរាល់ ១០០%!")
                st.text_area("មើលគំរូ SRT:", srt_content, height=150)
        except Exception as e:
            st.error(f"កំហុសបច្ចេកទេស៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
