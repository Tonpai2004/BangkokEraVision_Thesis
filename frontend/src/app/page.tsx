"use client";

import Navbar from "@/components/Navbar";
import UploadSection from "@/components/UploadSection";
import Link from "next/link";
import { useState } from "react";

import { useLanguage } from "@/context/LanguageContext";

// 1. สร้างชุดคำแปลสำหรับหน้าหลัก
const PAGE_TEXT = {
  TH: {
    title: "BANGKOK ERAVISION คืออะไร?",
    desc_prefix: "คืออินเทอร์เฟซไทม์แมชชีนที่จะพาคุณย้อนเวลากลับไปสู่พระนครในยุค 2500 สัมผัสประสบการณ์",
    desc_highlight: "เวนิสตะวันออก",
    desc_suffix: "สุดคลาสสิกผ่านเทคโนโลยีจำลองสถานการณ์ด้วย AI ขั้นสูงของเรา",
    link_dev: "พบกับทีมนักพัฒนาของเรา →"
  },
  ENG: {
    title: "WHAT IS BANGKOK ERAVISION?",
    desc_prefix: "is a time-machine interface that transports you back to Phra Nakhon in the 1960s. Experience the classic",
    desc_highlight: "Venice of the East",
    desc_suffix: "through our advanced AI simulation technology.",
    link_dev: "Meet our developers →"
  }
};

export default function Home() {

  const { language } = useLanguage();
  const text = PAGE_TEXT[language];

  return (
    <main className="w-full px-6 pb-20 mx-auto">
      <Navbar />

      {/* Hero Section */}
      <section className="mt-0 mb-0 md:mt-10 md:mb-7">
        <h1 className="bg-dark text-white p-3 text-center text-xl md:text-5xl font-bold tracking-[0.2em] mb-8 py-8 font-mono shadow-[6px_6px_0px_#D4B666]">
          {text.title}
        </h1>
        <div className="flex flex-col md:flex-row gap-8 items-stretch mt-10">
          {/* ส่วนที่ 1: กล่องรูปภาพ */}
          <div className="w-full md:flex-1 md:h-[490px] bg-gold shrink-0 border-[3px] border-dark flex items-center justify-center relative shadow-md">
            <span className="opacity-30 text-5xl font-serif font-bold rotate-[-15deg]">1960s</span>
          </div>

          {/* ส่วนที่ 2: กล่องข้อความ */}
          <div className="w-full md:flex-1 flex flex-col justify-between">
            <p className="text-base md:text-lg leading-loose mb-6 text-justify">
              <strong className="text-2xl serif-font italic">Bangkok EraVision</strong> {text.desc_prefix} "{text.desc_highlight}" {text.desc_suffix}
            </p>
            <Link href="/about" className="self-start font-bold text-xl underline decoration-2 underline-offset-4 hover:opacity-80 transition-colors">
              {text.link_dev}
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

      {/* Upload Section ส่งภาษาปัจจุบันไปด้วย */}
      <UploadSection currentLang={language} />
    </main>
  );
}