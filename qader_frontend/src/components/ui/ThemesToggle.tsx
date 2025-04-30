"use client";

import { useTheme } from "next-themes";
import {
  MoonIcon,
  SunIcon,
  NoSymbolIcon,
} from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";

export function ThemesToggles() {
  const { setTheme, theme } = useTheme();

  return (
    <div className="flex gap-2 items-center">
      <Button
        variant={theme === "light" ? "default" : "outline"}
        size="icon"
        onClick={() => setTheme("light")}
      >
        <SunIcon className="h-5 w-5" />
        <span className="sr-only">Light theme</span>
      </Button>

      <Button
        variant={theme === "dark" ? "default" : "outline"}
        size="icon"
        onClick={() => setTheme("dark")}
      >
        <MoonIcon className="h-5 w-5" />
        <span className="sr-only">Dark theme</span>
      </Button>

      <Button
        variant={theme === "system" ? "default" : "outline"}
        size="icon"
        onClick={() => setTheme("system")}
      >
        <NoSymbolIcon className="h-5 w-5" />
        <span className="sr-only">System theme</span>
      </Button>
    </div>
  );
}
