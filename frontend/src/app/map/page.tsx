import Navbar from "@/components/Navbar";

export default function MapPage() {
  return (
    <main className="w-full max-w-4xl px-6 pb-20">
      <Navbar />
      
      <h1 className="text-center text-4xl md:text-5xl serif-font font-bold mb-10 italic">
        Historical Map
      </h1>

      <div className="relative w-full aspect-square md:aspect-[16/9] bg-paper border-[4px] border-dark p-2 shadow-[10px_10px_0px_rgba(0,0,0,0.2)]">
        {/* Mock Map Container */}
        <div className="w-full h-full bg-[#3a3a3a] relative overflow-hidden flex items-center justify-center grayscale contrast-125">
             <div className="text-background text-center z-10 p-4 border-2 border-background bg-black/50 backdrop-blur-sm">
                <p className="text-xl font-bold mb-2">[ INTERACTIVE MAP MODULE ]</p>
                <p className="font-mono text-sm">Status: Under Construction</p>
             </div>
             
             {/* Decorative Elements */}
             <div className="absolute top-1/4 left-1/4 text-4xl animate-bounce">📍</div>
             <div className="absolute bottom-1/3 right-1/4 text-4xl animate-bounce delay-75">📍</div>
             <div className="absolute top-1/2 left-1/2 text-4xl animate-bounce delay-150">📍</div>
        </div>
      </div>
      
      <div className="mt-8 text-center max-w-xl mx-auto">
        <p className="font-mono text-sm md:text-base opacity-70">
          Explore the historical landmarks of Phra Nakhon district. Select a pin to view historical context and available AI transformations.
        </p>
      </div>
    </main>
  );
}