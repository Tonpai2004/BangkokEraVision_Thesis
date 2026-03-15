import type { Metadata } from "next";
<<<<<<< HEAD
// Import Google Fonts
import { Courier_Prime, Playfair_Display } from "next/font/google";
// *** บรรทัดนี้สำคัญที่สุด! ห้ามลืม ***
import "./globals.css"; 

// Setup Fonts
const courier = Courier_Prime({ 
  weight: ['400', '700'], 
  subsets: ["latin"],
  variable: '--font-courier',
  display: 'swap',
});

const playfair = Playfair_Display({ 
  weight: ['400', '700', '900'], // เพิ่มน้ำหนัก 900 สำหรับหัวข้อหนาๆ
  subsets: ["latin"],
  variable: '--font-playfair',
=======
// 1. Import จาก Google
import { Merriweather, Krub } from "next/font/google";
// 2. Import สำหรับฟอนต์ในเครื่อง (Local)
import localFont from 'next/font/local';
import "./globals.css"; 

import { LanguageProvider } from "@/context/LanguageContext";

// --- Setup Google Fonts ---
const merriweather = Merriweather({ 
  weight: ['300', '400', '700', '900'], 
  subsets: ["latin"],
  variable: '--font-merriweather',
  display: 'swap',
});

const krub = Krub({ 
  weight: ['300', '400', '500', '600', '700'], 
  subsets: ["thai", "latin"],
  variable: '--font-krub',
  display: 'swap',
});

// --- Setup Local Fonts ---
// หมายเหตุ: ตรวจสอบ path ไฟล์ให้ตรงกับที่คุณวางไว้ใน public/fonts/
const prachachon = localFont({
  src: '../../public/fonts/TS-Prachachon-NP.ttf',
  variable: '--font-prachachon',
  display: 'swap',
});

const pimdeed = localFont({
  src: '../../public/fonts/PSPimpdeedIINew.ttf', // แก้ชื่อไฟล์ให้ตรงกับที่มี
  variable: '--font-pimdeed',
>>>>>>> adf2ac546a3170a7b21d2bd37160ceb0367a368b
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Bangkok EraVision",
  description: "Experience 1960s Phra Nakhon through AI simulation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
<<<<<<< HEAD
    <html lang="en" className={`${courier.variable} ${playfair.variable}`}>
      <body className="min-h-screen flex flex-col items-center antialiased overflow-x-hidden">
        {/* Container หลักเพื่อคุมความกว้างให้เหมือน Design */}
        <div className="w-full max-w-[800px] flex flex-col items-center">
          {children}
=======
    <html lang="en">
      {/* 3. ใส่ Variable ทั้งหมดลงใน body */}
      <body className={`
        ${merriweather.variable} 
        ${krub.variable} 
        ${prachachon.variable} 
        ${pimdeed.variable}
        min-h-screen flex flex-col items-center antialiased overflow-x-hidden relative
      `}>
        
        {/* --- Global Background Texture (กระดาษเก่า) --- */}
        <div 
          className="fixed inset-0 -z-10 pointer-events-none opacity-20"></div>

        {/* Container หลัก */}
        <div className="w-full max-w-[1440px] flex flex-col items-center relative z-0">
          <LanguageProvider>
            {children}
          </LanguageProvider>
>>>>>>> adf2ac546a3170a7b21d2bd37160ceb0367a368b
        </div>
      </body>
    </html>
  );
}