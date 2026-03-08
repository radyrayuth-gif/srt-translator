import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment
from pydub.effects import speedup

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - High Quality Sync", page_icon="🎙️")

def parse_srt(srt_text):
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000
    for match in matches:
        start = to_ms(match[1])
        end = to_ms(match[2])
        subtitles.append({
            "start_ms": start,
            "end_ms": end,
            "duration_ms": end - start,
            "text": match[3].strip()
        })
    return subtitles

async def fetch_audio_chunk(text, voice, rate_str, pitch_str):
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception:
        return None

def change_audio_speed(audio_segment, target_ms):
    """បច្ចេកទេសសម្រួលល្បឿនឱ្យស្ដាប់ទៅធម្មជាតិបំផុត (High Quality Speed Adjustment)"""
    current_duration = len(audio_segment)
    if current_duration == 0:
        return audio_segment
    
    speed_ratio = current_duration / target_ms
    
    # បើល្បឿនលឿនជាងធម្មតា (Ratio > 1.0) យើងប្រើ Speedup (កាត់ចន្លោះស្ងាត់ៗចោល)
    # វិធីនេះជួយឱ្យសំឡេងនៅតែច្បាស់ មិនញ័រ
    if speed_ratio > 1.0:
        # speedup របស់ pydub ធ្វើការបានល្អបំផុតក្នុងកម្រិតនេះ
        return speedup(audio_segment, playback_speed=speed_ratio)
    elif speed_ratio < 0.9:
        # បើសំឡេងខ្លីពេក ឱ្យវាអានធម្មតាចុះ (មិនបាច់ពន្យឺតឱ្យវែងពេកទេ នាំឱ្យស្តាប់មិនដឹងរឿង)
        return audio_segment
    
    return audio_segment

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    tasks = [fetch_audio_chunk(sub['text'], voice, rate_str, pitch_str) for sub in subs]
    audio_chunks = await asyncio.gather(*tasks)

    # បង្កើត Timeline
    max_duration = subs[-1]['end_ms'] + 5000
    final_combined = AudioSegment.silent(duration=max_duration)
    
    for i, sub in enumerate(subs):
        if audio_chunks[i]:
            segment = AudioSegment.from_file(io.BytesIO(audio_chunks[i]), format="mp3")
            
            # សម្រួលល្បឿនដោយប្រើបច្ចេកទេស Speedup
            segment_fixed = change_audio_speed(segment, sub['duration_ms'])
            
            # ដាក់ចូលតាម Start Time
            final_combined = final_combined.overlay(segment_fixed, position=sub['start_ms'])

    final_combined = final_combined[:subs[-1]['end_ms'] + 1000]
    buffer = io.BytesIO()
    final_combined.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer SRT - High Quality Sync")
st.info("💡 ជំនាន់នេះប្រើបច្ចេកទេស Speedup កាត់ចន្លោះទំនេរដើម្បីឱ្យត្រូវតាមម៉ោង SRT ដោយរក្សាសំឡេងឱ្យនៅច្បាស់។")

col1, col2 = st.columns(2)
with col1:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed = st.slider("ល្បឿនអានទូទៅ (%):", -20, 50, 0, 5)
with col2:
    pitch = st.slider("កម្រិតសំឡេង (Hz):", -10, 10, 0, 1)

srt_input = st.text_area("បញ្ចូល SRT ទីនេះ:", height=250)

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងរៀបចំសំឡេងឱ្យត្រូវតាមពេលវេលា..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_choice, speed, pitch))
                if final_audio:
                    st.audio(final_audio)
                    st.download_button("📥 ទាញយក MP3", final_audio, "clear_sync.mp3")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
