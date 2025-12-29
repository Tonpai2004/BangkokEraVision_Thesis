'use client';
import { useState, useRef } from 'react';

const LOCATIONS = [
  "อนุสาวรีย์ประชาธิปไตย", "ศาลาเฉลิมกรุง", "เสาชิงช้า & วัดสุทัศน์",
  "เยาวราช", "ถนนข้าวสาร", "ป้อมพระสุเมรุ", "สนามหลวง", "พิพิธภัณฑสถานแห่งชาติ"
];

// เพิ่ม Interface สำหรับ props
interface UploadSectionProps {
  onAnalysisResult?: (result: any) => void;
}

export default function UploadSection({ onAnalysisResult }: UploadSectionProps) {
  const [selectedLocation, setSelectedLocation] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
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

    setLoading(true);
    const formData = new FormData();
    formData.append('image', file);
    formData.append('location', selectedLocation);

    try {
      const res = await fetch('http://localhost:5000/process', {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      
      // 1. ส่งผลลัพธ์ (ไม่ว่าจะผ่านหรือไม่ผ่าน) กลับไปที่ page.tsx เพื่อแสดง Dashboard
      if (onAnalysisResult) {
        onAnalysisResult(data);
      }

      // 2. ตรวจสอบว่าผ่านหรือไม่ (ถ้าไม่ผ่าน ให้หยุดตรงนี้ ไม่ต้องโชว์ Modal)
      if (!res.ok) {
        // กรณี Classifier Rejected: หน้า page.tsx จะแสดงผล Error ให้เอง
        // เราแค่ log ไว้ และออกจาก function
        console.warn("Analysis Failed:", data);
        return; 
      }
      
      // 3. ถ้าผ่าน (Success): เซ็ตข้อมูลเพื่อแสดง Modal รูปภาพ
      setResult({
        image: data.image,
        desc: data.description,
        location: data.location_name
      });

    } catch (err: any) {
      console.error(err);
      
      // กรณี System Error (เช่น ต่อ Server ไม่ได้)
      const errorData = { 
         status: 'error', 
         title: 'Connection Error', 
         details: err.message || "Cannot connect to server" 
      };

      // แจ้ง page.tsx
      if (onAnalysisResult) {
         onAnalysisResult(errorData);
      }
      
      alert(`⚠️ System Error:\n${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <form onSubmit={handleGenerate} className="dashed-box p-6 md:p-8 relative transition-all hover:shadow-lg">
        {/* Location Select */}
        <div className="flex justify-between items-center py-2 font-bold text-lg md:text-xl">
          <label htmlFor="location-select">Choose a location</label>
          <div className="relative w-1/2">
            <select 
                id="location-select"
                title="Select Location"
                aria-label="Choose a historical location"
                value={selectedLocation} 
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full bg-transparent border-none outline-none text-right font-mono cursor-pointer appearance-none pr-6 truncate"
                required
            >
                <option value="" disabled>-- Select --</option>
                {LOCATIONS.map(loc => <option key={loc} value={loc}>{loc}</option>)}
            </select>
            <span className="absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none text-sm">▼</span>
          </div>
        </div>
        <hr className="thin-line" />

        {/* File Upload */}
        <div className="flex justify-between items-center py-2 font-bold text-lg md:text-xl">
            <label htmlFor="file-upload">Upload your Photo</label>
            <button 
                type="button" 
                onClick={() => fileInputRef.current?.click()} 
                className="text-3xl hover:scale-110 transition-transform p-2"
                title="Click to select image"
            >
                📷
            </button>
            <input 
                id="file-upload"
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                accept="image/*" 
                className="hidden"
                aria-label="Upload image"
            />
        </div>
        <hr className="thin-line" />

        {/* Drop Zone / Preview */}
        <div 
            className="min-h-[250px] flex justify-center items-center cursor-pointer hover:bg-[#EAE7DB] transition-colors border-2 border-transparent hover:border-dashed hover:border-gray-400 p-4"
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

        {/* Submit Button */}
        <button 
            type="submit" 
            disabled={loading}
            className="w-full mt-8 bg-accent hover:bg-accent-hover text-white py-4 text-2xl md:text-3xl serif-font transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-[4px_4px_0px_#2C2C2C] active:translate-y-[2px] active:shadow-[2px_2px_0px_#2C2C2C]"
        >
            {loading ? "PROCESSING..." : "GENERATE"}
        </button>
      </form>

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/90 z-50 flex flex-col justify-center items-center text-white">
            <div className="text-4xl md:text-6xl font-bold mb-6 animate-blink serif-font tracking-widest text-gold">LOADING</div>
            <p className="font-mono text-sm md:text-base opacity-70 tracking-wider">
                Verifying Location & Reconstructing 1960s...
            </p>
        </div>
      )}

      {/* Result Modal (Success Only) */}
      {result && (
        <div className="fixed inset-0 bg-black/85 z-50 flex justify-center items-center p-4" onClick={() => setResult(null)}>
            <div 
                className="bg-background p-6 md:p-8 max-w-3xl w-full border-[3px] border-dark shadow-[15px_15px_0px_rgba(0,0,0,0.5)] relative max-h-[90vh] overflow-y-auto" 
                onClick={e => e.stopPropagation()}
            >
                <button 
                    onClick={() => setResult(null)} 
                    className="absolute top-4 right-4 text-4xl font-bold leading-none hover:text-accent"
                >
                    &times;
                </button>
                
                <h3 className="serif-font text-2xl md:text-4xl font-bold mb-6 mt-2 text-center italic">
                    {result.location}
                </h3>
                
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