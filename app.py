import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - Time Sync", page_icon="🎙️")

def parse_srt(srt_text):
    """បំប្លែង SRT ទៅជាបញ្ជីទិន្នន័យ (Start, End, Text, Duration)"""
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
    """ទាញយកសំឡេងពី Microsoft Edge TTS"""
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception:
        return None

def match_target_duration(audio_segment, target_ms):
    """បច្ចេកទេសពន្លឿន ឬបន្ថយសំឡេងឱ្យត្រូវនឹងម៉ោងក្នុង SRT"""
    current_duration = len(audio_segment)
    if current_duration == 0:
        return audio_segment
    
    # គណនាផលធៀបល្បឿន (Speed Ratio)
    speed_ratio = current_duration / target_ms
    
    # បង្កើន ឬបន្ថយល្បឿន (ប្រើ frame_rate ដើម្បីកុំឱ្យប្តូរ Pitch សំឡេង)
    # វិធីនេះហៅថា Time Stretching
    new_segment = audio_segment._spawn(audio_segment.raw_data, overrides={
        "frame_rate": int(audio_segment.frame_rate * speed_ratio)
    })
    return new_segment.set_frame_rate(audio_segment.frame_rate)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    # ១. ទាញយកសំឡេង
    tasks = [fetch_audio_chunk(sub['text'], voice, rate_str, pitch_str) for sub in subs]
    audio_chunks = await asyncio.gather(*tasks)

    # ២. បង្កើត Timeline (កំណត់ប្រវែងតាម SRT ចុងក្រោយ)
    max_duration = subs[-1]['end_ms'] + 2000
    final_combined = AudioSegment.silent(duration=max_duration)
    
    for i, sub in enumerate(subs):
        if audio_chunks[i]:
            segment = AudioSegment.from_file(io.BytesIO(audio_chunks[i]), format="mp3")
            
            # --- ផ្នែកសំខាន់៖ បង្ខំឱ្យសំឡេងត្រូវនឹងរយៈពេល SRT ---
            target_duration = sub['duration_ms']
            # បន្ថែមការឆែក៖ បើសំឡេងវែងជាងម៉ោង SRT ទើបយើងពន្លឿន
            # (ឬបើចង់ឱ្យត្រូវដាច់ខាត ទោះខ្លីក៏ពន្យឺត គឺប្រើ match_target_duration តែម្តង)
            segment_fixed = match_target_duration(segment, target_duration)
            
            # ដាក់ចូលតាម Start Time ច្បាស់លាស់
            final_combined = final_combined.overlay(segment_fixed, position=sub['start_ms'])

    # កាត់ត្រឹមម៉ោងបញ្ចប់ពិតប្រាកដ
    final_combined = final_combined[:subs[-1]['end_ms'] + 500]

    buffer = io.BytesIO()
    final_combined.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer SRT - Perfect Time Sync")
st.warning("⚠️ ប្រយ័ត្ន៖ បើអត្ថបទវែងពេក ហើយម៉ោងក្នុង SRT ខ្លីពេក សំឡេង AI នឹងអានលឿនខ្លាំងស្តាប់មិនទាន់។")

col1, col2 = st.columns(2)
with col1:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed = st.slider("ល្បឿនមូលដ្ឋាន (%):", -50, 50, 0, 5)
with col2:
    pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)

srt_input = st.text_area("បញ្ចូល SRT ទីនេះ:", height=250)

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងគណនា និងសម្រួលល្បឿនឱ្យត្រូវនឹងម៉ោង..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_choice, speed, pitch))
                if final_audio:
                    st.audio(final_audio)
                    st.download_button("📥 ទាញយក MP3", final_audio, "time_synced_khmer.mp3")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
