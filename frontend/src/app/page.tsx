import Navbar from "@/components/Navbar";
import UploadSection from "@/components/UploadSection";
import Link from "next/link";

export default function Home() {
  return (
    <main className="w-full max-w-3xl px-6 pb-20">
      <Navbar />

      {/* Hero Section */}
      <section className="mb-12">
        <h1 className="bg-dark text-background p-3 text-center text-xl md:text-2xl font-bold tracking-[0.2em] mb-8 font-mono shadow-[6px_6px_0px_#D4B666]">
          WHAT IS BANGKOK ERAVISION?
        </h1>
        <div className="flex flex-col md:flex-row gap-8 items-start">
           {/* Placeholder Image */}
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

      {/* Ornament Divider */}
      <div className="flex items-center justify-center my-12 px-4 opacity-80">
        <div className="h-[2px] bg-dark flex-1"></div>
        <span className="mx-6 text-3xl font-serif">⚜</span>
        <div className="h-[2px] bg-dark flex-1"></div>
      </div>

      {/* Interaction Area */}
      <UploadSection />
    </main>
  );
}