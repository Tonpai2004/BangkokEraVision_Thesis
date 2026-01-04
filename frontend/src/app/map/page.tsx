"use client";

import Navbar from "@/components/Navbar";
import { useLanguage } from "@/context/LanguageContext";
import { useState } from "react";
import { TransformWrapper, TransformComponent, useControls } from "react-zoom-pan-pinch";

const MAP_LOCATIONS = [
  { id: 1, th: "อนุสาวรีย์ประชาธิปไตย", en: "Democracy Monument", top: "45%", left: "55%" },
  { id: 2, th: "ศาลาเฉลิมกรุง", en: "Sala Chalermkrung", top: "70%", left: "60%" },
  { id: 3, th: "เสาชิงช้า & วัดสุทัศน์", en: "Giant Swing & Wat Suthat", top: "55%", left: "58%" },
  { id: 4, th: "ถนนข้าวสาร", en: "Khaosan Road", top: "35%", left: "45%" },
  { id: 5, th: "ป้อมพระสุเมรุ", en: "Phra Sumen Fort", top: "16.5%", left: "16%" },
  { id: 6, th: "พิพิธภัณฑสถานแห่งชาติ", en: "National Museum", top: "40%", left: "30%" },
  { id: 7, th: "ถนนเยาวราช", en: "Yaowarat (Chinatown)", top: "80%", left: "70%" },
  { id: 8, th: "สนามหลวง", en: "Sanam Luang", top: "45%", left: "35%" },
];

const Controls = () => {
  const { zoomIn, zoomOut, resetTransform } = useControls();
  return (
    <div className="absolute bottom-4 right-4 flex flex-col gap-2 z-10">
      <button onClick={() => zoomIn()} className="w-10 h-10 bg-white/80 text-dark font-bold text-xl shadow-md hover:scale-105 transition-transform">+</button>
      <button onClick={() => zoomOut()} className="w-10 h-10 bg-white/80 text-dark font-bold text-xl shadow-md hover:scale-105 transition-transform">-</button>
      <button onClick={() => resetTransform()} className="w-10 h-10 bg-white/80 text-dark border-2 border-dark font-bold text-xs shadow-md hover:scale-105 transition-transform">RESET</button>
    </div>
  );
};

export default function MapPage() {
  const { language } = useLanguage();
  const [activePin, setActivePin] = useState<number | null>(null);

  return (
    <main className="w-full px-4 md:px-6 pb-20 mx-auto">
      <Navbar />
      
      <h1 className="text-center text-3xl md:text-5xl serif-font font-bold mt-8 mb-6 md:mt-12 md:mb-10 italic">
        {language === 'TH' ? "แผนที่ประวัติศาสตร์" : "Historical Map"}
      </h1>

      <div className="w-full max-w-5xl mx-auto bg-paper border-[4px] border-dark p-2 shadow-[10px_10px_0px_rgba(0,0,0,0.2)]">
        
        <div className="w-full h-[500px] md:h-[600px] relative overflow-hidden bg-dark cursor-grab active:cursor-grabbing">
             
             <TransformWrapper
                initialScale={0.5}
                minScale={0.5} // ปรับให้ซูมออกได้เยอะขึ้น จะได้หาภาพเจอเวลามันหลุดจอ
                maxScale={8}
                centerOnInit={true}
                wheel={{ step: 0.1 }}
                limitToBounds={true} // ปลดล็อกขอบเขต ให้ลากไปไหนก็ได้อิสระ
             >
                <Controls />
                <TransformComponent wrapperClass="!w-full !h-full" contentClass="!w-full flex items-center justify-center">
                    
                    <div className="relative w-auto h-auto inline-block">
                        
                        {/* รูปภาพ */}
                        <img 
                            src="/images/map.png" 
                            alt="Phra Nakhon Map"
                            className="block max-w-none w-[800px] md:w-[1200px] h-auto object-contain"
                            draggable={false}
                        />

                        {/* หมุด */}
                        {MAP_LOCATIONS.map((loc) => (
                            <div 
                                key={loc.id}
                                className="absolute group cursor-pointer origin-bottom"
                                style={{ top: loc.top, left: loc.left, transform: 'translate(-50%, -100%)' }}
                                onMouseEnter={() => setActivePin(loc.id)}
                                onMouseLeave={() => setActivePin(null)}
                                onMouseDown={(e) => e.stopPropagation()} 
                                onTouchStart={(e) => e.stopPropagation()}
                            >
                                <div className="text-4xl md:text-5xl drop-shadow-md text-red-600 hover:scale-125 transition-transform animate-bounce-slow">
                                    📍
                                </div>

                                <div className={`
                                    absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-max px-3 py-1 
                                    bg-black/90 text-white text-xs md:text-sm font-mono tracking-wide border border-gold
                                    transition-opacity duration-200 pointer-events-none z-50 rounded shadow-lg
                                    ${activePin === loc.id ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
                                `}>
                                    {language === 'TH' ? loc.th : loc.en}
                                </div>
                            </div>
                        ))}
                    </div>
                </TransformComponent>
             </TransformWrapper>

             <div className="absolute top-4 left-4 bg-white/80 backdrop-blur-sm p-2 border border-dark text-xs font-mono pointer-events-none z-10">
                {language === 'TH' ? "🖱️ เลื่อนเมาส์เพื่อซูม / คลิกแล้วลากเพื่อขยับ" : "🖱️ Scroll to Zoom / Drag to Pan"}
             </div>
        </div>
      </div>
      
      <div className="mt-8 text-center max-w-xl mx-auto">
        <p className="font-mono text-sm md:text-base opacity-70">
          {language === 'TH' 
            ? "สำรวจสถานที่สำคัญทางประวัติศาสตร์ในเขตพระนคร เลือกหมุดเพื่อดูบริบทในอดีต"
            : "Explore the historical landmarks of Phra Nakhon district. Hover over a pin to view location name."}
        </p>
      </div>
    </main>
  );
}