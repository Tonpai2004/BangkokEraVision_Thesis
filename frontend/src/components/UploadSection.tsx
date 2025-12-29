'use client';
import { useState, useRef } from 'react';

const LOCATIONS = [
  "อนุสาวรีย์ประชาธิปไตย", "ศาลาเฉลิมกรุง", "เสาชิงช้า & วัดสุทัศน์",
  "เยาวราช", "ถนนข้าวสาร", "ป้อมพระสุเมรุ", "สนามหลวง", "พิพิธภัณฑสถานแห่งชาติ"
];

export default function UploadSection() {
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
      const res = await fetch('http://localhost:5000/process', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResult({ image: data.image, desc: data.description, location: data.location_name });
    } catch (err) {
      alert("System Error: Cannot connect to Backend.");
      console.error(err);
    } finally {
      setLoading(false);
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
                className="min-h-[300px] flex justify-center items-center cursor-pointer hover:bg-dark/5 transition-colors mt-8"
                onClick={() => fileInputRef.current?.click()}
            >
                {preview ? (
                    <img src={preview} alt="Preview" className="max-h-[300px] w-auto object-contain border-4 border-dark shadow-md p-2 bg-white" />
                ) : (
                    // ไอคอนลูกศรชี้ขึ้น
                    <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-dark opacity-80">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                )}
            </div>
        </div>

        {/* Submit Button (สีแดง) */}
        <button 
            type="submit" 
            disabled={loading}
            className="w-full mt-10 bg-accent hover:bg-[#B83629] text-white py-4 text-3xl serif-font font-bold transition-colors disabled:opacity-50 shadow-sm"
        >
            {loading ? "PROCESSING..." : "Generate"}
        </button>
      </form>

      {/* Loading Overlay & Result Modal (คงเดิม) */}
      {loading && (
        <div className="fixed inset-0 bg-black/90 z-50 flex flex-col justify-center items-center text-white">
            <div className="text-5xl font-bold mb-6 animate-pulse serif-font tracking-widest text-gold">LOADING</div>
        </div>
      )}
      {result && (
        <div className="fixed inset-0 bg-black/85 z-50 flex justify-center items-center p-4" onClick={() => setResult(null)}>
            <div className="bg-[#F0EAD6] p-6 max-w-3xl w-full border-[4px] border-dark shadow-xl relative max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                <button onClick={() => setResult(null)} className="absolute top-2 right-4 text-5xl leading-none hover:text-accent">&times;</button>
                <h3 className="serif-font text-3xl md:text-4xl font-bold mb-6 mt-4 text-center italic">{result.location}</h3>
                <div className="border-[3px] border-dark mb-6 p-2 bg-white"><img src={result.image} alt="Generated" className="w-full h-auto block" /></div>
                <div className="p-4 border-t-2 border-b-2 border-dark font-mono text-lg leading-relaxed text-justify bg-[#EAE7DB]">{result.desc}</div>
            </div>
        </div>
      )}
    </>
  );
}