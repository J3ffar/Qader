import { getRequestConfig } from "next-intl/server";
import type { GetRequestConfigParams, RequestConfig } from "next-intl/server";
import { notFound } from "next/navigation";

export const locales = ["en", "ar"];
export const defaultLocale = "ar";

export default getRequestConfig(
  async (params: GetRequestConfigParams): Promise<RequestConfig> => {
    const resolvedLocale = params?.locale ?? defaultLocale;

    if (
      typeof resolvedLocale !== "string" ||
      !locales.includes(resolvedLocale)
    ) {
      // This scenario indicates an issue with how next-intl is resolving or being passed the locale.
      // It's often an internal state that shouldn't happen if `middleware` and `layout` correctly handle locales.
      notFound();
    }

    try {
      const commonMessages = (
        await import(`./locales/${resolvedLocale}/common.json`)
      ).default;
      const authMessages = (
        await import(`./locales/${resolvedLocale}/auth.json`)
      ).default;
      const navMessages = (await import(`./locales/${resolvedLocale}/nav.json`))
        .default;
      // Add other namespaces here

      return {
        locale: resolvedLocale,
        messages: {
          Common: commonMessages,
          Auth: authMessages,
          Nav: navMessages,
          // Add other namespaces here
        },
      };
    } catch (error) {
      // If message files for a supported locale are missing or corrupt,
      // this is a critical configuration or deployment error.
      notFound();
    }
  }
);
