"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes";
import { PropsWithChildren, useState } from "react";
// import { NextIntlClientProvider } from 'next-intl'; // We'll handle this differently for App Router

// Zustand store (example - create your store file separately)
// import { useAuthStore } from '@/store/auth.store';

export function Providers({
  children,
  ...props
}: PropsWithChildren<ThemeProviderProps>) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            refetchOnWindowFocus: false, // Optional: adjust as needed
          },
        },
      })
  );

  // If you need to pass messages to NextIntlClientProvider for client components,
  // you'd typically get them from a higher-level Server Component or useAbstractIntlMessages.
  // For now, let's assume next-intl setup will handle messages at the root or per-layout.

  return (
    <NextThemesProvider {...props}>
      <QueryClientProvider client={queryClient}>
        {children}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </NextThemesProvider>
  );
}
