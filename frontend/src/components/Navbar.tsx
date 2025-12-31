'use client';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

// 1. แก้ไข Interface: รับค่าภาษาที่ถูกเลือก (lang) แทนที่จะเป็น void
interface NavbarProps {
  language: 'TH' | 'ENG';
  onLanguageChange: (lang: 'TH' | 'ENG') => void; // เปลี่ยนชื่อจาก onToggleLanguage
}

// 2. รับ Props เข้ามาในฟังก์ชัน
export default function Navbar({ language, onLanguageChange }: NavbarProps) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // State สำหรับ Dropdown ภาษา
  const [isLangDropdownOpen, setIsLangDropdownOpen] = useState(false);
  
  const isActive = (path: string) => 
    pathname === path ? "underline decoration-2 underline-offset-4" : "";

  const Logo = () => (
    <div className="logo select-none cursor-pointer">
       <Image 
         src="/images/headlogo.png" alt="Bangkok EraVision Logo" width={80} height={80} className="object-contain"
       />
    </div>
  );

  // ฟังก์ชันเลือกภาษาแล้วปิด Dropdown
  const handleSelectLang = (lang: 'TH' | 'ENG') => {
    onLanguageChange(lang);
    setIsLangDropdownOpen(false);
    setIsMobileMenuOpen(false); // ปิดเมนูมือถือด้วย (ถ้าเปิดอยู่)
  };

  return (
    <nav className="w-full text-dark font-serif md:mb-7">
      
      {/* --- DESKTOP --- */}
      <div className="hidden md:flex flex-col items-center w-full">
        <div className="py-8"><Logo /></div>

        <div className="w-full border-y-[2px] border-dark flex justify-between items-center px-3 py-3">
          <div className="flex gap-12 font-bold italic text-xl tracking-wide">
            <Link href="/" className={`${isActive('/')} hover:opacity-70 transition-opacity`}>Home</Link>
            <Link href="/map" className={`${isActive('/map')} hover:opacity-70 transition-opacity`}>Map</Link>
            <Link href="/about" className={`${isActive('/about')} hover:opacity-70 transition-opacity`}>About Us</Link>
          </div>

          {/* 3. Dropdown ภาษา (Desktop) */}
          <div className="relative">
            <button 
              onClick={() => setIsLangDropdownOpen(!isLangDropdownOpen)}
              className="font-bold italic text-lg cursor-pointer hover:text-gray-600 select-none min-w-[60px] text-right flex items-center gap-2"
            >
              {language} <span className="text-sm">▼</span>
            </button>

            {/* ตัว Dropdown Box */}
            {isLangDropdownOpen && (
              <div className="absolute right-0 top-full mt-2 w-24 bg-background border-[2px] border-dark shadow-[4px_4px_0px_rgba(0,0,0,1)] flex flex-col z-50">
                <button 
                  onClick={() => handleSelectLang('ENG')}
                  className={`py-2 px-4 text-left hover:bg-gold hover:text-white transition-colors font-bold ${language === 'ENG' ? 'bg-gray-200' : ''}`}
                >
                  ENG
                </button>
                <button 
                  onClick={() => handleSelectLang('TH')}
                  className={`py-2 px-4 text-left hover:bg-gold hover:text-white transition-colors font-bold ${language === 'TH' ? 'bg-gray-200' : ''}`}
                >
                  TH
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* --- MOBILE --- */}
      <div className="md:hidden">
        <div className="flex justify-between items-center py-5 border-b-[2px] border-dark relative z-20">
          <Logo />
          <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 focus:outline-none">
             {/* ... (Icon SVG เหมือนเดิม) ... */}
             <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isMobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
              </svg>
          </button>
        </div>

        <div className={`flex flex-col items-center gap-6 py-6 border-b-[2px] border-dark transition-all duration-300 ease-in-out origin-top ${isMobileMenuOpen ? 'opacity-100 max-h-96' : 'opacity-0 max-h-0 overflow-hidden'}`}>
            <Link href="/" onClick={() => setIsMobileMenuOpen(false)} className={`${isActive('/')} text-xl font-bold italic`}>Home</Link>
            <Link href="/map" onClick={() => setIsMobileMenuOpen(false)} className={`${isActive('/map')} text-xl font-bold italic`}>Map</Link>
            <Link href="/about" onClick={() => setIsMobileMenuOpen(false)} className={`${isActive('/about')} text-xl font-bold italic`}>About Us</Link>
            
            {/* Mobile Language Options (แสดงเป็นปุ่มแยกเลยเพื่อให้กดยง่าย) */}
            <div className="pt-4 border-t border-gray-300 w-1/2 flex justify-center gap-6">
                <button 
                  onClick={() => handleSelectLang('ENG')}
                  className={`font-bold text-lg ${language === 'ENG' ? 'underline decoration-gold decoration-4' : 'opacity-50'}`}
                >
                  ENG
                </button>
                <span className="text-gray-400">|</span>
                <button 
                   onClick={() => handleSelectLang('TH')}
                   className={`font-bold text-lg ${language === 'TH' ? 'underline decoration-gold decoration-4' : 'opacity-50'}`}
                >
                  TH
                </button>
            </div>
        </div>
      </div>
    </nav>
  );
}