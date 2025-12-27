import streamlit as st
from openai import OpenAI
# រៀបចំ UI ឱ្យដូចវេបសាយអាជីព
st.set_page_config(page_title="KhmerTranslate AI", page_icon="🎬", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-title { color: #1e3a8a; text-align: center; font-size: 32px; font-weight: bold; }
    .sub-title { text-align: center; color: #64748b; margin-bottom: 30px; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)
st.markdown('<div class="main-title">AI Subtitle Translator (GPT-4o)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">បកប្រែអត្ថបទរឿងពីចិនមកខ្មែរ ឱ្យមានន័យពិរោះ និងអក្ខរាវិរុទ្ធត្រឹមត្រូវតាមបែបភាពយន្ត</div>', unsafe_allow_html=True)
# ផ្នែក Sidebar សម្រាប់បញ្ចូល API Key
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("OpenAI API Key", type="password", help="បញ្ចូល API Key របស់អ្នកនៅទីនេះ")
    st.info("ចំណាំ៖ ការប្រើប្រាស់ API នឹងត្រូវអស់ទឹកប្រាក់បន្តិចបន្តួចពីគណនី OpenAI របស់អ្នក។")
uploaded_file = st.file_uploader("Upload Chinese SRT File", type="srt")
def ai_translate_srt(content, api_key):
    client = OpenAI(api_key=api_key)
    
    # ការណែនាំ AI (System Prompt) ដើម្បីឱ្យវាបកប្រែបានល្អបំផុត
    system_instruction = """
    You are a master subtitle translator specializing in Chinese to Khmer movies. 
    Your task:
    1. Translate dialogue into natural, fluent, and cinematic Khmer.
    2. Maintain the emotional tone (e.g., romantic, martial arts, or modern).
    3. Keep all SRT timecodes [00:00:00,000 --> 00:00:00,000] and line numbers UNCHANGED.
    4. Use correct Khmer grammar and spelling.
    5. Avoid literal translations; make it sound like real people talking.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # អ្នកអាចប្ដូរជា "gpt-4o" ប្រសិនបើចង់បានគុណភាពខ្ពស់បំផុត
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": content}
            ],
            temperature=0.3 # កម្រិតនេះជួយឱ្យការបកប្រែមានភាពហ្មត់ចត់មិនរាយមាយ
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
if uploaded_file is not None:
    if st.button("Start AI Translation", type="primary", use_container_width=True):
        if not api_key:
            st.warning("សូមបញ្ចូល OpenAI API Key នៅក្នុង Sidebar ជាមុនសិន!")
        else:
            with st.spinner('AI កំពុងវិភាគ និងបកប្រែអត្ថបទរឿង... សូមរង់ចាំ'):
                raw_text = uploaded_file.read().decode("utf-8")
                
                # បញ្ជូនទៅ AI បកប្រែ
                translated_result = ai_translate_srt(raw_text, api_key)
                
                if "Error:" in translated_result:
                    st.error(translated_result)
                else:
                    st.success("ការបកប្រែតាមបែប AI បានជោគជ័យ!")
                    st.download_button(
                        label="Download AI Khmer SRT",
                        data=translated_result,
                        file_name=f"AI_Khmer_{uploaded_file.name}",
                        mime="text/plain",
                        use_container_width=True
                    )
