"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

import { confirmEmail, ConfirmEmailParams } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { QUERY_KEYS } from "@/constants/queryKeys";
// import { useTranslations } from 'next-intl';

export default function ConfirmEmailPage() {
  // const t = useTranslations('Auth.ConfirmEmail');
  const router = useRouter();
  const params = useParams(); // Gets { uidb64: string, token: string } from dynamic route
  const { login: storeLogin, isAuthenticated } = useAuthStore();

  const uidb64 = typeof params.uidb64 === "string" ? params.uidb64 : "";
  const token = typeof params.token === "string" ? params.token : "";

  const confirmEmailMutation = useMutation({
    mutationKey: QUERY_KEYS.CONFIRM_EMAIL,
    mutationFn: (data: ConfirmEmailParams) => confirmEmail(data),
    onSuccess: (data) => {
      storeLogin({ access: data.access, refresh: data.refresh }, data.user);
      toast.success("تم تأكيد بريدك الإلكتروني بنجاح!"); // t('successMessage')

      // Redirect based on profile completion
      if (!data.user.profile_complete) {
        router.replace(PATHS.COMPLETE_PROFILE || "/complete-profile");
      } else {
        router.replace(PATHS.STUDY_HOME || "/study");
      }
    },
    onError: (error: any) => {
      let errorMessage =
        "فشل تأكيد البريد الإلكتروني. قد يكون الرابط غير صالح أو منتهي الصلاحية."; // t('defaultErrorMessage')
      if (error.status === 400) {
        errorMessage =
          "الرابط المستخدم غير صالح أو قد انتهت صلاحيته. يرجى المحاولة مرة أخرى أو طلب رابط جديد."; // t('invalidOrExpiredLink')
      } else if (error.status === 404) {
        errorMessage = "لم يتم العثور على المستخدم المرتبط بهذا الرابط."; // t('userNotFound')
      } else if (error.message) {
        errorMessage = error.message;
      }
      // No toast here, display error directly on the page
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      // If user is already logged in, perhaps they clicked an old link.
      // Redirect them to their study page or dashboard.
      toast.info("أنت مسجل الدخول بالفعل."); // t('alreadyLoggedIn')
      const user = useAuthStore.getState().user;
      if (user?.is_super || user?.is_staff) {
        router.replace(PATHS.ADMIN_DASHBOARD || "/admin/dashboard");
      } else if (user?.profile_complete) {
        router.replace(PATHS.STUDY_HOME || "/study");
      } else {
        router.replace(PATHS.COMPLETE_PROFILE || "/complete-profile");
      }
      return;
    }

    if (uidb64 && token) {
      confirmEmailMutation.mutate({ uidb64, token });
    }
    // Adding confirmEmailMutation to dependencies can cause loops if not careful.
    // We only want to trigger this once when uidb64 and token are available.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uidb64, token, isAuthenticated, router, storeLogin]); // Removed confirmEmailMutation from deps

  if (!uidb64 || !token) {
    // This case should ideally not be reached if the route is set up correctly,
    // but good for robustness or if parameters are missing.
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background p-6 text-center">
        <AlertCircle className="w-16 h-16 text-destructive mb-4" />
        <h1 className="text-2xl font-semibold mb-2">خطأ في الرابط</h1>
        <p className="text-muted-foreground mb-6">
          {/*t('missingParams')*/}معلمات التأكيد مفقودة من الرابط.
        </p>
        <Button asChild>
          <Link href={PATHS.HOME || "/"}>العودة إلى الرئيسية</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center bg-background p-6 text-center rounded-4xl">
      {confirmEmailMutation.isPending && (
        <>
          <Loader2 className="w-16 h-16 text-primary animate-spin mb-4" />
          <h1 className="text-2xl font-semibold mb-2">
            جارٍ تأكيد بريدك الإلكتروني...
          </h1>{" "}
          {/*t('confirmingTitle')*/}
          <p className="text-muted-foreground">الرجاء الانتظار قليلاً.</p>{" "}
          {/*t('pleaseWait')*/}
        </>
      )}

      {confirmEmailMutation.isSuccess && (
        <>
          <CheckCircle2 className="w-16 h-16 text-green-500 mb-4" />
          <h1 className="text-2xl font-semibold text-green-600 mb-2">
            تم تأكيد البريد بنجاح!
          </h1>{" "}
          {/*t('successTitle')*/}
          <p className="text-muted-foreground mb-6">
            {/*t('redirectingMessage')*/}سيتم توجيهك الآن...
          </p>
          {/* Optional: Add a manual redirect button if auto-redirect fails or for user convenience */}
          <Button
            onClick={() => {
              const user = confirmEmailMutation.data?.user;
              if (user && !user.profile_complete) {
                router.replace(PATHS.COMPLETE_PROFILE || "/complete-profile");
              } else {
                router.replace(PATHS.STUDY_HOME || "/study");
              }
            }}
          >
            متابعة
          </Button>
        </>
      )}

      {confirmEmailMutation.isError && (
        <>
          <AlertCircle className="w-16 h-16 text-destructive mb-4" />
          <h1 className="text-2xl font-semibold text-destructive mb-2">
            فشل تأكيد البريد الإلكتروني
          </h1>{" "}
          {/*t('errorTitle')*/}
          <p className="text-muted-foreground mb-6">
            {(confirmEmailMutation.error as any)?.message ||
              "حدث خطأ غير متوقع."}
          </p>
          <div className="space-x-4 rtl:space-x-reverse">
            <Button
              variant="outline"
              onClick={() => confirmEmailMutation.mutate({ uidb64, token })}
            >
              {/*t('retryButton')*/}إعادة المحاولة
            </Button>
            <Button asChild>
              <Link href={PATHS.HOME || "/"}>العودة إلى الرئيسية</Link>
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
