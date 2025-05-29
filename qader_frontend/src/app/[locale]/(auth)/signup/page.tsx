"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link"; // Corrected import
import { useRouter } from "next/navigation"; // Corrected import
import { toast } from "sonner";
import { User, Mail, Lock, Eye, EyeOff, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  SignupSchema,
  type SignupFormValues,
  type ApiSignupData,
} from "@/types/forms/auth.schema"; // Adjust path
import { signupUser } from "@/services/auth.service"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import { QUERY_KEYS } from "@/constants/queryKeys"; // Adjust path
import { useAuthStore } from "@/store/auth.store"; // Adjust path
import { AuthFormCard } from "@/components/auth/AuthFormCard"; // Adjust path

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
  const { isAuthenticated, user: authUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const CurrentSignupSchema = useMemo(() => SignupSchema(tAuth), [tAuth]);

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
    reset,
  } = useForm<SignupFormValues>({
    resolver: zodResolver(CurrentSignupSchema),
    defaultValues: signupPageDefaultValues,
  });

  useEffect(() => {
    if (isAuthenticated && authUser) {
      toast.info(tAuth("alreadyLoggedIn"));
      if (authUser.profile_complete) {
        if (authUser.is_super || authUser.is_staff) {
          router.replace(PATHS.ADMIN_DASHBOARD);
        } else {
          router.replace(PATHS.STUDY_HOME);
        }
      } else {
        router.replace(PATHS.COMPLETE_PROFILE);
      }
    }
  }, [isAuthenticated, authUser, router, tAuth]);

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
      toast.success(data.detail || tAuth("activationLinkSent"), {
        duration: 8000,
      });
      reset();
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
        <Sparkles className="mb-4 h-12 w-12 animate-pulse text-primary" />
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
      showLogo={true}
    >
      {signupMutation.isSuccess ? (
        <Alert
          variant="default"
          className="mb-4 border-green-300 bg-green-50 text-green-700 dark:border-green-700 dark:bg-green-900/30 dark:text-green-300"
        >
          <Sparkles className="h-5 w-5 text-green-600 dark:text-green-400" />
          <AlertTitle className="font-semibold">
            {tAuth("successMessageTitle")}
          </AlertTitle>
          <AlertDescription>
            {signupMutation.data?.detail || tAuth("activationLinkSent")}
          </AlertDescription>
        </Alert>
      ) : (
        signupMutation.error &&
        !(signupMutation.error as any).data?.detail &&
        !(signupMutation.error as any).data?.email && (
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>{tAuth("errorAlertTitle")}</AlertTitle>
            <AlertDescription>
              {(signupMutation.error as any)?.message ||
                tAuth("signupFailedCheckData")}
            </AlertDescription>
          </Alert>
        )
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <Label htmlFor="signup-page-fullname">{tAuth("fullName")}</Label>
          <div className="relative mt-1">
            <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3" />
            <Input
              id="signup-page-fullname"
              type="text"
              placeholder={tAuth("fullNamePlaceholder")}
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
          <Label htmlFor="signup-page-email">{tAuth("email")}</Label>
          <div className="relative mt-1">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3" />
            <Input
              id="signup-page-email"
              type="email"
              placeholder={tAuth("emailPlaceholder")}
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
          <Label htmlFor="signup-page-password">{tAuth("password")}</Label>
          <div className="relative mt-1">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3" />
            <Input
              id="signup-page-password"
              type={showPassword ? "text" : "password"}
              placeholder={tAuth("passwordPlaceholder")}
              {...register("password")}
              className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
              aria-invalid={errors.password ? "true" : "false"}
              disabled={signupMutation.isSuccess}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rtl:left-3"
              aria-label={
                showPassword ? tCommon("hidePassword") : tCommon("showPassword")
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
          <Label htmlFor="signup-page-confirm-password">
            {tAuth("confirmPassword")}
          </Label>
          <div className="relative mt-1">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3" />
            <Input
              id="signup-page-confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              placeholder={tAuth("passwordPlaceholder")}
              {...register("password_confirm")}
              className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
              aria-invalid={errors.password_confirm ? "true" : "false"}
              disabled={signupMutation.isSuccess}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rtl:left-3"
              aria-label={
                showConfirmPassword
                  ? tCommon("hidePassword")
                  : tCommon("showPassword")
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

        <div className="flex items-start space-x-2 pt-1 rtl:space-x-reverse">
          <Controller
            name="termsAccepted"
            control={control}
            render={({ field }) => (
              <Checkbox
                id="termsAcceptedSignupPage"
                checked={field.value}
                onCheckedChange={field.onChange} // Unique ID
                aria-invalid={errors.termsAccepted ? "true" : "false"}
                disabled={signupMutation.isSuccess}
                className="mt-0.5"
              />
            )}
          />
          <Label
            htmlFor="termsAcceptedSignupPage"
            className="cursor-pointer text-sm font-normal leading-snug text-muted-foreground"
          >
            {tAuth("agreeTo")}{" "}
            <Link
              href={PATHS.TERMS_AND_CONDITIONS}
              className="font-medium text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {tAuth("termsAndConditions")}
            </Link>
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
          disabled={signupMutation.isPending || signupMutation.isSuccess}
        >
          {signupMutation.isPending ? (
            <>
              <Sparkles className="mr-2 h-4 w-4 animate-spin rtl:ml-2 rtl:mr-0" />
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
