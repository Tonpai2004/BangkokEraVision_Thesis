'use client';
import { useState, useRef } from 'react';

const LOCATIONS = [
  "อนุสาวรีย์ประชาธิปไตย", "ศาลาเฉลิมกรุง", "เสาชิงช้า & วัดสุทัศน์",
  "เยาวราช", "ถนนข้าวสาร", "ป้อมพระสุเมรุ", "สนามหลวง", "พิพิธภัณฑสถานแห่งชาติ"
];

interface UploadSectionProps {
  onAnalysisResult?: (result: any) => void;
}

export default function UploadSection({ onAnalysisResult }: UploadSectionProps) {
  const [selectedLocation, setSelectedLocation] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  
  // แยก state loading
  const [verifying, setVerifying] = useState(false);
  const [generating, setGenerating] = useState(false);
  
  const [result, setResult] = useState<{image: string, desc: string, location: string} | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedLocation) return alert("Please select location and image.");

    // เริ่มการตรวจสอบ
    setVerifying(true);
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('location', selectedLocation);

    try {
      // 1. เรียก API ตรวจสอบ (เร็ว)
      const verifyRes = await fetch('http://localhost:5000/verify', {
        method: 'POST',
        body: formData,
      });
      
      const verifyData = await verifyRes.json();
      
      // ส่งผลการวิเคราะห์กลับไปทันที (ไม่ว่าจะผ่านหรือไม่ผ่าน)
      if (onAnalysisResult) {
        onAnalysisResult(verifyData);
      }

      setVerifying(false); // จบการโหลดขั้นแรก

      // ถ้าตรวจสอบไม่ผ่าน หรือมีปัญหา ให้หยุดแค่นี้
      if (!verifyRes.ok || verifyData.status === 'rejected') {
        console.warn("Analysis Rejected/Failed");
        return; 
      }

      // 2. ถ้าผ่าน! เริ่มเจนรูปต่อทันที (ช้า)
      setGenerating(true); // เปิด Loading Overlay ตัวใหม่ (หรือใช้ตัวเดิมแล้วเปลี่ยนข้อความ)

      // ต้องสร้าง FormData ใหม่สำหรับ request ที่ 2 (เนื่องจาก stream ถูกอ่านไปแล้วในบาง browser)
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
      }

    } catch (err: any) {
      console.error(err);
      alert(`Error: ${err.message}`);
    } finally {
      setVerifying(false);
      setGenerating(false);
    }
  };

  return (
    <>
      <form onSubmit={handleGenerate} className="w-full max-w-2xl mx-auto mt-8">
        
        {/* กรอบเส้นประ */}
        <div className="dashed-box-container">
            {/* Location Select */}
            <div className="flex justify-between items-end py-2 font-bold text-xl md:text-2xl serif-font">
            <label htmlFor="location-select" className="whitespace-nowrap mr-4">Choose a location</label>
            <div className="relative w-full flex-1 border-b-2 border-dark">
                <select 
                    id="location-select"
                    value={selectedLocation} 
                    onChange={(e) => setSelectedLocation(e.target.value)}
                    className="w-full bg-transparent border-none outline-none text-right font-serif font-bold cursor-pointer appearance-none pr-8 pb-1 truncate text-dark"
                    required
                >
                    <option value="" disabled></option>
                    {LOCATIONS.map(loc => <option key={loc} value={loc}>{loc}</option>)}
                </select>
                <span className="absolute right-0 bottom-2 pointer-events-none text-sm">▼</span>
            </div>
            </div>
            
            <div className="h-6"></div> {/* Spacer */}

            {/* File Upload Header */}
            <div className="flex justify-between items-end py-2 font-bold text-xl md:text-2xl serif-font border-b-2 border-dark relative">
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

            {/* Drop Zone / Preview */}
            <div 
                // แก้ไขบรรทัดนี้: เปลี่ยนจาก border-transparent เป็น border-dashed border-gray-400
                className="min-h-[250px] flex justify-center items-center cursor-pointer hover:bg-[#EAE7DB] transition-colors border-2 border-dashed border-gray-400 hover:border-dark p-4"
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                aria-label="Drop zone for image upload"
            >
                {preview ? (
                    <img src={preview} alt="Preview" className="max-h-[300px] w-auto object-contain border-2 border-dark shadow-md" />
                ) : (
                    <div className="flex flex-col items-center opacity-50">
                        <span className="text-6xl mb-2">⬆</span>
                        <span className="text-sm font-mono">Click or Drag photo here</span>
                    </div>
                )}
            </div>
        </div>

        {/* Submit Button */}
        <button 
            type="submit" 
            disabled={verifying || generating}
            className="w-full mt-8 bg-accent hover:bg-accent-hover text-white py-4 text-2xl md:text-3xl serif-font transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-[4px_4px_0px_#2C2C2C] active:translate-y-[2px] active:shadow-[2px_2px_0px_#2C2C2C]"
        >
            {verifying ? "VERIFYING..." : generating ? "GENERATING..." : "GENERATE"}
        </button>
      </form>

      {/* Loading Overlay */}
      {(verifying || generating) && (
        <div className="fixed inset-0 bg-black/90 z-50 flex flex-col justify-center items-center text-white">
            <div className="text-4xl md:text-6xl font-bold mb-6 animate-blink serif-font tracking-widest text-gold">
                {verifying ? "ANALYZING" : "RECONSTRUCTING"}
            </div>
            <p className="font-mono text-sm md:text-base opacity-70 tracking-wider">
                {verifying ? "Checking Location Match..." : "Travel back to 1960s..."}
            </p>
        </div>
      )}

      {/* Result Modal (Success Only) */}
      {result && (
        <div className="fixed inset-0 bg-black/85 z-50 flex justify-center items-center p-4" onClick={() => setResult(null)}>
            <div className="bg-background p-6 md:p-8 max-w-3xl w-full border-[3px] border-dark shadow-[15px_15px_0px_rgba(0,0,0,0.5)] relative max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                <button onClick={() => setResult(null)} className="absolute top-4 right-4 text-4xl font-bold leading-none hover:text-accent">&times;</button>
                <h3 className="serif-font text-2xl md:text-4xl font-bold mb-6 mt-2 text-center italic">{result.location}</h3>
                <div className="border-[3px] border-dark mb-6 bg-black">
                    <img src={result.image} alt="Generated" className="w-full h-auto block" />
                </div>
                <div className="bg-paper p-6 border border-gray-400 font-mono text-sm md:text-base leading-relaxed text-justify">
                    <span className="font-bold block mb-2 text-lg">Historical Context:</span>
                    {result.desc}
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
                    Download Image
                </button>
            </div>
        </div>
      )}
    </>
  );
}