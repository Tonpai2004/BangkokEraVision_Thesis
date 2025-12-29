"use client"; // จำเป็นต้องใส่บรรทัดนี้เพื่อใช้ State

import { useState } from "react";
import Navbar from "@/components/Navbar";
import UploadSection from "@/components/UploadSection";
import Link from "next/link";

// สร้าง Type สำหรับข้อมูลผลลัพธ์
type AnalysisResult = {
  status: "success" | "rejected" | "error";
  title?: string;
  details?: string;
  score?: number;
};

export default function Home() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  // ฟังก์ชันนี้จะถูกส่งไปให้ UploadSection เรียกใช้เมื่อได้ผลลัพธ์จาก API
  const handleAnalysisComplete = (result: any) => {
    if (result.error || result.status === 'rejected') {
      setAnalysisResult({
        status: "rejected",
        title: result.title || "Image Rejected",
        details: result.details || result.error,
        score: result.score
      });
    } else {
      setAnalysisResult({
        status: "success",
        title: "Verification Passed",
        details: `Identity confirmed: ${result.location_name}`,
        score: result.analysis_report?.score
      });
    }
  };

  return (
    <main className="w-full max-w-3xl px-6 pb-20 mx-auto">
      <Navbar />

      {/* Hero Section */}
      <section className="mb-12">
        <h1 className="bg-dark text-background p-3 text-center text-xl md:text-2xl font-bold tracking-[0.2em] mb-8 font-mono shadow-[6px_6px_0px_#D4B666]">
          WHAT IS BANGKOK ERAVISION?
        </h1>
        <div className="flex flex-col md:flex-row gap-8 items-start">
           <div className="w-full md:w-[260px] h-[260px] bg-gold shrink-0 border-[3px] border-dark flex items-center justify-center relative shadow-md">
              <span className="opacity-30 text-5xl font-serif font-bold rotate-[-15deg]">1960s</span>
           </div>
           
           <div className="flex-1 flex flex-col justify-between h-full">
              <p className="text-base md:text-lg leading-loose mb-6 text-justify">
                <strong className="text-xl serif-font italic">Bangkok EraVision</strong> is a time-machine interface that transports you back to Phra Nakhon in the 1960s. Experience the classic "Venice of the East" through our advanced AI simulation technology.
              </p>
              <Link href="/about" className="self-start font-bold underline decoration-2 underline-offset-4 hover:text-accent transition-colors">
                Read more at About Us →
              </Link>
           </div>
        </div>
      </section>

      {/* --- NEW: Analysis Feedback Dashboard --- */}
      {analysisResult && (
        <div className={`mb-12 p-6 border-2 shadow-[4px_4px_0px_#000] animate-in fade-in slide-in-from-bottom-4 duration-500
          ${analysisResult.status === 'success' ? 'bg-[#e6ffe6] border-green-800' : 'bg-[#fff0f0] border-red-800'}`}>
          
          <h2 className={`text-xl font-bold font-mono mb-2 flex items-center gap-2
            ${analysisResult.status === 'success' ? 'text-green-900' : 'text-red-900'}`}>
            {analysisResult.status === 'success' ? '✅ VERIFICATION PASSED' : '🚫 VERIFICATION FAILED'}
          </h2>
          
          <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
            <div>
              <p className="font-bold text-lg">{analysisResult.title}</p>
              <p className="text-sm opacity-80 font-mono mt-1">
                REASON: {analysisResult.details}
              </p>
            </div>
            
            {analysisResult.score !== undefined && (
              <div className="bg-white/50 px-4 py-2 rounded border border-dark/20 text-center">
                <span className="block text-xs uppercase tracking-wide opacity-70">Confidence Score</span>
                <span className={`text-2xl font-bold ${analysisResult.score > 70 ? 'text-green-700' : 'text-red-700'}`}>
                  {typeof analysisResult.score === 'number' ? analysisResult.score.toFixed(1) : analysisResult.score}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Ornament Divider */}
      <div className="flex items-center justify-center my-12 px-4 opacity-80">
        <div className="h-[2px] bg-dark flex-1"></div>
        <span className="mx-6 text-3xl font-serif">⚜</span>
        <div className="h-[2px] bg-dark flex-1"></div>
      </div>

      {/* Interaction Area */}
      {/* ส่ง prop onResult ไปให้ UploadSection เรียกใช้ */}
      <UploadSection onAnalysisResult={handleAnalysisComplete} />
    </main>
  );
}