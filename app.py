                # រក្សាទុកក្នុង Memory ដើម្បី Download
                buffer = io.BytesIO()
                
                # បង្ខំឱ្យ Export ជា MP3 ជាមួយ Bitrate ត្រឹមត្រូវ
                final_audio.export(buffer, format="mp3")
                
                # កំណត់ Pointer មកដើមវិញ ដើម្បីឱ្យ Streamlit អានទិន្នន័យបាន
                buffer.seek(0)
                audio_data = buffer.getvalue()

                # បង្ហាញ Player និងប៊ូតុង Download
                if audio_data:
                    st.audio(audio_data, format="audio/mp3")
                    st.download_button(
                        label="📥 ទាញយកឯកសារសំឡេង (.mp3)",
                        data=audio_data,
                        file_name=f"khmer_sync_{datetime.now().strftime('%H%M%S')}.mp3",
                        mime="audio/mp3"
                    )
