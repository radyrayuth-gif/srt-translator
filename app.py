import streamlit as st
import whisper
import os
import google.generativeai as genai
import time

# កំណត់ទម្រង់ទំព័រវេបសាយ
st.set_page_config(page_title="បកប្រែវីដេអូជាមួយ Gemini AI", page_icon="🇰🇭")

# --- ផ្នែក Sidebar សម្រាប់បញ្ចូល API Key ---
with st.sidebar:
    st.title("⚙️ ការកំណត់")
    gemini_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក៖", type="password")
    st.info("យក Key នៅទីនេះ៖ [Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.markdown("---")
    st.write("ជំនាន់៖ AI Translator v2.0")

st.title("🇰🇭 កម្មវិធីបកប្រែវីដេអូចិន-ខ្មែរ (Gemini AI)")
st.markdown("---")

# ១. មុខងារបកប្រែដោយប្រើ Gemini 1.5 Flash (កែសម្រួលដោះស្រាយ Error 404)
def translate_with_gemini(text, api_key):
    if not api_key:
        return "សូមបញ្ចូល API Key"
    
    try:
        genai.configure(api_key=api_key)
        # ប្រើ 'gemini-1.5-flash' ឬ 'gemini-1.5-flash-latest'
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a professional Chinese-to-Khmer translator. 
        Translate the following Chinese subtitle text into natural, conversational, and smooth Khmer language.
        Maintain the original emotion and context.
        Text: {text}
        """
        
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "ការបកប្រែមិនអាចធ្វើទៅបាន"
            
    except Exception as e:
        return f"Error: {str(e)}"

# ២. មុខងារបង្កើតឯកសារ SRT
def create_srt(segments, api_key):
    srt_content = ""
    progress_text = "កំពុងបកប្រែឃ្លានីមួយៗ..."
    my_bar = st.progress(0, text=progress_text)
    total = len(segments)
    
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # បកប្រែដោយប្រើ Gemini
        translated = translate_with_gemini(text, api_key)
        
        # ទម្រង់ពេលវេលា SRT (00:00:00,000)
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated}\n\n"
        
        # បង្ហាញ Progress
        pct = (i + 1) / total
        my_bar.progress(pct, text=f"បកប្រែបាន {int(pct*100)}%")
        
        # បន្ថែម Delay បន្តិចដើម្បីកុំឱ្យលើស Limit របស់ Free API
        time.sleep(0.5) 
        
    return srt_content

# ៣. Load Model Whisper (បម្លែងសំឡេងជាអក្សរ)
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

whisper_model = load_whisper()

# ៤. ផ្នែក Upload វីដេអូ
uploaded_file = st.file_uploader("បង្ហោះវីដេអូចិនរបស់អ្នក (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 ចាប់ផ្ដើមបកប្រែដោយ AI"):
        if not gemini_key:
            st.warning("⚠️ សូមបញ្ចូល Gemini API Key ក្នុង Sidebar ជាមុនសិន!")
        else:
            with st.spinner('កំពុងដំណើរការ... អាចប្រើពេលយូរតាមទំហំវីដេអូ'):
                # រក្សាទុកវីដេអូបណ្ដោះអាសន្ន
                video_path = os.path.join(os.getcwd(), "temp_video.mp4")
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # ជំហានទី ១៖ ស្ដាប់សំឡេងបម្លែងជាអក្សរ
                    st.info("🔄 ជំហានទី ១៖ កំពុងបម្លែងសំឡេងជាអក្សរ (Transcription)...")
                    result = whisper_model.transcribe(video_path, fp16=False)
                    
                    # ជំហានទី ២៖ បកប្រែ និងបង្កើត SRT
                    st.info("🔄 ជំហានទី ២៖ Gemini AI កំពុងបកប្រែជាភាសាខ្មែរ...")
                    srt_data = create_srt(result['segments'], gemini_key)
                    
                    # បង្ហាញលទ្ធផលជោគជ័យ
                    st.success("✅ ការបកប្រែជោគជ័យ!")
                    
                    st.download_button(
                        label="📥 ទាញយកឯកសារ Subtitle ខ្មែរ (.srt)",
                        data=srt_data,
                        file_name="subtitles_khmer.srt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"កើតមានបញ្ហា៖ {e}")
                
                finally:
                    # លុបឯកសារវីដេអូចោលវិញ
                    if os.path.exists(video_path):
                        os.remove(video_path)

st.markdown("---")
st.caption("ចំណាំ៖ ការបកប្រែប្រើប្រាស់ Gemini 1.5 Flash ដើម្បីធានានូវអត្ថន័យសមស្របតាមបរិបទខ្មែរ។")
