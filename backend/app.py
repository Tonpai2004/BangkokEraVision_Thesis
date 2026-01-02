from flask import Flask, request, jsonify
import os
import base64
import tempfile
from dotenv import load_dotenv
from google import genai
from google.genai import types
from flask_cors import CORS

# Import Classifier ที่คุณสร้างไว้ (จาก Code 1)
from classifier import classify_image

# --- 1. Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app)  # อนุญาตให้ Frontend (Next.js) เรียกใช้งาน API ได้

# --- 2. Historical Data Configuration ---

# Mapping ชื่อไทย (จาก Frontend) -> ชื่ออังกฤษ (สำหรับ Classifier)
# (ส่วนนี้คงไว้จาก Code 1 เพื่อให้ระบบ Verify ทำงานได้)
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

# ข้อมูลคำบรรยายภาษาไทย (อัปเดตจาก Code 2)
LOCATION_INFO = {
    "อนุสาวรีย์ประชาธิปไตย": {
        "prompt_key": "Democracy Monument",
        "desc_60s": "ตัวอนุสาวรีย์สีครีมปูนชัดเจน พานรัฐธรรมนูญสีโลหะรมดำ ประตูสีแดงชาด อาคารราชดำเนินสีส้มอิฐ ถนนกว้างไร้เส้นจราจร"
    },
    "ศาลาเฉลิมกรุง": {
        "prompt_key": "Sala Chalermkrung",
        "desc_60s": "โรงมหรสพหลวงยุคโก๋หลังวัง อาคารสีขาวครีมที่มีคราบฝน โดดเด่นด้วย 'คัตเอาท์ยักษ์วาดมือ' เรื่อง 'บางกอกทวิกาล' หน้าโรง พร้อมดารานำชายสองสไตล์ บรรยากาศรอบข้างคึกคักด้วยวัยรุ่นยุค 60s รถแท็กซี่เฟียต และรถรางวิ่งผ่านหน้าโรง"
    },
    "เสาชิงช้า & วัดสุทัศน์": {
        "prompt_key": "Giant Swing",
        "desc_60s": "เสาชิงช้ามีฐานปูนชัดเจน รถวิ่งอ้อมฐานห้ามลอดผ่าน ไม่มีรถราง ถนนลูกรัง วัดสุทัศน์ดูเก่าแก่ตามกาลเวลา"
    },
    "เยาวราช": {
        "prompt_key": "Yaowarat",
        "desc_60s": "รถรางโปร่งแบบเปิดข้างวิ่งชิดขอบทาง ป้ายร้านค้าแนบตึกไม่ยื่นรกตา ตึกแถวเก่าแก่ บรรยากาศการค้าขายแบบดั้งเดิม"
    },
    "ถนนข้าวสาร": {
        "prompt_key": "Khaosan Road",
        "desc_60s": "ชุมชนบางลำพูย่านค้าข้าวสาร ห้องแถวไม้ประตูบานเฟี้ยม มีกระสอบข้าววางหน้าร้าน บรรยากาศเงียบสงบแบบย่านพักอาศัย ไม่ใช่ย่านท่องเที่ยว"
    },
    "ป้อมพระสุเมรุ": {
        "prompt_key": "Phra Sumen Fort",
        "desc_60s": "ป้อมสีขาวขุ่นทรุดโทรมมีคราบตะไคร่ บ้านเรือนไม้สังกะสีสร้างเบียดเสียดติดตัวป้อม ไม่เห็นมุมคลองมากนัก ไม่มีสวนสาธารณะ"
    },
    "สนามหลวง": {
        "prompt_key": "Sanam Luang",
        "desc_60s": "ตลาดนัดสนามหลวง พื้นดินแดงปนหญ้าแห้ง ร่มผ้าใบสีขาวสลับแดง/น้ำเงิน รถเข็นขายน้ำอ้อยสีฟ้า ว่าวไทยลอยเต็มฟ้า ฉากหลังวัดพระแก้ว"
    },
    "พิพิธภัณฑสถานแห่งชาติ": {
        "prompt_key": "National Museum",
        "desc_60s": "อาคารทรงไทยสีขาวหมองมีคราบตะไคร่ดำ สภาพรกรั้วด้วยต้นไม้ใหญ่เหมือนวัดป่า ถนนหน้าพระธาตุลาดยางเงียบสงบ รั้วเหล็กดัดหัวลูกศร"
    }
}

# --- The Master Prompt Database (Strict Historical Accuracy & Structure Lock) ---
# (อัปเดตจาก Code 2 เป๊ะทุกตัวอักษร)
LOCATION_PROMPTS = {
    "Democracy Monument": """
          **TASK:** Photorealistic Reconstruction of 1960s Democracy Monument.
          **STRUCTURAL LOCK:** Maintain the original perspective and monument geometry 100%.

          **VISUAL ELEMENTS:**
          - **Main Concrete Structure:** The four wing structures and the central turret column are **Matte Cement / Off-White Cream color**. **DO NOT** make the concrete wings look black, smoked, or dirty.
          - **The Pedestal Tray (Phan):** **ONLY** the central tray carrying the constitution at the very top is **Dark Black Oxidized Metal / Bronze**.
          - **The Doors:** The specific doors at the base of the central turret are **Red Ochre / Deep Red**.
          - **Sculptures:** The bas-relief sculptures at the base of the wings are **Cement Color** (same as the wings).
          - **Surroundings:** Flanking buildings along Ratchadamnoen Avenue are **Terracotta Brick Orange / Burnt Orange**.
          - **Street:** Wide asphalt, coarse texture. **NO traffic lines**. 
          - **Vehicles:** **White 'Nai Lert' Buses** (Rounded body). Vintage cars.
          - **Atmosphere:** Bright daylight, clear visibility, historical film grain.
      """,

    "Sala Chalermkrung": """
        **TASK:** Create a photorealistic color photograph of Sala Chalermkrung Theatre in Bangkok, circa 1967.
        **STRUCTURE LOCK (CRITICAL):** - **KEEP THE ROOF SIGN:** The wire-frame metal structure reading "ศาลาเฉลิมกรุง" on the roof MUST remain structurally identical to the input image. Do not change its shape.
        - **Modify Facade Only:** Apply the vintage aesthetic to the building walls and street level.
        
        **THE MOVIE POSTER INJECTION (MANDATORY):**
        - **Action:** Overlay a massive, hand-painted oil cut-out billboard on the front facade (covering the entrance area).
        - **Poster Content:** A Thai movie titled "**บางกอกทวิกาล**" (Bangkok EraVision).
        - **Visuals on Poster:**
            1. Actor 1: A **MUSCULAR, bulky man** in a suit wearing **GLASSES** (M.R. Mod-Or-Por style).
            2. Actor 2: A **SLIM, handsome man** in a suit with **Middle-part hair** (Nattapat style).
            3. Director credit: "Tor-Tum".
        - **Style:** 1960s Thai Cinema Art, vivid colors, dramatic brush strokes.

        **1960s STREET LEVEL:**
        - **Building:** Weathered Creamy White concrete walls with rain stains.
        - **Traffic:** **TRAM TRACKS** on the road. A Yellow/Red Tram passing by. Vintage Taxis (Fiat/Austin).
        - **Crowd:** Teenagers in 60s fashion (Elvis hair, high buns).
        
        **NEGATIVE PROMPT:** LED displays, Modern glass doors, BTS, Modern cars.
    """,

    "Giant Swing": """
        **TASK:** Photorealistic Reconstruction of The Giant Swing (1965).
        **STRUCTURAL LOCK:** Keep the exact perspective.

        **VISUAL ELEMENTS:**
        - **The Swing Structure:** - **Vibrant Red Teak Logs**. 
            - **CRITICAL:** The swing sits on a **Raised Stone Plinth/Base**. 
            - **CRITICAL:** **NO VEHICLES driving underneath the swing**. Traffic goes AROUND the base.
        - **Traffic:** - **REMOVE TRAMS**. No trams visible in this scene. 
            - Few vintage cars driving around the perimeter.
        - **Context:** - Wat Suthat in the background must look **aged, weathered, and historically accurate** (not pristine/renovated).
            - Surrounding area is residential wooden houses, unpaved or rough asphalt roads.
    """,

    "Yaowarat": """
        **TASK:** Photorealistic Reconstruction of Yaowarat Road (1968).
        **CONTEXT:** Chinatown.

        **VISUAL ELEMENTS:**
        - **Signage:** - Signs are **NOT projecting/jutting out far** into the street. 
            - Most signs are hung **flat against the building facades** or cloth banners.
            - Less density of neon than modern times.
        - **Architecture:** - Old shophouses, aged concrete, not the modern renovated look.
        - **Transport - TRAM:** - **Tram runs CLOSE TO THE CURB/SIDE**, NOT in the middle.
            - **Tram Type:** **Open-sided carriage** (airy, bench seating), NOT an enclosed solid train.
        - **Atmosphere:** Hazy, dusty, busy market but less chaotic overhead than today.
    """,

    "Khaosan Road": """
        **TASK:** Photorealistic Reconstruction of Bang Lamphu / Khaosan Road (1962).
        **CONTEXT:** A quiet **Rice Trading Residential Community**. NOT a tourist street.

        **VISUAL ELEMENTS:**
        - **Architecture:** **Wooden Row Houses** (2 stories) mixed with concrete shophouses.
        - **Storefronts:** **"Baan Fiam"** (Accordion wooden plank doors).
        - **Props:** Piles of **Hemp Rice Sacks** stacked in front. White rice dust on the ground. Large glass jars with biscuits.
        - **Signage:** Local Thai signs (e.g., "S. Thammapakdi"). **NO English bars/hostel signs.**
        - **Activity:** Children playing with bicycle tires. Quiet, domestic vibe.
    """,

    "Phra Sumen Fort": """
        **TASK:** Photorealistic Reconstruction of Phra Sumen Fort (1960).
        **CRITICAL:** **NO MODERN PARK. NO LAWN.**

        **VISUAL ELEMENTS:**
        - **The Fort:** - **Dilapidated and Weathered**. White plaster is heavily stained with **Green Moss and Black Algae**.
            - Looks ancient and neglected.
        - **Viewpoint:** - **Minimize the canal view**. Focus on the land side.
        - **Surroundings:** - **Encroachment:** Ramshackle **wooden houses and community dwellings** are built TIGHTLY against the fort walls.
            - Ground is **Mud and Dirt**.
    """,

    "Sanam Luang": """
        **TASK:** Photorealistic Reconstruction of Sanam Luang (Weekend Market 1968).

        **VISUAL ELEMENTS:**
        - **Ground:** **Red Dirt (Sanarm Chai)** mixed with dry patchy grass. Uneven surface.
        - **Market:** Sea of **Striped Canvas Parasols** (Red/White/Blue).
        - **Props:** **Light Blue Wooden Pushcarts** (Sugarcane). Cardboard boxes on the ground.
        - **Sky:** **Thai Kites** (Snake, Chula, Pakpao) flying.
        - **Backdrop:** Grand Palace (White walls, Gold spires).
    """,

    "National Museum": """
        **TASK:** Photorealistic Reconstruction of National Museum (1960).

        **VISUAL ELEMENTS:**
        - **Atmosphere:** "Temple in the Forest". Quiet, overgrown, ancient.
        - **Building:** Traditional Thai style. Walls are **Off-White with Heavy Black Mold**. Dark weathered roof tiles.
        - **Landscape:** **Dense Trees** casting deep shadows.
        - **Ground:** **Dirt paths/Gravel**. Unpaved.
        - **Fence:** **Spearhead Iron Fence** (Black/Rusty).
    """
}

# --- 3. Helper Functions ---

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    return genai.Client(api_key=api_key)

def step1_analyze(client, img_bytes):
    # อัปเดต Prompt Analyze จาก Code 2
    prompt = """
    Analyze the precise geometry, camera angle, and structural layout of this image.
    Identify the main building outlines, the vanishing point, and the horizon line.
    We need to preserve this exact composition for a strict image-to-image transformation.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # หรือ gemini-2.0-flash-exp ตามที่มี
            contents=[prompt, types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")]
        )
        return response.text
    except Exception as e:
        print(f"Analysis Error: {e}")
        return "Keep original perspective rigid."

def step2_generate(client, structure_desc, location_key, original_img_bytes):
    specific_prompt = LOCATION_PROMPTS.get(location_key, "")
    
    # อัปเดต Final Prompt Logic จาก Code 2 (Kodachrome Era)
    final_prompt = f"""
    {specific_prompt}
    
    **GEOMETRY & COMPOSITION CONSTRAINT:**
    - Reference Image Analysis: {structure_desc}
    - **DO NOT** change the camera angle, lens distortion, or the position of main buildings.
    - The output must layer perfectly over the original image geometry.

    **VISUAL AESTHETICS (KODACHROME ERA):**
    - **Film Stock:** Imitate **Kodachrome 64** or **Ektachrome** slide film.
    - **Color Grading:** Warm, slightly yellow-red cast, rich greens, high contrast shadows (Tropical Hard Light).
    - **Texture:** Add subtle **film grain**, slight softness (no digital sharpening).
    - **Realism:** Avoid "AI smoothness" or "plastic skin". Surfaces should look dusty, weathered, and lived-in.
    """
    
    try:
        response = client.models.generate_content(
            model="nano-banana-pro-preview", 
            contents=[
                final_prompt, 
                types.Part.from_bytes(data=original_img_bytes, mime_type="image/jpeg")
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                temperature=0.4 # อัปเดตเป็น 0.4 ตาม Code 2
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
# Route 1: สำหรับ Verify อย่างเดียว (เร็ว) (คงเดิมจาก Code 1)
@app.route('/verify', methods=['POST'])
def verify_image_route():
    temp_path = None
    try:
        if 'image' not in request.files or 'location' not in request.form:
            return jsonify({'error': 'Missing data'}), 400
        
        file = request.files['image']
        location_th = request.form['location']
        
        # รับค่าภาษาจาก Frontend (ถ้าไม่ส่งมา Default เป็น TH)
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
                 selected_name = LOCATION_MAPPING_TH_TO_EN.get(location_th, location_th)
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

# Route 2: สำหรับ Generate อย่างเดียว (ช้า) (คงเดิมจาก Code 1 แต่ Logic ภายในเรียกใช้ฟังก์ชันใหม่)
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