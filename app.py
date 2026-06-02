import streamlit as st
import pandas as pd
from st_audio_recorder import audio_recorder

st.set_page_config(page_title="Audio Audition Platform", layout="centered")

# 1. โหลดข้อมูลจาก Google Sheets ของคุณ
@st.cache_data
def load_data():
    # ลิงก์ Google Sheets ของคุณ
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCyZquKSv6jlhdnKA7r_L8tr9rrmbCO9oEID-v0YHHfMsBpzM8w9stkhJdvhNTb9MTRvz5b6nZbJ8E/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(csv_url)
    
    # สุ่มกลุ่มละ 2 แถวตามเงื่อนไขของคุณ
    sampled = df.groupby('label', group_keys=False).apply(
        lambda x: x.sample(n=min(len(x), 2), random_state=42)
    )
    return sampled.reset_index(drop=True)

df_sampled = load_data()

# สร้าง State สำหรับจำจำหน้าปัจจุบัน
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# ดึงข้อมูลแถวปัจจุบันมาแสดงผล
row = df_sampled.iloc[st.session_state.current_index]
emotion = row['label']
filename = row['filename']
transcript = row['transcript_canary']
audio_source_url = row.get('audio_url', '') # ดึงจากคอลัมน์ลิงก์เสียงที่เราสร้างไว้

st.title("🎙️ แพลตฟอร์มสำหรับอัดเสียงตามอารมณ์")
st.write(f"ความคืบหน้า: {st.session_state.current_index + 1} / {len(df_sampled)}")
st.progress((st.session_state.current_index + 1) / len(df_sampled))

st.markdown("---")
st.subheader(f"🎭 อารมณ์ที่ต้องแสดงออก: {emotion.upper()}")
st.info(f"**ข้อความที่ต้องอ่าน:** \n\n {transcript}")

# ส่วนที่ 1: ฟังเสียงตัวอย่าง
st.write("### 1. ฟังเสียงตัวอย่าง")
if pd.notna(audio_source_url) and str(audio_source_url).startswith("http"):
    st.audio(audio_source_url)
else:
    st.warning("⚠️ แถวนี้ยังไม่ได้ใส่ URL ไฟล์เสียงต้นแบบในกูเกิลชีต (ระบบจึงแสดงเสียงตัวอย่างจำลองให้ทดสอบ)")
    st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3") 

# ส่วนที่ 2: อัดเสียง
st.write("### 2. อัดเสียงของคุณ")
audio_bytes = audio_recorder(
    text="คลิกปุ่มไมค์เพื่อเริ่มอัด / คลิกอีกครั้งเพื่อหยุด",
    recording_color="#e74c3c",
    neutral_color="#2ecc71",
    icon_size="2x"
)

if audio_bytes:
    # แสดงเครื่องเล่นเสียงให้คนอัดกดรีฟังเสียงตัวเองได้
    st.audio(audio_bytes, format="audio/wav")
    
    # ระบบตั้งชื่อไฟล์ให้อัตโนมัติให้สอดคล้องกับไฟล์ต้นฉบับ
    output_filename = f"rec_{emotion}_{filename.replace('.flac', '.wav')}"
    
    # ปุ่มดาวน์โหลด
    st.download_button(
        label="📥 คลิกเพื่อดาวน์โหลดไฟล์เสียงนี้ลงเครื่องของคุณ",
        data=audio_bytes,
        file_name=output_filename,
        mime="audio/wav"
    )
    st.success(f"เมื่อดาวน์โหลดเสร็จแล้ว ไฟล์จะชื่อ: {output_filename} อย่าลืมรวบรวมส่งเข้า Google Drive นะครับ")

# ส่วนที่ 3: ปุ่มเปลี่ยนข้อความ ถัดไป-ย้อนกลับ
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("⬅️ ย้อนกลับ") and st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.rerun()
with col2:
    if st.button("ถัดไป ➡️") and st.session_state.current_index < len(df_sampled) - 1:
        st.session_state.current_index += 1
        st.rerun()