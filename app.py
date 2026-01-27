# បង្កើត Buffer ថ្មី
buffer = io.BytesIO()

# បញ្ជាក់ឱ្យច្បាស់ពី Format និងតម្រូវឱ្យវា Export ឱ្យចប់សព្វគ្រប់
final_audio.export(buffer, format="mp3", parameters=["-q:a", "0"])

# កំណត់ Pointer របស់ Buffer មកដើមវិញ (សំខាន់ខ្លាំង)
buffer.seek(0)

# បង្ហាញ Player និងប៊ូតុង Download
audio_bytes = buffer.read()
st.audio(audio_bytes, format="audio/mp3")

st.download_button(
    label="📥 ទាញយកឯកសារសំឡេង (.mp3)",
    data=audio_bytes,
    file_name=f"khmer_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3",
    mime="audio/mp3"
)
