from flask import Flask, request, jsonify
import os
import base64
import tempfile
from dotenv import load_dotenv
from google import genai
from google.genai import types
from flask_cors import CORS

# Import Classifier ที่คุณสร้างไว้
from classifier import classify_image

# --- 1. Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app)  # อนุญาตให้ Frontend (Next.js) เรียกใช้งาน API ได้

# --- 2. Historical Data Configuration ---

# Mapping ชื่อไทย (จาก Frontend) -> ชื่ออังกฤษ (สำหรับ Classifier)
LOCATION_MAPPING_TH_TO_EN = {
    "อนุสาวรีย์ประชาธิปไตย": "Ratchadamnoen Avenue – Democracy Monument",
    "ศาลาเฉลิมกรุง": "Sala Chalermkrung Royal Theatre",
    "เสาชิงช้า & วัดสุทัศน์": "Giant Swing – Wat Suthat",
    "เยาวราช": "Yaowarat (Chinatown)",
    "ถนนข้าวสาร": "Khao San Road",
    "ป้อมพระสุเมรุ": "Phra Sumen Fort – Santichaiprakan Park",
    "สนามหลวง": "Sanam Luang (Royal Field)",
    "พิพิธภัณฑสถานแห่งชาติ": "National Museum Bangkok"
}

LOCATION_INFO = {
    "อนุสาวรีย์ประชาธิปไตย": {
        "prompt_key": "Democracy Monument",
        "desc_60s": "อนุสาวรีย์ปูนปั้นสีครีมด้าน พานรัฐธรรมนูญสีดำรมดำ ตั้งตระหง่านกลางถนนราชดำเนินที่ไร้สะพานลอย"
    },
    "ศาลาเฉลิมกรุง": {
        "prompt_key": "Sala Chalermkrung",
        "desc_60s": "โรงมหรสพหลวงยุคโก๋หลังวัง หน้าโรงติดตั้งคัตเอาท์ยักษ์เรื่อง 'บางกอกทวิกาล' โดยฝีมือช่างวาดสีน้ำมันชั้นครู"
    },
    "เสาชิงช้า & วัดสุทัศน์": {
        "prompt_key": "Giant Swing",
        "desc_60s": "เสาชิงช้าไม้สักตั้งอยู่บนพื้นถนนยางมะตอย รถยนต์สามารถขับลอดผ่านขาเสาได้ ไม่มีเกาะกลางกั้น"
    },
    "เยาวราช": {
        "prompt_key": "Yaowarat",
        "desc_60s": "ย่านการค้าชาวจีนที่คึกคักด้วยรถรางและป้ายร้านค้าไม้แกะสลัก ผสมผสานกับแสงไฟนีออนดัดยุคแรก"
    },
    "ถนนข้าวสาร": {
        "prompt_key": "Khaosan Road",
        "desc_60s": "ตรอกค้าขายข้าวสารที่เงียบสงบ เต็มไปด้วยห้องแถวไม้และกระสอบข้าวเปลือก ยามค่ำคืนมีเพียงแสงไฟสลัว"
    },
    "ป้อมพระสุเมรุ": {
        "prompt_key": "Phra Sumen Fort",
        "desc_60s": "ป้อมปราการเก่าแก่ริมน้ำที่ถูกรายล้อมด้วยชุมชนบ้านไม้และเพิงสังกะสีอย่างชิดใกล้ สะท้อนวิถีชีวิตดั้งเดิม"
    },
    "สนามหลวง": {
        "prompt_key": "Sanam Luang",
        "desc_60s": "ตลาดนัดวันหยุดสุดสัปดาห์ที่ใหญ่ที่สุด แหล่งรวมแผงหนังสือเก่าและสินค้าเบ็ดเตล็ดบนลานดินกว้าง"
    },
    "พิพิธภัณฑสถานแห่งชาติ": {
        "prompt_key": "National Museum",
        "desc_60s": "วังหน้าในบรรยากาศร่มรื่นด้วยต้นไม้ใหญ่หนาทึบ อาคารเก่าแก่สีขาวหม่นดูขลังและเงียบสงบ"
    }
}

LOCATION_PROMPTS = {
    "Democracy Monument": """
        **TASK:** Photorealistic transformation to 1964 Bangkok.
        **STRUCTURE LOCK:** Keep original perspective and monument geometry rigid.
        **VISUAL ELEMENTS:**
        - **Monument:** The wings are **MATTE CEMENT/STUCCO** (Creamy Grey), showing water stains and weathering. **ABSOLUTELY NO GOLD PAINT**. The central tray is **Dark Bronze/Black**.
        - **Environment:** Wide asphalt avenue with **NO flyovers** and **NO modern streetlights**.
        - **Background:** Art Deco shophouses with **faded pastel paint** (Old Rose, Pale Green). Large Mahogany trees lining the road.
        - **Traffic:** Vintage 1960s Mercedes Fintail, Morris Minor, and "Nai Lert" white buses.
        - **Atmosphere:** Hot tropical daylight, high contrast shadows.
    """,
    "Sala Chalermkrung": """
        **TASK:** Photorealistic transformation to 1967 (Bangkok EraVision Project).
        **CRITICAL STRUCTURE LOCK (DO NOT CHANGE):**
        1. **The Roof Sign:** The wire-frame metal structure reading "ศาลาเฉลิมกรุง" on the roof MUST remain **skeletal, transparent, and identical** to the original image. DO NOT turn it into a solid box or change its text.
        2. **Building Shape:** Keep the original architectural lines perfectly.
        **THE MOVIE BILLBOARD (Hand-Painted Style):**
        - Overlay the front entrance with a massive **Hand-Painted Movie Poster** (Oil on Plywood texture).
        - **Title:** Thai Text "**บางกอกทวิกาล**" (Vintage Font).
        - **Visuals:**
            - **Actor 1 (Nattapat):** A slim, handsome gentleman in a sharp 60s suit, slicked-back hair.
            - **Actor 2 (M.R. Madam Pong):** A smart, handsome man in a suit wearing **vintage eyeglasses**, looking cool.
            - **Director Credit:** "Tor-Tum".
        **CONTEXT CLEANUP:**
        - **Surroundings:** Remove clutter. The area around the theatre is clean concrete pavement.
        - **Vibe:** "Old Hollywood of Asia". 
        - **Crowd:** Teenagers in 60s fashion (Elvis style) gathering in front.
    """,
    "Giant Swing": """
        **TASK:** Photorealistic transformation to 1965.
        **STRUCTURE LOCK:** Keep perspective.
        **KEY HISTORICAL FACTS:**
        - **The Base:** The Giant Swing's red teak pillars stand **DIRECTLY ON THE ROAD SURFACE**.
        - **Traffic Flow:** Cars and Tuk-Tuks are driving **THROUGH/UNDER** the pillars.
        - **Ground:** **NO grass island**, NO oval curb barrier. Just asphalt road.
        - **Background:** Wat Suthat walls are weathered white (not bright). 
        - **Corner:** A vintage "Shell" gas station with round pumps (if visible in angle).
    """,
    "Yaowarat": """
        **TASK:** Photorealistic transformation to 1968 Chinatown.
        **STRUCTURE LOCK:** Maintain building perspective.
        **AESTHETIC (Realism over Fantasy):**
        - **Tone:** Desaturated film look, not cyberpunk. It looks like a busy commercial district in the 60s.
        - **Signage:** Vertical signs in Chinese/Thai. Material is **Wood and Painted Metal**. A few **Analog Neon Tubes** (Red/Green) are visible but dim/dusty.
        - **Traffic:** A **Yellow & Red TRAM** running on tracks in the middle of the road.
        - **Vehicles:** 1950s Chevrolets, Samlors (Tricycles), and hand-pushed carts.
        - **Buildings:** Shophouse facades are stained with smoke and age.
    """,
    "Khaosan Road": """
        **TASK:** Photorealistic transformation to 1962.
        **STRUCTURE LOCK:** Narrow street perspective.
        **CONCEPT (The Rice Market):**
        - **Activity:** A quiet wholesale trade street. **NO TOURISTS**.
        - **Buildings:** Old wooden row houses (2 stories). Folding wooden doors (Baan Fiam).
        - **Props:** Piles of **Hemp Rice Sacks** (Gunny sacks) stacked in front of shops. Ancient weighing scales.
        - **Lighting:** Natural daylight or dim tungsten street lamps.
        - **Vibe:** Domestic, slow-paced, dusty.
    """,
    "Phra Sumen Fort": """
        **TASK:** Photorealistic transformation to 1960.
        **STRUCTURE LOCK:** Fort geometry.
        **ENVIRONMENT (The Lost Community):**
        - **The Fort:** White plaster is **heavily weathered, cracked, and covered in black mold**. It looks abandoned.
        - **The Slum:** A dense community of **wooden stilt houses and rusty zinc roofs** built **TIGHTLY AGAINST** the fort's walls. No green park lawns.
        - **Foreground:** Muddy river bank, wild Lamphu trees, small wooden rowboats.
        - **Atmosphere:** Gritty, lived-in, humid.
    """,
    "Sanam Luang": """
        **TASK:** Photorealistic transformation to 1968 (Sunday Market).
        **STRUCTURE LOCK:** Palace background.
        **MARKET DETAILS:**
        - **Ground:** **Red Dirt and Dust** (Sanarm Chai). Very little grass.
        - **Market:** Hundreds of **Canvas Parasols** (Striped Red/White/Blue) clustered together.
        - **Goods:** Old books on mats, pets in wooden cages, amulets.
        - **Sky:** Traditional Thai Kites (Chula & Pakpao) flying.
        - **Vibe:** Bustling, hot, dusty, authentic flea market.
    """,
    "National Museum": """
        **TASK:** Photorealistic transformation to 1960.
        **STRUCTURE LOCK:** Thai architecture.
        **STYLE (The Forgotten Palace):**
        - **Architecture:** The buildings look **ancient and weathered**. White walls are dull and stained.
        - **Nature:** **Overgrown and Jungle-like**. Big trees with hanging roots casting deep shadows over the buildings.
        - **Atmosphere:** Mystical, silent, isolated from the city.
        - **Ground:** Fallen leaves, unpaved paths.
    """
}

# --- 3. Helper Functions ---

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    return genai.Client(api_key=api_key)

def step1_analyze(client, img_bytes):
    prompt = """
    Analyze the image structure for a historical transformation.
    1. Identify the rigid architectural lines (building edges, horizons).
    2. Identify the perspective vanishing point.
    3. Output a description that ensures the new image aligns PERFECTLY with these lines.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=[prompt, types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")]
        )
        return response.text
    except Exception as e:
        print(f"Analysis Error: {e}")
        return "Keep original perspective rigid."

def step2_generate(client, structure_desc, location_key, original_img_bytes):
    specific_prompt = LOCATION_PROMPTS.get(location_key, "")
    final_prompt = f"""
    {specific_prompt}
    
    **TECHNICAL GUIDE (REALISM):**
    - **Reference:** {structure_desc}. The output MUST match the input image's camera angle and geometry exactly.
    - **Visual Style:** **Vintage Color Photography (Kodachrome 64)**.
    - **Texture:** Film grain, slightly washed-out blacks, high contrast (Tropical Sunlight).
    - **Materials:** Real-world textures (cracked cement, rusted metal, wood grain). Avoid "AI smooth" or "plastic" looks.
    
    **STRICT NEGATIVE PROMPT (REMOVE):**
    - Modern cars (Sedans after 1970), SUVs, Pickups.
    - Air Conditioners (Compressors on walls).
    - BTS Skytrain, MRT, Concrete Flyovers.
    - LED Signs, Digital Billboards, 7-Eleven.
    - Modern clothing, Smartphones, Tourists with backpacks.
    - Saturation too high, HDR effects.
    """
    try:
        response = client.models.generate_content(
            model="nano-banana-pro-preview", # หรือ imagen-3.0-generate-001 ตามที่คุณมีสิทธิ์
            contents=[
                final_prompt, 
                types.Part.from_bytes(data=original_img_bytes, mime_type="image/jpeg")
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                temperature=0.25
            )
        )
        
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
        return None

    except Exception as e:
        print(f"Generation Error: {e}")
        return None
    

LOCATION_MAPPING_EN_TO_TH = {v: k for k, v in LOCATION_MAPPING_TH_TO_EN.items()}

def get_friendly_error_message(raw_reason, lang='TH'):
    """
    แปล Error เป็นภาษาคน (ไทย/อังกฤษ) ตามค่า lang ที่ส่งมา
    lang: 'TH' หรือ 'ENG'
    """
    raw_reason = raw_reason.lower()
    is_eng = (lang == 'ENG')

    # 1. กลุ่มแสง/เวลา (Night, Dark)
    if any(x in raw_reason for x in ['night', 'dark', 'sunset', 'evening']):
        return "The image is too dark or taken at night. AI needs natural daylight." if is_eng else \
               "ภาพมืดหรือเป็นเวลากลางคืน (AI ต้องการแสงธรรมชาติช่วงกลางวันเพื่อความแม่นยำ)"

    # 2. กลุ่มคน/เซลฟี่ (Person, Selfie, Crowd)
    if any(x in raw_reason for x in ['person', 'selfie', 'face', 'crowd', 'body']):
        return "People or crowds are obstructing the view. Please use a clear shot of the scenery." if is_eng else \
               "ตรวจพบบุคคลหรือฝูงชนบดบังทัศนียภาพ (กรุณาใช้ภาพวิวที่เห็นสถานที่ชัดเจน)"

    # 3. กลุ่มถ่ายเจาะ/ซูม/พื้นผิว (Close-up, Pattern, Wall)
    if any(x in raw_reason for x in ['close-up', 'detail', 'macro', 'texture', 'wall', 'floor', 'sky']):
        return "The shot is too close or detailed. Please take a wider angle photo." if is_eng else \
               "ภาพถ่ายระยะใกล้หรือเจาะจงเกินไป (กรุณาถ่ายภาพมุมกว้างให้เห็นองค์ประกอบครบถ้วน)"

    # 4. กลุ่มสิ่งกีดขวาง/รถ (Vehicle, Bus, Truck)
    if any(x in raw_reason for x in ['vehicle', 'bus', 'truck', 'car', 'traffic']):
        return "Vehicles or obstacles are blocking the architecture." if is_eng else \
               "มียานพาหนะหรือสิ่งกีดขวางบดบังตัวอาคารมากเกินไป"

    # 5. กลุ่มไม่ใช่ภาพถ่ายสถานที่ (Text, Screenshot)
    if any(x in raw_reason for x in ['text', 'screenshot', 'map', 'drawing']):
        return "This image does not appear to be a real photo of the location." if is_eng else \
               "ภาพนี้ดูเหมือนไม่ใช่ภาพถ่ายสถานที่จริง (กรุณาใช้ภาพถ่ายต้นฉบับ)"
    
    # 6. กรณี Other (ไม่รู้จักที่ไหนเลย)
    if "other" in raw_reason:
        guess = raw_reason.replace("other", "").replace("(", "").replace(")", "").strip()
        if guess:
            return f"System could not identify this location. (AI sees: {guess})" if is_eng else \
                   f"ระบบไม่สามารถระบุสถานที่นี้ได้ชัดเจน (AI มองเห็นเป็น: {guess})"
        return "System could not identify the location. Please try a distinctive angle." if is_eng else \
               "ระบบไม่สามารถระบุสถานที่ในภาพได้ (กรุณาลองหามุมที่เป็นเอกลักษณ์ของสถานที่นั้นๆ)"

    # Default
    return "Image composition is unclear. Please try a different angle." if is_eng else \
           "องค์ประกอบภาพยังไม่ชัดเจนหรือมีสิ่งรบกวน (กรุณาลองเปลี่ยนมุมภาพ)"

# --- 4. Routes ---
# Route 1: สำหรับ Verify อย่างเดียว (เร็ว)
@app.route('/verify', methods=['POST'])
def verify_image_route():
    temp_path = None
    try:
        if 'image' not in request.files or 'location' not in request.form:
            return jsonify({'error': 'Missing data'}), 400
        
        file = request.files['image']
        location_th = request.form['location']
        
        # 👇 รับค่าภาษาจาก Frontend (ถ้าไม่ส่งมา Default เป็น TH)
        lang = request.form.get('language', 'TH').upper() 
        
        if location_th not in LOCATION_INFO:
            return jsonify({'error': 'Invalid location selection'}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name

        print(f"🕵️‍♂️ Verifying: {location_th} (Lang: {lang})...")
        detected_place, score, is_valid = classify_image(temp_path)
        expected_place_en = LOCATION_MAPPING_TH_TO_EN.get(location_th)
        
        analysis_report = {
            "status": "success" if is_valid else "rejected",
            "detected_place": detected_place,
            "score": round(score * 100, 2),
            "is_valid": is_valid
        }

        # --- CASE 1: ตรวจสอบไม่ผ่านเลย (Rejected / Other) ---
        if not is_valid:
            # ส่ง lang เข้าไปเพื่อให้ฟังก์ชันเลือกภาษาถูก
            friendly_message = get_friendly_error_message(detected_place, lang)
            
            return jsonify({
                'status': 'rejected', 
                'details': friendly_message, 
                'analysis_report': analysis_report
            }), 200
        
        # --- CASE 2: ผ่านคุณภาพ แต่ผิดสถานที่ (Location Mismatch) ---
        if detected_place != expected_place_en:
             # ถ้าเป็น ENG: ใช้ชื่ออังกฤษ (detected_place)
             # ถ้าเป็น TH: แปลงเป็นชื่อไทย
             if lang == 'ENG':
                 detected_name = detected_place
                 selected_name = LOCATION_MAPPING_TH_TO_EN.get(location_th, location_th) # พยายามหาชื่ออังกฤษของสิ่งที่เลือก
                 msg = f"AI detected: '{detected_name}'\nwhich does not match your selection ({selected_name})"
             else:
                 detected_name = LOCATION_MAPPING_EN_TO_TH.get(detected_place, detected_place)
                 msg = f"AI ตรวจพบ: '{detected_name}'\nซึ่งไม่ตรงกับที่คุณเลือก ({location_th})"
             
             return jsonify({
                'status': 'rejected', 
                'details': msg,
                'analysis_report': analysis_report
            }), 200

        # --- CASE 3: ผ่านฉลุย ---
        return jsonify({
            'status': 'success',
            'analysis_report': analysis_report
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)

# Route 2: สำหรับ Generate อย่างเดียว (ช้า)
@app.route('/generate', methods=['POST'])
def generate_image_route():
    try:
        file = request.files['image']
        location_th = request.form['location']
        
        # อ่านไฟล์เป็น bytes ตรงๆ เลย ไม่ต้อง classify ซ้ำแล้ว
        img_bytes = file.read()
        prompt_key = LOCATION_INFO[location_th]['prompt_key']
        client = get_client()
        
        structure = step1_analyze(client, img_bytes)
        result_bytes = step2_generate(client, structure, prompt_key, img_bytes)
        
        if result_bytes:
            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            return jsonify({
                'status': 'success',
                'image': f"data:image/png;base64,{result_b64}",
                'location_name': location_th,
                'description': LOCATION_INFO[location_th]['desc_60s']
            })
        else:
            return jsonify({'error': 'AI Generation failed'}), 500
            
    except Exception as e:
        print(f"Gen Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)