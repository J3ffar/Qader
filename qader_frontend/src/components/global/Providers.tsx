"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes";
import { PropsWithChildren, useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { appEvents } from "@/lib/events";

/**
 * SessionExpiredHandler is a small, client-only component responsible for listening to
 * a global event that signals an unrecoverable session error (e.g., invalid refresh token).
 * When the event is caught, it displays a user-friendly toast message.
 * The actual redirection logic is handled in the `auth.store.ts` logout function.
 */
const SessionExpiredHandler = () => {
  // We can use this hook because the parent <Providers> component is wrapped
  // by <NextIntlClientProvider> in the root layout.
  const t = useTranslations("Common");

  useEffect(() => {
    const handleSessionExpired = () => {
      toast.error(t("sessionExpiredTitle"), {
        description: t("sessionExpiredDescription"),
        duration: 6000, // Give the user a bit more time to read it
      });
    };

    appEvents.on("auth:session-expired", handleSessionExpired);

    return () => {
      appEvents.off("auth:session-expired", handleSessionExpired);
    };
  }, [t]);

  return null; // This component renders no UI.
};

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
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <NextThemesProvider {...props}>
      <QueryClientProvider client={queryClient}>
        {/* The SessionExpiredHandler is placed here. It's a client component
            that will be active on every page, ready to listen for our event. */}
        {/* <SessionExpiredHandler />  */}

        {children}

        {process.env.NODE_ENV === "development" && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </NextThemesProvider>
  );
}
