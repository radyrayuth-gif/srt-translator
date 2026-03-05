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
