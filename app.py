import streamlit as st
from deep_translator import GoogleTranslator
# រៀបចំ UI ឱ្យស្រស់ស្អាតដូចគំរូ Admin
st.set_page_config(page_title="KhmerTranslate Pro", page_icon="🔵")
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .title-text { color: #1e3a8a; font-weight: bold; text-align: center; font-size: 28px; font-family: 'Kantumruy Pro', sans-serif; }
    </style>
    """, unsafe_allow_html=True)
st.markdown('<h1 class="title-text">កម្មវិធីបកប្រែអត្ថបទរឿង (ចិន -> ខ្មែរ)</h1>', unsafe_allow_html=True)
st.write("សូម Upload ហ្វាយ .srt ចិនរបស់អ្នក។ ប្រព័ន្ធនឹងរក្សាម៉ោងឱ្យនៅដដែល និងបកប្រែអត្ថបទជាភាសាខ្មែរ។")
uploaded_file = st.file_uploader("", type="srt")
def clean_and_fix(text):
    # មុខងារជួយតម្រង់ពាក្យចិនមួយចំនួនឱ្យបកមកខ្មែរស្ដាប់គ្នាបាន
    fixes = {
        "你": "អ្នក",
        "我": "ខ្ញុំ",
        "好": "ល្អ",
        "是的": "បាទ/ចាស",
        "什么": "អ្វី"
    }
    for cn, kh in fixes.items():
        text = text.replace(cn, kh)
    return text
if uploaded_file is not None:
    if st.button("ចាប់ផ្ដើមបកប្រែ", type="primary"):
        with st.spinner('កំពុងបកប្រែ... សូមរង់ចាំ'):
            try:
                # ប្រើ GoogleTranslator ជំនួស googletrans ដើម្បីជៀសវាង Error លើ Cloud
                translator = GoogleTranslator(source='zh-CN', target='km')
                
                content = uploaded_file.read().decode("utf-8")
                lines = content.split('\n')
                translated_lines = []
                
                # បង្កើត Progress Bar ដើម្បីងាយស្រួលមើល
                progress_bar = st.progress(0)
                total_lines = len(lines)
                for i, line in enumerate(lines):
                    # បកប្រែតែអត្ថបទ (មិនបកលេខរៀង និង Timecode)
                    if line.strip() and not line.strip().isdigit() and '-->' not in line:
                        try:
                            # កែសម្រួលពាក្យចិនបន្តិចមុនបកប្រែ
                            ready_line = clean_and_fix(line)
                            res = translator.translate(ready_line)
                            translated_lines.append(res)
                        except:
                            translated_lines.append(line)
                    else:
                        translated_lines.append(line)
                    
                    # Update progress bar
                    progress_bar.progress((i + 1) / total_lines)
                
                result = '\n'.join(translated_lines)
                st.success("ការបកប្រែត្រូវបានបញ្ចប់ជាស្ថាពរ!")
                st.download_button("ទាញយកហ្វាយ SRT ខ្មែរ", result, file_name=f"Khmer_{uploaded_file.name}")
            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស៖ {str(e)}")
