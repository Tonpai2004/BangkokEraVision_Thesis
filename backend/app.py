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

# --- 2. Historical Data Configuration (เหมือนเดิมเป๊ะ) ---
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
        **STRUCTURE LOCK (CRITICAL):** - **KEEP THE ROOF SIGN:** The wire-frame metal structure reading "ศาลาเฉลิมกรุง" on the roof MUST remain structurally identical to the input image.
        - **Focus on the Main Building:** The theater building itself is the primary focus.

        **CLEAN SURROUNDINGS INSTRUCTION (CRITICAL):**
        - **REMOVE ALL UTILITY POLES AND WIRES:** The sky and street view must be completely clear of electrical wires, cables, and poles.
        - **MINIMIZE ADJACENT BUILDINGS:** The buildings immediately to the left and right of the theater should be less prominent, smaller, or partially obscured to emphasize the theater.
        - **REDUCE NATURE:** Remove or significantly reduce large trees and foliage that block the view of the building. Keep greenery sparse.
        
        **THE MOVIE POSTER INJECTION (MANDATORY - KEEP THIS):**
        - **Action:** Overlay a massive, hand-painted oil cut-out billboard on the front facade (covering the entrance area).
        - **Poster Content:** A Thai movie titled "**บางกอกทวิกาล**" (Bangkok EraVision).
        - **Visuals on Poster:**
            1. Actor 1: A **MUSCULAR, bulky man** in a suit wearing **GLASSES** (M.R. Mod-Or-Por style).
            2. Actor 2: A **SLIM, handsome man** in a suit with **Middle-part hair** (Nattapat style).
            3. Director credit: "Tor-Tum".
        - **Style:** 1960s Thai Cinema Art, vivid colors, dramatic brush strokes.

        **1960s STREET LEVEL:**
        - **Building Surface:** Weathered Creamy White concrete walls with rain stains.
        - **Traffic:** Asphalt road. **NO TRAMS. NO TRAM TRACKS.** Only a few Vintage Taxis (Fiat/Austin) parked or slowly driving.
        - **Crowd:** Teenagers in 60s fashion (Elvis hair, high buns) walking on the pavement.
        
        **NEGATIVE PROMPT:** LED displays, Modern glass doors, BTS, Modern cars, **Tram, Tram tracks, electrical wires, utility poles, dense trees, tall prominent surrounding buildings**.
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

# --- 3. Helper Functions (ที่มีการแก้ Retry Logic) ---

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
    
    # --- Retry Logic (พยายาม 3 ครั้ง) ---
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
            # ถ้าเป็น error 429 หรือ 503 ให้รอแล้วลองใหม่
            if "429" in error_msg or "503" in error_msg:
                wait_time = (2 ** attempt) + random.uniform(0, 1) # Exponential backoff: 1s, 2s, 4s...
                print(f"⚠️ Analysis Busy (Attempt {attempt+1}/{max_retries}): {error_msg} -> Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                # ถ้าเป็น error อื่นที่ไม่ใช่ server busy ให้ยอมแพ้เลย
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
    
    # --- Retry Logic (พยายาม 3 ครั้ง) ---
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
            
            # ถ้า Gen ผ่านแต่ไม่มีรูป ให้ลองใหม่
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
            # ส่ง 503 กลับไปบอก Frontend ว่า Server ยังไม่ว่างจริงๆ
            return jsonify({'error': 'AI Model Overloaded. Please try again in 1 minute.'}), 503
            
    except Exception as e:
        print(f"❌ Gen Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return "✅ Backend Server is Running! Ready to accept /verify and /generate requests."

if __name__ == '__main__':
    app.run(debug=True, port=5000)