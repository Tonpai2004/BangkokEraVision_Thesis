'use client';
import { useState, useRef } from 'react';

// 1. ข้อมูลสถานที่
const LOCATIONS_DATA = [
  { id: "อนุสาวรีย์ประชาธิปไตย", th: "อนุสาวรีย์ประชาธิปไตย", en: "Democracy Monument" },
  { id: "ศาลาเฉลิมกรุง", th: "ศาลาเฉลิมกรุง", en: "Sala Chalermkrung" },
  { id: "เสาชิงช้า & วัดสุทัศน์", th: "เสาชิงช้า & วัดสุทัศน์", en: "Giant Swing & Wat Suthat" },
  { id: "เยาวราช", th: "เยาวราช", en: "Yaowarat (Chinatown)" },
  { id: "ถนนข้าวสาร", th: "ถนนข้าวสาร", en: "Khaosan Road" },
  { id: "ป้อมพระสุเมรุ", th: "ป้อมพระสุเมรุ", en: "Phra Sumen Fort" },
  { id: "สนามหลวง", th: "สนามหลวง", en: "Sanam Luang" },
  { id: "พิพิธภัณฑสถานแห่งชาติ", th: "พิพิธภัณฑสถานแห่งชาติ", en: "Bangkok National Museum" }
];

// 2. ปรับข้อความ UI 
const UI_TEXT = {
  TH: {
    label_location: "เลือกสถานที่",
    label_upload: "อัปโหลดรูปถ่ายของคุณ",
    dropzone_text: "คลิก หรือ ลากรูปมาวางที่นี่",
    btn_main: "เริ่มย้อนเวลา",
    btn_try_again: "ลองรูปอื่น",
    btn_retry: "ลองใหม่อีกครั้ง",
    btn_download: "ดาวน์โหลดรูปภาพ",
    
    status_analyzing: "กำลังวิเคราะห์โครงสร้าง...",
    status_verify_pass: "ผ่านการตรวจสอบ",
    status_verify_fail: "การตรวจสอบไม่ผ่าน",
    status_tech_error: "เกิดข้อผิดพลาดทางเทคนิค",
    
    status_reconstructing: "กำลังจำลองภาพอดีต...",
    sub_analyzing: "ตรวจสอบความถูกต้องทางประวัติศาสตร์",
    sub_reconstructing: "อยู่ระหว่างดำเนินการ...",
    auto_proceed: "กำลังเริ่มกระบวนการย้อนเวลา...",
    
    error_desc_prefix: "ระบบขัดข้อง: "
  },
  ENG: {
    label_location: "Choose a location",
    label_upload: "Upload your Photo",
    dropzone_text: "Click or Drag photo here",
    btn_main: "GENERATE",
    btn_try_again: "Try Another Photo",
    btn_retry: "Retry again",
    btn_download: "Download Image",
    
    status_analyzing: "ANALYZING SCENE",
    status_verify_pass: "VERIFICATION PASSED",
    status_verify_fail: "VERIFICATION REJECTED",
    status_tech_error: "TECHNICAL ERROR",
    
    status_reconstructing: "RECONSTRUCTING",
    sub_analyzing: "Verifying historical compatibility...",
    sub_reconstructing: "In process...",
    auto_proceed: "Initializing Time Travel Sequence...",

    error_desc_prefix: "System Failure: "
  }
};

type ProcessStatus = 'idle' | 'verifying' | 'verified_pass' | 'verified_fail' | 'generating' | 'finished' | 'error';

interface UploadSectionProps {
  currentLang: 'TH' | 'ENG';
}

export default function UploadSection({ currentLang }: UploadSectionProps) {
  const [selectedLocation, setSelectedLocation] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  
  const [status, setStatus] = useState<ProcessStatus>('idle');
  const [failReason, setFailReason] = useState<string>("");
  const [passDetails, setPassDetails] = useState<{score: number, place: string} | null>(null);

  const [result, setResult] = useState<{image: string, desc: string, location: string} | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const text = UI_TEXT[currentLang];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
      if (status === 'verified_fail' || status === 'finished') {
        setStatus('idle');
        setResult(null);
      }
    }
  };

  // --- ฟังก์ชันเดียวจบ (One Click Flow) ---
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedLocation) return alert(currentLang === 'ENG' ? "Please select location and image." : "กรุณาเลือกสถานที่และรูปภาพ");

    // 1. สร้างตัวแปรมาคอยจำว่าตอนนี้อยู่ขั้นตอนไหน
    let currentStep = 'verifying'; 

    setStatus('verifying'); 
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('location', selectedLocation);
    formData.append('language', currentLang); 

    try {
      // ------------------------------------------------
      // STEP 1: Verify (เปลี่ยน URL เป็น 127.0.0.1)
      // ------------------------------------------------
      const verifyRes = await fetch('http://127.0.0.1:5000/verify', {
        method: 'POST',
        body: formData,
      });
      const verifyData = await verifyRes.json();

      if (!verifyRes.ok || verifyData.status === 'rejected') {
        setFailReason(verifyData.details || verifyData.error || "Unknown Error");
        setStatus('verified_fail'); 
        return; 
      }

      // ------------------------------------------------
      // STEP 2: Passed Verify -> Wait -> Generate
      // ------------------------------------------------
      setPassDetails({
        score: verifyData.analysis_report?.score || 0,
        place: verifyData.analysis_report?.detected_place || "Confirmed"
      });
      setStatus('verified_pass');

      // หน่วงเวลา 2 วิ ให้ User ดีใจว่าผ่าน
      await new Promise(r => setTimeout(r, 2000));

      currentStep = 'generating';
      setStatus('generating');

      const genFormData = new FormData();
      genFormData.append('image', file);
      genFormData.append('location', selectedLocation);

      // (เปลี่ยน URL เป็น 127.0.0.1)
      const genRes = await fetch('http://127.0.0.1:5000/generate', {
          method: 'POST',
          body: genFormData,
      });
      const genData = await genRes.json();

      if (genData.image) {
          setResult({
            image: genData.image,
            desc: genData.description,
            location: genData.location_name
          });
          setStatus('finished');
      } else {
          throw new Error(genData.error || "Generation process failed");
      }

    } catch (err: any) {
        console.error("Fetch Error Details:", err); // เพิ่ม Log ให้ดูง่ายขึ้น
        setFailReason(err.message);
        
        if (currentStep === 'generating') {
            setStatus('error'); 
        } else {
            // ถ้า Error ตั้งแต่ Verify (เช่น Failed to fetch) จะมาตกตรงนี้
            setStatus('verified_fail'); 
        }
    }
  };

  return (
    <>
      <form onSubmit={handleGenerate} className="w-full mx-auto mt-8">
        
        <div className="dashed-box-container">
            {/* Location Select */}
            <div className="flex justify-between items-end py-2 font-bold text-xl md:text-2xl serif-font border-b-2 border-dark">
              <label htmlFor="location-select" className="whitespace-nowrap mr-4">
                {text.label_location}
              </label>
              <div className="relative w-full flex-1">
                  <select 
                      id="location-select"
                      value={selectedLocation} 
                      onChange={(e) => setSelectedLocation(e.target.value)}
                      className="w-full bg-transparent border-none outline-none text-right font-serif font-bold cursor-pointer appearance-none pr-8 truncate text-dark"
                      required
                  >
                      <option value="" disabled></option>
                      {LOCATIONS_DATA.map(loc => (
                        <option key={loc.id} value={loc.id}>
                          {currentLang === 'ENG' ? loc.en : loc.th}
                        </option>
                      ))}
                  </select>
                  <span className="absolute right-0 bottom-2 pointer-events-none text-sm ">▼</span>
              </div>
            </div>
            
            <div className="h-1"></div>

            {/* File Upload */}
            <div className="flex justify-between items-end pb-2 font-bold text-xl md:text-2xl mb-3 serif-font border-b-2 border-dark relative">
                <label htmlFor="file-upload" className="flex-1">{text.label_upload}</label>
                <button 
                    type="button" 
                    onClick={() => fileInputRef.current?.click()} 
                    className="text-3xl hover:scale-110 transition-transform"
                    title="Click to select image"
                >
                    📷
                </button>
                <input 
                    id="file-upload" type="file" ref={fileInputRef} onChange={handleFileChange} 
                    accept="image/*" className="hidden"
                />
            </div>

            {/* Drop Zone */}
            <div 
                className="min-h-[250px] flex justify-center items-center cursor-pointer transition-colors border-2 border-transparent p-4"
                onClick={() => fileInputRef.current?.click()}
            >
                {preview ? (
                    <img src={preview} alt="Preview" className="max-h-[300px] w-auto object-contain border-2 border-dark shadow-md" />
                ) : (
                    <div className="flex flex-col items-center opacity-50 hover:opacity-80 transition-opacity">
                        <span className="text-6xl mb-2">⬆</span>
                        <span className="text-sm font-mono">{text.dropzone_text}</span>
                    </div>
                )}
            </div>
        </div>

        {/* ปุ่มเดียวจบ: GENERATE */}
        <button 
            type="submit" 
            disabled={status !== 'idle' && status !== 'verified_fail' && status !== 'finished'}
            className="w-full mt-8 bg-dark text-white text-bold py-4 text-2xl md:text-3xl serif-font transition-colors disabled:opacity-50 disabled:cursor-not-allowed active:translate-y-[2px] active:shadow-[2px_2px_0px_#2C2C2C]"
        >
            {text.btn_main}
        </button>
      </form>

      {/* --- OVERLAY --- */}
      {status !== 'idle' && status !== 'finished' && (
        <div className="fixed inset-0 bg-black/95 z-50 flex flex-col justify-center items-center text-white px-4 text-center">
            
            {/* 1. STATE: VERIFYING */}
            {status === 'verifying' && (
                <>
                    <div className="text-4xl md:text-6xl font-bold mb-6 animate-pulse serif-font tracking-widest text-gold">
                        {text.status_analyzing}
                    </div>
                    <p className="font-mono text-sm md:text-base opacity-70 tracking-wider">
                        {text.sub_analyzing}
                    </p>
                </>
            )}

            {/* 2. STATE: VERIFIED PASS */}
            {status === 'verified_pass' && (
                <>
                    <div className="text-6xl mb-4 text-green-500">✓</div>
                    <div className="text-3xl md:text-5xl font-bold mb-4 serif-font text-green-400">
                        {text.status_verify_pass}
                    </div>
                    <div className="font-mono text-xl mb-2">
                        {passDetails?.place}
                    </div>
                    <div className="font-mono text-sm opacity-70 mb-8">
                        Confidence Score: {passDetails?.score.toFixed(1)}%
                    </div>
                </>
            )}

            {/* 3. STATE: VERIFIED FAIL (User Error) */}
            {status === 'verified_fail' && (
                <div className="border-2 border-accent p-8 max-w-2xl bg-black">
                    <div className="text-6xl mb-4 text-accent">✕</div>
                    <div className="text-3xl md:text-5xl font-bold mb-6 serif-font text-accent">
                        {text.status_verify_fail}
                    </div>
                    <p className="font-mono text-lg md:text-xl text-white mb-8 leading-relaxed whitespace-pre-line">
                        {failReason}
                    </p>
                    <button 
                        onClick={() => setStatus('idle')}
                        className="border border-white px-8 py-3 hover:bg-white hover:text-black font-mono tracking-widest transition-colors uppercase"
                    >
                        {text.btn_try_again}
                    </button>
                </div>
            )}

            {/* 4. STATE: TECHNICAL ERROR (System Error) */}
            {status === 'error' && (
                <div className="border-2 border-accent p-8 max-w-2xl bg-black shadow-[0_0_50px_rgba(255,255,255,0.1)]">
                    <div className="text-6xl mb-4 text-red-500">✕</div>
                    <div className="text-3xl md:text-5xl font-bold mb-6 serif-font text-accent">
                        {text.status_tech_error}
                    </div>
                    <p className="font-mono text-lg md:text-xl text-white mb-8 leading-relaxed whitespace-pre-line">
                        {failReason}
                    </p>
                    <button 
                        onClick={() => setStatus('idle')}
                        className="border border-white px-8 py-3 hover:bg-white hover:text-black font-mono tracking-widest transition-colors uppercase"
                    >
                        {text.btn_retry}
                    </button>
                </div>
            )}

            {/* 5. STATE: GENERATING */}
            {status === 'generating' && (
                <>
                    <div className="text-4xl md:text-6xl font-bold mb-6 animate-blink serif-font tracking-widest text-gold">
                        {text.status_reconstructing}
                    </div>
                    <p className="font-mono text-sm md:text-base opacity-70 tracking-wider">
                        {text.sub_reconstructing}
                    </p>
                </>
            )}
        </div>
      )}

      {/* --- RESULT MODAL --- */}
      {result && (
        <div className="fixed inset-0 bg-black/85 z-50 flex justify-center items-center p-4" onClick={() => setResult(null)}>
            <div className="bg-background p-6 md:p-8 max-w-3xl w-full border-[3px] border-dark shadow-[15px_15px_0px_rgba(0,0,0,0.5)] relative max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                <button onClick={() => setResult(null)} className="absolute top-4 right-4 text-4xl font-bold leading-none hover:text-accent">&times;</button>
                <h3 className="serif-font text-2xl md:text-4xl font-bold mb-6 mt-2 text-center italic">{result.location}</h3>
                <div className="border-[3px] border-dark mb-6 bg-black">
                    <img src={result.image} alt="Generated" className="w-full h-auto block" />
                </div>
                
                <button 
                    onClick={() => {
                        const link = document.createElement('a');
                        link.href = result.image;
                        link.download = `bangkok-1960s-${Date.now()}.png`;
                        link.click();
                    }}
                    className="w-full mt-6 border-2 border-dark py-3 font-bold hover:bg-dark hover:text-white transition-colors uppercase tracking-widest"
                >
                    {text.btn_download}
                </button>
            </div>
        </div>
      )}
    </>
  );
}