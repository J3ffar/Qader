/**
 * Retrieves the current locale from the window.location.pathname.
 * This is a client-side utility. For server-side, you'd get locale from params or middleware.
 * Assumes locale is the first segment (e.g., /ar/..., /en/...).
 * @returns The current locale string (e.g., "ar", "en") or a default ('ar').
 */
export const getLocaleFromPathname = (): string => {
  if (typeof window !== "undefined") {
    const pathSegments = window.location.pathname.split("/");
    // Check if the first segment looks like a locale code (e.g., 'ar', 'en', 'en-US')
    if (pathSegments[1] && /^[a-z]{2}(-[A-Z]{2})?$/.test(pathSegments[1])) {
      return pathSegments[1];
    }
  }
  return "ar"; // Default locale if not found or on server (should be handled differently on server)
};
