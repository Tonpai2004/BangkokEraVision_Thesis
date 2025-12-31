"use client";

import Navbar from "@/components/Navbar";
import UploadSection from "@/components/UploadSection";
import Link from "next/link";
import { useState } from "react";

export default function Home() {

  // 1. สร้าง State ภาษา (ค่าเริ่มต้น ENG หรือ TH ตามใจชอบ)
  const [language, setLanguage] = useState<'TH' | 'ENG'>('ENG');

  // 2. ฟังก์ชันสลับภาษา
  const handleLanguageChange = (lang: 'TH' | 'ENG') => {
    setLanguage(lang);
  };

  return (
    <main className="w-full px-6 pb-20 mx-auto">
      <Navbar 
        language={language} 
        onLanguageChange={handleLanguageChange} 
      />

      {/* Hero Section */}
      <section className="mt-0 mb-0 md:mt-10 md:mb-7">
        <h1 className="bg-dark text-white p-3 text-center text-xl md:text-5xl font-bold tracking-[0.2em] mb-8 py-8 font-mono">
          WHAT IS BANGKOK ERAVISION?
        </h1>
        <div className="flex flex-col md:flex-row gap-8 items-stretch mt-10">
          {/* ส่วนที่ 1: กล่องรูปภาพ */}
          {/* แก้: ลบ md:w-[670px] ใส่ md:flex-1 แทน */}
          <div className="w-full md:flex-1 md:h-[490px] bg-gold shrink-0 border-[3px] border-dark flex items-center justify-center relative shadow-md">
            <span className="opacity-30 text-5xl font-serif font-bold rotate-[-15deg]">1960s</span>
          </div>

          {/* ส่วนที่ 2: กล่องข้อความ */}
          {/* แก้: ใส่ w-full และ md:flex-1 */}
          <div className="w-full md:flex-1 flex flex-col justify-between">
            <p className="text-base md:text-lg leading-loose mb-6 text-justify">
              <strong className="text-2xl serif-font italic">Bangkok EraVision</strong> is a time-machine interface that transports you back to Phra Nakhon in the 1960s. Experience the classic "Venice of the East" through our advanced AI simulation technology.
            </p>
            <Link href="/about" className="self-start font-bold text-xl underline decoration-2 underline-offset-4 hover:opacity-80 transition-colors">
              Meet our developers →
            </Link>
          </div>
        </div>
      </section>

      {/* Ornament Divider */}
      <div className="flex items-center justify-center mb-12">
        <div className="h-[2px] bg-dark flex-1"></div>
        <span className="mx-6 text-3xl font-serif">⚜</span>
        <div className="h-[2px] bg-dark flex-1"></div>
      </div>

      {/* Upload Section แบบใหม่ ไม่ต้องส่ง Props */}
      <UploadSection currentLang={language} />
    </main>
  );
}