from xmlrpc import client
from flask import Flask, request, jsonify, send_from_directory
import os
import base64
import time
import random
import pickle
import numpy as np
import tempfile
import datetime
import requests # จำเป็นสำหรับการยิง Runway
from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer
from PIL import Image
import io
from dotenv import load_dotenv
from google import genai
from google.genai import types
from flask_cors import CORS
from classifier import classify_image

# --- 1. Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app)

# ==========================================
# 💾 AUTO-SAVE SYSTEM
# ==========================================
HISTORY_FOLDER = os.path.join(os.path.dirname(__file__), 'generated_history')
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'generated_videos')

if not os.path.exists(HISTORY_FOLDER): os.makedirs(HISTORY_FOLDER)
if not os.path.exists(VIDEO_FOLDER): os.makedirs(VIDEO_FOLDER)

# ==========================================
# 🧠 AI MEMORY LOADING
# ==========================================
print("⏳ Initializing System...")
SEARCH_MODEL = None
LOCATION_INDICES = {}

def load_ai_memory():
    global SEARCH_MODEL, LOCATION_INDICES
    try:
        print("👁️  Loading CLIP Vision Model...")
        # SEARCH_MODEL = SentenceTransformer('clip-ViT-L-14')
        SEARCH_MODEL = SentenceTransformer('clip-ViT-B-32')
        
        indices_path = os.path.join(os.path.dirname(__file__), 'indices')
        if os.path.exists(indices_path):
            print("🧠 Loading Location Indices...")
            for filename in os.listdir(indices_path):
                if filename.endswith('.pkl'):
                    location_key = filename.replace('.pkl', '')
                    with open(os.path.join(indices_path, filename), 'rb') as f:
                        LOCATION_INDICES[location_key] = pickle.load(f)
                    print(f"  - Loaded Memory: {location_key}")
            print("✅ AI System Ready: Smart Match Enabled!")
        else:
            print("⚠️ 'indices' folder not found. ML features will be disabled.")
            
    except Exception as e:
        print(f"⚠️ Warning: AI System Failed. ({e})")
        SEARCH_MODEL = None

load_ai_memory()

# ==========================================
# 📍 MAPPINGS & DATA
# ==========================================

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

LOCATION_MAPPING_EN_TO_TH = {v: k for k, v in LOCATION_MAPPING_TH_TO_EN.items()}

LOCATION_KEY_MAP = {
    "อนุสาวรีย์ประชาธิปไตย": "Democracy Monument",
    "ศาลาเฉลิมกรุง": "Sala Chalermkrung Royal Theatre",
    "เสาชิงช้า & วัดสุทัศน์": "Giant Swing – Wat Suthat",
    "เยาวราช": "Yaowarat (Chinatown)",
    "ป้อมพระสุเมรุ": "Phra Sumen Fort – Santichaiprakarn Park",
    "สนามหลวง": "Sanam Luang (Royal Field)",
    "พิพิธภัณฑสถานแห่งชาติ": "Phra Nakhon National Museum"
}

LOCATION_INFO = {
    "อนุสาวรีย์ประชาธิปไตย": { "prompt_key": "Democracy Monument", "desc_60s": "ตัวอนุสาวรีย์สีครีมปูนชัดเจน พานรัฐธรรมนูญสีโลหะรมดำ ประตูสีแดงชาด อาคารราชดำเนินสีส้มอิฐ ถนนกว้างไร้เส้นจราจร" },
    "ศาลาเฉลิมกรุง": { "prompt_key": "Sala Chalermkrung", "desc_60s": "โรงมหรสพหลวงยุคโก๋หลังวัง อาคารสีขาวครีมที่มีคราบฝน โดดเด่นด้วย 'คัตเอาท์ยักษ์วาดมือ' เรื่อง 'บางกอกทวิกาล' หน้าโรง พร้อมดารานำชายสองสไตล์ บรรยากาศรอบข้างคึกคักด้วยวัยรุ่นยุค 60s รถแท็กซี่เฟียต และรถรางวิ่งผ่านหน้าโรง" },
    "เสาชิงช้า & วัดสุทัศน์": { "prompt_key": "Giant Swing", "desc_60s": "เสาชิงช้ามีฐานปูนชัดเจน รถวิ่งอ้อมฐานห้ามลอดผ่าน ไม่มีรถราง ถนนลูกรัง วัดสุทัศน์ดูเก่าแก่ตามกาลเวลา" },
    "เยาวราช": { "prompt_key": "Yaowarat", "desc_60s": "รถรางโปร่งแบบเปิดข้างวิ่งชิดขอบทาง ป้ายร้านค้าแนบตึกไม่ยื่นรกตา ตึกแถวเก่าแก่ บรรยากาศการค้าขายแบบดั้งเดิม" },
    "ถนนข้าวสาร": { "prompt_key": "Khaosan Road", "desc_60s": "ชุมชนบางลำพูย่านค้าข้าวสาร ห้องแถวไม้ประตูบานเฟี้ยม มีกระสอบข้าววางหน้าร้าน บรรยากาศเงียบสงบแบบย่านพักอาศัย ไม่ใช่ย่านท่องเที่ยว" },
    "ป้อมพระสุเมรุ": { "prompt_key": "Phra Sumen Fort", "desc_60s": "ป้อมสีขาวขุ่นทรุดโทรมมีคราบตะไคร่ บ้านเรือนไม้สังกะสีสร้างเบียดเสียดติดตัวป้อม ไม่เห็นมุมคลองมากนัก ไม่มีสวนสาธารณะ" },
    "สนามหลวง": { "prompt_key": "Sanam Luang", "desc_60s": "ตลาดนัดสนามหลวง พื้นดินแดงปนหญ้าแห้ง ร่มผ้าใบสีขาวสลับแดง/น้ำเงิน รถเข็นขายน้ำอ้อยสีฟ้า ว่าวไทยลอยเต็มฟ้า ฉากหลังวัดพระแก้ว" },
    "พิพิธภัณฑสถานแห่งชาติ": { "prompt_key": "National Museum", "desc_60s": "อาคารทรงไทยสีขาวหมองมีคราบตะไคร่ดำ สภาพรกรั้วด้วยต้นไม้ใหญ่เหมือนวัดป่า ถนนหน้าพระธาตุลาดยางเงียบสงบ รั้วเหล็กดัดหัวลูกศร" }
}

# --- THE MASTER PROMPT DATABASE (V.17 - FLAWLESS & HISTORICAL) ---
LOCATION_PROMPTS = {
      
    # "Democracy Monument": """
    #     TASK: Create a HYPER-REALISTIC photograph of the Democracy Monument area in Bangkok, circa 1960s. The image must look like authentic vintage film photography.

    #     1. ABSOLUTE PERSPECTIVE LOCK (CRITICAL):
    #     - Use the uploaded image as a rigid geometric skeleton for the main monument's shape. 
    #     - DO NOT rotate, zoom, or shift the camera angle. The alignment must be perfect.

    #     2. THE MONUMENT (HISTORICAL COLORS & TEXTURE):
    #     - CONSTITUTION TRAY (TOP): Dark bronze or aged black metallic finish. (Absolutely NO gold).
    #     - TURRET DOORS: Vibrant Thai Red (See-Daeng-Chad) lacquer finish.
    #     - WINGS & BODY: Weathered, stained cream or off-white stucco. Show visible age, humidity stains, and subtle dirt streaks. 
    #     - BASE: Rough, aged grey concrete with heavy black iron chains looping around.

    #     3. ARCHITECTURAL OVERHAUL (THE 1960s RATCHADAMNOEN LOOK):
    #     - SKYLINE PURGE: STRICT HEIGHT LIMIT. Delete all modern high-rises, skyscrapers and building. 
    #     - No building in the background can be taller than 3-4 stories. The horizon must be open sky.
    #     - SHOPHOUSES: Replace all modern buildings with **1960s Thai Art Deco Building but the building inside monument roundabout will turn into 1-2 stories shophouse rows**.
    #     - ART DECO DETAILS: Include rounded building corners, vertical decorative concrete fins (fins), recessed balconies, and geometric window grilles.
    #     - COLORS: Use a palette of **Aged Terracotta/Brick Orange**. Paint must look sun-faded and slightly peeled.

    #     4. STREET & ATMOSPHERE:
    #     - THE ROAD: Wide, worn asphalt avenue with NO lane markings and NO zebra crossings.
    #     - VINTAGE TRAFFIC: Only a few 1950s-1960s vintage cars (e.g., Opel Kadett (1300cc), Toyota KE10, or Mercedes-Benz W110) driving around the roundabout and cars turn in the same way.
    #     - ENVIRONMENT: Remove all modern signage, LED screens, billboards, and air conditioning units.

    #     NEGATIVE PROMPT: 
    #     gold constitution, white doors, modern skyscrapers, glass towers, high-rise buildings, modern cars, heavy traffic, modern road signs, zebra crossings, air conditioners, satellite dishes, clean pristine buildings, 3d render look, digital painting style, unrealistic lighting.
    # """,

    "Democracy Monument": """
        TASK: Create a HYPER-REALISTIC photograph of Democracy Monument in Bangkok (1960s). 
        The final image must preserve the historical dignity of the site with absolute structural integrity.

        1. PERSPECTIVE & SEMANTIC LOCK (CRITICAL):
        - BLUEPRINT: Use [IMAGE 1] for camera angle and placement. 
        - WING INTEGRITY: Maintain all 4 wings surrounding the central turret exactly as positioned in the input. 
        - DO NOT merge wings into background buildings. They must be isolated, standalone structures.

        2. THE MONUMENT (HISTORICAL ACCURACY):
        - CONSTITUTION TRAY (TOP): Aged metallic black or dark bronze (NO gold).
        - TURRET DOORS: Vibrant Thai Red (See-Daeng-Chad).
        - WINGS & BODY: Weathered cream stucco with visible humidity stains and age patina. 
        - BASE: Grey concrete with heavy black iron chains looping between the wings.

        3. ARCHITECTURAL TRANSFORMATION (RATCHADAMNOEN PERIMETER):
        - SKYLINE PURGE: Erase ALL modern skyscrapers and glass towers from the background. 
        - SHOPHOUSES: Replace buildings BEHIND the monument with 1960s 2-4 story Thai Art Deco buildings that perfectly follow the outer ring of the roundabout..
        - LOCATION FIX: Shophouses MUST stay along the street perimeter, NOT inside the monument base area.
        - ART DECO STYLE: Rounded corners, vertical concrete fins, recessed balconies, and terracotta/brick orange faded paint.

        4. ATMOSPHERE & TRAFFIC:
        - ROAD: Wide and aged asphalt with NO lane markings. 
        - VEHICLES: 2-3 vintage cars (Opel Kadett (1300cc), Toyota KE10, or Mercedes-Benz W110) driving around the roundabout and cars turn in the same way.
        - CLEANUP: Remove LED signs, modern street lamps, and air conditioners.

        NEGATIVE PROMPT: 
        gold constitution, white doors, buildings touching the monument wings, buildings inside the monument base, modern skyscrapers, glass towers, modern cars, zebra crossings, clean pristine look.
    """,
    
    "Sala Chalermkrung": """
    TASK: TRANSFORM into a maintained, dignified, hyper-photorealistic color photograph of Sala Chalermkrung Theatre, circa 1967. Strictly adhere to the historical and architectural reality of the 1960s as seen in the provided reference images. NO over-creation; NO structural additions.

    🔒 0. MAIN STRUCTURE RIGIDITY LOCK (NEW & CRITICAL - V.22 Update):
    The entire Art Deco concrete frame, central body, columns, and dome profile (if visible) of the main Sala Chalermkrung building must remain structurally unchanged. The input geometry is a rigid Map. DO NOT alter the building's Fundamental Art Deco geometry, scale, or subject positioning. Maintained Dignity: The concrete surfaces must show weathering (Krap-fon) in a way that looks maintained but aged, with a visible aged patina reflecting its maintained royal connection, not dilapidated or crumbling. HISTORICAL DETAILING ONLY: Any updates within the main building's concrete frame must be period-accurate detailing changes, not structural changes. Doors within visible archways must be the Original 1930s/1960s Art Deco service doors, not modern glass ones. If windows are not covered by posters, they must be period-appropriate casement or multi-pane styles (ช่องหน้าต่างบานกระทุ้งโบราณ).

    🔒 1. ABSOLUTE SIGNAGE NON-TRANSFORM LOCK (CRITICAL):
    The large "SALA CHALERMKRUNG" roof sign (Thai and English letters) is under an ABSOLUTE NON-TRANSFORM LOCK. DO NOT alter its font, geometry, structural frame, or placement. It must remain 100% pixel-perfect identical to the modern input image.

    🎭 2. THE IMPENETRABLE POSTER WALL (EXACTLY 3 PANELS - FACADE MASKING - CRITICAL ADDITION):
    Locate the modern glass window lines on the ground and middle floors of the theatre's central angled facade. Install EXACTLY THREE (3) massive, impenetrable, hand-painted movie poster panels scaled to create a flawless wall of art, ensuring zero trace of glass, glass slivers, or glass reflections is visible on the covered facade levels. Place ONE poster on the center facade, ONE on the left-angled facade, and ONE on the right-angled facade. POSTER ART (MUST ADHERE): The three posters may contain different compositions, but each must depict only the same two gentlemen set with thick hair on their surface: one in a white shirt and glasses, the other without glasses. Hand-painted vintage Thai art style (billboard style), not digital. The only text allowed is the Thai title "บางกอกทวิกาล" and period Thai text. No posters on plain walls.

    🏛️ 3. LEFT WING EXTENSION REVEAL & RIGHT SIDE RESTORATION (HISTORICAL CONTINUITY - V.24 Update):
    Flatten and simplify any modern attachments on the secondary building sections immediately to the left and right of the main theatre. REVEAL AND RECONSTRUCT LEFT EXTENSION (V.23 Update): Transform the building section to the immediate left of the main theatre. Surgically erase all left-side trees and modern attachments to fully reveal the building's historically extend. Reconstruct this area as a massive, elongated 3-story Art Deco masonry block seamlessly matching the main building. CRITICAL ARCHITECTURAL DETAILS FOR LEFT WING: It MUST feature a continuous, flat concrete awning (กันสาดคอนกรีตแบนเรียบแนวยาว) running horizontally to separate the ground floor from the upper levels. The upper floors must feature recessed vertical panels or tall vertical slit windows (ร่องเว้าหรือช่องหน้าต่างแนวตั้งลึก) containing rows of strictly closed period multi-pane casement windows with dark weathered frames. The ground floor beneath the awning must consist of repetitive vintage wooden folding doors or metal shutter doors (บานเฟี้ยมหรือประตูเหล็กยืดโบราณ) acting as theatre exits. The wall texture must be weathered cream stucco matching the main tower perfectly. RIGHT SIDE (Ground Floor - V.24 Update): ERASE all modern cafes, umbrellas, and modern storefronts from the right side extension. Reconstruct as a solid, perfectly flat cream stucco wall. CRITICAL ARCHITECTURAL DETAILS FOR RIGHT WING: It MUST feature a continuous, orderly horizontal row of strictly closed vintage dark-framed multi-pane hopper/casement windows (ช่องหน้าต่างบานกระทุ้งกระจกแบ่งช่องลูกฟักแบบโบราณ). These windows must be set flush or slightly recessed into the wall without any protruding modern frames or decorations. Above this row of windows, maintain a simple, subtle concrete eyebrow canopy (กันสาดคอนกรีตแผ่นเรียบเล็กๆ) separating the ground floor from the upper level. Absolutely DO NOT add any creative architectural elements, new signs, or modern structures to this right wing; it must remain a historically accurate, plain utilitarian Art Deco extension flawlessly integrated into the historical wing.

    🏘️ 4. DIGNIFIED 1960s SURROUNDINGS & AMBIANCE (CRITICAL ADDITION - V.22 Update):
    Do not invent creative architecture. Buildings further left, right, and in the background must strictly reflect the historical context of the provided reference images and the 1960s Charoen Krung district (plain, utilitarian masonry commercial shophouses/คูหาอาคารปูน 2-3 ชั้น), with strictly closed windows on all floors. Background Skyline (V.20 Update): Delete 100 percent of modern skyscrapers and glass high-rises from the furthest horizon and replace with a seamless view of period-appropriate traditional 2-3 story masonry commercial shophouses. The skyline must be traditional low-rise. Sidewalks & Ground Level (V.20 Update): Reconstruct sidewalks as wide, maintained clear Aged Concrete surfaces (not new paving or tarpaulin-covered) with period-appropriate props (old newspaper stands, vendors with shoulder poles), ensuring they are completely free of modern chairs, modern awnings, and modern clutter. Modern Removal (V.20 Update): DELETE 100% of modern street lamps, bank logos, ATMs, LEDs, satellite dishes, and modern wiring. Bundle wires together and hide them behind shophouse eaves or remove completely from plain view. People: Maintain a sparse crowd of pedestrians walking in natural 1960s Thai fashion (men in tucked-in shirts, women in mod-dresses) near the entrance sidewalks.

    🚗 5. EMPTY ROYAL AVENUE (V.20 Update):
    The wide worn asphalt road is majestic and completely EMPTY. Reveal the clean road surface. NO motorized vehicles: no modern cars, no buses, no motorcycles, no tuk-tuks, no taxis. Clear asphalt. Only sparse crowd on sidewalks.

    🎨 6. FILM STYLE: Kodak Kodachrome film (1967), characteristic Kodachrome shift, natural light, soft film grain, high historical fidelity.Maintained dignified atmosphere. Natural afternoon light.

    🔒 7. PERSPECTIVE INTEGRITY LOCK (NEW & CRITICAL - V.20):
    The final image must retain the exact camera angle, subject positioning, and depth of field of [IMAGE 1]. Structural alignment between and final result must be pixel-perfect. Ensure no camera rotation or shift. Every architectural vector is locked to.

    NEGATIVE PROMPT: modern cars, traffic, tuk-tuks, altered roof sign, missing sign, 1 poster, 2 posters, 4 posters, visible facade glass, glass reflection on posters, modern display windows, modern attached structures, modern canopies, modern awnings, modern screens, modern lamps, modern utility poles, modern wiring, open windows on any building, new construction look, dilapidated building form, crumbling walls, structural transformation of columns, excessive poster plastering.
    """,

    # "Giant Swing": """

    #     **TASK:** TRANSFORM [IMAGE 1] into a **1960s Phra Nakhon Era** scene using strict structural preservation. **Apply these rules with equal strictness from the immediate foreground to the furthest visible pixel on the horizon.**

    #     **🔒 1. ABSOLUTE GEOMETRY & SPATIAL LOCK (THE "STENCIL" RULE):**
    #     - **FIXED LAYOUT:** The input image is a rigid map. **DO NOT CHANGE THE SPACING** between buildings.
    #     - **PRESERVE GAPS:** If there is empty sky or space between buildings in the source, **KEEP IT EMPTY**. Do not fill gaps with new shophouses.
    #     - **CAMERA FREEZE:** **DO NOT ROTATE. DO NOT ZOOM. DO NOT PAN. OR ENLARGE THE IMAGE** The perspective must perfectly overlay the original image.

    #     **🔄 2. ARCHITECTURAL RE-SKINNING (NO NEW BUILDINGS):**
    #     - **DETECT SKYSCRAPERS:** Identify all modern builiding, skyscrapers/tall buildings in the image, from the nearest to the **farthest point on the horizon**. **Do NOT retain the modern silhouette of distant buildings.** **Surgically DELETE** them and replace with **clear blue sky or soft clouds**. No structure should be taller than 2-story building.
    #     - **STRICT TRANSFORMATION:** Detect ALL buildings present. Transform their **surfaces** to match the **1960s COLONIAL STYLE** (SINGLE MASSING of 2-story masonry structures with **rectangle Windows** and **Weathered Cream Stucco**, **Dark Wooden Folding Doors (Ban-Fiam)**, Dark brown **CLOSED HIPPED ROOF** with Clay Tiles. **The roof structure must be a continuous lid with closed triangular ends.**). 
    #     - **HORIZON OVERRIDE:** You MUST **reconstruct the silhouette** of distant buildings; do not simply re-texture them. If a building at the horizon is taller than 2 stories, **You MUST overwrite these pixels with the sky and clouds.**.
    #     - **NO GHOST SILHOUETTES: Do not attempt to re-texture distant tall buildings. If it is not a 2-story shophouse or the Giant Swing, it MUST NOT EXIST. Paint the sky over it completely.
    #     - **VANISHING POINT CLEANUP: At the furthest point of the street, ensure there are NO vertical lines or box shapes peeking out. The sky must meet the shophouse roofline directly.

        
    #     **📍 THE SEMANTIC BOUNDARY RULE:
    #     -TEMPLE ISOLATION: Identify the white masonry perimeter walls (Kamphaeng Kaeo) and the ornate gate structures. These white walls are an ABSOLUTE BARRIER.
    #     -NO OVERLAP: Shophouses and wooden textures MUST NOT touch, cross, or overlap with any white temple walls or religious structures.
    #     - **NO SOLID ENCLOSURE:** Do not render temple side-buildings as closed concrete rooms. They must maintain their "Open Pavilion" identity.
        
    #     **⛩️ 3. THE GIANT SWING (HISTORICAL TWO-TIER BASE):**
    #     - **DUAL-LAYER BASE (CRITICAL):** Render the base structure accurately with **TWO DISTINCT CONCRETE LEVELS**:
    #         1. **The Plinths:** Concrete blocks directly supporting the red teak legs.
    #         2. **The Island Platform:** A **Blank** wide, raised **curbed concrete island (Traffic Island)** that the whole structure sits upon.
    #     - **DECORATION BAN:** The base must be **BARE**, **BLANK**, CLEAN WHITE/GREY CONCRETE**. Absolutely **NO FLOWERS**, no garlands, no fabric wrappings, no pot, and no ornate carvings.

    #     **🛣️ 4. CLEAN ROAD (ZERO VEHICLES):**
    #     - **REMOVE TRAFFIC:** The road must be **MAJESTICALLY EMPTY**. Remove all cars, tuk-tuks, and buses.
    #     - **SURFACE:** Reveal the road surface underneath. Render it as **Clean, Weathered Grey Asphalt**.
    #     - **TRAM TRACKS:** Create a weathered tram tracks that locate **in front of WAT SUTHAT temple** only.

    #     ** 5. LIGHTING & ATMOSPHERE:**
    #     - **Crowd:** Add a few pedestrians in 1960s attire walking on the sidewalk or in front of the temple some standing on the island of giant swing. No one should be on the road.

    #     **⛔ NEGATIVE PROMPT:** modern architectural silhouettes, background blocks, distant urban noise, modern cars, traffic, vehicles, people in middle of road, **added buildings**, **filling gaps**, **crowded skyline**, **flowers on base**, garlands, fantasy decorations, changing angle, **modern windows in distance, air conditioners in background.**

    # """,

    "Giant Swing": """
        **TASK:** RE-TEXTURE [IMAGE 1] into a 1960s scene. 
        **URGENT:** ACT AS A SURFACE-ONLY REPLACEMENT ENGINE. DO NOT RE-COMPOSE.

        **🔒 1. FIXED COORDINATE SYSTEM (PIXEL-PERFECT):**
        - **RIGID BLUEPRINT:** Every edge and line in [IMAGE 1] is a FIXED VECTOR. 
        - **NO CAMERA LIBERTY:** Strictly PROHIBITED from zooming out, changing focal length, or shifting the subject. 
        - **1:1 ALIGNMENT:** The Giant Swing pillars in your result MUST align bit-for-bit with the pillars in [IMAGE 1]. If they are large and cut off at the top in [IMAGE 1], they MUST stay large and cut off at the top in your output.

        **🔄 2. CONTEXTUAL ARCHITECTURAL RE-SKINNING:**
        - **DETECT SKYSCRAPERS:** Erase all modern high-rises/skyscrapers from the nearest to the furthest horizon. Replace with clear sky.
        
        - **CASE A: TEMPLE SIDE DETECTED** (If white walls or ornate roofs are in background):
            - **TEMPLE ISOLATION:** Keep Wat Suthat area intact. White perimeter walls (Kamphaeng Kaeo) are an ABSOLUTE BARRIER.
            - **OPENNESS:** Do NOT fill spaces between temple pillars with solid walls. Keep pavilions **OPEN-AIR**.
            - **TRAM:** Add weathered tram tracks ON THE ROAD directly in front of the temple.

        - **CASE B: CITY HALL / PLAZA SIDE DETECTED** (If modern offices or open plaza appear):
            - **ADMINISTRATIVE STYLE:** Keep the shape of **Bangkok City Hall**. Do not alter their form or add new structures. Only re-texture the surface by applying a little weathering and fading.
            - **OPEN PLAZA:** Keep the Lan Khon Mueang area as an **OPEN CONCRETE FIELD** with a lawn area in front(UNPAVED RED EARTH AND PATCHY DRY GRASS) also have a basketball field in Lan Khon Mueang's area. No modern tiles or LED screens. 
            - **ACTIVITY:** Populate the field with people in 1960s attire. Optionally, add a group of Thai youths in white tank tops playing basketball on the raw field.
            - **NO HALLUCINATION:** Strictly **PROHIBIT** adding temple structures if none exist in [IMAGE 1].

        - **CASE B: CITY HALL / PLAZA SIDE DETECTED** (If modern offices or open plaza appear):
            - **ADMINISTRATIVE STYLE:** Keep the shape of **Bangkok City Hall**. Do not alter their form or add new structures. Only re-texture the surface by applying a little weathering and fading.
            - **THE HYBRID PLAZA (LAN KHON MUEANG):** Transform the modern plaza into a realistic 1960s multi-purpose field:
                1. **THE BASKETBALL COURT:** Render a specific rectangular section as **weathered, rough grey concrete**. Include vintage basketball backboards on poles.
                2. **THE RAW TERRAIN:** A vertical large lawn area and the surrounding areas must be **UNPAVED DIRT** mixed with irregular patches of **DRY, SUN-BLEACHED GRASS**.
                3. **PHYSICAL BOUNDARY:** This plaza must be clearly separated from the Giant Swing island by a wide, clean **grey asphalt road**. Do NOT allow grass or dirt to bleed onto the asphalt.
            - **SOCIAL ACTIVITY:** Populate the concrete court with Thai youths in 1960s white tank tops and dark shorts playing basketball.
            - **NO HALLUCINATION:** Strictly PROHIBIT adding temple structures or ornate gates if none exist in the original [IMAGE 1] background.

        - **GENERAL BUILDINGS:** Transform other structures into **1960s COLONIAL STYLE** (Only 2-story masonry rows, weathered cream stucco, dark wooden folding doors, continuous hipped clay tile roofs).

        **⛩️ 3. THE GIANT SWING (HISTORICAL TWO-TIER BASE):**
        - **PILLARS:** Massive Aged Red Teak.
        - **DUAL-LAYER BASE:** Render accurately with **TWO DISTINCT CONCRETE LEVELS**:
            1. **The Plinths:** Concrete blocks supporting the legs.
            2. **The Island Platform:** A wide, blank, raised **curbed concrete island**.
        - **ZERO VEGETATION RULE:** The entire island platform and the swing plinths must be **100 percent FREE of grass, weeds, moss, or soil**. It must be a sharp, man-made concrete zone with a clean curb.
        - **DECORATION BAN:** BARE CONCRETE ONLY. No flowers, no garlands, no pots.

        **🛣️ 4. CLEAN ROAD & ATMOSPHERE:**
        - **ROAD:** Reveal weathered grey asphalt. **REMOVE ALL TRAFFIC** (cars, buses, tuk-tuks). 
        - **CROWD:** Sparse pedestrians in 1960s attire on sidewalks or the island platform. No one on the road.

        **⛔ NEGATIVE PROMPT:** modern architectural silhouettes, background blocks, modern cars, traffic, people in middle of road, flowers on base, garlands, air conditioners, adding temple to City Hall side, hallucinating Wat Suthat when facing Plaza.
    """,

    "Yaowarat": """
        **TASK:** Create a **PHOTOREALISTIC COLOR PHOTOGRAPH** of Yaowarat Road (1968).
        **LOCK:** Maintain exact building geometry and camera height of [IMAGE 1].

        **📸 1. SPATIAL SCALING & ROAD DOMINANCE (FIXING NARROWNESS):**
        - **ROAD WIDTH INTEGRITY:** Identify the road edges in [IMAGE 1]. You MUST maintain the **EXACT distance** between the left and right building facades. Do NOT encroach the shophouses into the asphalt area.
        - **ASPHALT SCALE:** The road surface must occupy the same pixel percentage as the original. Maintain a wide, expansive asphalt view to prevent the scene from looking cramped.
        - **FROZEN TRIPOD:** No shifting, rotating, or zooming. The perspective must perfectly overlay [IMAGE 1].

        **🏘️ 2. ARCHITECTURAL FACADES:**
        - **REPLACE ALL MODERN BUILDINGS:** 2-4 story Chinese-Colonial shophouses.
        - **TEXTURE:** Weathered off-white/faded grey stucco with heavy soot and rain stains (Krap-fon).
        - **GROUND FLOOR:** Dark **Wooden Folding Doors (Ban-Fiam)**. Ensure the "sidewalk" area is clear and distinct from the road.

        **🔤 3. SIGNAGE HIERARCHY & TYPOGRAPHY (FIXING FONT BALANCE):**
        - **TIER 1 (OVERSIZED VERTICAL SIGNS):** Populate the scene with **Large, Massive Vertical Signs** that hang perpendicular to the buildings. These signs should span 1-2 stories in height.
        - **FONT WEIGHT:** Use **Extra Bold, Thick Strokes** for all Thai and Chinese characters. No thin or delicate fonts.
        - **LEGIBILITY:** Foreground signs like "**ห้างทอง**", "**ร้านยา**", "**โรงแรม**", "**ร้านทอง**", "**ภัตตาคาร**" must be large and prominent.
        - **TIER 2 (STOREFRONT BANNERS):** Horizontal signs above the ground floor doors should be bold and use high-contrast colors (Red/Gold, Yellow/Black).
        - **PATINA:** Signs must look hand-painted with visible aging and weathering. Avoid "perfect" digital-looking text.

        **🚋 4. TRAM & ROAD PHYSICS:**
        - **SINGLE TRACK:** A single weathered tram track on the right side.
        - **YELLOW/RED TRAM:** A wooden open-sided tram that is scaled correctly to the street width.
        - **Trash & Debris:** Add small bits of scattered litter (paper scraps, leaves) and dust along the curb edges and road for realism.
        - **SURFACE:** Used, worn asphalt with realistic debris and dust near the curbs.

        **🚦 5. ATMOSPHERE & CROWD:**
        - **VEHICLE:** NO cars or tuk-tuks. Only **Pedal Samlors** (Rickshaws).
        - **URBAN DENSITY:** A thick, lively crowd in 1960s Thai-Chinese fashion. Pedestrians should be concentrated on the sidewalks and road edges, keeping the center of the road mostly clear to emphasize its width.
        - **STREET LIFE:** Mobile hawkers (Mae-Ka-Hab-Ray) weaving through the crowd.

        **⛔ NEGATIVE PROMPT:** **narrow street**, **cramped perspective**, **tiny signs**, thin fonts, floating text, modern skyscrapers, glass facades, cars, motorized vehicles, LED signs, neon glow, plastic banners, air conditioners, changing lens, zooming.
    """,

    "Khaosan Road": """
        **TASK:** Create a **PHOTOREALISTIC COLOR PHOTOGRAPH** of Bang Lamphu / Khaosan Road (1962).

        **🔒 PERSPECTIVE LOCK (CRITICAL):**
        - **Blueprint:** Use the Uploaded Image as the **LAYOUT REFERENCE** for street path and alignment.

        **🏘️ HYBRID URBAN DENSITY (BALANCING ROWS & GAPS):**
        - **2-STORY LIMIT:** All structures are 1-2 stories max.
        - **INTERMITTENT ROWS:** Instead of one infinite row, create **CLUSTERS of 3-4 connected wooden shophouses** that share common walls.
        - **URBAN GAPS:** Between these clusters, insert **narrow gaps (1-2 meters)** or small wooden alleyway entrances. Do NOT make them wide open yards.
        - **STANDALONE INTEGRATION:** Occasionally place a single standalone masonry or wooden house between the clusters to break the repetition.
        - **VARYING FACADES:** Even within a cluster, each unit must have slightly different window styles or paint weathering (e.g., one unit has louvered shutters, the next has open frames).
        - **STREET PROXIMITY:** Ensure buildings sit relatively close to the road to maintain an **"Urban Residential"** feel. Avoid large front yards or long fences that look rural.

        **🚫 STRICT 1960s TIME-CAPSULE RULE:**
        - **NO MODERN ELEMENTS:** Absolutely NO air conditioners, NO satellite dishes, NO 7-Eleven signs, NO plastic chairs.
        - **AUTHENTIC HISTORY:** A quiet but established residential rice-trading community.

        **🚶 PEOPLE & TRAFFIC (QUIET COMMUNITY):**
        - **ZERO VEHICLES:** The narrow street is empty of cars.
        - **Locals Only:** Authentic Thai residents in 1960s attire some may look casual and some may look more relaxed than others.
        - **Activity:** Neighbors gathered near house entrances or sitting on porch steps.

        **🍚 PROPS:**
        - **RICE TRADING HUB:** Increase the density of rice sacks and wooden crates. They should look like they are part of the daily commerce, stacked near the "connected shophouse" sections.
        - ** Grain of rice on the ground, small bits of straw, and dust to enhance the realism of the trading environment.**
        - ** Other than rice sacks there can be some small market props like wooden carts, baskets, and simple hand tools for handling rice.**

        ** Road surface: Worn asphalt with scattered debris and dust near the curbs. **

        **⛔ NEGATIVE PROMPT:** **rural village look**, **wide open yards**, **distant isolated houses**, **suburban fences**, skyscrapers, modern hotels, cars, backpackers, tourists, uniform row houses, identical buildings.
    """,

    "Phra Sumen Fort": """
        **TASK:** TRANSFORM [IMAGE 1] into a historical 1960s scene. **CRITICAL: INPUT-ANGLE LOCK + REF-TEXTURE MAPPING.**

        **📐 0. ABSOLUTE GEOMETRY & ANGLE LOCK (INPUT DOMINANCE):**
        - **PRIMARY RULE:** The **Camera Angle, Eye Level, and Object Orientation** are DICTATED BY [IMAGE 1] ONLY.
        - **ANGLE ANALYSIS:**
            - **Step 1:** Analyze [IMAGE 1]. Is the fort facing Front? Left-Oblique? Right-Oblique? Is the camera Low or High?
            - **Step 2:** Analyze [IMAGE 2] (Reference). Note that it might only show specific angles (e.g., Side View).
            - **Step 3 (EXECUTION):** If [IMAGE 1] is Frontal but [IMAGE 2] is Side view, **IGNORE THE REFERENCE ANGLE.** You must paint the Reference's texture onto the **FRONTAL GEOMETRY** of [IMAGE 1].
        - **PERSPECTIVE FREEZE:** The Vanishing Points and Horizon Line of the output must align **PERFECTLY** with [IMAGE 1].

        **✂️ 1. MANDATORY DECAPITATION (IMMEDIATE ACTION):**
        - **TRIGGER:** As soon as you process [IMAGE 1], identify the upper wooden pavilion, roof, and spire.
        - **EXECUTION:** **CUT THEM OFF IMMEDIATELY.**
        - **REPLACEMENT:** The area where the roof exists in the input MUST become **EMPTY SKY**.
        - **SILHOUETTE:** The fort must become a **"Headless Stump"** ending abruptly at the masonry rim, exactly matching the silhouette style of [IMAGE 2].

        **🎨 2. SMART DETAIL ADAPTATION (REALISM INJECTION):**
        - **TEXTURE PROJECTION:** Take the *mold, soot, and peeling plaster details* from [IMAGE 2] and **PROJECT** them onto the specific surfaces of [IMAGE 1], respecting the input's lighting and depth.
        - **CONTEXTUAL ELEMENTS:** Look for small details in [IMAGE 2] (fences, ground texture, wall stains). Add these elements to [IMAGE 1] to increase realism, but **PLACE THEM** according to [IMAGE 1]'s perspective grid.

        **🛣️ 3. ROAD CONDITION (CLEAN ASPHALT EXCEPTION):**
        - **SURFACE:** While the surroundings follow the reference, the **ROADWAY** itself must remain **SMOOTH, CLEAN ASPHALT**.
        - **NO MESS:** The road is functional. **NO RUBBLE. NO MUD.**

        **⛔ NEGATIVE PROMPT:** **roof**, **pavilion**, **spire**, **golden top**, **wooden structure**, restored condition, modern park, garden, inventing buildings, adding houses, creative additions, rubble on road, **shifting angle**, **changing perspective**, **zooming**, **using reference angle instead of input angle**.
    """,
    
    "Sanam Luang": """
        **TASK:** TRANSFORM [IMAGE 1] into a **VIBRANT & LIVELY** 1968 photograph of Sanam Luang.

        **📸 1. PERSPECTIVE LOCK:**
        - **STRICT MATCH:** Use [IMAGE 1] as the rigid layout. **Do NOT shift or change the camera angle**.
        
        - **BEYOND THE LENS:** Imagine the market stalls and tents are located **BEYOND the edges of the camera view**. You should only see a few stall edges peeking in from the very far left or right.
        - **NO ENCLOSURE:** Do NOT create a "street" or "alley" of tents. This is a massive open field, not a market lane.

        **🎪 2. DEPTH-BASED ZONING (CRITICAL):**
        - **BOTTOM HALF VOID (CRITICAL):** The entire bottom 50 percent of the image MUST be **100 percent EMPTY** of any stalls, tents, umbrellas, or man-made structures. This area is strictly reserved for dry grass, and pedestrians.
        - **IMMEDIATE FOREGROUND (BOTTOM OF IMAGE):** This area MUST be **100% CLEAR** of any market stalls, umbrellas, tents, or permanent structures. It should only be dry red dirt, dust, and people walking, riding bicycles, or sitting.
        - **THE PERIMETER (FAR LEFT, FAR RIGHT, & DISTANCE):** All makeshift stalls, tent shanties, and disorganized clusters of umbrellas MUST be pushed to the **EXTREME LEFT and RIGHT EDGES** of the frame, and the far distant boundary near the trees.
        - **THE CENTRAL CORE:** Maintain a wide, open corridor from the bottom-center of the image all the way to the Wat Phra Kaew in the background. No stalls allowed in this central viewing lane.
        
        - **PERIPHERAL ONLY:** Any makeshift stalls or umbrellas must be pushed so far to the edges that they are almost **OFF-SCREEN**.

        - **HAPHAZARD CLUSTERING:** Market stalls and umbrellas must be **disorganized and unevenly scattered**. Some should overlap, some should be tilted at odd angles, and they should **NOT** follow a straight line.
        - **MAKESHIFT MATERIALS:** Use weathered materials: **stained canvas tents, worn-out wooden poles, aged bamboo sticks, and faded, multi-colored umbrellas** with visible patches or tears.
        
        **🏃 3. POPULATION & ACTIVITY (MINIMAL KITES):**
        - **VIBRANT CENTER:** Fill the foreground and middle ground with **DOZENS of people scattered throughout**. Focus on activities like riding **vintage bicycles**, sitting in groups on mats, strolling, playing kites, selling things, and socializing.
        - **KITE RESTRICTION:** **VERY FEW TO ZERO KITES.** If any are present, they must be small and distant in the background sky, not dominating the scene.
        - **MOBILE VENDORS:** Include **Mobile Hawkers (Mae-Ka-Hab-Ray)** with shoulder poles walking in the foreground to add life without blocking the view.

        **🏜️ 4. TERRAIN & LIGHTING:**
        - **SURFACE:** A little dirt and fine dust with green-to-yellow grass. Absolutely **NO ASPHALT, NO CONCRETE, and NO ROADS**.
        - **TEXTURE:** The ground must look organic and healthy. **MINIMIZE** exposed yellow dirt or fine dust. Focus on a soft, carpet-like natural grass texture that looks alive, not scorched.
        - **DYNAMIC LIGHTING:** Strictly follow the lighting and time of day (Day/Night) from [IMAGE 1].

        **⛔ NEGATIVE PROMPT:** stalls in foreground, umbrellas near camera, market structures at the bottom of the image, empty field, ghost town, asphalt, roads, **many kites**, **large kites**.
    """,
    
    
    "National Museum": """
        **TASK:** Create a **VINTAGE 1960s** view of the National Museum Bangkok.

        **🧱 1. LINEAR FENCE GEOMETRY (THE SINGLE PLANE RULE - CRITICAL):**
        - **SINGLE STRAIGHT LINE:** The entire fence line MUST exist on a **SINGLE FLAT GEOMETRIC PLANE** (180 degrees).
        - **NO RECESS / NO LOOPS:** Absolutely **NO fences wrapping inward**, NO "L-shaped" or "U-shaped" fences, and NO internal loops. The gate area must NOT be recessed.
        - **REPEATING PATTERN:** Follow a strict rhythm: **(One small masonry pillar -> One section of iron bars -> One small masonry pillar)**. Ensure intermediate pillars are visible along the entire line.
        - **VISIBLE MASONRY BASE:** The iron fence must sit on a **SOLID WHITE MASONRY BASE** (Knee-high). Do NOT render it as a flat line.
        - **SURGICAL DELETION:** Erase the side-door structures and the green signage beam from [IMAGE 1] entirely.

        **🚪 2. DOUBLE-SWING GATE & PILLARS:**
        - **DESIGN:** A **DOUBLE-SWING weathered IRON GATE** with vertical bars and a visible center-split line. the structure is same like a fence.
        - **THE GAP:** Create a clear **VOID OF AIR** between the standalone gate pillars. No horizontal connections allowed.
        - **PILLAR STYLE:** All pillars must be rectangular blocks with **COMPLETELY FLAT SQUARE TOPS**.
        - **LOW PROFILE:** Keep the structure **SHORT (Waist-high)** to reveal the museum architecture behind.

        **🚧 3. ROAD & ENVIRONMENT:**
        - **SURFACE:** Asphalt road. No traffic markings. Zebra crossings or painted lines.
        - **CLEANUP:** Remove all flags, flagpoles, modern signs, and traffic markings.
        
        ** 4. People & Atmosphere:**
        - **MINIMAL CROWD:** A few people walking on the curb that meets the masonry base directly and also walk in the museum in 1960s attire.
        - **NO VEHICLES:** The road and inside the museum is completely clear of cars and traffic.

        **⛔ NEGATIVE PROMPT:** thin fence base, missing intermediate pillars, side gates, merged pillars, curved entrance, recessed gate, concrete sidewalk, raised curb, pointed pillars, flags.
    """,
}

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise ValueError("GEMINI_API_KEY not found")
    return genai.Client(api_key=api_key)

# --- Friendly Error Message ---
def get_friendly_error_message(raw_reason, lang='TH'):
    raw_reason = raw_reason.lower()
    is_eng = (lang == 'ENG')

    if any(x in raw_reason for x in ['night', 'dark', 'sunset', 'evening']):
        return "The image is too dark or taken at night." if is_eng else "ภาพมืดหรือเป็นเวลากลางคืน (AI ต้องการแสงธรรมชาติ)"
    if any(x in raw_reason for x in ['person', 'selfie', 'face', 'crowd', 'body']):
        return "People are obstructing the view." if is_eng else "ตรวจพบบุคคลหรือฝูงชนบดบังทัศนียภาพ"
    if any(x in raw_reason for x in ['close-up', 'detail', 'macro', 'texture', 'wall']):
        return "The shot is too close or detailed." if is_eng else "ภาพถ่ายระยะใกล้เกินไป กรุณาถ่ายมุมกว้าง"
    if any(x in raw_reason for x in ['vehicle', 'bus', 'truck', 'car', 'traffic']):
        return "Vehicles are blocking the architecture." if is_eng else "มียานพาหนะบดบังตัวอาคารมากเกินไป"
    if any(x in raw_reason for x in ['text', 'screenshot', 'map', 'drawing']):
        return "This image does not appear to be a real photo." if is_eng else "ภาพนี้ไม่ใช่ภาพถ่ายสถานที่จริง"
    if "other" in raw_reason:
        guess = raw_reason.replace("other", "").replace("(", "").replace(")", "").strip()
        if guess:
            return f"System identifies this as: {guess}" if is_eng else f"ระบบระบุว่าเป็น: {guess} ซึ่งไม่ตรงกับที่เลือก"
        return "System could not identify the location." if is_eng else "ระบบไม่สามารถระบุสถานที่ในภาพได้"
    
    return "Image composition is unclear." if is_eng else "องค์ประกอบภาพยังไม่ชัดเจน"

SIMILARITY_THRESHOLD = 0.6
# --- CLIP Logic ---
def get_best_match_reference(location_th, user_img_bytes):
    # ✅ เพิ่ม "เสาชิงช้า & วัดสุทัศน์" ลงไปในเงื่อนไขนี้ เพื่อไม่ต้องใช้ไฟล์ .pkl
    if location_th == "ถนนข้าวสาร" or location_th == "เสาชิงช้า & วัดสุทัศน์":
        return None

    mapped_key = LOCATION_KEY_MAP.get(location_th)
    if not mapped_key or not SEARCH_MODEL or mapped_key not in LOCATION_INDICES:
        return None
    
    try:
        data = LOCATION_INDICES[mapped_key]
        user_img = Image.open(io.BytesIO(user_img_bytes))
        user_vector = SEARCH_MODEL.encode(user_img)
        
        distances = cdist([user_vector], data['vectors'], metric='cosine')[0]
        best_idx = np.argmin(distances)
        min_distance = distances[best_idx]
        
        # --- เพิ่ม Logic ตรงนี้ ---
        if min_distance > SIMILARITY_THRESHOLD:
            print(f"⚠️ No close match found (Dist: {min_distance:.2f}). Skipping Reference Image.")
            return None
            
        best_filename = data['filenames'][best_idx]
        print(f"🎯 Smart Match ({mapped_key}): Dist {min_distance:.2f} -> {best_filename}")
        file_path = os.path.join(os.path.dirname(__file__), "reference_images", mapped_key, best_filename)
        with open(file_path, "rb") as f:
            return f.read()
            
    except Exception as e:
        print(f"❌ Smart Match Error: {e}")
        return None

def get_random_reference(folder_name):
    base_path = os.path.join(os.path.dirname(__file__), "reference_images", folder_name)
    if not os.path.exists(base_path): return None
    
    images = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        import glob
        images.extend(glob.glob(os.path.join(base_path, ext)))
        
    if not images: return None
    selected = random.choice(images)
    print(f"🎲 Random Ref ({folder_name}): {os.path.basename(selected)}")
    with open(selected, "rb") as f:
        return f.read()

# --- Gemini Generation Logic ---
def step1_analyze(client, img_bytes):
    # ปรับ Prompt ให้เป็น Structured Analysis
    prompt = """
    ACT AS A SENIOR CINEMATOGRAPHER & ARCHITECTURAL ANALYST.
    Analyze this modern image for a STENCIL-BASED historical reconstruction.
    
    Provide a concise 'GEOMETRY CONSTRAINT' covering:
    
    1. **TECHNICAL PERSPECTIVE**: Identify exact Camera Height (e.g., Low-Angle looking UP, Eye-level, or Bird's-eye). Note the horizon line position and if the composition is 'Symmetrical' or 'Off-center'.
    2. **VANISHING POINTS & DIAGONALS**: Describe the trajectory of the main structural lines (e.g., 'Facades receding towards a vanishing point', 'Vertical pillars with slight lens distortion at edges').
    3. **SPATIAL ANCHORS**: Map the main subjects to quadrants (e.g., 'Primary landmark sits in the center-midground', 'Street leads from bottom-left to top-right vanishing point').
    4. **LENS TYPE**: Estimate if it's Wide-angle (expanded space) or Telephoto (compressed depth).
    5. **MODERN CLUTTER MAP**: Specific objects to erase (e.g., 'Digital signs', 'Modern vehicles', 'Air conditioners', 'Cables/Wires', 'CCTV cameras').

    OUTPUT FORMAT: A brief technical paragraph. FOCUS ONLY ON GEOMETRY AND PERSPECTIVE.
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-001", 
                contents=[prompt, types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")]
            )
            # เราจะได้คำบรรยายที่ระบุมุมมองชัดเจน เช่น "POV from sidewalk, only the base visible..."
            return response.text 
        except Exception as e:
            if "429" in str(e) or "503" in str(e):
                # สูตรใหม่: (2 ยกกำลัง attempt) * 2
                # Attempt 0: (1)*2 = 2 วินาที
                # Attempt 1: (2)*2 = 4 วินาที
                # Attempt 2: (4)*2 = 8 วินาที
                wait_time = (2 ** attempt) * 2 + random.uniform(1, 3) 
                print(f"⚠️ API Busy (Analysis). Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                break
    return "Maintain original perspective and visible structures exactly."

def step2_generate(client, structure_desc, location_key, original_img_bytes, ref_img_bytes=None):
    specific_prompt = LOCATION_PROMPTS.get(location_key, "")
    
    # 1. สร้างฐานคำสั่งกลาง (เพิ่ม Spatial Integrity)
    perspective_instr = f"""
    **MANDATORY PERSPECTIVE INSTRUCTION:**
    - {structure_desc}
    - **GEOMETRY SOURCE:** Use [IMAGE 1] as the ONLY source for composition.
    - **STRICT CONSTRAINT:** No rotation, zooming, or shifting. Perfect overlay required.
    """
    
    if location_key == "Phra Sumen Fort":
        perspective_instr += """
    - **ANGLE MATCHING (CRITICAL):** Check the camera angle of the Input [IMAGE 1]. The Output MUST match it exactly. (e.g., If Input is Left-Oblique, Output MUST be Left-Oblique).
    - **IMMEDIATE DECAPITATION:** The moment you see the roof/pavilion in the input, **TURN IT INTO SKY**. The fort is a headless stump.
    - **REFERENCE DETAILS:** Fill the scene with the *texture and clutter details* seen in [IMAGE 2], but place them according to the perspective of [IMAGE 1].
    - **NO PARK:** Remove all manicured grass/parks.
    - **CLEAN ROAD:** Keep the road surface **smooth and clean**.
        """
    
    # elif location_key == "Giant Swing":
    #     perspective_instr += """
    # - **SPATIAL ENFORCEMENT:** 1. LEFT OF SWING = Temple (No-Build Zone). 2. RIGHT OF SWING = 2-story Shophouses (No Temple Elements).
    # - **ROAD PURGE:** Identify the road surface in the foreground and center. **ERASE** any structures generated on the asphalt. Keep it a clear, empty grey road.
    # - **TEXTURE ISOLATION:** Do not bleed temple textures onto the right-side shophouses.
    # - **MONOLITHIC ROOF:** Flatten the shophouse roofs into one continuous line.
    # - **SKYLINE DELETION:** Replace skyscrapers with sky.
    #     """
        
    elif location_key == "Yaowarat":
        perspective_instr += """
    - **SIGNAGE DENSITY:** Allow a high density of signs. Do NOT leave pillars bare; fill them with vertical hand-painted signs.

    - **CHARACTER BOLDNESS:** Force all distant typography to use **EXTRA BOLD STROKES**.
    - **SYMBOLIC OVERRIDE:** If a distant word is failing to render, replace it with a **single, clear, large Chinese character** in Gold/Red color.

    - **ROAD DETAIL:** Add heavy "surface grime" and tire marks to the asphalt.
    - **CROWD INJECTION:** Populate the scene with a high-density crowd. Ensure they look naturally integrated into the perspective of [IMAGE 1].
    - **INFRASTRUCTURE:** Add vintage utility poles and street-level clutter to fill visual gaps.
        """

    elif location_key == "National Museum":
        perspective_instr += """
    - **PATTERN REPLICATION:** Identify the (Pillar -> Iron Railing -> Pillar) rhythm. You MUST replicate this pattern across the entire fence, especially where side-gates were removed.
    - **BASE ENFORCEMENT:** Ensure the masonry base has a clear, visible height (approx. 40cm). It should look like a solid wall base, not a flat line on the ground.
    - **SIDE GATE DELETION:** Completely DELETE the side entrance structures. Fill the resulting gap with **EMPTY SKY** or the **BACKGROUND BUILDING** to separate the pillars.
    - **LINEAR ALIGNMENT:** Force the fence into a **PERFECTLY STRAIGHT LINE**. Ignore the modern recessed curves from [IMAGE 1].
    - **FLATTEN TOPS:** All pillars must have FLAT SQUARE TOPS.
        """

    elif location_key == "Sanam Luang":
        perspective_instr += """
    - **VASTNESS ENFORCEMENT:** Treat the edges of [IMAGE 1] as "Infinite Borders". 
    - **PERIPHERAL BIAS:** PUSH all market elements (tents, stalls) as far away from the center as possible. 
    - **OFF-SCREEN LOGIC:** It is OKAY if some stalls listed in the prompt are NOT visible in the frame. Priority is a **CLEAR, WIDE OPEN RED DIRT FIELD**.
    - **HORIZON CLEARANCE:** Ensure a direct, unobstructed line of sight to the temples in the background.
        """

    elif location_key == "Sala Chalermkrung":
        perspective_instr += """
    - STRUCTURAL INTEGRITY: Lock the geometry of the entire main building and columns to. Update only period-correct detailing (original doors, period casement windows if not covered by posters) within the locked concrete frame. Do not extend vertically or add extra wings to the main facade.
    - SIGNAGE ANCHOR: The top roof sign is the anchor. Do not move or modify it. It must remain 100% pixel-perfect identical to.
    - FACADE MASKING: Ensure exactly 3 posters cover the central facade's glass areas, strictly creating an impenetrable wall with zero visible glass trace or reflection on the covered facade levels. The posters must strictly adhere to the defined gentleman image requirements (V.19/V.20).
    - AMBIANCE FIX: Flatten and simplify modern attachments on the left/right wings extension area. Surgically erase left side trees to fully reveal historical extend. Enforce the long horizontal concrete awning and repetitive vertical window panels on the left wing. Enforce a perfectly flat cream wall with an orderly row of dark-framed multi-pane casement windows and a subtle eyebrow canopy on the right wing, strictly prohibiting any modern storefronts or creative additions. Force all surrounding background buildings to become utilitarian 2-3 story masonry commercial shophouses (no skyscrapers). Ensure all other windows in the scene are strictly closed. Reconstruct sidewalks as clear aged concrete. Remove all modern lamps, utility poles, and wiring. Empty the road of all motorized vehicles and tuk-tuks. The entire surroundings must strictly reflect the historical Charoen Krung context and V.19/V.20 requirements. Ensure maintained dignity for weathered concrete. Ensure pixel-perfect structural overlay with.
        """

    # 3. ประกอบ Global Style (ล็อคอารมณ์ภาพ)
    global_style = f"""
    {perspective_instr}
    
    **GLOBAL STYLE:**
    - Output: Photorealistic color 1960s Kodachrome filter.
    - **RECONSTRUCTION RULE:** Discard any modern architecture from [IMAGE 1] and replace with historical elements from [IMAGE 2] or Prompt.
    - Remove all traffic lights, LED lamps, and digital signage.
    """
    
    # ส่วนการประกอบ Parts และเรียก AI
    parts = [f"{specific_prompt}\n{global_style}\n\n**[IMAGE 1] THE STRUCTURAL BLUEPRINT:**"]
    parts.append(types.Part.from_bytes(data=original_img_bytes, mime_type="image/jpeg"))

    if ref_img_bytes:
        style_instruction = """
        **[IMAGE 2] THE STYLE REFERENCE:**
        - USE ONLY for: Color grading, film grain, and 1960s atmosphere.
        - **DANGER:** Do NOT follow the architecture or camera angle of [IMAGE 2].
        """
        parts.append(style_instruction)
        parts.append(types.Part.from_bytes(data=ref_img_bytes, mime_type="image/jpeg"))

    # Config การเรนเดอร์ (แนะนำ temperature=0.1 เพื่อให้มีความยืดหยุ่นเล็กน้อยแต่ไม่หลุดกรอบ)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        temperature=0.1 
    )
    # 3. เรียกโมเดลด้วยค่าความสร้างสรรค์ต่ำที่สุด (Locking the result)
    model_name = "gemini-3-pro-image-preview" 
    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"🎨 Generating Image (Attempt {attempt+1}) using {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=parts, # ส่งแบบ List ที่แยกคำสั่งกับรูปสลับกัน
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    temperature=0.0, # ลดเหลือ 0.1 เพื่อให้ทำตามโครงสร้างเดิมเป๊ะขึ้น
                    http_options={'timeout': 180000}
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data: return part.inline_data.data
            
            print(f"⚠️ Warning: Model returned no image (Attempt {attempt+1})")
            
        except Exception as e:
            if "not found" in str(e).lower() and model_name == "gemini-3-pro-image-preview":
                print("⚠️ Switching model to gemini-3-pro-image-preview...")
                model_name = "gemini-3.1-flash-image-preview" # ถ้าไม่ได้ปรับไปตัวกากๆ(ประหยัดงบ)
                time.sleep(1)
                continue

            if "429" in str(e) or "503" in str(e):
                t = (5 * (2 ** attempt)) + random.uniform(1, 5) 
                print(f"⚠️ Server Busy ({model_name}) -> Waiting {t:.1f}s before retry...")
                time.sleep(t)

            if "503" in str(e) or "429" in str(e):
                # 🔄 ถ้าตัว Pro ยุ่ง ให้ลองสลับไปใช้ตัว Flash รุ่นใหม่ๆ ในลิสต์ของคุณ
                if attempt == 0:
                    model_name = "gemini-3.1-flash-image-preview" # ลองตัว 3.1 ล่าสุด
                elif attempt == 1:
                    model_name = "gemini-2.5-flash-image" # ลองตัว 2.5
                
                wait_time = (10 * (2 ** attempt)) # เพิ่มเวลารอ
                time.sleep(wait_time)
                continue

            else:
                print(f"❌ Critical Gen Error: {e}")
                if model_name != "gemini-3-pro-image-preview":
                     model_name = "gemini-3-pro-image-preview"
                     continue
                return None
                
    return None

# ==========================================
# 🎬 RUNWAY ML INTEGRATION (STRICT & REALISTIC)
# ==========================================

# ==========================================
# 🎬 RUNWAY ML INTEGRATION (STRICT & REALISTIC)
# ==========================================

import os
import io
import time
import base64
import datetime
import requests
from PIL import Image

def generate_video_runway(image_bytes, location_key):
    runway_key = os.getenv("RUNWAYML_API_KEY")
    if not runway_key:
        print("❌ Error: ไม่เจอ RUNWAYML_API_KEY ในไฟล์ .env")
        return None

    try:
        print("🎬 Starting Runway Video Generation (V.17 - Ultimate Polishing)...")
        
        # 1. Image Pre-processing
        try:
            print("🎬 Starting Runway Gen-3 Video Generation (Multi-Aspect Letterbox)...")
            
            # 1. Image Orientation & Ratio Logic
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            # ✅ กำหนดค่ามาตรฐาน (Canvas) ตามทิศทางของภาพ
            if width >= height:
                print(f"📐 Detected: LANDSCAPE ({width}x{height})")
                runway_ratio_str = "1280:768"
                target_width, target_height = 1280, 768 # ประกาศค่าไว้ใช้ตรงนี้
            else:
                print(f"📐 Detected: PORTRAIT ({width}x{height})")
                runway_ratio_str = "768:1280"
                target_width, target_height = 768, 1280 # ประกาศค่าไว้ใช้ตรงนี้

            target_ratio = target_width / target_height
            current_ratio = width / height

            # --- 🎬 SMART LETTERBOX: ถมดำแทนการ Crop เพื่อไม่ให้ภาพโดนซูม ---
            if abs(current_ratio - target_ratio) > 0.05:
                print("🎬 Using Letterbox mode to preserve full building view...")
                
                # ย่อรูปให้พอดีกับด้านที่ยาวที่สุด (Thumbnail จะรักษาสัดส่วนภาพเดิมไว้)
                img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                
                # สร้างพื้นหลังสีดำขนาดเป๊ะๆ ตามที่ Runway ต้องการ (1280x768 หรือ 768x1280)
                new_img = Image.new("RGB", (target_width, target_height), (0, 0, 0))
                
                # วางรูปต้นฉบับไว้ตรงกลางพื้นหลังสีดำ
                offset = ((target_width - img.size[0]) // 2, (target_height - img.size[1]) // 2)
                new_img.paste(img, offset)
                img = new_img
                
                # บันทึกภาพที่จัดการแล้วกลับเป็น bytes
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                image_bytes = buffered.getvalue()
                print(f"✅ Letterboxed to: {img.size}")

        except Exception as crop_err:
            print(f"⚠️ Warning: Auto-crop failed ({crop_err}). Sending original image.")

        base64_str = base64.b64encode(image_bytes).decode('utf-8')

        # 2. RUNWAY PROMPT ENGINEERING (FLAWLESS & GLITCH-FREE)
        # Goal: Static camera, realistic physics, no filters, no glitches.
        base_prompt = """
        Static tripod camera shot, absolutely NO panning, NO zooming, NO rotation.
        Hyper-realistic 8k video, high fidelity.
        Subtle environmental motion only. Stable structures, no morphing buildings.
        Natural 1960s lighting with very subtle film grain. No visual glitches.
        """

        location_prompts = {
            "Democracy Monument": "Static tripod shot, No Zoom out, filmed in HIGH-FRAMERATE SLOW MOTION (smooth, dreamy, absolutely NO timelapse). **CRITICAL: The Democracy Monument is an IMMOVABLE CONCRETE OBJECT. It must remain STONE-STILL and RIGID.** Zero warping. **ABSOLUTE PROHIBITION ON ADDITIONS:** It is STRICTLY FORBIDDEN to spawn, generate, or add cars, buses, people, or debris. The road must remain completely DESERTED. **NO VEHICLES ALLOWED.** **PRESERVE BLACK BORDERS/BARS:** If the input has black space, KEEP IT EXACTLY AS IS. Do not fill, inpaint, or crop. Motion is limited strictly to lazy, slow-drifting clouds and heat haze only.",
            "Giant Swing": "Static tripod shot. Red pillars and all surrounding buildings MUST REMAIN PERFECTLY RIGID and STILL. DO NOT ADD any vehicles or new objects. People walk slowly and naturally, realistically. Gentle leaf rustle and atmospheric haze. No strange deformations or glitches.",
            "Yaowarat": "Heat haze shimmering slightly above the asphalt. Subtle flickering of sunlight reflecting off aged glass windows. No movement of vehicles or people at all.",
            "Khaosan Road": "Calm and still residential atmosphere.",
            "Phra Sumen Fort": "Sunlight filtering through trees, creating moving dappled shadows on the white stone ruins. Overgrown grass on top of the ruin swaying slightly. No reconstruction of the fort.",
            "Sanam Luang": "Nothing moving in the video except a very gentle breeze rustling the leaves of distant trees. Subtle shifting of sunlight and shadows on the dry grass field. A crowd of people moving slowly but no walking or vehicles.",
            "National Museum": "A very calm, Zen-like atmosphere. Dappled sunlight and shadows shifting slowly on the white walls and gravel ground. Tree are swaying gently and slowly."
        }

        specific_action = location_prompts.get(location_key, "Natural lighting changes, realistic texture rendering.")
        final_prompt = f"{base_prompt} {specific_action}"
        print(f"📝 Video Prompt: {final_prompt}")

        url = "https://api.dev.runwayml.com/v1/image_to_video"
        payload = {
            "promptImage": f"data:image/png;base64,{base64_str}",
            "model": "gen3a_turbo",
            "promptText": final_prompt,
            "duration": 5,
            "ratio": "1280:768"
        }
        headers = {
            "Authorization": f"Bearer {runway_key}",
            "X-Runway-Version": "2024-11-06",
            "Content-Type": "application/json"
        }
        
        # 3. Send Request
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"❌ Runway API Failed ({response.status_code}): {response.text}")
            return None
            
        task_id = response.json().get('id')
        print(f"⏳ Runway Task ID: {task_id}")
        
        # 4. Polling
        for i in range(30):
            time.sleep(3)
            status_res = requests.get(f"https://api.dev.runwayml.com/v1/tasks/{task_id}", headers=headers)
            if status_res.status_code == 200:
                data = status_res.json()
                status = data.get('status')
                
                if status == "SUCCEEDED":
                    print("✅ Video Generation Complete!")
                    return data.get('output', [None])[0]
                elif status == "FAILED":
                    print(f"❌ Video Generation FAILED: {data.get('failure', 'Unknown error')}")
                    return None
                else:
                    print(f" ...processing ({i+1}/30)")
            else:
                print(f"⚠️ Polling Error: {status_res.status_code}")

        print("❌ Timeout: Runway took too long.")
        return None

    except Exception as e:
        print(f"❌ Critical Runway Error: {e}")
        return None

def save_generated_image(image_bytes, location_name_th):
    try:
        if not os.path.exists(HISTORY_FOLDER):
            os.makedirs(HISTORY_FOLDER)

        file_prefix = LOCATION_MAPPING_TH_TO_EN.get(location_name_th, "unknown_location")
        safe_name = "place"
        
        if "Democracy" in file_prefix: safe_name = "democracymonument"
        elif "Sala" in file_prefix: safe_name = "salachalermkrung"
        elif "Swing" in file_prefix: safe_name = "giantswing"
        elif "Yaowarat" in file_prefix: safe_name = "yaowarat"
        elif "Khao San" in file_prefix: safe_name = "khaosan"
        elif "Phra Sumen" in file_prefix: safe_name = "phrasumenfort"
        elif "Sanam Luang" in file_prefix: safe_name = "sanamluang"
        elif "National Museum" in file_prefix: safe_name = "nationalmuseum"
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_1960s_{timestamp}.png"
        filepath = os.path.join(HISTORY_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        print(f"💾 Auto-saved result to: {filename}")
        return filepath 

    except Exception as e:
        print(f"⚠️ Failed to auto-save image: {e}")
        return None

def save_generated_video(video_url, location_key):
    try:
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)

        print(f"⬇️ Downloading video from: {video_url}")
        response = requests.get(video_url, stream=True)
        
        if response.status_code == 200:
            file_prefix = location_key.replace(" ", "").lower()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{file_prefix}_video_{timestamp}.mp4"
            filepath = os.path.join(VIDEO_FOLDER, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk: f.write(chunk)
            
            print(f"🎥 Auto-saved video to: {filepath}")
            return filename, filepath
        else:
            print(f"❌ Download Failed. Status: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"⚠️ Save Video Failed: {e}")
        return None, None
    
def translate_error_with_gemini(raw_reason, lang='TH'):
    """ใช้ Gemini แปลผลเทคนิคหรือ Error ให้เป็นภาษามนุษย์ที่สุภาพและเข้าใจง่าย"""
    try:
        client = get_client() # เรียกใช้ client จากฟังก์ชันที่มีอยู่แล้ว
        target_lang = "Thai" if lang == 'TH' else "English"
        
        # ปรับ Prompt ให้คุมโทนย้อนยุคและสุภาพ
        prompt = f"""
        Objective: Return a 3-6 word COMMAND in {target_lang} based on "{raw_reason}".
        Constraint: NO English characters. NO introductory text. NO apologies.
        
        RULES:
        - If input is about 'car' or 'vehicle' -> "กรุณาหามุมใหม่ ที่ไม่มีสิ่งกีดขวาง"
        - If input is 'dark' or 'night' -> "ภาพมืดไป กรุณาถ่ายตอนกลางวัน"
        - If input is 'server' or 'busy' -> "ระบบกำลังมีปัญหา กรุณาลองใหม่"
        - If input mentions a specific place (e.g., 'Detected Yaowarat but user selected...') 
          -> Tell the user what was detected briefly, like "ระบบระบุได้ว่าเป็น "[ชื่อสถานที่]" กรุณาเลือกสถานที่ให้ถูกต้อง"
        - If input is anything else (including "{raw_reason}") -> "รูปภาพไม่ชัดเจน กรุณาอัปโหลดใหม่"

        Final Output must be ONLY the {target_lang} string.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=40)
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini Translation Failed: {e}")
        # ถ้า AI แปลพัง ให้กลับไปใช้ Dictionary พื้นฐานที่เราทำไว้
        return get_friendly_error_message(raw_reason, lang)

# ==========================================
# 🚀 ROUTES
# ==========================================

@app.route('/verify', methods=['POST'])
def verify_image_route():
    try:
        if 'image' not in request.files: return jsonify({'error': 'No image'}), 400
        file = request.files['image']
        location_th = request.form['location']
        lang = request.form.get('language', 'TH').upper()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
            file.save(temp.name)
            temp_path = temp.name
            
        detected_place, score, is_valid = classify_image(temp_path)
        os.remove(temp_path)
        
        expected_en = LOCATION_MAPPING_TH_TO_EN.get(location_th)
        analysis_report = {
            "status": "success" if is_valid else "rejected",
            "detected_place": detected_place,
            "score": round(score * 100, 2),
            "is_valid": is_valid
        }
        
        # ❌ กรณีภาพไม่ผ่านเกณฑ์ (เช่น มืดไป, มีรถบัง)
        if not is_valid:
            # ✅ ใช้ Gemini แปลเหตุผลให้ User เข้าใจง่าย
            friendly_message = translate_error_with_gemini(detected_place, lang)
            return jsonify({'status': 'rejected', 'details': friendly_message, 'analysis_report': analysis_report}), 200
            
        # ❌ กรณีถ่ายถูกที่ แต่เลือกสถานที่ในแอปผิด
        if detected_place != expected_en: 
             # ส่งข้อความที่มีชื่อสถานที่ที่ตรวจเจอ (detected_place) ไปให้ Gemini แปล
             msg_raw = f"Detected {detected_place} but user selected {location_th}"
             friendly_message = translate_error_with_gemini(msg_raw, lang)
             return jsonify({'status': 'rejected', 'details': friendly_message, 'analysis_report': analysis_report}), 200
             

        return jsonify({'status': 'success', 'analysis_report': analysis_report})
    except Exception as e: 
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_image_route():
    try:
        print("🚀 [Step 1] Generative Image...")
        file = request.files['image']
        location_th = request.form['location']
        lang = request.form.get('language', 'TH').upper()
        img_bytes = file.read()
        
        ref_bytes = get_best_match_reference(location_th, img_bytes)
        client = get_client()
        structure = step1_analyze(client, img_bytes)
        
        prompt_key = LOCATION_INFO.get(location_th, {}).get('prompt_key', "Democracy Monument")
        result_bytes = step2_generate(client, structure, prompt_key, img_bytes, ref_bytes)
        
        if result_bytes:
            save_generated_image(result_bytes, location_th)
            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            desc = LOCATION_INFO.get(location_th, {}).get('desc_60s', "")
            
            return jsonify({
                'status': 'success',
                'image': f"data:image/png;base64,{result_b64}",
                'location_name': location_th,
                'location_key': prompt_key, 
                'description': desc
            })
        else:
            # ✅ ถ้า AI Busy ให้ Gemini ช่วยบอกขอโทษแบบสุภาพ
            err_msg = translate_error_with_gemini("AI Model Busy", lang)
            return jsonify({'error': err_msg}), 503
    except Exception as e:
        friendly_err = translate_error_with_gemini(str(e), lang)
        return jsonify({'error': friendly_err}), 500

@app.route('/animate', methods=['POST'])
def animate_video_route():
    try:
        print("🚀 [Step 2] Animating Video...")
        data = request.json
        image_data = data.get('image')
        location_key = data.get('location_key')
        lang = data.get('language', 'TH') # รับภาษามาจาก Frontend

        if "," in image_data: image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)

        video_url = generate_video_runway(image_bytes, location_key)
        
        if video_url:
            vid_filename, vid_path = save_generated_video(video_url, location_key)
            final_video_src = video_url 
            if vid_path and os.path.exists(vid_path):
                with open(vid_path, "rb") as f:
                    vid_b64 = base64.b64encode(f.read()).decode('utf-8')
                    final_video_src = f"data:video/mp4;base64,{vid_b64}"

            return jsonify({'status': 'success', 'video': final_video_src})
        else:
            # ✅ แปล Error จาก Runway ให้ดูเป็นมิตร
            err_msg = translate_error_with_gemini("Video generation failed", lang)
            return jsonify({'error': err_msg}), 500
    except Exception as e:
        friendly_err = translate_error_with_gemini(str(e), lang)
        return jsonify({'error': friendly_err}), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)