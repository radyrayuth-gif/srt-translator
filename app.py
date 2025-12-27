import streamlit as st
from googletrans import Translator
# រៀបចំរូបរាង UI ឱ្យដូចគំរូរបស់អ្នក
st.set_page_config(page_title="KhmerTranslate", page_icon="🔵")
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .title-text { color: #1e3a8a; font-weight: bold; text-align: center; font-size: 28px; }
    .upload-box { border: 2px dashed #60a5fa; border-radius: 15px; padding: 20px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)
st.markdown('<h1 class="title-text">Translate Subtitles to Khmer</h1>', unsafe_allow_html=True)
st.write("Upload your .srt file. We'll preserve the exact timecodes while AI handles the translation.")
uploaded_file = st.file_uploader("", type="srt")
if uploaded_file is not None:
    if st.button("Start Translation", type="primary"):
        with st.spinner('Translating...'):
            translator = Translator()
            content = uploaded_file.read().decode("utf-8")
            lines = content.split('\n')
            translated_lines = []
            
            for line in lines:
                # បកប្រែតែអត្ថបទ (មិនបកលេខរៀង និងម៉ោង)
                if line.strip() and not line.strip().isdigit() and '-->' not in line:
                    try:
                        res = translator.translate(line, src='zh-cn', dest='km')
                        translated_lines.append(res.text)
                    except:
                        translated_lines.append(line)
                else:
                    translated_lines.append(line)
            
            result = '\n'.join(translated_lines)
            st.success("Done!")

            st.download_button("Download SRT", result, file_name="khmer_subtitle.srt")
