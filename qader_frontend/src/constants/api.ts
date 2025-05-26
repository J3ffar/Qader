export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://qader.vip";
export const API_VERSION = "v1";
// Language prefix might be handled by next-intl or needs dynamic insertion
// For now, we'll assume auth.service.ts handles the full path construction including locale if necessary
