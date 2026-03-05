import os
import time
from google import genai
from dotenv import load_dotenv

# 1. โหลด API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def check_gemini_status():
    client = genai.Client(api_key=api_key)
    print("🔍 กำลังตรวจสอบสถานะ Gemini API...")
    
    try:
        # ใช้คำสั่งที่เบาที่สุด (Text Generation) แทนการเจนรูป
        # เพื่อเช็คว่าเซิร์ฟเวอร์ 503 หรือไม่
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents="ping"
        )
        
        if response.text:
            print("✅ [STATUS: OK] - เซิร์ฟเวอร์พร้อมใช้งาน เริ่มเจนรูปได้เลย!")
            return True
            
    except Exception as e:
        err_msg = str(e)
        if "503" in err_msg:
            print("❌ [STATUS: BUSY] - เซิร์ฟเวอร์ยัง Error 503 อยู่ (คนใช้เยอะ)")
        elif "429" in err_msg:
            print("⚠️ [STATUS: QUOTA] - ติดโควต้าการใช้งาน (รอ 1 นาที)")
        else:
            print(f"❓ [STATUS: ERROR] - เกิดข้อผิดพลาดอื่น: {err_msg}")
            
    return False

if __name__ == "__main__":
    # รันเช็ค 1 ครั้ง
    check_gemini_status()