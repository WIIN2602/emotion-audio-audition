import streamlit as st
import pandas as pd
import requests
import io
import re

@st.cache_data(show_spinner=False)
def fetch_audio_bytes(url: str) -> bytes | None:
    """ดึงไฟล์เสียงจาก URL ใดก็ได้ (รวมถึง Google Drive) มาเป็น bytes
    รองรับทั้ง:
      - https://drive.google.com/file/d/FILE_ID/view
      - https://docs.google.com/uc?export=download&id=FILE_ID
      - URL ปกติอื่นๆ
    """
    # แปลง Google Drive share link → direct download link
    gdrive_file_pattern = r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)"
    gdrive_uc_pattern   = r"(?:docs\.google\.com/uc|drive\.google\.com/uc).*[?&]id=([a-zA-Z0-9_-]+)"

    file_id = None
    m = re.search(gdrive_file_pattern, url)
    if m:
        file_id = m.group(1)
    else:
        m = re.search(gdrive_uc_pattern, url)
        if m:
            file_id = m.group(1)

    if file_id:
        # ใช้ export=download พร้อม confirm=t เพื่อข้าม virus-scan warning
        url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"

    try:
        resp = requests.get(url, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        st.warning(f"⚠️ โหลดเสียงไม่สำเร็จ: {e}")
        return None


st.set_page_config(page_title="Audio Audition Platform", layout="centered")

# 1. โหลดข้อมูลจาก Google Sheets เฉพาะแท็บ Audition_Data ที่เปิดเผยแพร่แล้ว
@st.cache_data
def load_data():
    # ลิงก์ตรงที่เจาะจงเฉพาะแท็บ Audition_Data (gid=189130504) ในรูปแบบส่งออก CSV
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCyZquKSv6jlhdnKA7r_L8tr9rrmbCO9oEID-v0YHHfMsBpzM8w9stkhJdvhNTb9MTRvz5b6nZbJ8E/pub?gid=189130504&single=true&output=csv"
    
    # ดึงข้อมูลพร้อมตั้งค่า Timeout ป้องกันการค้าง
    df = pd.read_csv(csv_url)
    
    # ทำความสะอาดช่องว่างรอบๆ ชื่อคอลัมน์ ป้องกันการตรวจจับพลาด
    df.columns = df.columns.str.strip()
    
    # เลือกตัดแถวที่เป็นค่าว่างออก
    df = df.dropna(subset=['label', 'filename'])
    
    return df.reset_index(drop=True)

# โหลดข้อมูลเข้าสู่ระบบ
try:
    df_audition = load_data()
except Exception as e:
    st.error(f"❌ เกิดปัญหาในการดึงข้อมูลจากแท็บ Audition_Data: {e}")
    st.info("💡 วิธีแก้ไข: โปรดตรวจสอบว่าได้กด 'ไฟล์ > แชร์ > เผยแพร่ไปยังเว็บ' และเลือกแท็บ 'Audition_Data' บน Google Sheets แล้วหรือยัง")
    st.stop()

# สร้างระบบจำหน้าปัจจุบัน
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# ดึงข้อมูลแถวปัจจุบันมาใช้งาน
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

# ส่วนที่ 1: ฟังเสียงตัวอย่าง
st.write("### 1. ฟังเสียงตัวอย่าง")
if pd.notna(audio_source_url) and str(audio_source_url).startswith("http"):
    with st.spinner("กำลังโหลดเสียงตัวอย่าง..."):
        audio_bytes = fetch_audio_bytes(str(audio_source_url))
    if audio_bytes:
        st.audio(audio_bytes)
    else:
        st.error("❌ โหลดเสียงตัวอย่างไม่สำเร็จ กรุณาตรวจสอบว่าไฟล์ใน Google Drive ตั้งเป็น 'Anyone with the link'")
else:
    st.warning("⚠️ ไม่พบ URL ไฟล์เสียงต้นแบบในช่อง audio_url ของแถวนี้")
    st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")

# ส่วนที่ 2: อัดเสียงด้วยฟังก์ชันมาตรฐานของ Streamlit
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
        
