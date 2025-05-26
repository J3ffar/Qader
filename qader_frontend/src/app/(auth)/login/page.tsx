"use client";

import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Mail, Lock, Eye, EyeOff, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import { LoginSchema, type LoginCredentials } from "@/types/forms/auth.schema";
import { loginUser } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { AuthFormCard } from "@/components/auth/AuthFormCard";
// import { useTranslations } from 'next-intl';

export default function LoginPage() {
  // const t = useTranslations('Auth.Login');
  // const tCommon = useTranslations('Common');
  const router = useRouter();
  // const searchParams = useSearchParams();
  const { login: storeLogin, isAuthenticated, user: authUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
    reset,
  } = useForm<LoginCredentials>({
    resolver: zodResolver(LoginSchema),
    defaultValues: {
      username: "",
      password: "",
      rememberMe: false,
    },
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
        router.replace(PATHS.COMPLETE_PROFILE || "/complete-profile");
      }
    }
  }, [isAuthenticated, authUser, router]);

  const loginMutation = useMutation({
    mutationKey: [QUERY_KEYS.LOGIN],
    mutationFn: loginUser,
    onSuccess: (data) => {
      storeLogin({ access: data.access, refresh: data.refresh }, data.user);
      toast.success("تم تسجيل الدخول بنجاح!");
      reset();
      // const redirectUrl =
      //   searchParams.get("redirect") ||
      //   (data.user.profile_complete
      //     ? data.user.is_super || data.user.is_staff
      //       ? PATHS.ADMIN_DASHBOARD
      //       : PATHS.STUDY_HOME
      //     : PATHS.COMPLETE_PROFILE);
      // router.replace(redirectUrl);
    },
    onError: (error: any) => {
      if (error.status === 400 && error.data) {
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof LoginCredentials;
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : String(error.data[key]);
          if (field === "username" || field === "password") {
            setFormError(field, { type: "server", message });
          }
        });
        if (error.data.detail) {
          toast.error(String(error.data.detail));
        } else {
          toast.error("بيانات الدخول غير صحيحة أو حساب غير مفعل.");
        }
      } else {
        toast.error(error.message || "فشل الاتصال بالخادم. حاول لاحقاً.");
      }
    },
  });

  const onSubmit = (data: LoginCredentials) => {
    loginMutation.mutate(data);
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
      title="أهلاً بعودتك!" // t('welcomeBack')
      description="أدخل بياناتك لتسجيل الدخول إلى حسابك." // t('loginPrompt')
      footerPromptText="ليس لديك حساب؟" // t('noAccount')
      footerLinkText="إنشاء حساب" // t('createAccount')
      footerLinkHref={PATHS.SIGNUP || "/signup"}
      // showLogo // Optional: if you want logo on login page too
    >
      {loginMutation.error &&
        !(loginMutation.error as any).data?.detail &&
        !(loginMutation.error as any).data?.username &&
        !(loginMutation.error as any).data?.password && (
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>خطأ في تسجيل الدخول</AlertTitle>
            <AlertDescription>
              {(loginMutation.error as any)?.message ||
                "بيانات الدخول غير صحيحة أو حساب غير مفعل."}
            </AlertDescription>
          </Alert>
        )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <Label htmlFor="login-username">
            البريد الإلكتروني أو اسم المستخدم
          </Label>
          <div className="relative mt-1">
            <Mail className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="login-username"
              type="text"
              placeholder="you@example.com"
              {...register("username")}
              className="pl-10 rtl:pr-10"
              aria-invalid={errors.username ? "true" : "false"}
            />
          </div>
          {errors.username && (
            <p className="mt-1 text-xs text-red-500">
              {errors.username.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="login-password">كلمة المرور</Label>
          <div className="relative mt-1">
            <Lock className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="login-password"
              type={showPassword ? "text" : "password"}
              placeholder="********"
              {...register("password")}
              className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
              aria-invalid={errors.password ? "true" : "false"}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={
                showPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"
              }
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

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2 rtl:space-x-reverse">
            <Checkbox id="rememberMe" {...register("rememberMe")} />
            <Label
              htmlFor="rememberMe"
              className="font-normal text-muted-foreground"
            >
              حفظ الجلسة
            </Label>
          </div>
          <Link
            href={PATHS.FORGOT_PASSWORD || "/auth/forgot-password"}
            className="text-sm text-primary hover:underline"
          >
            نسيت كلمة السر؟
          </Link>
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={loginMutation.isPending}
        >
          {loginMutation.isPending ? (
            <>
              <Sparkles className="mr-2 h-4 w-4 animate-spin rtl:ml-2 rtl:mr-0" />
              جارٍ الدخول...
            </>
          ) : (
            "دخول"
          )}
        </Button>
      </form>
    </AuthFormCard>
  );
}
