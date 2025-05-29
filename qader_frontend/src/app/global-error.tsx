// src/app/global-error.tsx
"use client";

import { useEffect } from "react";
import { Frown, RotateCcw } from "lucide-react"; // Example icons
// It's generally safer NOT to use useTranslations here, as i18n setup might be part of the error.
// Use hardcoded basic strings or very minimal i18n.

import { Button } from "@/components/ui/button"; // Assuming Button is simple and unlikely to fail

interface GlobalErrorProps {
  error: Error & { digest?: string }; // digest is added by Next.js for server-originated errors
  reset: () => void; // Function to attempt to re-render the route segment
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    // Log the error to an error reporting service (e.g., Sentry, LogRocket)
    console.error("Global Error Boundary Caught:", error);
    // You could send error.digest to your logging service if it exists
  }, [error]);

  // Basic locale detection for dir, try to keep this simple
  let dir: "ltr" | "rtl" = "ltr";
  if (typeof window !== "undefined") {
    const pathLocale = window.location.pathname.split("/")[1];
    if (pathLocale === "rtl") {
      dir = "rtl";
    }
  }

  return (
    <html lang="en" dir={dir}>
      {" "}
      {/* Provide a default lang, dir can be dynamic but keep simple */}
      <head>
        <title>Application Error</title> {/* Simple title */}
        {/* Minimal head elements */}
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* Link to a very basic global stylesheet if absolutely necessary and safe */}
        {/* <link rel="stylesheet" href="/minimal-error-styles.css" /> */}
        <style>{`
          body { margin: 0; font-family: system-ui, sans-serif; color: #333; background-color: #f9fafb; }
          .error-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; text-align: center; padding: 1.5rem; }
          .error-icon { width: 6rem; height: 6rem; color: #ef4444; margin-bottom: 2rem; }
          .error-title { font-size: 2.25rem; font-weight: bold; margin-bottom: 1rem; color: #111827 }
          .error-message { font-size: 1.125rem; color: #4b5563; margin-bottom: 2rem; max-width: 36rem; }
          .error-actions button {
            background-color: #3b82f6; color: white; font-weight: 500; padding: 0.75rem 1.5rem; border-radius: 0.375rem; border: none; cursor: pointer;
            display: inline-flex; align-items: center;
          }
          .error-actions button:hover { background-color: #2563eb; }
          .error-actions button svg { margin-right: 0.5rem; width: 1.25rem; height: 1.25rem; }
          [dir="rtl"] .error-actions button svg { margin-left: 0.5rem; margin-right: 0; }
        `}</style>
      </head>
      <body>
        <div className="error-container">
          <Frown className="error-icon" strokeWidth={1.5} />
          <h1 className="error-title">
            {dir === "rtl" ? "عذراً، حدث خطأ ما" : "Oops, Something Went Wrong"}
          </h1>
          <p className="error-message">
            {dir === "rtl"
              ? "نواجه بعض الصعوبات التقنية في الوقت الحالي. فريقنا يعمل على إصلاح المشكلة. يرجى المحاولة مرة أخرى بعد قليل."
              : "We're experiencing some technical difficulties right now. Our team is working on fixing it. Please try again in a little while."}
          </p>
          {error?.digest && ( // Display error digest if available (for server errors)
            <p
              className="error-message"
              style={{ fontSize: "0.875rem", color: "#6b7281" }}
            >
              {dir === "rtl"
                ? `معرف الخطأ: ${error.digest}`
                : `Error ID: ${error.digest}`}
            </p>
          )}
          <div className="error-actions">
            <Button
              onClick={
                // Attempt to recover by trying to re-render the segment
                () => reset()
              }
              // Basic inline styling for the button to avoid relying on external CSS that might be broken
              // Or use the imported Button component if it's simple enough
            >
              <RotateCcw strokeWidth={2} />
              <span>{dir === "rtl" ? "إعادة المحاولة" : "Try Again"}</span>
            </Button>
          </div>
          <p
            style={{
              marginTop: "3rem",
              fontSize: "0.875rem",
              color: "#6b7281",
            }}
          >
            <a
              href="/"
              style={{ color: "#3b82f6", textDecoration: "underline" }}
            >
              {dir === "rtl" ? "العودة إلى الصفحة الرئيسية" : "Go to Homepage"}
            </a>
          </p>
        </div>
      </body>
    </html>
  );
}
