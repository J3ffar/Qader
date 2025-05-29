"use client";

import { useEffect } from "react";
import { Frown, RotateCcw } from "lucide-react";
// Button import is fine if it's simple
// import { Button } from "@/components/ui/button";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    console.error("Global Error Boundary Caught:", error);
  }, [error]);

  let dir: "ltr" | "rtl" = "ltr"; // Default
  let lang: string = "en"; // Default
  if (typeof window !== "undefined") {
    const pathLocale = window.location.pathname.split("/")[1];
    if (pathLocale === "ar") {
      dir = "rtl";
      lang = "ar";
    }
    // Add more else if for other locales if needed for GlobalError
  }

  return (
    // NO WHITESPACE directly inside <html> other than <head> and <body>
    <html lang={lang} dir={dir}>
      <head>
        <title>{lang === "ar" ? "خطأ في التطبيق" : "Application Error"}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta charSet="utf-8" /> {/* Good practice */}
        <style>{`
          body { margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; color: #333; background-color: #f9fafb; line-height: 1.5; }
          .error-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; text-align: center; padding: 24px; box-sizing: border-box; }
          .error-icon { width: 5rem; height: 5rem; color: #ef4444; margin-bottom: 1.5rem; }
          .error-title { font-size: 1.875rem; font-weight: 700; margin-bottom: 0.75rem; color: #111827; }
          .error-message { font-size: 1rem; color: #4b5563; margin-bottom: 1.5rem; max-width: 32rem; }
          .error-digest { font-size: 0.875rem; color: #6b7281; margin-bottom: 1.5rem; word-break: break-all; }
          .error-actions button {
            background-color: #3b82f6; color: white; font-weight: 500; padding: 0.625rem 1.25rem; border-radius: 0.375rem; border: none; cursor: pointer;
            display: inline-flex; align-items: center; transition: background-color 0.2s ease-in-out;
          }
          .error-actions button:hover { background-color: #2563eb; }
          .error-actions button svg { margin-right: 0.5rem; width: 1.125rem; height: 1.125rem; }
          html[dir="rtl"] .error-actions button svg { margin-left: 0.5rem; margin-right: 0; }
          .error-home-link { margin-top: 2.5rem; font-size: 0.875rem; color: #3b82f6; text-decoration: underline; }
          .error-home-link:hover { color: #1d4ed8; }
        `}</style>
      </head>
      <body>
        <div className="error-container">
          <Frown className="error-icon" strokeWidth={1.5} />
          <h1 className="error-title">
            {lang === "ar" ? "عذراً، حدث خطأ ما" : "Oops, Something Went Wrong"}
          </h1>
          <p className="error-message">
            {lang === "ar"
              ? "نواجه بعض الصعوبات التقنية. فريقنا يعمل على الإصلاح. يرجى المحاولة مرة أخرى بعد قليل."
              : "We're experiencing some technical difficulties. Our team is working on it. Please try again soon."}
          </p>
          {error?.digest && (
            <p className="error-digest">
              {lang === "ar"
                ? `معرف الخطأ: ${error.digest}`
                : `Error ID: ${error.digest}`}
            </p>
          )}
          <div className="error-actions">
            {/* Using a native button for max reliability in error state */}
            <button onClick={() => reset()}>
              <RotateCcw
                strokeWidth={2}
                style={{
                  width: "1.125rem",
                  height: "1.125rem",
                  [dir === "rtl" ? "marginLeft" : "marginRight"]: "0.5rem",
                }}
              />
              <span>{lang === "ar" ? "إعادة المحاولة" : "Try Again"}</span>
            </button>
          </div>
          <p>
            <a href="/" className="error-home-link">
              {lang === "ar" ? "العودة إلى الصفحة الرئيسية" : "Go to Homepage"}
            </a>
          </p>
        </div>
      </body>
    </html>
  );
}
