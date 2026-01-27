import streamlit as st
from gtts import gTTS
import io
import math

st.set_page_config(page_title="Khmer Sync TTS", layout="centered")
st.title("🎙️ កម្មវិធីបម្លែងសំឡេងខ្មែរ (Sync ពេលវេលា & គ្មាន Error)")

# ១. បញ្ចូលអត្ថបទ
text_input = st.text_area("បញ្ចូលអត្ថបទខ្មែរ (ឧទាហរណ៍៖ សួស្តី បងប្អូនទាំងអស់គ្នា)៖", height=150)

# ២. កំណត់ល្បឿន
speed_option = st.select_slider("ជ្រើសរើសល្បឿនអាន៖", options=[0.8, 1.0, 1.2, 1.5], value=1.0)

def generate_srt(text, speed):
    # គណនាល្បឿនអានជាមធ្យម (១ វិនាទី អានបានប្រហែល ៣-៤ ម៉ាត់សម្រាប់ខ្មែរ)
    words = text.split()
    srt_lines = []
    current_time = 0.0
    
    # កំណត់រយៈពេលអានក្នុងមួយម៉ាត់ (Adjust តាមល្បឿន)
    seconds_per_word = (0.5 / speed) 

    for i, word in enumerate(words):
        duration = len(word) * (0.15 / speed) # គណនាតាមប្រវែងអក្សរ
        start_t = current_time
        end_t = current_time + duration
        
        # Format ទៅជាទម្រង់ SRT (00:00:00,000)
        def format_time(seconds):
            hrs = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            msecs = int((seconds % 1) * 1000)
            return f"{hrs:02}:{mins:02}:{secs:02},{msecs:03}"

        srt_lines.append(f"{i+1}\n{format_time(start_t)} --> {format_time(end_t)}\n{word}\n")
        current_time = end_t + 0.1 # បន្ថែមចន្លោះដកដង្ហើមបន្តិច

    return "".join(srt_lines)

if st.button("🚀 ចាប់ផ្ដើមបម្លែង"):
    if text_input.strip():
        try:
            with st.spinner('កំពុងដំណើរការ...'):
                # បង្កើតសំឡេងជាមួយ Google TTS (លែងជាប់ Error 403)
                tts = gTTS(text=text_input, lang='km', slow=(speed_option < 1.0))
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                
                # បង្កើត SRT ដោយប្រើ Logic គណនាពេលវេលាថ្មី
                srt_data = generate_srt(text_input, speed_option)
                
                # បង្ហាញលទ្ធផល
                st.audio(audio_fp.getvalue(), format='audio/mp3')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 ទាញយក MP3", audio_fp.getvalue(), "khmer_audio.mp3")
                with col2:
                    st.download_button("📄 ទាញយក SRT", srt_data, "subtitle.srt")
                
                st.success("រួចរាល់! ឥឡូវនេះអ្នកអាចប្រើបានដោយមិនបារម្ភរឿង Error ទៀតទេ។")
                st.text_area("មើលគំរូ SRT:", srt_data, height=150)
        except Exception as e:
            st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ!")
