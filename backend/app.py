from flask import Flask, request, jsonify
import os
import base64
from dotenv import load_dotenv
from google import genai
from google.genai import types
from flask_cors import CORS

# --- 1. Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app)  # อนุญาตให้ Frontend (Next.js) เรียกใช้งาน API ได้

# --- 2. Historical Data Configuration (Bangkok EraVision 1960s) ---

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

# --- 3. The Master Prompt Database (Strict 1960s Context) ---

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
        - **Props:** Piles of **Hemp Rice Sacks** (Gunny sacks) stacked in front of shops. White rice dust on the floor.
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

# --- 4. Helper Functions ---

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    return genai.Client(api_key=api_key)

def step1_analyze(client, img_bytes):
    """
    วิเคราะห์โครงสร้างภาพเพื่อรักษา Perspective ให้แม่นยำ
    """
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
    
    # Master Instruction: ผสานภาพจริงกับบริบทปี 60s
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

# --- 5. Routes ---
@app.route('/process', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files or 'location' not in request.form:
            return jsonify({'error': 'Missing data'}), 400
        
        file = request.files['image']
        location = request.form['location']
        
        if location not in LOCATION_INFO:
            return jsonify({'error': 'Invalid location'}), 400

        prompt_key = LOCATION_INFO[location]['prompt_key']
        img_bytes = file.read()
        client = get_client()
        
        # Step 1: Analyze Structure
        structure = step1_analyze(client, img_bytes)
        
        # Step 2: Generate
        result_bytes = step2_generate(client, structure, prompt_key, img_bytes)
        
        if result_bytes:
            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            return jsonify({
                'image': f"data:image/png;base64,{result_b64}",
                'location_name': location,
                'description': LOCATION_INFO[location]['desc_60s']
            })
        else:
            return jsonify({'error': 'Generation failed'}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)