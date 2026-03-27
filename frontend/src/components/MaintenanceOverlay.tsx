// components/MaintenanceOverlay.tsx
'use client';

import { useLanguage } from "@/context/LanguageContext";

const MAINTENANCE_TEXT = {
  TH: {
    logo_img: "/images/logo-th.png", 
    title: "ขออภัยในความไม่สะดวก",
    message: "ขณะนี้ 'บางกอกทวิกาล'ได้รับข้อเสนอแนะตามเป้าหมายแล้ว \nทางเราขอปิดระบบชั่วคราวเพื่อพัฒนาและปรับปรุงระบบให้สมบูรณ์ยิ่งขึ้นต่อไป",
    sub: "ขอบพระคุณที่ร่วมเป็นส่วนหนึ่งของการเดินทางย้อนเวลา",
    btn: "ติดตามความคืบหน้า"
  },
  ENG: {
    logo_img: "/images/logo-en.png",
    title: "TEMPORARY MAINTENANCE",
    message: "Due to overwhelming feedback and high demand,\nwe are temporarily closing to process your suggestions\nand improve the experience for everyone.",
    sub: "Thank you for being part of our time-travel journey.",
    btn: "Follow Updates"
  }
};

export default function MaintenanceOverlay({ lang }: { lang: 'TH' | 'ENG' }) {
  const { language } = useLanguage();
  const text = MAINTENANCE_TEXT[language];
  const fontClass = language === 'ENG' ? 'font-merri' : 'font-krub';

  return (
    <div className="fixed inset-0 z-[100] bg-[#0A0A0A] flex flex-col justify-center items-center text-center px-6 overflow-hidden">
      
      {/* 📺 Background Texture (ใช้ตัวเดิมแต่ปรับให้มืดสนิทขึ้น) */}
      <div 
        className="absolute inset-0 -z-10 opacity-[0.2] pointer-events-none grayscale"
        style={{ 
          backgroundImage: "url('/images/grunge-paper-background3.jpg')", 
          backgroundSize: 'cover'
        }}
      ></div>
      
      {/* 🖼️ Logo Section */}
      <div className="relative w-full flex justify-center px-4 mt-3 mb-6 md:mb-12">
        <img 
          src={text.logo_img} 
          alt="Bangkok EraVision Logo" 
          // invert(1) จะเปลี่ยนสีดำเป็นสีขาวทันที!
          className="w-[85%] sm:w-[60%] md:w-[450px] h-auto object-contain invert-[0.9] sepia-[0.3] contrast-[1.1]"
        />
      </div>

      <div className="relative z-10 max-w-6xl">
        <h1 className={`text-3xl md:text-5xl lg:text-6xl font-bold text-gold mb-6 md:mb-10 tracking-tight uppercase drop-shadow-sm ${fontClass}`}>
          {text.title}
        </h1>
        
        <p className={`text-base md:text-xl lg:text-3xl text-white/90 leading-relaxed mb-12 font-light px-4 
            whitespace-normal text-balance ${fontClass}`}>
            {text.message.split('\n').map((line, i) => (
            <span key={i}>
            {line}
            {/* ✅ สั่งให้ขึ้นบรรทัดใหม่เฉพาะในหน้าจอคอม (md:block) แต่ในมือถือให้เป็นช่องว่างปกติ */}
            {i === 0 && <br className="hidden md:block" />}
            </span>
        ))}
        </p>

        {/* Ornament Divider */}
        <div className="flex items-center justify-center gap-4 mb-12 opacity-40">
           <div className="h-[1px] w-full bg-gold"></div>
           <div className="text-gold text-2xl">⚜</div>
           <div className="h-[1px] w-full bg-gold"></div>
        </div>

        <p className={`text-sm md:text-base text-gold tracking-[0.4em] uppercase mb-12 opacity-70 ${fontClass}`}>
          {text.sub}
        </p>
      </div>

    </div>
  );
}