'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path ? "text-accent underline decoration-2 underline-offset-4" : "text-dark";

  return (
    <header className="w-full flex flex-col md:flex-row justify-between items-center py-5 border-b-[3px] border-dark mb-8 gap-4">
      <div className="logo select-none">
         {/* เปลี่ยนเป็น <img src="/logo.png" ... /> ได้ถ้ามีไฟล์ */}
         <div className="w-12 h-12 border-[3px] border-dark flex items-center justify-center text-2xl font-bold font-serif bg-gold shadow-[3px_3px_0px_#2C2C2C]">
            B
         </div>
      </div>
      <nav className="flex gap-8 font-bold italic text-lg tracking-wide">
        <Link href="/" className={`${isActive('/')} hover:opacity-70 transition-opacity`}>Home</Link>
        <Link href="/map" className={`${isActive('/map')} hover:opacity-70 transition-opacity`}>Map</Link>
        <Link href="/about" className={`${isActive('/about')} hover:opacity-70 transition-opacity`}>About Us</Link>
        <span className="cursor-pointer ml-4 font-normal not-italic hover:text-gray-600">ENG ▼</span>
      </nav>
    </header>
  );
}