"use client";

import React, { useEffect, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { User, Mail, Lock, Eye, EyeOff, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  SignupSchema,
  type SignupFormValues,
  type ApiSignupData,
} from "@/types/forms/auth.schema";
import { signupUser } from "@/services/auth.service";
import { PATHS } from "@/constants/paths";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import { AuthFormCard } from "@/components/auth/AuthFormCard";
// import { useTranslations } from 'next-intl';

const signupPageDefaultValues: SignupFormValues = {
  full_name: "",
  email: "",
  password: "",
  password_confirm: "",
  termsAccepted: false,
};

export default function SignupPage() {
  // const t = useTranslations('Auth.Signup');
  // const tCommon = useTranslations('Common');
  const router = useRouter();
  const { isAuthenticated, user: authUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
    reset,
  } = useForm<SignupFormValues>({
    resolver: zodResolver(SignupSchema),
    defaultValues: signupPageDefaultValues,
  });

  // Redirect if already authenticated (logic remains the same)
  useEffect(() => {
    if (isAuthenticated && authUser) {
      toast.info("أنت مسجل الدخول بالفعل.");
      if (authUser.profile_complete) {
        if (authUser.is_super || authUser.is_staff) {
          router.replace(PATHS.ADMIN_DASHBOARD || "/admin/dashboard");
        } else {
          router.replace(PATHS.STUDY_HOME || "/study");
        }
      } else {
        router.replace(PATHS.COMPLETE_PROFILE || "/auth/complete-profile");
      }
    }
  }, [isAuthenticated, authUser, router]);

  const signupMutation = useMutation({
    mutationKey: [QUERY_KEYS.SIGNUP],
    mutationFn: (data: SignupFormValues) => {
      const apiPayload: ApiSignupData = {
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        password_confirm: data.password_confirm,
      };
      return signupUser(apiPayload);
    },
    onSuccess: (data) => {
      toast.success(
        data.detail ||
          "تم إرسال رابط التفعيل إلى بريدك الإلكتروني. يرجى التحقق من بريدك الوارد والمجلدات الأخرى.",
        { duration: 8000 }
      );
      reset();
      // Optionally, you might want to display a persistent message on the page
      // or automatically redirect to login after a few seconds or to a "check your email" page.
      // For now, we just show a toast and clear the form.
    },
    onError: (error: any) => {
      if (error.status === 400 && error.data) {
        let specificErrorSet = false;
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof SignupFormValues;
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : String(error.data[key]);

          if (Object.keys(signupPageDefaultValues).includes(field)) {
            setFormError(field, { type: "server", message });
            specificErrorSet = true;
          }
        });

        if (error.data.detail) {
          toast.error(String(error.data.detail));
        } else if (!specificErrorSet) {
          // If no specific field errors were mapped from error.data and no detail message
          toast.error("فشل التسجيل. الرجاء التحقق من البيانات المدخلة.");
        }
      } else {
        toast.error(error.message || "فشل الاتصال بالخادم. حاول لاحقاً.");
      }
    },
  });

  const onSubmit = (data: SignupFormValues) => {
    signupMutation.mutate(data);
  };

  if (isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background p-6">
        <Sparkles className="w-12 h-12 text-primary animate-pulse mb-4" />
        <p className="text-muted-foreground">جاري التوجيه...</p>
      </div>
    );
  }

  return (
    <AuthFormCard
      title="إنشاء حساب جديد" // t('createAccountTitle')
      description="املأ النموذج أدناه لإنشاء حسابك." // t('signupPrompt')
      footerPromptText="لديك حساب بالفعل؟" // t('alreadyHaveAccount')
      footerLinkText="تسجيل الدخول" // t('login')
      footerLinkHref={PATHS.LOGIN || "/login"}
      showLogo={true} // Show logo on signup
    >
      {signupMutation.isSuccess ? (
        <Alert
          variant="default"
          className="mb-4 bg-green-50 dark:bg-green-900/30 border-green-300 dark:border-green-700 text-green-700 dark:text-green-300"
        >
          <Sparkles className="h-5 w-5 text-green-600 dark:text-green-400" />
          <AlertTitle className="font-semibold">تم بنجاح!</AlertTitle>
          <AlertDescription>
            {signupMutation.data?.detail ||
              "تم إرسال رابط التفعيل. يرجى التحقق من بريدك الإلكتروني."}
          </AlertDescription>
        </Alert>
      ) : (
        signupMutation.error &&
        !(signupMutation.error as any).data?.detail &&
        !(signupMutation.error as any).data?.email && ( // Add other fields if needed
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>خطأ في التسجيل</AlertTitle>
            <AlertDescription>
              {(signupMutation.error as any)?.message ||
                "فشل التسجيل. الرجاء التحقق من البيانات المدخلة."}
            </AlertDescription>
          </Alert>
        )
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <Label htmlFor="signup-fullname">الاسم الكامل</Label>
          <div className="relative mt-1">
            <User className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="signup-fullname"
              type="text"
              placeholder="الاسم الثلاثي"
              {...register("full_name")}
              className="pl-10 rtl:pr-10"
              aria-invalid={errors.full_name ? "true" : "false"}
              disabled={signupMutation.isSuccess}
            />
          </div>
          {errors.full_name && (
            <p className="mt-1 text-xs text-red-500">
              {errors.full_name.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="signup-email">البريد الإلكتروني</Label>
          <div className="relative mt-1">
            <Mail className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="signup-email"
              type="email"
              placeholder="you@example.com"
              {...register("email")}
              className="pl-10 rtl:pr-10"
              aria-invalid={errors.email ? "true" : "false"}
              disabled={signupMutation.isSuccess}
            />
          </div>
          {errors.email && (
            <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="signup-password">كلمة المرور</Label>
          <div className="relative mt-1">
            <Lock className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="signup-password"
              type={showPassword ? "text" : "password"}
              placeholder="********"
              {...register("password")}
              className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
              aria-invalid={errors.password ? "true" : "false"}
              disabled={signupMutation.isSuccess}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={
                showPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"
              }
              disabled={signupMutation.isSuccess}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.password && (
            <p className="mt-1 text-xs text-red-500">
              {errors.password.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="signup-confirm-password">تأكيد كلمة المرور</Label>
          <div className="relative mt-1">
            <Lock className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="signup-confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              placeholder="********"
              {...register("password_confirm")}
              className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
              aria-invalid={errors.password_confirm ? "true" : "false"}
              disabled={signupMutation.isSuccess}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={
                showConfirmPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"
              }
              disabled={signupMutation.isSuccess}
            >
              {showConfirmPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.password_confirm && (
            <p className="mt-1 text-xs text-red-500">
              {errors.password_confirm.message}
            </p>
          )}
        </div>

        <div className="flex items-start space-x-2 rtl:space-x-reverse pt-1">
          <Controller
            name="termsAccepted"
            control={control}
            render={({ field }) => (
              <Checkbox
                id="termsAccepted"
                checked={field.value}
                onCheckedChange={field.onChange}
                aria-invalid={errors.termsAccepted ? "true" : "false"}
                disabled={signupMutation.isSuccess}
                className="mt-0.5" // Align better with label
              />
            )}
          />
          <Label
            htmlFor="termsAccepted"
            className="text-sm font-normal text-muted-foreground leading-snug cursor-pointer"
          >
            أوافق على{" "}
            <Link
              href={PATHS.TERMS_AND_CONDITIONS || "/conditions"}
              className="font-medium text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              الشروط والأحكام
            </Link>
          </Label>
        </div>
        {errors.termsAccepted && (
          <p className="text-xs text-red-500 -mt-4">
            {" "}
            {/* Adjusted margin */}
            {errors.termsAccepted.message}
          </p>
        )}

        <Button
          type="submit"
          className="w-full"
          disabled={signupMutation.isPending || signupMutation.isSuccess}
        >
          {signupMutation.isPending ? (
            <>
              <Sparkles className="mr-2 h-4 w-4 animate-spin rtl:ml-2 rtl:mr-0" />
              جارٍ التسجيل...
            </>
          ) : (
            "إنشاء حساب"
          )}
        </Button>
      </form>
    </AuthFormCard>
  );
}
