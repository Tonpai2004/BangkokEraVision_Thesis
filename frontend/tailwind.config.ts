import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F0EAD6", // สีครีมกระดาษ
        dark: "#2C2C2C",       // สีดำเทา
        accent: "#D84335",     // สีแดงปุ่ม Generate
        gold: "#E3C565",       // สีเหลืองทองกล่องรูป
      },
    },
  },
  plugins: [],
};
export default config;