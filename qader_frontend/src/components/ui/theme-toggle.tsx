"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={`
        w-10 h-5 cursor-pointer rounded-full p-[2px] flex items-center relative transition-colors
        ${isDark ? "bg-[#2D495A]" : "bg-[#D3D4D5]"}
      `}
    >
      <span
        className={`
          w-4 h-4 rounded-full absolute top-[2px] left-[2px]
          flex items-center justify-center shadow-md
          transition-all duration-300 ease-in-out
          ${isDark ? "translate-x-5 bg-black" : "translate-x-0 bg-white"}
        `}
      >
        <Sun
          className={`
            w-2.5 h-2.5 absolute text-black
            transition-all duration-300 ease-in-out
            ${isDark ? "opacity-0 scale-0" : "opacity-100 scale-100"}
          `}
        />
        <Moon
          className={`
            w-2.5 h-2.5 absolute text-white
            transition-all duration-300 ease-in-out
            ${isDark ? "opacity-100 scale-100" : "opacity-0 scale-0"}
          `}
        />
      </span>
    </button>
  );
}
// 