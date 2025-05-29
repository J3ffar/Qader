import createMiddleware from "next-intl/middleware";
import { NextRequest, NextResponse } from "next/server";
import { locales, defaultLocale } from "./i18n";

const intlMiddleware = createMiddleware({
  locales,
  defaultLocale,
  localePrefix: "as-needed",
  pathnames: {
    // Optional: if you want to translate pathnames themselves
    // Example:
    // '/about': {
    //   en: '/about-us',
    //   ar: '/من-نحن'
    // }
  },
  localeDetection: true,
});

export default function middleware(req: NextRequest): NextResponse {
  // Let next-intl's middleware handle the request
  const response = intlMiddleware(req);
  return response;
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|images|fonts|favicon.ico|manifest.json|robots.txt|sw.js|workbox-.*\\.js).*)",
  ],
};
