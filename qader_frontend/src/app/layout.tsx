import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic, Harmattan } from "next/font/google";
import "./globals.css";
import Footer from "@/components/layout/Footer";
import Navbar from "@/components/layout/Navbar";
import { ThemeProvider } from "@/components/ui/theme-provider";

const ibm = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-body",
});
const harmattan = Harmattan({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-heading",
});

export const metadata: Metadata = {
  title: "قادر | Qader - استعدادك لاختبار القدرات",
  description:
    "منصة قادر لمساعدتك على الاستعداد لاختبار القدرات العامة بفعالية.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" suppressHydrationWarning dir="rtl">
      <body
        className={`${ibm.variable} ${harmattan.variable} font-body bg-background text-foreground`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex flex-col min-h-screen">
            {" "}
            {/* Ensure footer sticks to bottom */}
            <Navbar />
            <main className="flex-grow">{children}</main> {/* Use main tag */}
            <Footer />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
