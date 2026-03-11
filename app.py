import streamlit as st
import asyncio
import edge_tts
import srt
import io
import re
from pydub import AudioSegment
from pydub.effects import speedup

# កំណត់ការបង្ហាញទំព័រ
st.set_page_config(page_title="Khmer TTS - Sync Guaranteed", page_icon="🎙️")

# Function សម្រាប់កាត់ផ្នែកស្ងាត់នៅខាងដើម និងខាងចុងសំឡេង AI
def trim_audio_silence(audio, threshold=-50.0):
    start_trim = 0
    end_trim = 0
    # រកមើលកន្លែងដែលចាប់ផ្តើមឮសំឡេង
    while start_trim < len(audio) and audio[start_trim:start_trim+10].dBFS < threshold:
        start_trim += 10
    # រកមើលកន្លែងដែលចប់សំឡេង
    while end_trim < len(audio) and audio[len(audio)-end_trim-10:len(audio)-end_trim].dBFS < threshold:
        end_trim += 10
    return audio[start_trim:len(audio)-end_trim]

async def fetch_audio_chunk(text, voice, rate_str):
    """ផលិតសំឡេងពី Edge TTS"""
    try:
        # សម្អាតអក្សរដែលមិនមែនជាភាសាខ្មែរ/អង់គ្លេស/លេខ
        clean_text = re.sub(r'[^\u1780-\u17FF\u19E0-\u19FFa-zA-Z0-9\s\.\?\!]', '', text)
        if not clean_text.strip(): return None
        
        communicate = edge_tts.Communicate(clean_text, voice, rate=rate_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception:
        return None

async def process_sync_audio(srt_content, voice, base_speed):
    try:
        subs = list(srt.parse(srt_content))
        if not subs: return None
    except:
        st.error("ទម្រង់ SRT មិនត្រឹមត្រូវទេ!")
        return None

    rate_str = f"{base_speed:+d}%"
    
    # បង្កើតផ្ទៃសំឡេងស្ងាត់ (Canvas) តាមប្រវែង SRT សរុប
    total_duration_ms = int(subs[-1].end.total_seconds() * 1000) + 1000
    final_audio = AudioSegment.silent(duration=total_duration_ms, frame_rate=44100)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, sub in enumerate(subs):
        status_text.text(f"កំពុងផលិតសំឡេងទី {i+1}...")
        audio_data = await fetch_audio_chunk(sub.content, voice, rate_str)
        
        if audio_data:
            segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            segment = trim_audio_silence(segment) # កាត់ចន្លោះស្ងាត់

            # គណនាម៉ោងក្នុង SRT
            srt_start_ms = int(sub.start.total_seconds() * 1000)
            srt_end_ms = int(sub.end.total_seconds() * 1000)
            allowed_duration = srt_end_ms - srt_start_ms
            
            current_len = len(segment)

            # ប្រសិនបើសំឡេងវែងជាងម៉ោង SRT យើងបង្ខំពន្លឿនវា
            if current_len > allowed_duration and allowed_duration > 0:
                ratio = current_len / allowed_duration
                # ពន្លឿនឱ្យទាន់ពេល (កំណត់ត្រឹម ២ដង កុំឱ្យបែកសំឡេងពេក)
                segment = speedup(segment, playback_speed=min(ratio, 2.2), chunk_size=50, crossfade=15)
                # កាត់ផ្នែកដែលនៅសល់ (បើនៅតែលើសបន្តិចបន្តួច)
                segment = segment[:allowed_duration]

            # ដាក់សំឡេងចូលទៅក្នុង Timeline ឱ្យចំម៉ោង Start
            final_audio = final_audio.overlay(segment, position=srt_start_ms)
        
        progress_bar.progress((i + 1) / len(subs))

    status_text.text("ជោគជ័យ! សំឡេងត្រូវបានផលិតរួចរាល់។")
    
    # Export ជា MP3
    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3", bitrate="128k")
    return buffer.getvalue()

# --- Streamlit UI ---
st.title("🎙️ Khmer TTS Sync Pro")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនអានទូទៅ (%):", -50, 100, 25)

srt_input = st.text_area("សូមផាស (Paste) អត្ថបទ SRT របស់អ្នកនៅទីនេះ:", height=300, placeholder="1\n00:00:01,000 --> 00:00:03,500\nសួស្តីបងប្អូនទាំងអស់គ្នា...")

if st.button("🔊 ផលិតសំឡេង និងទាញយក"):
    if srt_input.strip():
        # ប្រើ asyncio.run សម្រាប់ដំណើរការ
        final_mp3 = asyncio.run(process_sync_audio(srt_input, voice_choice, speed))
        
        if final_mp3:
            st.audio(final_mp3, format="audio/mp3")
            st.download_button(
                label="📥 ទាញយកឯកសារ MP3",
                data=final_mp3,
                file_name="khmer_synced_audio.mp3",
                mime="audio/mp3"
            )
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")
