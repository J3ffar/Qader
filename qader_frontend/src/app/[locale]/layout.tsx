import { ReactNode, Suspense } from "react";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";
import { IBM_Plex_Sans_Arabic, Harmattan } from "next/font/google";

import { Providers } from "@/components/global/Providers";
import { NProgressHandler } from "@/components/global/NProgressHandler";
import { Toaster } from "@/components/ui/sonner";
import { locales as appLocales } from "@/config/i18n.config";
import "@/app/globals.css";
import { cn } from "@/lib/utils";

// Fonts
const ibm = IBM_Plex_Sans_Arabic({
  subsets: ["arabic", "latin"],
  weight: ["400", "700"],
  variable: "--font-body",
});
const harmattan = Harmattan({
  subsets: ["arabic", "latin"],
  weight: ["400", "700"],
  variable: "--font-heading",
});

interface LocaleLayoutProps {
  children: ReactNode;
  params: {
    locale: string;
  };
}

export async function generateMetadata({
  params,
}: {
  params: { locale: string };
}) {
  const resolvedParams = await params;
  const currentLocale = resolvedParams.locale;

  if (!appLocales.includes(currentLocale)) {
    notFound();
  }

  try {
    const t = await getTranslations({
      locale: currentLocale,
      namespace: "Common",
    });
    return {
      title: t("appName"),
      description: t("siteDescription"),
    };
  } catch (error) {
    // Fallback metadata in case of error loading translations
    return {
      title: "Qader",
      description: "Qader E-learning platform.",
    };
  }
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const resolvedParams = await params;
  const currentLocale = resolvedParams.locale;

  if (!appLocales.includes(currentLocale)) {
    notFound();
  }

  let messages;
  try {
    messages = await getMessages({ locale: currentLocale });
  } catch (error) {
    // If messages can't be loaded, the page can't render correctly.
    // This is a critical error.
    notFound();
  }

  return (
    <html
      lang={currentLocale}
      dir={currentLocale === "ar" ? "rtl" : "ltr"}
      suppressHydrationWarning
    >
      <body
        className={cn(
          "font-body bg-background text-foreground antialiased",
          ibm.variable, // Apply the variable class
          harmattan.variable
        )}
      >
        <NextIntlClientProvider locale={currentLocale} messages={messages}>
          <Providers
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <Suspense fallback={null}>
              <NProgressHandler />
            </Suspense>
            {children}
            <Toaster richColors position="top-center" closeButton />
          </Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
