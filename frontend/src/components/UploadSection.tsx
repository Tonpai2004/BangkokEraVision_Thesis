'use client';
import { useState, useRef } from 'react';

const LOCATIONS = [
  "อนุสาวรีย์ประชาธิปไตย", "ศาลาเฉลิมกรุง", "เสาชิงช้า & วัดสุทัศน์",
  "เยาวราช", "ถนนข้าวสาร", "ป้อมพระสุเมรุ", "สนามหลวง", "พิพิธภัณฑสถานแห่งชาติ"
];

// กำหนด State ของกระบวนการทั้งหมด
type ProcessStatus = 'idle' | 'verifying' | 'verified_pass' | 'verified_fail' | 'generating' | 'finished';

// 1. ✅ เพิ่ม Interface ตรงนี้
interface UploadSectionProps {
  currentLang: 'TH' | 'ENG';
}

export default function UploadSection({ currentLang }: UploadSectionProps) {
  const [selectedLocation, setSelectedLocation] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  
  // State ใหม่ คุม Flow ทั้งหมด
  const [status, setStatus] = useState<ProcessStatus>('idle');
  const [failReason, setFailReason] = useState<string>("");
  const [passDetails, setPassDetails] = useState<{score: number, place: string} | null>(null);

  const [result, setResult] = useState<{image: string, desc: string, location: string} | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
      // Reset status เมื่อเลือกรูปใหม่
      if (status === 'verified_fail' || status === 'finished') {
        setStatus('idle');
        setResult(null);
      }
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedLocation) return alert("Please select location and image.");

    setStatus('verifying'); // เริ่มหมุนติ้วๆ
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('location', selectedLocation);

    formData.append('language', currentLang);

    try {
      // 1. เรียก API ตรวจสอบ
      const verifyRes = await fetch('http://localhost:5000/verify', {
        method: 'POST',
        body: formData,
      });
      const verifyData = await verifyRes.json();

      // เช็คผลลัพธ์
      if (!verifyRes.ok || verifyData.status === 'rejected') {
        // --- กรณีไม่ผ่าน ---
        setFailReason(verifyData.details || verifyData.error || "Unknown Error");
        setStatus('verified_fail'); // เปลี่ยนหน้า Overlay เป็นสีแดง
        return; 
      }

      // --- กรณีผ่าน ---
      setPassDetails({
        score: verifyData.analysis_report?.score || 0,
        place: verifyData.analysis_report?.detected_place || "Confirmed"
      });
      setStatus('verified_pass'); // เปลี่ยนหน้า Overlay เป็นสีเขียว (โชว์สัก 2 วิ)

      // หน่วงเวลา 2 วินาที ให้ user เห็นว่า "ผ่านนะ" ก่อนไปต่อ
      await new Promise(r => setTimeout(r, 2000));

      // 2. เริ่มเจนรูป (เปลี่ยน Overlay เป็น Generating)
      setStatus('generating');

      const genFormData = new FormData();
      genFormData.append('image', file);
      genFormData.append('location', selectedLocation);

      const genRes = await fetch('http://localhost:5000/generate', {
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
        setStatus('finished'); // ปิด Overlay
      } else {
         throw new Error("Generation failed without error message");
      }

    } catch (err: any) {
      console.error(err);
      setFailReason(err.message);
      setStatus('verified_fail');
    }
  };

  return (
    <>
      <form onSubmit={handleGenerate} className="w-full mx-auto mt-8">
        
        {/* --- ส่วน Form เหมือนเดิม --- */}
        <div className="dashed-box-container">
            {/* Location Select */}
            <div className="flex justify-between items-end py-2 font-bold text-xl md:text-2xl serif-font border-b-2 border-dark">
            <label htmlFor="location-select" className="whitespace-nowrap mr-4">Choose a location</label>
            <div className="relative w-full flex-1">
                <select 
                    id="location-select"
                    value={selectedLocation} 
                    onChange={(e) => setSelectedLocation(e.target.value)}
                    className="w-full bg-transparent border-none outline-none text-right font-serif font-bold cursor-pointer appearance-none pr-8 truncate text-dark"
                    required
                >
                    <option value="" disabled></option>
                    {LOCATIONS.map(loc => <option key={loc} value={loc}>{loc}</option>)}
                </select>
                <span className="absolute right-0 bottom-2 pointer-events-none text-sm ">▼</span>
            </div>
            </div>
            
            <div className="h-1"></div>

            {/* File Upload Header */}
            <div className="flex justify-between items-end pb-2 font-bold text-xl md:text-2xl mb-3 serif-font border-b-2 border-dark relative">
                <label htmlFor="file-upload" className="flex-1">Upload your Photo</label>
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
                        <span className="text-sm font-mono">Click or Drag photo here</span>
                    </div>
                )}
            </div>
        </div>

        {/* Submit Button */}
        <button 
            type="submit" 
            disabled={status !== 'idle' && status !== 'verified_fail' && status !== 'finished'}
            className="w-full mt-8 bg-dark text-white text-bold py-4 text-2xl md:text-3xl serif-font transition-colors disabled:opacity-50 disabled:cursor-not-allowed active:translate-y-[2px] active:shadow-[2px_2px_0px_#2C2C2C]"
        >
            {status === 'generating' ? "GENERATING..." : "GENERATE"}
        </button>
      </form>

      {/* --- ALL-IN-ONE OVERLAY --- */}
      {status !== 'idle' && status !== 'finished' && (
        <div className="fixed inset-0 bg-black/95 z-50 flex flex-col justify-center items-center text-white px-4 text-center">
            
            {/* 1. STATE: VERIFYING (กำลังตรวจ) */}
            {status === 'verifying' && (
                <>
                    <div className="text-4xl md:text-6xl font-bold mb-6 animate-pulse serif-font tracking-widest text-gold">
                        ANALYZING SCENE
                    </div>
                    <p className="font-mono text-sm md:text-base opacity-70 tracking-wider">
                        Verifying historical compatibility...
                    </p>
                </>
            )}

            {/* 2. STATE: VERIFIED PASS (ผ่านฉลุย - โชว์แป๊บเดียว) */}
            {status === 'verified_pass' && (
                <>
                    <div className="text-6xl mb-4 text-green-500">✓</div>
                    <div className="text-3xl md:text-5xl font-bold mb-4 serif-font text-green-400">
                        VERIFICATION PASSED
                    </div>
                    <div className="font-mono text-xl mb-2">
                        {passDetails?.place}
                    </div>
                    <div className="font-mono text-sm opacity-70">
                        Confidence Score: {passDetails?.score.toFixed(1)}%
                    </div>
                    <p className="mt-8 text-sm animate-bounce text-gold">
                        Constructing 1960s Simulation...
                    </p>
                </>
            )}

            {/* 3. STATE: VERIFIED FAIL (ไม่ผ่าน - ค้างไว้ให้กดปิด) */}
            {status === 'verified_fail' && (
                <div className="border-2 border-accent p-8 max-w-2xl bg-black">
                    <div className="text-6xl mb-4 text-accent">✕</div>
                    <div className="text-3xl md:text-5xl font-bold mb-6 serif-font text-accent">
                        VERIFICATION REJECTED
                    </div>
                    <p className="font-mono text-lg md:text-xl text-white mb-8 leading-relaxed">
                        {failReason}
                    </p>
                    <button 
                        onClick={() => setStatus('idle')}
                        className="border border-white px-8 py-3 hover:bg-white hover:text-black font-mono tracking-widest transition-colors uppercase"
                    >
                        Try Another Photo
                    </button>
                </div>
            )}

            {/* 4. STATE: GENERATING (กำลังเจนรูป) */}
            {status === 'generating' && (
                <>
                    <div className="text-4xl md:text-6xl font-bold mb-6 animate-blink serif-font tracking-widest text-gold">
                        RECONSTRUCTING
                    </div>
                    <p className="font-mono text-sm md:text-base opacity-70 tracking-wider">
                        Applying Kodak Chrome 64 film grain...
                    </p>
                </>
            )}
        </div>
      )}

      {/* --- RESULT MODAL (Success) --- */}
      {result && (
        <div className="fixed inset-0 bg-black/85 z-50 flex justify-center items-center p-4" onClick={() => setResult(null)}>
            <div className="bg-background p-6 md:p-8 max-w-3xl w-full border-[3px] border-dark shadow-[15px_15px_0px_rgba(0,0,0,0.5)] relative max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                <button onClick={() => setResult(null)} className="absolute top-4 right-4 text-4xl font-bold leading-none hover:text-accent">&times;</button>
                <h3 className="serif-font text-2xl md:text-4xl font-bold mb-6 mt-2 text-center italic">{result.location}</h3>
                <div className="border-[3px] border-dark mb-6 bg-black">
                    <img src={result.image} alt="Generated" className="w-full h-auto block" />
                </div>
                {/* <div className="bg-paper p-6 border border-gray-400 font-mono text-sm md:text-base leading-relaxed text-justify">
                    <span className="font-bold block mb-2 text-lg">Historical Context:</span>
                    {result.desc}
                </div> */}
                <button 
                    onClick={() => {
                        const link = document.createElement('a');
                        link.href = result.image;
                        link.download = `bangkok-1960s-${Date.now()}.png`;
                        link.click();
                    }}
                    className="w-full mt-6 border-2 border-dark py-3 font-bold hover:bg-dark hover:text-white transition-colors uppercase tracking-widest"
                >
                    Download Image
                </button>
            </div>
        </div>
      )}
    </>
  );
}