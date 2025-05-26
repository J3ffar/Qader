"use client";

import { useEffect } from "react";
import NProgress from "nprogress";
import "nprogress/nprogress.css"; // Import NProgress styles
import { usePathname, useSearchParams } from "next/navigation";

// Customize NProgress appearance (optional, can be in global CSS)
// Example: if you put this in globals.css, you don't need it here
// NProgress.configure({ showSpinner: false });

export function NProgressHandler() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    NProgress.done(); // Ensure it's done on initial load or if it was stuck
  }, []); // Empty dependency array, runs once on mount

  useEffect(() => {
    NProgress.start();
    // Delay NProgress.done slightly to ensure it's visible
    const timer = setTimeout(() => NProgress.done(), 200); // Adjust delay as needed
    return () => {
      clearTimeout(timer);
      NProgress.done(); // Ensure NProgress is done on unmount or if component re-renders before timer
    };
  }, [pathname, searchParams]);

  return null; // This component doesn't render anything
}
