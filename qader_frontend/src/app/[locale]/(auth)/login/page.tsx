"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation"; // Corrected import
import Link from "next/link"; // Corrected import
import { toast } from "sonner";
import { Mail, Lock, Eye, EyeOff, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  createLoginSchema,
  type LoginCredentials,
} from "@/types/forms/auth.schema"; // Adjust path
import { loginUser } from "@/services/auth.service"; // Adjust path
import { useAuthStore } from "@/store/auth.store"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import { QUERY_KEYS } from "@/constants/queryKeys"; // Adjust path
import { AuthFormCard } from "@/components/auth/AuthFormCard"; // Adjust path

export default function LoginPage() {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common");
  const router = useRouter();
  const { login: storeLogin, isAuthenticated, user: authUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const CurrentLoginSchema = useMemo(() => createLoginSchema(tAuth), [tAuth]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
    reset,
  } = useForm<LoginCredentials>({
    resolver: zodResolver(CurrentLoginSchema),
    defaultValues: { username: "", password: "", rememberMe: false },
  });

  useEffect(() => {
    if (isAuthenticated && authUser) {
      toast.info(tAuth("alreadyLoggedIn"));
      if (authUser.profile_complete) {
        if (authUser.is_super || authUser.is_staff) {
          router.replace(PATHS.ADMIN_DASHBOARD || "/admin/dashboard");
        } else {
          router.replace(PATHS.STUDY_HOME || "/study");
        }
      } else {
        router.replace(PATHS.COMPLETE_PROFILE || "/auth/complete-profile"); // Ensure PATHS.COMPLETE_PROFILE leads to the correct localized route
      }
    }
  }, [isAuthenticated, authUser, router, tAuth]);

  const loginMutation = useMutation({
    mutationKey: [QUERY_KEYS.LOGIN],
    mutationFn: loginUser,
    onSuccess: (data) => {
      storeLogin({ access: data.access, refresh: data.refresh }, data.user);
      toast.success(tAuth("loginSuccess"));
      reset();
      if (data.user?.is_super || data.user?.is_staff) {
        router.push(PATHS.ADMIN_DASHBOARD);
      } else if (!data.user.profile_complete) {
        router.push(PATHS.COMPLETE_PROFILE);
      } else {
        router.push(PATHS.STUDY_HOME);
      }
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
          toast.error(tAuth("loginFailed"));
        }
      } else {
        toast.error(error.message || tAuth("loginErrorServer"));
      }
    },
  });

  const onSubmit = (data: LoginCredentials) => loginMutation.mutate(data);

  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6">
        <Sparkles className="mb-4 h-12 w-12 animate-pulse text-primary" />
        <p className="text-muted-foreground">{tAuth("redirecting")}</p>
      </div>
    );
  }

  return (
    <AuthFormCard
      title={tAuth("welcomeBack")}
      description={tAuth("loginPrompt")}
      footerPromptText={tAuth("noAccount")}
      footerLinkText={tAuth("createAccount")}
      footerLinkHref={PATHS.SIGNUP} // PATHS.SIGNUP should be a simple path like '/signup'
    >
      {loginMutation.error &&
        !(loginMutation.error as any).data?.detail &&
        !(loginMutation.error as any).data?.username &&
        !(loginMutation.error as any).data?.password && (
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>{tAuth("loginErrorAlertTitle")}</AlertTitle>
            <AlertDescription>
              {(loginMutation.error as any)?.message || tAuth("loginFailed")}
            </AlertDescription>
          </Alert>
        )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <Label htmlFor="login-page-username">
            {tAuth("emailOrUsername")}
          </Label>
          <div className="relative mt-1">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3" />
            <Input
              id="login-page-username"
              type="text"
              placeholder={tAuth("emailOrUsernamePlaceholder")}
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
          <Label htmlFor="login-page-password">{tAuth("password")}</Label>
          <div className="relative mt-1">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3" />
            <Input
              id="login-page-password"
              type={showPassword ? "text" : "password"}
              placeholder={tAuth("passwordPlaceholder")}
              {...register("password")}
              className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
              aria-invalid={errors.password ? "true" : "false"}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground ltr:right-3 rtl:left-3"
              aria-label={
                showPassword ? tCommon("hidePassword") : tCommon("showPassword")
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
            <Checkbox id="rememberMeLoginPage" {...register("rememberMe")} />{" "}
            {/* Unique ID */}
            <Label
              htmlFor="rememberMeLoginPage"
              className="font-normal text-muted-foreground"
            >
              {tAuth("rememberMe")}
            </Label>
          </div>
          <Link
            href={PATHS.FORGOT_PASSWORD}
            className="text-sm text-primary hover:underline"
          >
            {tAuth("forgotPassword")}
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
              {tAuth("loggingInLoading")}
            </>
          ) : (
            tAuth("login")
          )}
        </Button>
      </form>
    </AuthFormCard>
  );
}
