import streamlit as st
import asyncio
import edge_tts
import re
from datetime import datetime

st.set_page_config(page_title="Khmer Stable TTS", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    """បំប្លែងពេលវេលាពី SRT ទៅជាវិនាទី"""
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)
    except:
        return 0

def parse_srt_clean(srt_text):
    """ទាញយកតែអក្សរខ្មែរសុទ្ធ និងពេលវេលា (លុបលេខរៀង និង Tag ចេញឱ្យអស់)"""
    # ស្វែងរកផ្នែកដែលមានពេលវេលា និងអត្ថបទ
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 2:
            # ស្វែងរកជួរដែលមានសញ្ញា --> (ពេលវេលា)
            time_line = ""
            text_lines = []
            for line in lines:
                if "-->" in line:
                    time_line = line
                elif not line.strip().isdigit(): # មិនយកជួរដែលមានតែលេខរៀង
                    text_lines.append(line.strip())
            
            if time_line and text_lines:
                start_time_str = time_line.split("-->")[0].strip()
                text_content = " ".join(text_lines)
                # លុប Tag HTML បើមាន (ដូចជា <i>...</i>)
                text_content = re.sub(r'<[^>]*>', '', text_content)
                
                subtitles.append({
                    "start": srt_time_to_seconds(start_time_str),
                    "text": text_content
                })
    return subtitles

async def generate_audio(subtitles, voice):
    """ប្រើ SSML បញ្ជាឱ្យ AI ផ្អាកឱ្យចំវិនាទី និងមិនអាន Tag ចេញមកក្រៅ"""
    ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"
    current_time = 0
    
    for sub in subtitles:
        wait_time = sub["start"] - current_time
        if wait_time > 0:
            ssml += f"<break time='{int(wait_time * 1000)}ms'/>"
        
        # បញ្ចូលតែអត្ថបទសុទ្ធសម្រាប់អាន
        ssml += f"{sub['text']}"
        # បន្ថែមការផ្អាកបន្តិចក្រោយចប់ឃ្លា ដើម្បីកុំឱ្យជាន់គ្នា
        current_time = sub["start"] + 0.5 
        
    ssml += "</speak>"
    
    # បង្កើតសំឡេងពី SSML ដែលបានរៀបចំរួច
    communicate = edge_tts.Communicate(ssml, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI ---
st.title("🎙️ កម្មវិធីអានខ្មែរ (Sync & Clean Version)")
voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិត"):
    if srt_input:
        subs = parse_srt_clean(srt_input)
        if subs:
            with st.spinner("កំពុងផលិតសំឡេង..."):
                try:
                    audio_bytes = asyncio.run(generate_audio(subs, voice_id))
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_bytes, "clean_sync_voice.mp3")
                except Exception as e:
                    st.error(f"កំហុស៖ {e}")
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ ឬរកមិនឃើញអត្ថបទ!")
