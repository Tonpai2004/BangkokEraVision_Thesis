from flask import Flask, request, jsonify
import os
import base64
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
from flask_cors import CORS

# Import Classifier (คอมเม้นต์ไว้ก่อน เพื่อ Bypass)
# from classifier import classify_image 

# --- 1. Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app)

# --- 2. Historical Data Configuration ---
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

# --- The Master Prompt Database (UPDATED PROMPTS) ---
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

    # 1. ศาลาเฉลิมกรุง: ลบตึกรอบข้าง เน้นโรงหนัง รักษาป้ายชื่อเดิม
    "Sala Chalermkrung": """
        **TASK:** Create a photorealistic color photograph of Sala Chalermkrung Theatre in Bangkok, circa 1967.
        
        **STRUCTURE LOCK (EXTREME PRIORITY):** - **THE ROOF SIGN:** The wire-frame metal structure reading "ศาลาเฉลิมกรุง" MUST remain 100% IDENTICAL to the input. DO NOT change, warp, or translate the text.
        - **THEATER SHAPE:** Keep the original architectural form of the theater.

        **ISOLATION INSTRUCTION (CRITICAL):**
        - **REMOVE SIDE BUILDINGS:** Any buildings visible to the immediate left or right of the theater must be removed, lowered significantly, or blurred out. The theater must be the undisputed dominant structure.
        - **CLEAR SKY:** Remove all utility poles, electrical wires, and cables crossing the sky.
        - **NO TALL NEIGHBORS:** Do not allow any modern skyscrapers or tall structures to peek from behind.

        **THE MOVIE POSTER INJECTION:**
        - **Action:** Overlay a massive, hand-painted oil cut-out billboard on the front facade.
        - **Poster Content:** A Thai movie titled "**บางกอกทวิกาล**".
        - **Visuals:** 1. Muscular man in suit with glasses. 2. Slim man with middle-part hair. 3. Text "Tor-Tum".
        - **Style:** Hand-painted Thai cinema art.

        **STREET CONTEXT:**
        - **Road:** Asphalt road. **NO TRAMS. NO TRACKS.** - **Vehicles:** 2-3 Vintage Taxis (Fiat/Austin). 
        - **Crowd:** Thai teenagers in 60s fashion walking.
    """,

    # 2. เสาชิงช้า: ปรับบ้านเรือนรอบข้างเป็นวิถีชุมชน
    "Giant Swing": """
        **TASK:** Photorealistic Reconstruction of The Giant Swing (1965).
        **STRUCTURAL LOCK:** Keep the exact perspective of the Swing and Wat Suthat.

        **VISUAL ELEMENTS:**
        - **The Swing:** Vibrant Red Teak Logs on a **Raised Stone Plinth**.
        - **Traffic Rule:** Traffic goes AROUND the plinth. **NO vehicles under the swing.**
        - **Vehicles:** Vintage cars, Samlors (Three-wheeled bikes). **NO TRAMS.**

        **SURROUNDING COMMUNITY (CONTEXT):**
        - **Architecture:** The surrounding shop houses must be strictly **1960s Bangkok Style** (Sino-Portuguese shophouses mixed with wooden row houses). 
        - **Condition:** Weathered, lived-in, earthy tones (cream, light yellow, wood). 
        - **Roofing:** Clay tiles or rusted corrugated iron. 
        - **Road:** Rough asphalt or paved stone, dusty.
    """,

    # 3. เยาวราช: รถรางชิดขอบ ป้ายเขียนมือภาษาไทย ไม่ฉูดฉาด
    "Yaowarat": """
        **TASK:** Photorealistic Reconstruction of Yaowarat Road (1968).
        
        **VISUAL ELEMENTS:**
        - **TRAM SYSTEM:** - **Position:** The Tram MUST run **CLOSE TO THE SIDEWALK/CURB**, NOT in the middle of the road.
            - **Type:** Open-sided 1960s Bangkok Tram.
        
        **SIGNAGE & ATMOSPHERE (STRICT):**
        - **Sign Style:** **Hand-painted wooden or metal signs**. Cloth banners hanging vertically.
        - **Lighting:** **NO NEON GLOW.** NO LED. Muted colors (Red, Gold, Black).
        - **Density:** Signs should not be overly dense or cluttered like modern times.
        - **TEXT RULE:** All visible text must be **THAI SCRIPT** (ภาษาไทย) or Chinese characters. NO English.
        
        **ARCHITECTURE:**
        - Old Sino-Thai shophouses. 2-3 stories high. 
        - Weathered concrete.
        - **Traffic:** Vintage trucks, rickshaws.
    """,

    # 4. ข้าวสาร: ย่านค้าข้าว เงียบสงบ ไม่ใช่ถนนท่องเที่ยว
    "Khaosan Road": """
        **TASK:** Photorealistic Reconstruction of Bang Lamphu / Khaosan Road (1962).
        **CONTEXT:** A quiet **Rice Trading Residential Community**. 
        **NEGATIVE PROMPT:** Tourist, Backpacker, Bar, Club, Beer, English Sign, Neon, Party.

        **VISUAL ELEMENTS:**
        - **Architecture:** **Wooden Row Houses** (2 stories) with "Baan Fiam" (folding wooden doors). 
        - **Trade:** Piles of **Hemp Rice Sacks** (White/Brown) stacked in front of shops. 
        - **Ground:** Dusty street, traces of white rice dust. 
        - **Signs:** Simple wooden signs in **THAI LANGUAGE** (e.g., "หจก. ข้าวสาร").
        - **Vibe:** Domestic, quiet, bicycle tires, children playing, old men sitting.
    """,

    # 5. ป้อมพระสุเมรุ: เก่า ทรุดโทรม เปลี่ยนสนามหญ้าเป็นคลอง/ดิน
    "Phra Sumen Fort": """
        **TASK:** Photorealistic Reconstruction of Phra Sumen Fort (1960).
        
        **THE FORT CONDITION:**
        - **Texture:** The white plaster must look **aged, stained with black mold, and green moss**. 
        - **Structure:** The top battlements may look slightly crumbled or imperfect (not pristine renovation).

        **SURROUNDINGS (CRITICAL REPLACEMENT):**
        - **IF GRASS IS DETECTED:** Replace all green manicured lawns/parks with **DIRT GROUND** or **CANAL WATER**.
        - **Road side:** Rough asphalt/dirt road.
        - **Community:** Ramshackle wooden houses built close to the fort wall. Lived-in but not completely slum-like.
        - **River side:** Muddy banks, traditional boats.
    """,

    # 6. สนามหลวง: ตลาดไม่อัดแน่น ว่าวน้อยลง วังเก่า
    "Sanam Luang": """
        **TASK:** Photorealistic Reconstruction of Sanam Luang (Weekend Market 1968).

        **VISUAL ELEMENTS:**
        - **Market Layout:** Stalls are **spaced out**, not jammed together. 
        - **Stall Type:** Simple canvas parasols (Red/White/Blue) and wooden tables.
        - **Merchandise:** Old books, amulets, sugarcane juice, traditional food.
        - **The Sky:** A **FEW** Thai Kites (Chula/Pakpao) flying (do not fill the whole sky).
        - **Backdrop (Grand Palace):** The walls must look aged (Off-white/Yellowish), gold spires slightly dulled by time. **NO SCAFFOLDING.**
        - **Ground:** Red dirt (Sanarm Chai) mixed with patches of dry grass.
    """,

    # 7. พิพิธภัณฑ์: เน้นหน้าอาคาร ไม่โทรมเกินไป แต่เก่าสมจริง
    "National Museum": """
        **TASK:** Photorealistic Reconstruction of National Museum Bangkok (1960).
        
        **VISUAL ELEMENTS:**
        - **Viewpoint:** Focus on the **Front Facade** and the immediate courtyard.
        - **Building Condition:** Dignified but aged. 
            - Walls: Off-white with natural weathering/rain stains (not dirty, just old).
            - Roof: Darkened tiles.
        - **Context:** Large trees providing shade (Temple in forest vibe).
        - **Ground:** Gravel paths, well-swept but unpaved.
        - **Fence:** Black iron spearhead fence (slightly rusted).
        - **Atmosphere:** Quiet, scholarly, ancient.
    """
}

# --- 3. Helper Functions (Retry Logic Included) ---

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    return genai.Client(api_key=api_key)

def step1_analyze(client, img_bytes):
    prompt = """
    Analyze the precise geometry, camera angle, and structural layout of this image.
    Identify the main building outlines, the vanishing point, and the horizon line.
    We need to preserve this exact composition for a strict image-to-image transformation.
    """
    
    # --- Retry Logic (3 Attempts) ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=[prompt, types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")]
            )
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "503" in error_msg:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Analysis Busy (Attempt {attempt+1}/{max_retries}): {error_msg} -> Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                print(f"Analysis Error: {e}")
                break
    
    return "Keep original perspective rigid."

def step2_generate(client, structure_desc, location_key, original_img_bytes):
    specific_prompt = LOCATION_PROMPTS.get(location_key, "")
    
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
    
    # --- Retry Logic (3 Attempts) ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="nano-banana-pro-preview", 
                contents=[
                    final_prompt, 
                    types.Part.from_bytes(data=original_img_bytes, mime_type="image/jpeg")
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    temperature=0.4
                )
            )
            
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            
            print(f"⚠️ Warning: Model returned no image (Attempt {attempt+1})")
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "503" in error_msg:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Generation Busy (Attempt {attempt+1}/{max_retries}): {error_msg} -> Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                print(f"Generation Error: {e}")
                return None
                
    return None

LOCATION_MAPPING_EN_TO_TH = {v: k for k, v in LOCATION_MAPPING_TH_TO_EN.items()}

# --- 4. Routes ---

@app.route('/verify', methods=['POST'])
def verify_image_route():
    try:
        if 'image' not in request.files or 'location' not in request.form:
            return jsonify({'error': 'Missing data'}), 400
        
        file = request.files['image']
        location_th = request.form['location']
        
        print(f"🚧 DEBUG MODE: Skipping classification for {location_th}. Assuming valid.")
        
        detected_place = LOCATION_MAPPING_TH_TO_EN.get(location_th, "Debug Place")
        score = 0.99
        is_valid = True
        
        analysis_report = {
            "status": "success",
            "detected_place": detected_place,
            "score": round(score * 100, 2),
            "is_valid": is_valid
        }
        
        return jsonify({
            'status': 'success',
            'analysis_report': analysis_report
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_image_route():
    try:
        print("🚀 Starting Generation Process...")
        file = request.files['image']
        location_th = request.form['location']
        
        img_bytes = file.read()
        prompt_key = LOCATION_INFO[location_th]['prompt_key']
        client = get_client()
        
        print(f"📸 1. Analyzing Structure for: {location_th}...")
        structure = step1_analyze(client, img_bytes)
        print("✅ Structure Analysis Complete.")
        
        print(f"🎨 2. Generating Image with {prompt_key} prompt...")
        result_bytes = step2_generate(client, structure, prompt_key, img_bytes)
        
        if result_bytes:
            print("🎉 Generation Success! Sending image back to frontend.")
            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            return jsonify({
                'status': 'success',
                'image': f"data:image/png;base64,{result_b64}",
                'location_name': location_th,
                'description': LOCATION_INFO[location_th]['desc_60s']
            })
        else:
            print("❌ Generation Failed: No image returned (Exhausted retries).")
            return jsonify({'error': 'AI Model Overloaded. Please try again in 1 minute.'}), 503
            
    except Exception as e:
        print(f"❌ Gen Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return "✅ Backend Server is Running! Ready to accept /verify and /generate requests."

if __name__ == '__main__':
    app.run(debug=True, port=5000)