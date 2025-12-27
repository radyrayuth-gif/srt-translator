import streamlit as st
from deep_translator import GoogleTranslator
import time
# រៀបចំ UI ឱ្យស្រស់ស្អាត
st.set_page_config(page_title="Khmer Subtitle Pro", page_icon="🎬")
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-title { color: #1e40af; text-align: center; font-family: 'Kantumruy Pro', sans-serif; }
    .info-text { text-align: center; color: #475569; }
    </style>
    """, unsafe_allow_html=True)
st.markdown('<h1 class="main-title">កម្មវិធីបកប្រែអត្ថបទរឿង (ចិន-ខ្មែរ)</h1>', unsafe_allow_html=True)
st.markdown('<p class="info-text">បកប្រែហ្វាយ .srt ដោយរក្សាម៉ោងឱ្យនៅដដែល និងប្រើឃ្លាប្រយោគសមស្រប</p>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("សូមជ្រើសរើសហ្វាយ SRT ចិន", type="srt")
def improve_khmer(text):
    # មុខងារជំនួយសម្រាប់កែសម្រួលពាក្យឱ្យកាន់តែសមស្របតាមបែបខ្មែរ
    replacements = {
        "你": "អ្នក",
        "我": "ខ្ញុំ",
        "是的": "បាទ/ចាស",
        "谢谢": "អរគុណ",
        "什么": "អ្វី"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
if uploaded_file is not None:
    if st.button("ចាប់ផ្ដើមបកប្រែ", type="primary"):
        with st.spinner('កំពុងបកប្រែ... សូមរង់ចាំ'):
            # ប្រើ GoogleTranslator ជាមួយការកំណត់ខ្ពស់
            translator = GoogleTranslator(source='zh-CN', target='km')
            
            content = uploaded_file.read().decode("utf-8")
            lines = content.split('\n')
            translated_lines = []
            
            progress_bar = st.progress(0)
            for i, line in enumerate(lines):
                # បកប្រែតែអត្ថបទសន្ទនា
                if line.strip() and not line.strip().isdigit() and '-->' not in line:
                    try:
                        # កែសម្រួលអត្ថបទមុនបកប្រែដើម្បីឱ្យកាន់តែច្បាស់
                        cleaned_line = improve_khmer(line)
                        res = translator.translate(cleaned_line)
                        translated_lines.append(res)
                    except:
                        translated_lines.append(line)
                else:
                    translated_lines.append(line)
                
                # បង្ហាញ Progress
                progress_bar.progress((i + 1) / len(lines))
            
            result = '\n'.join(translated_lines)
            st.success("ការបកប្រែត្រូវបានបញ្ចប់!")
            st.download_button("ទាញយកហ្វាយបកប្រែរួច", result, file_name=f"Khmer_{uploaded_file.name}")
