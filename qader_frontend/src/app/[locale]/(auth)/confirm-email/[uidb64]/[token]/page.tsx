"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation"; // Keep next/navigation for useParams
import { useRouter } from "next/navigation"; // Use next's Router
import { useMutation } from "@tanstack/react-query";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import { confirmEmail, ConfirmEmailParams } from "@/services/auth.service"; // Adjust path
import { useAuthStore } from "@/store/auth.store"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import { Button } from "@/components/ui/button";
import Link from "next/link"; // Use next's Link
import { QUERY_KEYS } from "@/constants/queryKeys"; // Adjust path

export default function ConfirmEmailPage() {
  const tAuth = useTranslations("Auth");
  const router = useRouter();
  const params = useParams();
  const { login: storeLogin, isAuthenticated } = useAuthStore();

  const uidb64 = typeof params.uidb64 === "string" ? params.uidb64 : "";
  const token = typeof params.token === "string" ? params.token : "";

  const confirmEmailMutation = useMutation({
    mutationKey: [QUERY_KEYS.CONFIRM_EMAIL],
    mutationFn: (data: ConfirmEmailParams) => confirmEmail(data),
    onSuccess: (data) => {
      storeLogin({ access: data.access, refresh: data.refresh }, data.user);
      toast.success(tAuth("confirmEmailSuccessMessage"));
      if (!data.user.profile_complete) {
        router.replace(PATHS.COMPLETE_PROFILE);
      } else {
        router.replace(PATHS.STUDY_HOME);
      }
    },
    onError: (error: any) => {
      // Error message will be displayed on the page, not via toast here.
      // The specific error message is determined in the render block.
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      toast.info(tAuth("confirmEmailAlreadyLoggedIn"));
      const user = useAuthStore.getState().user;
      if (user?.is_super || user?.is_staff)
        router.replace(PATHS.ADMIN_DASHBOARD);
      else if (user?.profile_complete) router.replace(PATHS.STUDY_HOME);
      else router.replace(PATHS.COMPLETE_PROFILE);
      return;
    }
    if (uidb64 && token) {
      confirmEmailMutation.mutate({ uidb64, token });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uidb64, token, isAuthenticated, router, storeLogin]);

  if (!uidb64 || !token) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center">
        <AlertCircle className="mb-4 h-16 w-16 text-destructive" />
        <h1 className="mb-2 text-2xl font-semibold">
          {tAuth("confirmEmailMissingParamsTitle")}
        </h1>
        <p className="mb-6 text-muted-foreground">
          {tAuth("confirmEmailMissingParams")}
        </p>
        <Button asChild>
          <Link href={PATHS.HOME}>{tAuth("confirmEmailBackToHome")}</Link>
        </Button>
      </div>
    );
  }

  // Get the current locale to set the page direction
  // This could also be done by passing locale from params to a layout if this page had one
  const locale = typeof params.locale === "string" ? params.locale : "ar"; // Default to 'ar' or your defaultLocale

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
          <Button
            onClick={() => {
              const user = confirmEmailMutation.data?.user;
              if (user && !user.profile_complete)
                router.replace(PATHS.COMPLETE_PROFILE);
              else router.replace(PATHS.STUDY_HOME);
            }}
          >
            {tAuth("confirmEmailContinueButton")}
          </Button>
        </>
      )}
      {confirmEmailMutation.isError && (
        <>
          <AlertCircle className="mb-4 h-16 w-16 text-destructive" />
          <h1 className="mb-2 text-2xl font-semibold text-destructive">
            {tAuth("confirmEmailErrorTitle")}
          </h1>
          <p className="mb-6 text-muted-foreground">
            {(confirmEmailMutation.error as any)?.status === 400
              ? tAuth("confirmEmailInvalidOrExpiredLink")
              : (confirmEmailMutation.error as any)?.status === 404
              ? tAuth("confirmEmailUserNotFound")
              : (confirmEmailMutation.error as any)?.message ||
                tAuth("confirmEmailDefaultErrorMessage")}
          </p>
          <div className="space-x-4 rtl:space-x-reverse">
            <Button
              variant="outline"
              onClick={() => confirmEmailMutation.mutate({ uidb64, token })}
            >
              {tAuth("confirmEmailRetryButton")}
            </Button>
            <Button asChild>
              <Link href={PATHS.HOME}>{tAuth("confirmEmailBackToHome")}</Link>
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
