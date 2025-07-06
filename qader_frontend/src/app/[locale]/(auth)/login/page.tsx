"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation"; // Added useSearchParams
import Link from "next/link";
import { toast } from "sonner";
import { Mail, Lock, Eye, EyeOff, Sparkles, Loader2 } from "lucide-react"; // Added Loader2
import { useTranslations } from "next-intl";
import Cookies from "js-cookie";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  createLoginSchema,
  type LoginCredentials,
} from "@/types/forms/auth.schema";
import { loginUser } from "@/services/auth.service";
import { useAuthCore, useAuthActions, useAuthStore } from "@/store/auth.store"; // Added useAuthCore
import { PATHS } from "@/constants/paths";
import { AuthFormCard } from "@/components/auth/AuthFormCard";
import type { ApiError, LoginResponse } from "@/types/api/auth.types";
import { queryKeys } from "@/constants/queryKeys";

export default function LoginPage() {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common");
  const router = useRouter();
  const searchParams = useSearchParams(); // For redirect_to

  const { isAuthenticated, user: authUser } = useAuthCore(); // Use custom hook
  const { login: storeLogin, setIsProfileComplete } = useAuthActions(); // Use custom hook
  const [showPassword, setShowPassword] = useState(false);

  const CurrentLoginSchema = useMemo(() => createLoginSchema(tAuth), [tAuth]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError: setFormError,
    reset,
  } = useForm<LoginCredentials>({
    resolver: zodResolver(CurrentLoginSchema),
    defaultValues: { username: "", password: "", rememberMe: false },
  });

  useEffect(() => {
    if (isAuthenticated && authUser) {
      // toast.info(tAuth("alreadyLoggedIn"), { id: "already-logged-in-toast" });
      const redirectTo =
        searchParams.get("redirect_to") ||
        (authUser.profile_complete
          ? authUser.is_super || authUser.is_staff
            ? PATHS.ADMIN.DASHBOARD
            : PATHS.STUDY.HOME
          : PATHS.COMPLETE_PROFILE);
      router.replace(redirectTo);
    }
  }, [isAuthenticated, authUser, router, tAuth, searchParams]);

  const loginMutation = useMutation<LoginResponse, ApiError, LoginCredentials>({
    mutationKey: queryKeys.auth.login(),
    mutationFn: loginUser,
    onSuccess: (data) => {
      storeLogin({ access: data.access }, data.user);
      setIsProfileComplete(data.user.profile_complete); // Set profile completeness
      toast.success(tAuth("loginSuccess"));
      reset(); // Clear form

      if (data.user.is_staff || data.user.is_super) {
        Cookies.set("qader-user-role", "admin", { path: "/" });
      } else {
        Cookies.set("qader-user-role", "student", { path: "/" });
      }

      const redirectTo = searchParams.get("redirect_to");
      if (redirectTo) {
        router.replace(redirectTo); // Handle redirect from middleware
      } else if (data.user?.is_super || data.user?.is_staff) {
        router.replace(PATHS.ADMIN.DASHBOARD);
      } else if (!data.user.profile_complete) {
        router.replace(PATHS.COMPLETE_PROFILE);
      } else {
        router.replace(PATHS.STUDY.HOME);
      }
    },
    onError: (error: ApiError) => {
      if (error.status === 400 && error.data) {
        let specificErrorSet = false;
        Object.keys(error.data).forEach((key) => {
          if (key === "username" || key === "password") {
            const field = key as keyof LoginCredentials;
            const message = Array.isArray(error.data![key])
              ? (error.data![key] as string[]).join(", ")
              : String(error.data![key]);
            setFormError(field, { type: "server", message });
            specificErrorSet = true;
          }
        });
        if (error.data.detail) {
          toast.error(String(error.data.detail));
        } else if (!specificErrorSet) {
          toast.error(tAuth("loginFailedInvalidCredentials")); // More specific
        }
      } else if (error.status === 401) {
        // Handle 401 specifically if not caught by 400
        toast.error(tAuth("loginFailedInvalidCredentials"));
      } else {
        toast.error(error.message || tAuth("loginErrorServer"));
      }
    },
  });

  const onSubmit = (data: LoginCredentials) => loginMutation.mutate(data);

  // Loading indicator if already authenticated and redirecting
  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6">
        <Loader2 className="mb-4 h-12 w-12 animate-spin text-primary" />
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
      footerLinkHref={PATHS.SIGNUP}
    >
      {/* General non-field error display */}
      {loginMutation.isError && loginMutation.error.data?.detail && (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>{tAuth("loginErrorAlertTitle")}</AlertTitle>
          <AlertDescription>
            {String(loginMutation.error.data.detail)}
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <Label htmlFor="login-page-username">
            {tAuth("emailOrUsername")}
          </Label>
          <div className="relative mt-1">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
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
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
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
              className="absolute top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none ltr:right-3 rtl:left-3"
              aria-label={
                showPassword ? tCommon("hidePassword") : tCommon("showPassword")
              }
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5" />
              ) : (
                <Eye className="h-5 w-5" />
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
            <Checkbox id="rememberMeLoginPage" {...register("rememberMe")} />
            <Label
              htmlFor="rememberMeLoginPage"
              className="font-normal text-muted-foreground hover:cursor-pointer"
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
          disabled={loginMutation.isPending || isSubmitting}
        >
          {loginMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin rtl:ml-2 rtl:mr-0" />
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
