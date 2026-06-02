import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Audio Audition Platform", layout="centered")

# ฟังก์ชันแปลงลิงก์ Google Drive ให้เป็น Direct Download Link เพื่อให้เครื่องเล่น st.audio กดฟังได้
def to_direct_link(url):
    if pd.isna(url) or not str(url).startswith("http"):
        return None
    url = str(url).strip()
    # ตรวจจับโครงสร้างลิงก์ของ Google Drive (uc?id=... หรือ file/d/.../)
    match = re.search(r'(?:id=|/d/)([\w-]+)', url)
    if "drive.google.com" in url and match:
        file_id = match.group(1)
        return f"https://docs.google.com/uc?export=download&id={file_id}"
    return url

# 1. โหลดข้อมูลเจาะจงเฉพาะแท็บ Audition_Data (gid=189130504)
@st.cache_data(ttl=60)  # ตั้งเวลาเคลียร์แคชทุกๆ 1 นาที เผื่อมีการอัปเดตข้อมูลบนชีต
def load_data():
    # ใช้ลิงก์ตรงสำหรับส่งออก CSV จากแท็บ Audition_Data
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCyZquKSv6jlhdnKA7r_L8tr9rrmbCO9oEID-v0YHHfMsBpzM8w9stkhJdvhNTb9MTRvz5b6nZbJ8E/pub?gid=189130504&single=true&output=csv"
    df = pd.read_csv(csv_url)
    
    # ทำความสะอาดช่องว่างรอบๆ ชื่อคอลัมน์
    df.columns = df.columns.str.strip()
    
    # เลือกตัดแถวที่เป็นค่าว่างในส่วนสำคัญออก
    df = df.dropna(subset=['label', 'filename'])
    
    return df.reset_index(drop=True)

# โหลดข้อมูลเข้าสู่ระบบ
try:
    df_audition = load_data()
except Exception as e:
    st.error(f"❌ เกิดปัญหาในการดึงข้อมูลจากแท็บ Audition_Data: {e}")
    st.info("💡 แนะนำให้ตรวจสอบว่ากด 'ไฟล์ > แชร์ > เผยแพร่ไปยังเว็บ' บน Google Sheets เรียบร้อยแล้ว")
    st.stop()

# ระบบจำหน้าปัจจุบัน
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# ตรวจสอบขอบเขตเผื่อจำนวนแถวเปลี่ยนไป
if st.session_state.current_index >= len(df_audition):
    st.session_state.current_index = 0

# ดึงข้อมูลแถวปัจจุบันมาแสดงผล
row = df_audition.iloc[st.session_state.current_index]
emotion = row['label']
filename = row['filename']
transcript = row['transcript_canary']
audio_source_url = row.get('audio_url', '')

st.title("🎙️ แพลตฟอร์มสำหรับอัดเสียงตามอารมณ์")
st.write(f"ความคืบหน้า: {st.session_state.current_index + 1} / {len(df_audition)}")
st.progress((st.session_state.current_index + 1) / len(df_audition))

st.markdown("---")
st.subheader(f"🎭 อารมณ์ที่ต้องแสดงออก: {emotion.upper()}")
st.info(f"**ข้อความที่ต้องอ่าน:** \n\n {transcript}")

# ส่วนที่ 1: ฟังเสียงตัวอย่าง (เปิดใช้งาน Direct Link)
st.write("### 1. ฟังเสียงตัวอย่าง")
direct_audio_url = to_direct_link(audio_source_url)

if direct_audio_url:
    st.audio(direct_audio_url)
else:
    st.warning("⚠️ ไม่พบลิงก์เสียงตัวอย่างในช่อง audio_url ของแถวนี้ หรือลิงก์ไม่ถูกต้อง")
    st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3") 

# ส่วนที่ 2: อัดเสียงด้วยโมดูลของ Streamlit
st.write("### 2. อัดเสียงของคุณ")
audio_file = st.audio_input("💡 คลิกที่ปุ่มไมโครโฟนเพื่อเริ่มอัดเสียง")

if audio_file is not None:
    audio_bytes = audio_file.read()
    output_filename = f"rec_{emotion}_{filename.replace('.flac', '.wav')}"
    
    st.markdown("#### 📥 ดาวน์โหลดไฟล์ที่อัดสำเร็จ")
    st.download_button(
        label="📥 คลิกที่นี่เพื่อดาวน์โหลดไฟล์เสียงลงเครื่อง",
        data=audio_bytes,
        file_name=output_filename,
        mime="audio/wav"
    )
    st.success(f"ชื่อไฟล์ตอนเซฟจะเป็น: {output_filename}")

# ส่วนที่ 3: ปุ่มเปลี่ยนข้อความ ย้อนกลับ - ถัดไป
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("⬅️ ย้อนกลับ") and st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.rerun()
with col2:
    if st.button("ถัดไป ➡️") and st.session_state.current_index < len(df_audition) - 1:
        st.session_state.current_index += 1
        st.rerun()
