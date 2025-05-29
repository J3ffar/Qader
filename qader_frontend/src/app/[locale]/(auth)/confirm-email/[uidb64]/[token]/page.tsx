// qader_frontend/src/app/[locale]/(auth)/confirm-email/[uidb64]/[token]/page.tsx
"use client";

import { useEffect, useMemo } from "react"; // Added useMemo
import { useParams, useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Loader2, AlertCircle, CheckCircle2, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import Link from "next/link";

import {
  confirmEmail,
  ConfirmEmailParams,
  ConfirmEmailResponse,
} from "@/services/auth.service";
import { useAuth, useAuthActions, useAuthStore } from "@/store/auth.store"; // Added useAuth
import { PATHS } from "@/constants/paths";
import { Button } from "@/components/ui/button";
import { QUERY_KEYS } from "@/constants/queryKeys";
import type { ApiError } from "@/types/api/auth.types";

export default function ConfirmEmailPage() {
  const tAuth = useTranslations("Auth");
  const router = useRouter();
  const params = useParams();

  const { isAuthenticated, user } = useAuth(); // Use custom hook
  const { login: storeLogin, setIsProfileComplete: storeSetIsProfileComplete } =
    useAuthActions(); // Use custom hook

  // Memoize params to prevent re-renders if params object identity changes but values don't
  const uidb64 = useMemo(
    () => (typeof params.uidb64 === "string" ? params.uidb64 : ""),
    [params.uidb64]
  );
  const token = useMemo(
    () => (typeof params.token === "string" ? params.token : ""),
    [params.token]
  );

  const confirmEmailMutation = useMutation<
    ConfirmEmailResponse, // TData: Response from confirmEmail (LoginResponse structure)
    ApiError, // TError
    ConfirmEmailParams // TVariables: { uidb64, token }
  >({
    mutationKey: [QUERY_KEYS.CONFIRM_EMAIL, uidb64, token], // Include params in key
    mutationFn: (data: ConfirmEmailParams) => confirmEmail(data),
    onSuccess: (data) => {
      // data is ConfirmEmailResponse
      storeLogin({ access: data.access, refresh: data.refresh }, data.user);
      storeSetIsProfileComplete(data.user.profile_complete); // Ensure this is set
      toast.success(tAuth("confirmEmailSuccessMessage"));

      // Redirect logic based on profile completeness
      if (!data.user.profile_complete) {
        router.replace(PATHS.COMPLETE_PROFILE);
      } else if (data.user.is_super || data.user.is_staff) {
        router.replace(PATHS.ADMIN_DASHBOARD);
      } else {
        router.replace(PATHS.STUDY_HOME);
      }
    },
    onError: (error: ApiError) => {
      // Display error specific to confirmation failure, avoid generic toast if page shows details
      // The page will display a detailed error message.
      // console.error("Email confirmation failed:", error.data?.detail || error.message);
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      // User is already logged in.
      toast.info(tAuth("confirmEmailAlreadyLoggedIn"));
      // Redirect based on existing user's state
      if (user?.is_super || user?.is_staff) {
        router.replace(PATHS.ADMIN_DASHBOARD);
      } else if (user?.profile_complete) {
        router.replace(PATHS.STUDY_HOME);
      } else {
        router.replace(PATHS.COMPLETE_PROFILE);
      }
      return; // Stop further execution
    }

    // If not authenticated, and uidb64 & token are present, attempt confirmation
    if (uidb64 && token) {
      if (
        !confirmEmailMutation.isPending &&
        !confirmEmailMutation.isSuccess &&
        !confirmEmailMutation.isError
      ) {
        confirmEmailMutation.mutate({ uidb64, token });
      }
    }
    // No need to include storeLogin, router in deps if they are stable (which they usually are from Next.js/Zustand)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uidb64, token, isAuthenticated, user, router]); // Added user to deps for the redirect logic

  // Get current locale for dir attribute
  const locale = typeof params.locale === "string" ? params.locale : "ar";

  // Early exit for missing parameters
  if (!uidb64 || !token) {
    if (isAuthenticated) return null; // Already handled by useEffect redirect
    return (
      <div
        className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center"
        dir={locale === "ar" ? "rtl" : "ltr"}
      >
        <ShieldAlert className="mb-4 h-16 w-16 text-destructive" />
        <h1 className="mb-2 text-2xl font-semibold">
          {tAuth("confirmEmailMissingParamsTitle")}
        </h1>
        <p className="mb-6 text-muted-foreground">
          {tAuth("confirmEmailMissingParams")}
        </p>
        <Button asChild>
          <Link href={PATHS.LOGIN}>{tAuth("goToLogin")}</Link>
        </Button>
      </div>
    );
  }

  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center"
      dir={locale === "ar" ? "rtl" : "ltr"}
    >
      {confirmEmailMutation.isPending && (
        <>
          <Loader2 className="mb-4 h-16 w-16 animate-spin text-primary" />
          <h1 className="mb-2 text-2xl font-semibold">
            {tAuth("confirmEmailConfirmingTitle")}
          </h1>
          <p className="text-muted-foreground">
            {tAuth("confirmEmailPleaseWait")}
          </p>
        </>
      )}
      {confirmEmailMutation.isSuccess && (
        <>
          <CheckCircle2 className="mb-4 h-16 w-16 text-green-500" />
          <h1 className="mb-2 text-2xl font-semibold text-green-600">
            {tAuth("confirmEmailSuccessTitle")}
          </h1>
          <p className="mb-6 text-muted-foreground">
            {tAuth("confirmEmailRedirectingMessage")}
          </p>
          {/* Button is optional as redirect happens automatically, could be a fallback */}
          <Button
            onClick={() => {
              const confirmedUser = confirmEmailMutation.data?.user;
              if (confirmedUser && !confirmedUser.profile_complete) {
                router.replace(PATHS.COMPLETE_PROFILE);
              } else if (confirmedUser?.is_super || confirmedUser?.is_staff) {
                router.replace(PATHS.ADMIN_DASHBOARD);
              } else {
                router.replace(PATHS.STUDY_HOME);
              }
            }}
            className="mt-4"
          >
            {tAuth("confirmEmailContinueButton")}
          </Button>
        </>
      )}
      {confirmEmailMutation.isError && (
        <>
          <AlertCircle className="mb-4 h-16 w-16 text-destructive" />
          <h1 className="mb-2 text-2xl font-semibold text-destructive">
            {tAuth("confirmEmailErrorTitlePage")}{" "}
            {/* More specific key for page title */}
          </h1>
          <p className="mb-6 text-muted-foreground">
            {confirmEmailMutation.error?.data?.detail ||
              confirmEmailMutation.error?.message ||
              tAuth("confirmEmailErrorDefault")}
          </p>
          <div className="flex space-x-4 rtl:space-x-reverse">
            <Button
              variant="outline"
              onClick={() => confirmEmailMutation.mutate({ uidb64, token })}
              disabled={confirmEmailMutation.isPending}
            >
              {confirmEmailMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              {tAuth("confirmEmailRetryButton")}
            </Button>
            <Button asChild>
              <Link href={PATHS.LOGIN}>{tAuth("goToLogin")}</Link>
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
