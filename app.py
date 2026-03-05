import os

# ... កូដខាងលើរក្សាទុកដដែល ...

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("ចាប់ផ្ដើមបកប្រែ"):
        with st.spinner('កំពុងទាញយកសំឡេង និងបកប្រែ...'):
            # កំណត់ឈ្មោះឯកសារឱ្យច្បាស់លាស់ជាមួយ Path បច្ចុប្បន្ន
            video_path = os.path.join(os.getcwd(), "temp_video.mp4")
            
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                # ប្រើ Whisper បកប្រែ
                # បន្ថែម fp16=False ដើម្បីកុំឱ្យ Error លើម៉ាស៊ីនដែលគ្មាន GPU
                result = model.transcribe(video_path, fp16=False)
                chinese_text = result['text']

                # បកប្រែជាខ្មែរ
                translated_text = GoogleTranslator(source='zh-CN', target='km').translate(chinese_text)

                st.success("រួចរាល់!")
                st.write(translated_text)
                
            except Exception as e:
                st.error(f"កើតមានបញ្ហា៖ {e}")
            
            finally:
                # លុបឯកសារចោលក្រោយពេលរួចរាល់
                if os.path.exists(video_path):
                    os.remove(video_path)
# មុខងារបង្កើតអក្សរសម្រាប់ឯកសារ SRT
def create_srt(segments):
    srt_content = ""
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # បកប្រែអក្សរក្នុង segment នីមួយៗ
        translated_segment = GoogleTranslator(source='zh-CN', target='km').translate(text)
        
        # ទម្រង់ពេលវេលា SRT (00:00:00,000)
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{translated_segment}\n\n"
    return srt_content

# បន្ទាប់ពីបង្ហាញអក្សររួច បន្ថែមប៊ូតុងនេះ៖
if st.button("បង្កើតឯកសារ Subtitle (.srt)"):
    srt_data = create_srt(result['segments'])
    st.download_button(
        label="📥 ទាញយកឯកសារ Subtitle ភាសាខ្មែរ",
        data=srt_data,
        file_name="subtitles_khmer.srt",
        mime="text/plain"
    )
    
