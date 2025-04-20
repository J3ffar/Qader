"use client"

import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"
import { useEffect, useState } from "react"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  const isDark = theme === "dark"

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="w-8 h-5 rounded-full p-[2px] flex items-center bg-[#074182] relative transition-colors"
    >
      <span
        className={`w-4 h-4 rounded-full bg-white absolute top-[2px] left-[2px] flex items-center justify-center shadow-md transition delay-700 duration-300 ease-in-out ${
          isDark ? "translate-x-3" : "translate-x-0"
        }`}
      >
        {/* Sun Icon */}
        <Sun
          className={`w-2.5 h-2.5 absolute transition-all duration-500 ease-in-out text-yellow-500 ${
            isDark ? "opacity-0 scale-0" : "opacity-100 scale-100"
          }`}
        />
        {/* Moon Icon */}
        <Moon
          className={`w-2.5 h-2.5 absolute transition-all duration-500 ease-in-out text-black ${
            isDark ? "opacity-100 scale-100" : "opacity-0 scale-0"
          }`}
        />
      </span>
    </button>
  )
}
