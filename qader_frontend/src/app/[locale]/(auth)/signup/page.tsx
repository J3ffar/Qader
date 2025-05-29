// qader_frontend/src/app/[locale]/(auth)/signup/page.tsx
"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation"; // Added useSearchParams
import { toast } from "sonner";
import {
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Sparkles,
  Loader2,
  CheckCircle,
} from "lucide-react"; // Added Loader2, CheckCircle
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  createSignupSchema, // Renamed from SignupSchema in previous step
  type SignupFormValues,
  type ApiSignupData,
} from "@/types/forms/auth.schema";
import { signupUser } from "@/services/auth.service";
import { PATHS } from "@/constants/paths";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { useAuthCore, useAuthStore } from "@/store/auth.store"; // Added useAuthCore
import { AuthFormCard } from "@/components/auth/AuthFormCard";
import type { ApiError, SignupResponse } from "@/types/api/auth.types";

const signupPageDefaultValues: SignupFormValues = {
  full_name: "",
  email: "",
  password: "",
  password_confirm: "",
  termsAccepted: false,
};

export default function SignupPage() {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common");
  const router = useRouter();
  const searchParams = useSearchParams(); // For redirect_to if applicable

  const { isAuthenticated, user: authUser } = useAuthCore(); // Use custom hook
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Use the createSignupSchema function
  const CurrentSignupSchema = useMemo(() => createSignupSchema(tAuth), [tAuth]);

  const {
    control,
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError: setFormError,
    reset,
  } = useForm<SignupFormValues>({
    resolver: zodResolver(CurrentSignupSchema),
    defaultValues: signupPageDefaultValues,
  });

  useEffect(() => {
    if (isAuthenticated && authUser) {
      toast.info(tAuth("alreadyLoggedIn"), { id: "already-logged-in-toast" });
      // Redirect logic similar to login, though less common to have redirect_to for signup
      const redirectTo =
        searchParams.get("redirect_to") ||
        (authUser.profile_complete
          ? authUser.is_super || authUser.is_staff
            ? PATHS.ADMIN_DASHBOARD
            : PATHS.STUDY_HOME
          : PATHS.COMPLETE_PROFILE);
      router.replace(redirectTo);
    }
  }, [isAuthenticated, authUser, router, tAuth, searchParams]);

  const signupMutation = useMutation<
    SignupResponse,
    ApiError,
    SignupFormValues
  >({
    mutationKey: [QUERY_KEYS.SIGNUP],
    mutationFn: (data: SignupFormValues) => {
      const apiPayload: ApiSignupData = {
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        password_confirm: data.password_confirm,
        // termsAccepted is not part of ApiSignupData
      };
      return signupUser(apiPayload);
    },
    onSuccess: (data) => {
      toast.success(data.detail || tAuth("activationLinkSentDefault"), {
        // Use a more specific default
        duration: 10000, // Longer duration for important messages
        icon: <CheckCircle className="text-green-500" />,
      });
      reset(); // Clear the form on success
      // Optionally, you could redirect to login or a page saying "check your email"
      // router.push(PATHS.LOGIN);
    },
    onError: (error: ApiError) => {
      if (error.status === 400 && error.data) {
        let specificErrorSet = false;
        Object.keys(error.data).forEach((key) => {
          // Ensure key is a valid form field before setting error
          if (key in signupPageDefaultValues) {
            const field = key as keyof SignupFormValues;
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
          toast.error(tAuth("signupFailedCheckData"));
        }
      } else {
        toast.error(error.message || tAuth("signupErrorServer"));
      }
    },
  });

  const onSubmit = (data: SignupFormValues) => signupMutation.mutate(data);

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
      title={tAuth("createAccountTitle")}
      description={tAuth("signupPrompt")}
      footerPromptText={tAuth("alreadyHaveAccount")}
      footerLinkText={tAuth("login")}
      footerLinkHref={PATHS.LOGIN}
      showLogo={true} // Assuming this is a prop of AuthFormCard
    >
      {/* Success message display within the card */}
      {signupMutation.isSuccess && (
        <Alert
          variant="default" // Or 'success' if you have a custom variant
          className="mb-6 border-green-500 bg-green-50 text-green-700 dark:border-green-600 dark:bg-green-900/20 dark:text-green-300"
        >
          <CheckCircle className="h-5 w-5 text-current" />
          <AlertTitle className="font-semibold">
            {tAuth("signupSuccessTitle")}
          </AlertTitle>
          <AlertDescription>
            {signupMutation.data?.detail || tAuth("activationLinkSentDefault")}{" "}
            {/* Space */}
            {tAuth("checkEmailPrompt")}
          </AlertDescription>
        </Alert>
      )}

      {/* General non-field error display (only if not success) */}
      {signupMutation.isError &&
        signupMutation.error.data?.detail &&
        !signupMutation.isSuccess && (
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>{tAuth("errorAlertTitle")}</AlertTitle>
            <AlertDescription>
              {String(signupMutation.error.data.detail)}
            </AlertDescription>
          </Alert>
        )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Full Name */}
        <div>
          <Label htmlFor="signup-page-fullname">{tAuth("fullName")}</Label>
          <div className="relative mt-1">
            <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
            <Input
              id="signup-page-fullname"
              type="text"
              placeholder={tAuth("fullNamePlaceholder")}
              {...register("full_name")}
              className="pl-10 rtl:pr-10"
              aria-invalid={errors.full_name ? "true" : "false"}
              disabled={signupMutation.isSuccess || signupMutation.isPending}
            />
          </div>
          {errors.full_name && (
            <p className="mt-1 text-xs text-red-500">
              {errors.full_name.message}
            </p>
          )}
        </div>

        {/* Email */}
        <div>
          <Label htmlFor="signup-page-email">{tAuth("email")}</Label>
          <div className="relative mt-1">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
            <Input
              id="signup-page-email"
              type="email"
              autoComplete="email"
              placeholder={tAuth("emailPlaceholder")}
              {...register("email")}
              className="pl-10 rtl:pr-10"
              aria-invalid={errors.email ? "true" : "false"}
              disabled={signupMutation.isSuccess || signupMutation.isPending}
            />
          </div>
          {errors.email && (
            <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <Label htmlFor="signup-page-password">{tAuth("password")}</Label>
          <div className="relative mt-1">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
            <Input
              id="signup-page-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder={tAuth("passwordPlaceholder")}
              {...register("password")}
              className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
              aria-invalid={errors.password ? "true" : "false"}
              disabled={signupMutation.isSuccess || signupMutation.isPending}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none ltr:right-3 rtl:left-3"
              aria-label={
                showPassword ? tCommon("hidePassword") : tCommon("showPassword")
              }
              disabled={signupMutation.isSuccess || signupMutation.isPending}
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

        {/* Confirm Password */}
        <div>
          <Label htmlFor="signup-page-confirm-password">
            {tAuth("confirmPassword")}
          </Label>
          <div className="relative mt-1">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
            <Input
              id="signup-page-confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder={tAuth("passwordPlaceholder")}
              {...register("password_confirm")}
              className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
              aria-invalid={errors.password_confirm ? "true" : "false"}
              disabled={signupMutation.isSuccess || signupMutation.isPending}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none ltr:right-3 rtl:left-3"
              aria-label={
                showConfirmPassword
                  ? tCommon("hidePassword")
                  : tCommon("showPassword")
              }
              disabled={signupMutation.isSuccess || signupMutation.isPending}
            >
              {showConfirmPassword ? (
                <EyeOff className="h-5 w-5" />
              ) : (
                <Eye className="h-5 w-5" />
              )}
            </button>
          </div>
          {errors.password_confirm && (
            <p className="mt-1 text-xs text-red-500">
              {errors.password_confirm.message}
            </p>
          )}
        </div>

        {/* Terms Accepted */}
        <div className="flex items-start space-x-2 pt-1 rtl:space-x-reverse">
          <Controller
            name="termsAccepted"
            control={control}
            render={({ field }) => (
              <Checkbox
                id="termsAcceptedSignupPage"
                checked={field.value}
                onCheckedChange={field.onChange}
                aria-invalid={errors.termsAccepted ? "true" : "false"}
                disabled={signupMutation.isSuccess || signupMutation.isPending}
                className="mt-0.5 shrink-0" // Added shrink-0
              />
            )}
          />
          <Label
            htmlFor="termsAcceptedSignupPage"
            className="cursor-pointer text-sm font-normal leading-snug text-muted-foreground"
          >
            {tAuth.rich("agreeTo", {
              // Using rich for inline link
              termsLink: (chunks) => (
                <Link
                  href={PATHS.TERMS_AND_CONDITIONS}
                  className="font-medium text-primary hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {chunks}
                </Link>
              ),
              // Assuming your translation key is like: "I agree to the <termsLink>Terms and Conditions</termsLink>"
            })}
          </Label>
        </div>
        {errors.termsAccepted && (
          <p className="-mt-4 text-xs text-red-500">
            {errors.termsAccepted.message}
          </p>
        )}

        <Button
          type="submit"
          className="w-full"
          disabled={
            signupMutation.isPending || signupMutation.isSuccess || isSubmitting
          }
        >
          {signupMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin rtl:ml-2 rtl:mr-0" />
              {tAuth("creatingAccountLoading")}
            </>
          ) : (
            tAuth("createAccount")
          )}
        </Button>
      </form>
    </AuthFormCard>
  );
}
