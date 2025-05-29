// src/i18n.ts (or src/config/i18n.config.ts in target structure)
import {
  getRequestConfig,
  GetRequestConfigParams,
  RequestConfig,
} from "next-intl/server";
import type { AbstractIntlMessages } from "next-intl";
import { notFound } from "next/navigation";

// Ensure these match the locales you support and have .json files for
export const locales = ["en", "ar"]; // Use "as const" for stricter typing
export const defaultLocale: Locale = "ar";

export type Locale = (typeof locales)[number];

export default getRequestConfig(
  async (params: GetRequestConfigParams): Promise<RequestConfig> => {
    const resolvedLocale = params?.locale ?? defaultLocale;
    // Validate that the incoming `locale` parameter is valid
    if (!locales.includes(resolvedLocale as any)) notFound(); // Cast as any if resolvedLocale type from next-intl is just string

    let messages: AbstractIntlMessages;
    try {
      // Using separate imports for each namespace for clarity and potential code-splitting benefits
      // The structure of messages will be { Common: {...}, Auth: {...}, Nav: {...} }
      messages = {
        Common: (await import(`@/locales/${resolvedLocale}/common.json`))
          .default,
        Auth: (await import(`@/locales/${resolvedLocale}/auth.json`)).default,
        Nav: (await import(`@/locales/${resolvedLocale}/nav.json`)).default,
        // Add other namespaces as they are created
        // Example: Study: (await import(`../locales/${resolvedLocale}/study.json`)).default,
      };
    } catch (error) {
      // If message files for a supported resolvedLocale are missing or corrupt,
      // this is a critical configuration or deployment error.
      console.error(
        `Could not load messages for resolvedLocale: ${resolvedLocale}`,
        error
      );
      notFound();
    }

    return {
      locale: resolvedLocale,
      messages,
      // You can override the default timeZone and now strategy on a per-locale basis
      // timeZone: '...',
      // now: new Date(),
    };
  }
);
