// src/middleware.ts
import createNextIntlMiddleware from "next-intl/middleware";
import { NextRequest, NextResponse } from "next/server";
import { locales, defaultLocale } from "./config/i18n.config";
import { PATHS } from "./constants/paths";
import { jwtDecode } from "jwt-decode"; // Using a lightweight decoder
import { ROLE_COOKIE_NAME } from "./constants/auth";

const REFRESH_TOKEN_COOKIE_NAME = "qader-refresh-token";

// Define protected routes
const platformRoutes = [PATHS.STUDY.HOME, PATHS.COMPLETE_PROFILE];
const adminRoutes = [PATHS.ADMIN.DASHBOARD];
const authRoutes = [PATHS.LOGIN, PATHS.SIGNUP, PATHS.FORGOT_PASSWORD];

const intlMiddleware = createNextIntlMiddleware({
  locales: locales as unknown as string[],
  defaultLocale: defaultLocale as string,
  localePrefix: "as-needed",
  localeDetection: false,
});

export default function middleware(req: NextRequest) {
  // Run next-intl middleware first to get correct locale and response
  const response = intlMiddleware(req);
  const locale = req.headers.get("x-next-intl-locale") || defaultLocale;
  const { pathname } = req.nextUrl;

  // Derive pathname without locale for matching
  const pathnameWithoutLocale = pathname.startsWith(`/${locale}`)
    ? pathname.substring(`/${locale}`.length) || "/"
    : pathname;

  // Get session status from the secure cookie
  const refreshToken = req.cookies.get(REFRESH_TOKEN_COOKIE_NAME)?.value;
  const isAuthenticated = !!refreshToken;

  // --- Authorization Logic ---
  const userRole = req.cookies.get(ROLE_COOKIE_NAME)?.value; // 'admin' or 'student'
  const isStaff = userRole === "admin";

  // 1. Redirect unauthenticated users from protected routes
  if (
    !isAuthenticated &&
    (platformRoutes.some((path) => pathnameWithoutLocale.startsWith(path)) ||
      adminRoutes.some((path) => pathnameWithoutLocale.startsWith(path)))
  ) {
    if (pathname != "/study-preview") {
      const loginUrl = new URL(`/${locale}${PATHS.LOGIN}`, req.url);
      loginUrl.searchParams.set("redirect_to", pathname); // Redirect back after login
      return NextResponse.redirect(loginUrl);
    }
  }

  // 2. Redirect authenticated users from auth pages
  if (
    isAuthenticated &&
    authRoutes.some((path) => pathnameWithoutLocale.startsWith(path))
  ) {
    const redirectPath = isStaff
      ? PATHS.ADMIN.EMPLOYEES_MANAGEMENT
      : PATHS.STUDY.HOME;
    return NextResponse.redirect(new URL(`/${locale}${redirectPath}`, req.url));
  }

  // 3. Protect admin routes from non-staff users
  if (
    isAuthenticated &&
    !isStaff &&
    adminRoutes.some((path) => pathnameWithoutLocale.startsWith(path))
  ) {
    // Redirect non-admins to the student dashboard
    return NextResponse.redirect(
      new URL(`/${locale}${PATHS.STUDY.HOME}`, req.url)
    );
  }

  // If all checks pass, continue with the response from next-intl
  return response;
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|images|fonts|favicon.ico|manifest.json|robots.txt|sw.js|workbox-.*.js).*)",
  ],
};
