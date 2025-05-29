"use client";

import React, { useState, useMemo } from "react";
import { useRouter } from "next/navigation"; // Use next's Router
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Mail,
  KeyRound,
  ShieldCheck,
  Loader2,
  Eye,
  EyeOff,
  ArrowLeft,
} from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSeparator,
  InputOTPSlot,
} from "@/components/ui/input-otp";

import {
  createRequestOtpSchema,
  type RequestOtpFormValues,
  createVerifyOtpSchema,
  type VerifyOtpFormValues,
  createResetPasswordSchema,
  type ResetPasswordFormValues,
} from "@/types/forms/auth.schema"; // Adjust path
import {
  requestOtp,
  verifyOtp,
  resetPasswordWithOtp,
} from "@/services/auth.service"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import Link from "next/link"; // Use next's Link

type Step = "request" | "verify" | "reset";

const REQUEST_OTP_KEY = ["requestPasswordOtp"];
const VERIFY_OTP_KEY = ["verifyPasswordOtp"];
const RESET_PASSWORD_KEY = ["resetPasswordWithOtp"];

export default function ForgotPasswordPage() {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common"); // For generic texts like show/hide password
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>("request");
  const [identifier, setIdentifier] = useState<string>("");
  const [resetTokenState, setResetTokenState] = useState<string>(""); // Renamed to avoid conflict
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const CurrentRequestOtpSchema = useMemo(
    () => createRequestOtpSchema(tAuth),
    [tAuth]
  );
  const CurrentVerifyOtpSchema = useMemo(
    () => createVerifyOtpSchema(tAuth),
    [tAuth]
  );
  const CurrentResetPasswordSchema = useMemo(
    () => createResetPasswordSchema(tAuth),
    [tAuth]
  );

  const requestOtpForm = useForm<RequestOtpFormValues>({
    resolver: zodResolver(CurrentRequestOtpSchema),
    defaultValues: { identifier: "" },
  });
  const verifyOtpForm = useForm<VerifyOtpFormValues>({
    resolver: zodResolver(CurrentVerifyOtpSchema),
    defaultValues: { identifier: "", otp: "" },
  });
  const resetPasswordForm = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(CurrentResetPasswordSchema),
    defaultValues: {
      reset_token: "",
      new_password: "",
      new_password_confirm: "",
    },
  });

  const requestOtpMutation = useMutation({
    mutationKey: REQUEST_OTP_KEY,
    mutationFn: requestOtp,
    onSuccess: (data, variables) => {
      toast.success(data.detail || tAuth("activationLinkSent")); // Using generic success message from API or a fallback
      setIdentifier(variables.identifier);
      verifyOtpForm.setValue("identifier", variables.identifier);
      setCurrentStep("verify");
      requestOtpForm.reset();
    },
    onError: (error: any) => {
      if (error.data?.identifier)
        requestOtpForm.setError("identifier", {
          type: "server",
          message: error.data.identifier.join(", "),
        });
      else
        toast.error(error.message || tAuth("forgotPasswordOtpRequestFailed"));
    },
  });

  const verifyOtpMutation = useMutation({
    mutationKey: VERIFY_OTP_KEY,
    mutationFn: verifyOtp,
    onSuccess: (data) => {
      toast.success(data.detail || tAuth("otpVerified")); // Assuming 'otpVerified' key
      setResetTokenState(data.reset_token);
      resetPasswordForm.setValue("reset_token", data.reset_token);
      setCurrentStep("reset");
      verifyOtpForm.reset();
    },
    onError: (error: any) => {
      if (error.data?.otp)
        verifyOtpForm.setError("otp", {
          type: "server",
          message: error.data.otp.join(", "),
        });
      else if (error.data?.identifier)
        toast.error(
          `${tAuth("identifierInvalid")}: ${error.data.identifier.join(", ")}`
        );
      else
        toast.error(
          error.message || tAuth("forgotPasswordOtpVerificationFailed")
        );
    },
  });

  const resetPasswordMutation = useMutation({
    mutationKey: RESET_PASSWORD_KEY,
    mutationFn: resetPasswordWithOtp,
    onSuccess: (data) => {
      toast.success(data.detail || tAuth("passwordResetSuccess")); // Assuming 'passwordResetSuccess' key
      router.push(PATHS.LOGIN);
      resetPasswordForm.reset();
      setCurrentStep("request");
      setIdentifier("");
      setResetTokenState("");
    },
    onError: (error: any) => {
      if (error.data?.new_password)
        resetPasswordForm.setError("new_password", {
          type: "server",
          message: error.data.new_password.join(", "),
        });
      else if (error.data?.new_password_confirm)
        resetPasswordForm.setError("new_password_confirm", {
          type: "server",
          message: error.data.new_password_confirm.join(", "),
        });
      else if (error.data?.reset_token)
        toast.error(
          tAuth("forgotPasswordResetTokenError", {
            error: error.data.reset_token.join(", "),
          })
        );
      else toast.error(error.message || tAuth("forgotPasswordResetFailed"));
    },
  });

  const onRequestOtpSubmit = (data: RequestOtpFormValues) =>
    requestOtpMutation.mutate(data);
  const onVerifyOtpSubmit = (data: VerifyOtpFormValues) =>
    verifyOtpMutation.mutate(data);
  const onResetPasswordSubmit = (data: ResetPasswordFormValues) =>
    resetPasswordMutation.mutate(data);

  const goBack = () => {
    if (currentStep === "verify") {
      setCurrentStep("request");
      verifyOtpForm.reset();
    } else if (currentStep === "reset") {
      setCurrentStep("verify");
      resetPasswordForm.reset({
        reset_token: resetTokenState,
        new_password: "",
        new_password_confirm: "",
      });
    }
  };

  // Add a key to your common.json for dir: "dir": "rtl" for ar, "dir": "ltr" for en
  const dir = tCommon("dir") as "ltr" | "rtl";

  return (
    <div
      className="flex min-h-screen items-center justify-center p-4 bg-muted/30"
      dir={dir}
    >
      <Card className="w-full max-w-md">
        {currentStep !== "request" && (
          <Button
            variant="ghost"
            size="sm"
            onClick={goBack}
            className="absolute top-4 left-4 rtl:right-4 rtl:left-auto m-2"
          >
            <ArrowLeft className="w-4 h-4 mr-1 rtl:ml-1 rtl:mr-0" />{" "}
            {tAuth("goBack")}
          </Button>
        )}
        {currentStep === "request" && (
          <>
            <CardHeader>
              <CardTitle className="text-2xl">
                {tAuth("forgotPasswordTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordRequestSubtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={requestOtpForm.handleSubmit(onRequestOtpSubmit)}
                className="space-y-4"
              >
                <div>
                  <Label htmlFor="fp-identifier">
                    {tAuth("forgotPasswordIdentifierLabel")}
                  </Label>{" "}
                  {/* Unique ID */}
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="fp-identifier"
                      placeholder={tAuth("forgotPasswordIdentifierPlaceholder")}
                      {...requestOtpForm.register("identifier")}
                      className="pl-10 rtl:pr-10"
                    />
                  </div>
                  {requestOtpForm.formState.errors.identifier && (
                    <p className="mt-1 text-xs text-red-500">
                      {requestOtpForm.formState.errors.identifier.message}
                    </p>
                  )}
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  disabled={requestOtpMutation.isPending}
                >
                  {requestOtpMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 rtl:ml-2 h-4 w-4 animate-spin" />{" "}
                      {tAuth("forgotPasswordSendingOtp")}
                    </>
                  ) : (
                    tAuth("forgotPasswordSendOtpButton")
                  )}
                </Button>
              </form>
            </CardContent>
          </>
        )}
        {currentStep === "verify" && (
          <>
            <CardHeader>
              <CardTitle className="text-2xl">
                {tAuth("forgotPasswordVerifyTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordVerifySubtitle", { identifier })}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={verifyOtpForm.handleSubmit(onVerifyOtpSubmit)}
                className="space-y-6 flex flex-col items-center"
              >
                <Controller
                  name="otp"
                  control={verifyOtpForm.control}
                  render={({ field, fieldState }) => (
                    // OTP input is usually LTR by design for digit entry
                    <div
                      dir="ltr"
                      className="w-full flex flex-col items-center"
                    >
                      <Label htmlFor="fp-otp" className="sr-only">
                        {tAuth("forgotPasswordOtpLabel")}
                      </Label>{" "}
                      {/* Unique ID */}
                      <InputOTP id="fp-otp" maxLength={6} {...field}>
                        <InputOTPGroup>
                          <InputOTPSlot index={0} />
                          <InputOTPSlot index={1} />
                          <InputOTPSlot index={2} />
                        </InputOTPGroup>
                        <InputOTPSeparator />
                        <InputOTPGroup>
                          <InputOTPSlot index={3} />
                          <InputOTPSlot index={4} />
                          <InputOTPSlot index={5} />
                        </InputOTPGroup>
                      </InputOTP>
                      {fieldState.error && (
                        <p className="mt-2 text-xs text-red-500 text-center">
                          {fieldState.error.message}
                        </p>
                      )}
                    </div>
                  )}
                />
                <Button
                  type="submit"
                  className="w-full"
                  disabled={verifyOtpMutation.isPending}
                >
                  {verifyOtpMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 rtl:ml-2 h-4 w-4 animate-spin" />{" "}
                      {tAuth("forgotPasswordVerifyingOtp")}
                    </>
                  ) : (
                    tAuth("forgotPasswordVerifyOtpButton")
                  )}
                </Button>
              </form>
            </CardContent>
          </>
        )}
        {currentStep === "reset" && (
          <>
            <CardHeader>
              <CardTitle className="text-2xl">
                {tAuth("forgotPasswordResetTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordResetSubtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={resetPasswordForm.handleSubmit(onResetPasswordSubmit)}
                className="space-y-4"
              >
                <div>
                  <Label htmlFor="fp-new_password">
                    {tAuth("forgotPasswordNewPasswordLabel")}
                  </Label>{" "}
                  {/* Unique ID */}
                  <div className="relative mt-1">
                    <KeyRound className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="fp-new_password"
                      type={showPassword ? "text" : "password"}
                      placeholder={tAuth("passwordPlaceholder")}
                      {...resetPasswordForm.register("new_password")}
                      className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 rtl:left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      aria-label={
                        showPassword
                          ? tCommon("hidePassword")
                          : tCommon("showPassword")
                      }
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                  {resetPasswordForm.formState.errors.new_password && (
                    <p className="mt-1 text-xs text-red-500">
                      {resetPasswordForm.formState.errors.new_password.message}
                    </p>
                  )}
                </div>
                <div>
                  <Label htmlFor="fp-new_password_confirm">
                    {tAuth("forgotPasswordConfirmNewPasswordLabel")}
                  </Label>{" "}
                  {/* Unique ID */}
                  <div className="relative mt-1">
                    <ShieldCheck className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="fp-new_password_confirm"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder={tAuth("passwordPlaceholder")}
                      {...resetPasswordForm.register("new_password_confirm")}
                      className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      className="absolute right-3 rtl:left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      aria-label={
                        showConfirmPassword
                          ? tCommon("hidePassword")
                          : tCommon("showPassword")
                      }
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                  {resetPasswordForm.formState.errors.new_password_confirm && (
                    <p className="mt-1 text-xs text-red-500">
                      {
                        resetPasswordForm.formState.errors.new_password_confirm
                          .message
                      }
                    </p>
                  )}
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  disabled={resetPasswordMutation.isPending}
                >
                  {resetPasswordMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 rtl:ml-2 h-4 w-4 animate-spin" />{" "}
                      {tAuth("forgotPasswordResetting")}
                    </>
                  ) : (
                    tAuth("forgotPasswordResetPasswordButton")
                  )}
                </Button>
              </form>
            </CardContent>
          </>
        )}
        <CardFooter className="text-sm text-center block pt-6">
          <Link href={PATHS.LOGIN} className="text-primary hover:underline">
            {tAuth("forgotPasswordBackToLogin")}
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
