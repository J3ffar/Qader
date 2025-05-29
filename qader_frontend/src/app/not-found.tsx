"use client";

import Link from "next/link";
import { Home, SearchX } from "lucide-react";
import {
  NextIntlClientProvider,
  useTranslations,
  AbstractIntlMessages,
} from "next-intl";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { PATHS } from "@/constants/paths";
import {
  defaultLocale,
  locales as appLocales,
  Locale,
} from "@/config/i18n.config"; // Assuming your i18n config is here

// A simple function to get messages for the not-found page
// In a real app, you might want a more robust way or a minimal set of messages
function getNotFoundMessages(locale: Locale): AbstractIntlMessages {
  try {
    // Attempt to load common messages for the given locale
    // This is a simplified example; you might only need a small subset of messages.
    // WARNING: Dynamic imports inside client components are generally discouraged for initial render.
    // For a root not-found, it's better to have these messages statically available or fetched minimally.
    // Consider creating a very small `notfound.json` for each locale.
    if (locale === "ar") {
      return {
        Common: {
          NotFound: {
            title: "صفحة غير موجودة",
            description: "عذرًا، لم نتمكن من العثور على الصفحة التي تبحث عنها.",
            goHomeButton: "العودة إلى الرئيسية",
            errorCode: "رمز الخطأ: 404",
          },
        },
      };
    } else {
      // default to 'en' or your other locales
      return {
        Common: {
          NotFound: {
            title: "Page Not Found",
            description: "Sorry, we couldn't find the page you're looking for.",
            goHomeButton: "Go Back Home",
            errorCode: "Error Code: 404",
          },
        },
      };
    }
  } catch (e) {
    // Fallback messages if loading fails (should ideally not happen with static objects)
    console.error("Failed to load messages for not-found page", e);
    return {
      Common: {
        NotFound: {
          title: "Error",
          description: "Page not found.",
          goHomeButton: "Home",
          errorCode: "404",
        },
      },
    };
  }
}

function NotFoundContent() {
  // This component now correctly uses useTranslations within the provider's scope
  const t = useTranslations("Common.NotFound");
  const pathname = usePathname();
  // A more robust way to get locale for a root not-found page
  const currentSegments = pathname.split("/");
  let locale: Locale = defaultLocale;
  if (
    currentSegments.length > 1 &&
    appLocales.includes(currentSegments[1] as Locale)
  ) {
    locale = currentSegments[1] as Locale;
  }

  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center"
      dir={locale === "ar" ? "rtl" : "ltr"}
    >
      <SearchX className="mb-8 h-24 w-24" />
      <h1 className="mb-4 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
        {t("title")}
      </h1>
      <p className="mb-8 max-w-md text-lg text-muted-foreground">
        {t("description")}
      </p>
      <div className="flex flex-col space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0 rtl:sm:space-x-reverse">
        <Button asChild size="lg">
          {/* Ensure PATHS.HOME is just '/' so locale prefixing works */}
          <Link href={`/${locale}${PATHS.HOME === "/" ? "" : PATHS.HOME}`}>
            <Home className="mr-2 h-5 w-5 rtl:ml-2 rtl:mr-0" />
            {t("goHomeButton")}
          </Link>
        </Button>
      </div>
      {/* <p className="mt-12 text-sm text-muted-foreground">{t("errorCode")}</p> */}
    </div>
  );
}

export default function NotFound() {
  const pathname = usePathname();
  // Determine locale for the provider.
  // This needs to be done carefully as the path might not have a locale prefix
  // if the notFound() was triggered very early or for a non-prefixed path.
  const currentSegments = pathname.split("/");
  let locale: Locale = defaultLocale; // Fallback to default locale

  // Check if the first segment is a valid locale
  if (
    currentSegments.length > 1 &&
    appLocales.includes(currentSegments[1] as Locale)
  ) {
    locale = currentSegments[1] as Locale;
  }
  // If not, `defaultLocale` will be used. You need messages for the default locale.

  const messages = getNotFoundMessages(locale);

  return (
    <NextIntlClientProvider
      locale={locale}
      messages={messages}
      timeZone="Asia/Riyadh"
    >
      {" "}
      {/* Add your timezone */}
      <NotFoundContent />
    </NextIntlClientProvider>
  );
}
