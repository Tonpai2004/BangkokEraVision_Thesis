"use client"; // <--- เพิ่มบรรทัดนี้สำคัญมาก เพื่อให้ใช้ useState ได้

import Navbar from "@/components/Navbar";
import { useState } from "react"; // <--- เพิ่ม import

export default function AboutPage() {
  // 1. เพิ่ม State สำหรับจัดการภาษา
  const [language, setLanguage] = useState<'TH' | 'ENG'>('ENG');

  return (
    <main className="w-full max-w-3xl px-6 pb-20 mx-auto">
      {/* 2. ส่งค่า language และฟังก์ชัน setLanguage เข้าไปใน Navbar */}
      <Navbar 
        language={language} 
        onLanguageChange={setLanguage} 
      />

      <div className="text-center mb-12 mt-10">
        <h1 className="text-5xl md:text-7xl serif-font font-bold mb-6 italic tracking-tight text-dark">
          Bangkok<br/><span className="text-accent">EraVision</span>
        </h1>
        <div className="flex items-center justify-center my-8 opacity-60">
            <div className="h-[3px] bg-dark w-1/4"></div>
            <span className="mx-6 text-3xl font-serif">⚜</span>
            <div className="h-[3px] bg-dark w-1/4"></div>
        </div>
      </div>

      <div className="prose max-w-none font-mono mb-16 text-justify leading-relaxed">
        <p>
            Bangkok EraVision is a project dedicated to preserving and reimagining the architectural heritage of Bangkok during the 1960s. Using state-of-the-art Generative AI, we bridge the gap between the present and the past, allowing users to visualize history through their own lens.
        </p>
      </div>

      {/* Created By Section */}
      <section className="mb-20 text-center">
        <h2 className="text-center text-3xl md:text-4xl serif-font font-bold mb-10 italic bg-paper inline-block px-4 py-2 border-2 border-dark shadow-[4px_4px_0px_#D4B666]">
          Created By
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 px-4">
            {/* Creator 1 */}
            <div className="flex flex-col items-center group">
                <div className="w-full aspect-square bg-gold mb-4 border-[3px] border-dark shadow-[6px_6px_0px_#2C2C2C] group-hover:translate-y-[-5px] transition-transform"></div>
                <p className="font-bold text-xl mt-2">Your Name</p>
                <p className="text-sm font-mono opacity-70">Full Stack Developer</p>
            </div>
            {/* Creator 2 */}
            <div className="flex flex-col items-center group">
                <div className="w-full aspect-square bg-gold mb-4 border-[3px] border-dark shadow-[6px_6px_0px_#2C2C2C] group-hover:translate-y-[-5px] transition-transform"></div>
                <p className="font-bold text-xl mt-2">Co-Creator Name</p>
                <p className="text-sm font-mono opacity-70">Prompt Engineer / Historian</p>
            </div>
        </div>
      </section>

      {/* Advisor Section */}
      <section className="flex flex-col items-center">
        <h2 className="text-center text-3xl md:text-4xl serif-font font-bold mb-10 italic bg-paper inline-block px-4 py-2 border-2 border-dark shadow-[4px_4px_0px_#D4B666]">
          Advisor
        </h2>
        <div className="flex flex-col items-center w-full md:w-2/3 group">
            <div className="w-full aspect-square bg-gold mb-4 border-[3px] border-dark shadow-[6px_6px_0px_#2C2C2C] group-hover:translate-y-[-5px] transition-transform"></div>
            <p className="font-bold text-xl mt-2">Advisor Name</p>
            <p className="text-sm font-mono opacity-70">University / Organization</p>
        </div>
      </section>
    </main>
  );
}