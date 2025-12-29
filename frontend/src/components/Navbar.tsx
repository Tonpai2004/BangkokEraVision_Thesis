'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();
  const isActive = (path: string) => pathname === path ? "border-b-2 border-dark" : "";

  return (
    <header className="w-full flex flex-col md:flex-row justify-between items-center py-4 border-b-[3px] border-t-[1px] border-dark mb-10 gap-4 px-2 bg-[#F0EAD6] relative z-10">
      {/* Logo B */}
      <div className="logo select-none">
         {/* แก้ตรงนี้: ลบ style และเพิ่ม class text-shadow-retro */}
         <div className="text-5xl font-black font-serif tracking-tighter text-dark text-shadow-retro">
            B
         </div>
      </div>

      {/* Menu Links */}
      <nav className="flex gap-6 md:gap-10 font-bold italic text-lg tracking-wider font-serif text-dark">
        <Link href="/" className={`${isActive('/')} hover:opacity-70 transition-opacity`}>Home</Link>
        <Link href="/map" className={`${isActive('/map')} hover:opacity-70 transition-opacity`}>Map</Link>
        <Link href="/about" className={`${isActive('/about')} hover:opacity-70 transition-opacity whitespace-nowrap`}>About Us</Link>
      </nav>
      
      {/* Language Selector */}
      <div className="font-bold text-lg flex items-center gap-1 cursor-pointer hover:opacity-70">
        ENG <span className="text-sm">▼</span>
      </div>
    </header>
  );
}