import type { Metadata } from "next";
import "./globals.css"; // Keep global styles

// Metadata here is a fallback, real localized metadata will be in [locale] layout or pages.
export const metadata: Metadata = {
  title: "Qader Platform", // Generic non-localized title
  description: "Qader E-learning platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // This RootLayout must render <html> and <body>.
  // `next-intl` will work with the `[locale]` layout to set `lang` and `dir`.
  return (
    // suppressHydrationWarning is good practice with dynamic lang/dir and themes
    <html suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
