import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic, Harmattan } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/global/Providers";
import { NProgressHandler } from "@/components/global/NProgressHandler";
import { Toaster } from "@/components/ui/sonner";
// For next-intl, configuration is different in App Router
// Usually, you create a [locale] dynamic segment and use NextIntlClientProvider there or use middleware.
// For a basic setup without locale in path yet:

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
  // Add more metadata: icons, openGraph, etc. from your target config/site.ts
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // const locale = params.locale || 'ar'; // Default to Arabic or get from params

  // For next-intl, you'd typically fetch messages here if not using middleware for everything
  // let messages;
  // try {
  //   messages = (await import(`../../locales/${locale}.json`)).default;
  // } catch (error) {
  //   console.error("Could not load messages for locale:", locale, error);
  //   // Fallback or handle error appropriately
  //   messages = (await import(`../../locales/ar.json`)).default; // Fallback to Arabic
  // }

  return (
    <html lang={"ar"} suppressHydrationWarning dir="rtl">
      <body
        className={`${ibm.variable} ${harmattan.variable} font-body bg-background text-foreground antialiased`}
      >
        {/* NProgressHandler needs to be inside Suspense if it uses usePathname/useSearchParams directly in Next.js 13/14 */}
        {/* However, since it's a client component, it should be fine. Next.js 15 might handle this better. */}
        {/* For safety, wrap it in Suspense if you encounter static rendering issues. */}
        {/* <NProgressHandler /> */}
        <Providers
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {/* <NextIntlClientProvider locale={locale} messages={messages}> */}
          {children}
          <Toaster richColors position="top-center" />{" "}
          {/* Or your preferred position */}
          {/* </NextIntlClientProvider> */}
        </Providers>
      </body>
    </html>
  );
}
