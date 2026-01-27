import streamlit as st
import asyncio
import edge_tts
import io
import re

st.set_page_config(page_title="Khmer Stable TTS", page_icon="🎙️")

def parse_srt_to_text_list(srt_text):
    """ច្រោះយកតែអក្សរខ្មែរសុទ្ធ មិនយកលេខរៀង និងមិនយកពេលវេលា"""
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    clean_texts = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        text_lines = []
        for line in lines:
            # លក្ខខណ្ឌ៖ មិនយកជួរដែលមានសញ្ញា --> និងមិនយកជួរដែលមានតែលេខ
            if "-->" not in line and not line.strip().isdigit():
                # លុប Tag HTML ចេញ (ដូចជា <i>, </b>)
                clean_line = re.sub(r'<[^>]*>', '', line.strip())
                if clean_line:
                    text_lines.append(clean_line)
        
        if text_lines:
            clean_texts.append(" ".join(text_lines))
    return clean_texts

async def generate_final_audio(texts, voice):
    """បំប្លែងអត្ថបទម្ដងមួយឃ្លា រួចតភ្ជាប់គ្នាជា Bytes ផ្ទាល់"""
    final_audio = b""
    progress_bar = st.progress(0)
    
    for i, text in enumerate(texts):
        # ផ្ញើតែអត្ថបទខ្មែរសុទ្ធទៅឱ្យ AI (គ្មានលេខ គ្មានម៉ោង)
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                final_audio += chunk["data"]
        
        # បន្ថែមចន្លោះស្ងាត់បន្តិចរវាងឃ្លានីមួយៗ (Optional)
        # ចំណាំ៖ ការតភ្ជាប់ Bytes បែបនេះនឹងអានបន្តគ្នា ប៉ុន្តែធានាមិនអានលេខ និងម៉ោង
        progress_bar.progress((i + 1) / len(texts))
        
    return final_audio

st.title("🎙️ កម្មវិធីអានខ្មែរសុទ្ធ (មិនអានម៉ោងនាទី)")

voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT របស់អ្នកនៅទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិតសំឡេង"):
    if srt_input:
        with st.spinner("កំពុងច្រោះអត្ថបទ និងផលិតសំឡេង..."):
            try:
                # ជំហានទី១៖ ច្រោះយកតែអក្សរខ្មែរ
                texts_to_read = parse_srt_to_text_list(srt_input)
                
                if texts_to_read:
                    # ជំហានទី២៖ ផលិតសំឡេង
                    audio_data = asyncio.run(generate_final_audio(texts_to_read, voice_id))
                    
                    st.success("ផលិតជោគជ័យ! សំឡេងនេះនឹងអានតែអក្សរខ្មែរប៉ុណ្ណោះ។")
                    st.audio(audio_data, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_data, "khmer_clean_voice.mp3")
                else:
                    st.error("រកមិនឃើញអត្ថបទខ្មែរក្នុង SRT របស់អ្នកទេ!")
            except Exception as e:
                st.error(f"កំហុស៖ {e}")
