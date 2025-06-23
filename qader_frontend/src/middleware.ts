// src/middleware.ts
import createNextIntlMiddleware from "next-intl/middleware";
import { NextRequest, NextResponse } from "next/server";
import { locales, defaultLocale, Locale } from "./config/i18n.config"; // Assuming i18n.ts is at src/i18n.ts
import { API_BASE_URL } from "./constants/api"; // For checking API calls

const intlMiddleware = createNextIntlMiddleware({
  locales: locales as unknown as string[], // Cast if `locales` is readonly tuple
  defaultLocale: defaultLocale as string, // Cast if `defaultLocale` is specific type
  localePrefix: "as-needed", // Recommended: only adds prefix for non-default locales
  pathnames: {
    // Example: if you want to translate paths themselves
    // "/about": {
    //   en: "/about-us",
    //   ar: "/من-نحن",
    // },
  },
  localeDetection: false, // Enable automatic locale detection if needed, it's disable for now
});

// Paths that require authentication
const protectedPaths = [
  "/study", // Covers all sub-paths like /study/level, /study/traditional
  "/settings", // Assuming this is part of /study or a similar protected area
  // Add other top-level protected paths here
  // Example: "/profile", "/dashboard" (if not under /admin)
];

// Paths specific to admin
const adminPaths = ["/admin"];

export default async function middleware(
  req: NextRequest
): Promise<NextResponse> {
  const { pathname } = req.nextUrl;

  // 1. Skip middleware for API routes, static files, and images
  // The matcher config already handles this, but an explicit check can be clearer
  if (
    pathname.startsWith("/api/") || // Backend API calls proxied via Next.js (if any)
    pathname.startsWith(`${API_BASE_URL}`) || // Direct calls to external API
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/images/") ||
    pathname.startsWith("/fonts/") ||
    pathname.includes(".") // Generally files with extensions
  ) {
    return NextResponse.next();
  }

  // 2. Handle internationalization first
  const intlResponse = intlMiddleware(req);
  // If next-intl redirected, respect that.
  // We need to get the locale *after* intlMiddleware has processed it.

  // const locale = req.headers.get("x-next-intl-locale") || defaultLocale;
  // const derivedPathname = pathname.startsWith(`/${locale}`)
  //   ? pathname.substring(`/${locale}`.length) || "/"
  //   : pathname;

  // // 3. Authentication & Authorization Logic
  // // For simplicity, using a placeholder for fetching user session.
  // // In a real app, this would involve checking a secure cookie or making a quick API call.
  // // Example: const session = await getSessionFromCookie(req); // Implement this
  // const accessToken = req.cookies.get("qader-auth-storage.accessToken")?.value; // Example, depends on your store's cookie name if HttpOnly is not used for access token.
  // // If using HttpOnly cookies for tokens, you'd have an API route `/api/auth/me` that middleware calls.

  // const isAuthenticated = !!accessToken; // Simplified check

  // // Redirect to login if trying to access a protected path without authentication
  // if (
  //   !isAuthenticated &&
  //   protectedPaths.some((path) => derivedPathname.startsWith(path))
  // ) {
  //   const loginUrl = new URL(`/${locale}/login`, req.url);
  //   loginUrl.searchParams.set("redirect_to", derivedPathname); // Pass current path for redirect after login
  //   return NextResponse.redirect(loginUrl);
  // }

  // // If authenticated and trying to access auth pages (login, signup), redirect to study page or home
  // if (
  //   isAuthenticated &&
  //   (derivedPathname.startsWith("/login") ||
  //     derivedPathname.startsWith("/signup"))
  // ) {
  //   return NextResponse.redirect(new URL(`/${locale}/study`, req.url));
  // }

  // Admin route protection (placeholder for role check)
  // const userRole = session?.user?.role; // Example
  // if (adminPaths.some(path => derivedPathname.startsWith(path)) && userRole !== "admin") {
  //   return NextResponse.redirect(new URL(`/${locale}/`, req.url)); // Redirect to homepage
  // }

  return intlResponse; // Return the response from next-intl middleware
}

export const config = {
  // Matcher ignoring `/_next/` and `/api/`
  // Also ignoring static assets like images, fonts, ico, json, txt, js
  matcher: [
    "/((?!api|_next/static|_next/image|images|fonts|favicon.ico|manifest.json|robots.txt|sw.js|workbox-.*\\.js).*)",
  ],
};
