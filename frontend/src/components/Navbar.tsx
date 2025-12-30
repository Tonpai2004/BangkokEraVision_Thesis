'use client';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export default function Navbar() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isActive = (path: string) => 
    pathname === path ? "underline decoration-2 underline-offset-4" : "";

  // ส่วนของ Logo แยกออกมาเพื่อนำไปใช้ซ้ำทั้ง Mobile และ Desktop
  const Logo = () => (
    <div className="logo select-none">
       <div className="logo select-none cursor-pointer">
          <Image 
            src="/images/headlogo.png" alt="Bangkok EraVision Logo" width={80} height={80} className="object-contain"
          />
        </div>
    </div>
  );

  return (
    <nav className="w-full text-dark font-serif md:mb-7">
      
      {/* ------------------------------- */}
      {/* DESKTOP LAYOUT (Hidden on Mobile) */}
      {/* ------------------------------- */}
      <div className="hidden md:flex flex-col items-center w-full">
        
        {/* Logo Section (Top Center) */}
        <div className="py-8">
           <Logo />
        </div>

        {/* Navigation Strip */}
        <div className="w-full border-y-[2px] border-dark flex justify-between items-center px-3 py-3">
          {/* Left: Menu Links */}
          <div className="flex gap-12 font-bold italic text-xl tracking-wide">
            <Link href="/" className={`${isActive('/')} hover:opacity-70 transition-opacity`}>Home</Link>
            <Link href="/map" className={`${isActive('/map')} hover:opacity-70 transition-opacity`}>Map</Link>
            <Link href="/about" className={`${isActive('/about')} hover:opacity-70 transition-opacity`}>About Us</Link>
          </div>

          {/* Right: Language Selector */}
          <div className="font-bold italic text-lg cursor-pointer hover:text-gray-600">
            ENG ▼
          </div>
        </div>
      </div>

      {/* ------------------------------- */}
      {/* MOBILE LAYOUT (Hidden on Desktop) */}
      {/* ------------------------------- */}
      <div className="md:hidden">
        
        {/* Mobile Header Bar */}
        <div className="flex justify-between items-center py-5 border-b-[2px] border-dark relative z-20">
          {/* Logo Left */}
          <Logo />

          {/* Hamburger Icon Right */}
          <button 
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 focus:outline-none"
          >
            {isMobileMenuOpen ? (
              // Close Icon (X)
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              // Hamburger Icon
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Dropdown Menu */}
        <div className={`
            flex flex-col items-center gap-6 py-6 border-b-[2px] border-dark
            transition-all duration-300 ease-in-out origin-top
            ${isMobileMenuOpen ? 'opacity-100 max-h-96' : 'opacity-0 max-h-0 overflow-hidden'}
        `}>
            <Link href="/" onClick={() => setIsMobileMenuOpen(false)} className={`${isActive('/')} text-xl font-bold italic`}>Home</Link>
            <Link href="/map" onClick={() => setIsMobileMenuOpen(false)} className={`${isActive('/map')} text-xl font-bold italic`}>Map</Link>
            <Link href="/about" onClick={() => setIsMobileMenuOpen(false)} className={`${isActive('/about')} text-xl font-bold italic`}>About Us</Link>
            <span className="text-lg pt-4 border-t border-gray-300 w-1/2 text-center cursor-pointer">ENG ▼</span>
        </div>
      </div>

    </nav>
  );
}