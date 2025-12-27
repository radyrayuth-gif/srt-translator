import streamlit as st
from deep_translator import GoogleTranslator
# រៀបចំរូបរាង UI
st.set_page_config(page_title="KhmerTranslate", page_icon="🔵")
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .title-text { color: #1e3a8a; font-weight: bold; text-align: center; font-size: 28px; }
    </style>
    """, unsafe_allow_html=True)
st.markdown('<h1 class="title-text">Translate Subtitles to Khmer</h1>', unsafe_allow_html=True)
st.write("Upload your .srt file to translate from Chinese to Khmer.")
uploaded_file = st.file_uploader("", type="srt")
def translate_srt(content):
    translator = GoogleTranslator(source='zh-CN', target='km')
    lines = content.split('\n')
    translated_lines = []
    
    # បង្កើត Progress Bar
    progress_bar = st.progress(0)
    total = len(lines)
    for i, line in enumerate(lines):
        # បកប្រែតែអត្ថបទ (មិនបកលេខរៀង និង Timecode)
        if line.strip() and not line.strip().isdigit() and '-->' not in line:
            try:
                translated_text = translator.translate(line)
                translated_lines.append(translated_text)
            except:
                translated_lines.append(line)
        else:
            translated_lines.append(line)
        
        # Update progress
        progress_bar.progress((i + 1) / total)
            
    return '\n'.join(translated_lines)
if uploaded_file is not None:
    if st.button("Start Translation", type="primary"):
        with st.spinner('Translating... Please wait.'):
            raw_text = uploaded_file.read().decode("utf-8")
            result = translate_srt(raw_text)
            st.success("Done!")
            st.download_button("Download Khmer SRT", result, file_name=f"khmer_{uploaded_file.name}")
