import streamlit as st
import asyncio
import edge_tts
import io
import re
from pydub import AudioSegment
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync", page_icon="🎙️")

def srt_time_to_ms(time_str):
    """បំប្លែងពេលវេលាពី SRT ទៅជា Milliseconds"""
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)
    except:
        return 0

def parse_srt_clean(srt_text):
    """ច្រោះយកតែអត្ថបទខ្មែរ និងពេលវេលាចាប់ផ្ដើម"""
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = ""
        text_lines = []
        for line in lines:
            if "-->" in line:
                time_line = line
            elif not line.strip().isdigit():
                # លុប Tag ផ្សេងៗចេញឱ្យអស់
                clean_line = re.sub(r'<[^>]*>', '', line.strip())
                if clean_line:
                    text_lines.append(clean_line)
        
        if time_line and text_lines:
            start_time_str = time_line.split("-->")[0].strip()
            subtitles.append({
                "start_ms": srt_time_to_ms(start_time_str),
                "text": " ".join(text_lines)
            })
    return subtitles

async def get_voice_bytes(text, voice):
    """ផលិតសំឡេងជា Bytes ពី edge-tts"""
    communicate = edge_tts.Communicate(text, voice)
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

def process_full_audio(subs, voice):
    """បញ្ជូលសំឡេងតាមវិនាទីដោយប្រើ pydub (Overlay)"""
    # បង្កើតសំឡេងទទេជាមូលដ្ឋាន
    combined = AudioSegment.silent(duration=0)
    
    # បង្កើត Event Loop ថ្មីសម្រាប់ asyncio ក្នុង Streamlit
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for sub in subs:
        # ១. ទាញយកសំឡេងអាន (អានតែអក្សរខ្មែរ)
        audio_data = loop.run_until_complete(get_voice_bytes(sub["text"], voice))
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ២. បង្កើនប្រវែង Audio មូលដ្ឋានប្រសិនបើចាំបាច់
        if len(combined) < sub["start_ms"]:
            padding = sub["start_ms"] - len(combined)
            combined += AudioSegment.silent(duration=padding)
        
        # ៣. ដាក់សំឡេងអាន "ជាន់លើ" (Overlay) ចំវិនាទីចាប់ផ្ដើម
        combined = combined.overlay(segment, position=sub["start_ms"])
        
        # ប្រសិនបើសំឡេងអានវែងជាង ប្រវែងសរុបត្រូវអូសតាម
        if len(combined) < sub["start_ms"] + len(segment):
            extra_silence = (sub["start_ms"] + len(segment)) - len(combined)
            combined += AudioSegment.silent(duration=extra_silence)
            
    return combined

# --- UI ---
st.title("🎙️ Khmer TTS: Perfect Timing Sync")
st.write("អានត្រូវតាមវិនាទី និងមិនអានលេខ/ម៉ោងនាទីឡើយ។")

voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង Sync"):
    if srt_input:
        subs = parse_srt_clean(srt_input)
        if subs:
            with st.spinner("កំពុងផលិត... (អាចប្រើពេលបន្តិចតាមចំនួនអត្ថបទ)"):
                try:
                    final_segment = process_full_audio(subs, voice_id)
                    out_buf = io.BytesIO()
                    final_segment.export(out_buf, format="mp3")
                    
                    st.success("ផលិតរួចរាល់!")
                    st.audio(out_buf.getvalue(), format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", out_buf.getvalue(), "khmer_sync_fixed.mp3")
                except Exception as e:
                    st.error(f"កំហុសបច្ចេកទេស៖ {e}")
        else:
            st.error("រកមិនឃើញអត្ថបទក្នុង SRT ទេ!")

