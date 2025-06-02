"use client";

import React, { useState, useMemo, useEffect } from "react"; // Added useEffect
import { useRouter } from "next/navigation";
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
} from "@/types/forms/auth.schema";
import {
  requestOtp,
  verifyOtp,
  resetPasswordWithOtp,
} from "@/services/auth.service";
import { PATHS } from "@/constants/paths";
import Link from "next/link";

type Step = "request" | "verify" | "reset";

const REQUEST_OTP_KEY = ["requestPasswordOtp"];
const VERIFY_OTP_KEY = ["verifyPasswordOtp"];
const RESET_PASSWORD_KEY = ["resetPasswordWithOtp"];

export default function ForgotPasswordPage() {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common");
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>("request");
  const [identifier, setIdentifier] = useState<string>(""); // Used for display text
  const [resetTokenState, setResetTokenState] = useState<string>("");
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
    defaultValues: { identifier: "", otp: "" }, // identifier will be populated
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
      toast.success(data.detail || tAuth("activationLinkSent"));
      setIdentifier(variables.identifier); // Set for display in verify step
      verifyOtpForm.setValue("identifier", variables.identifier); // Crucially set identifier for verify form
      verifyOtpForm.setValue("otp", ""); // Clear any old OTP
      setCurrentStep("verify");
      requestOtpForm.reset();
    },
    onError: (error: any) => {
      if (error.data?.identifier) {
        requestOtpForm.setError("identifier", {
          type: "server",
          message: error.data.identifier.join(", "),
        });
      } else {
        toast.error(error.message || tAuth("forgotPasswordOtpRequestFailed"));
      }
    },
  });

  const verifyOtpMutation = useMutation({
    mutationKey: VERIFY_OTP_KEY,
    mutationFn: verifyOtp,
    onSuccess: (data) => {
      toast.success(data.detail || tAuth("otpVerified"));
      setResetTokenState(data.reset_token);
      resetPasswordForm.setValue("reset_token", data.reset_token);
      setCurrentStep("reset");
      verifyOtpForm.reset(); // Clear OTP form including identifier and otp
    },
    onError: (error: any) => {
      if (error.data?.otp) {
        verifyOtpForm.setError("otp", {
          type: "server",
          message: error.data.otp.join(", "),
        });
      } else if (error.data?.identifier) {
        // This error might occur if the identifier becomes invalid between steps, though unlikely
        toast.error(
          `${tAuth("identifierInvalid")}: ${error.data.identifier.join(", ")}`
        );
      } else {
        toast.error(
          error.message || tAuth("forgotPasswordOtpVerificationFailed")
        );
      }
    },
  });

  const resetPasswordMutation = useMutation({
    mutationKey: RESET_PASSWORD_KEY,
    mutationFn: resetPasswordWithOtp,
    onSuccess: (data) => {
      toast.success(data.detail || tAuth("passwordResetSuccess"));
      router.push(PATHS.LOGIN);
      // Reset all forms and states
      requestOtpForm.reset();
      verifyOtpForm.reset();
      resetPasswordForm.reset();
      setCurrentStep("request");
      setIdentifier("");
      setResetTokenState("");
    },
    onError: (error: any) => {
      if (error.data?.new_password) {
        resetPasswordForm.setError("new_password", {
          type: "server",
          message: error.data.new_password.join(", "),
        });
      } else if (error.data?.new_password_confirm) {
        resetPasswordForm.setError("new_password_confirm", {
          type: "server",
          message: error.data.new_password_confirm.join(", "),
        });
      } else if (error.data?.reset_token) {
        toast.error(
          tAuth("forgotPasswordResetTokenError", {
            error: error.data.reset_token.join(", "),
          })
        );
      } else {
        toast.error(error.message || tAuth("forgotPasswordResetFailed"));
      }
    },
  });

  const onRequestOtpSubmit = (data: RequestOtpFormValues) =>
    requestOtpMutation.mutate(data);

  // Memoize onVerifyOtpSubmit if it were to be used in a useEffect dependency array,
  // but for handleSubmit it's not strictly necessary.
  // However, to prevent re-creation on every render for the onComplete callback,
  // it's good practice.
  const onVerifyOtpSubmit = React.useCallback(
    (data: VerifyOtpFormValues) => {
      // console.log("Verifying OTP with data:", data); // For debugging if needed
      verifyOtpMutation.mutate(data);
    },
    [verifyOtpMutation] // Add other stable dependencies if any are used inside
  );

  const onResetPasswordSubmit = (data: ResetPasswordFormValues) =>
    resetPasswordMutation.mutate(data);

  const goBack = () => {
    if (currentStep === "verify") {
      setCurrentStep("request");
      verifyOtpForm.reset(); // Clear OTP form
      // requestOtpForm retains its last typed values which is fine
    } else if (currentStep === "reset") {
      setCurrentStep("verify");
      // Don't reset verifyOtpForm.identifier, it's still needed if they want to retry OTP
      // verifyOtpForm.setValue("otp", ""); // Clear only OTP if needed, or let user edit
      // resetPasswordForm is reset to clear password fields but keep the token
      resetPasswordForm.reset({
        reset_token: resetTokenState, // Preserve the token
        new_password: "",
        new_password_confirm: "",
      });
    }
  };

  const dir = tCommon("dir") as "ltr" | "rtl";

  return (
    <div className="flex items-center justify-center p-4" dir={dir}>
      <Card className="w-full max-w-md bg-background shadow">
        {currentStep !== "request" && (
          <Button
            variant="ghost"
            size="icon" // Making it an icon button for cleaner look
            onClick={goBack}
            className="absolute left-4 top-4 m-2 h-8 w-8 rtl:left-auto rtl:right-4" // Adjusted size
            aria-label={tAuth("goBack")}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
        )}
        {currentStep === "request" && (
          <>
            <CardHeader>
              <CardTitle className="text-2xl font-semibold">
                {tAuth("forgotPasswordTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordRequestSubtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={requestOtpForm.handleSubmit(onRequestOtpSubmit)}
                className="space-y-6" // Increased spacing
              >
                <div>
                  <Label htmlFor="fp-identifier" className="font-medium">
                    {tAuth("forgotPasswordIdentifierLabel")}
                  </Label>
                  <div className="relative mt-1.5">
                    {" "}
                    {/* Adjusted margin */}
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                    <Input
                      id="fp-identifier"
                      placeholder={tAuth("forgotPasswordIdentifierPlaceholder")}
                      {...requestOtpForm.register("identifier")}
                      className="pl-10 rtl:pr-10"
                      aria-describedby="identifier-error"
                    />
                  </div>
                  {requestOtpForm.formState.errors.identifier && (
                    <p
                      id="identifier-error"
                      className="mt-1.5 text-xs text-destructive"
                    >
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
                      <Loader2 className="mr-2 h-4 w-4 animate-spin rtl:ml-2 rtl:mr-0" />
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
              <CardTitle className="text-2xl font-semibold">
                {tAuth("forgotPasswordVerifyTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordVerifySubtitle", {
                  identifier: identifier,
                })}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                // We don't need onSubmit here if onComplete handles submission
                // onSubmit={verifyOtpForm.handleSubmit(onVerifyOtpSubmit)}
                className="flex flex-col items-center space-y-6"
              >
                <Controller
                  name="otp"
                  control={verifyOtpForm.control}
                  render={({ field, fieldState }) => (
                    <div
                      dir="ltr" // Crucial: OTP input itself should be LTR
                      className="flex w-full flex-col items-center"
                    >
                      <Label htmlFor="fp-otp" className="sr-only">
                        {tAuth("forgotPasswordOtpLabel")}
                      </Label>
                      <InputOTP
                        id="fp-otp"
                        maxLength={6}
                        value={field.value}
                        onChange={field.onChange}
                        onBlur={field.onBlur}
                        // ref={field.ref} // InputOTP should handle its own ref internally
                        onComplete={() => {
                          // Auto-submit when OTP is fully entered
                          // Ensure mutation is not already pending to prevent double submissions
                          if (!verifyOtpMutation.isPending) {
                            verifyOtpForm.handleSubmit(onVerifyOtpSubmit)();
                          }
                        }}
                        aria-describedby="otp-error"
                      >
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
                        <p
                          id="otp-error"
                          className="mt-2 text-center text-xs text-destructive"
                        >
                          {fieldState.error.message}
                        </p>
                      )}
                    </div>
                  )}
                />
                {/* Keep the manual submit button as a fallback or if auto-submit is not desired */}
                <Button
                  type="button" // Changed to button if auto-submit is primary
                  onClick={verifyOtpForm.handleSubmit(onVerifyOtpSubmit)}
                  className="w-full"
                  disabled={
                    verifyOtpMutation.isPending ||
                    verifyOtpForm.watch("otp")?.length !== 6
                  }
                >
                  {verifyOtpMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin rtl:ml-2 rtl:mr-0" />
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
              <CardTitle className="text-2xl font-semibold">
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
                  <Label htmlFor="fp-new_password" className="font-medium">
                    {tAuth("forgotPasswordNewPasswordLabel")}
                  </Label>
                  <div className="relative mt-1.5">
                    <KeyRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                    <Input
                      id="fp-new_password"
                      type={showPassword ? "text" : "password"}
                      placeholder={tAuth("passwordPlaceholder")}
                      {...resetPasswordForm.register("new_password")}
                      className="pl-10 pr-10 rtl:pl-10 rtl:pr-10" // Ensure correct padding for icon and toggle
                      aria-describedby="new-password-error"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rtl:left-3 rtl:right-auto"
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
                    <p
                      id="new-password-error"
                      className="mt-1.5 text-xs text-destructive"
                    >
                      {resetPasswordForm.formState.errors.new_password.message}
                    </p>
                  )}
                </div>
                <div>
                  <Label
                    htmlFor="fp-new_password_confirm"
                    className="font-medium"
                  >
                    {tAuth("forgotPasswordConfirmNewPasswordLabel")}
                  </Label>
                  <div className="relative mt-1.5">
                    <ShieldCheck className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                    <Input
                      id="fp-new_password_confirm"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder={tAuth("passwordPlaceholder")} // Assuming same placeholder
                      {...resetPasswordForm.register("new_password_confirm")}
                      className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
                      aria-describedby="confirm-password-error"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rtl:left-3 rtl:right-auto"
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
                    <p
                      id="confirm-password-error"
                      className="mt-1.5 text-xs text-destructive"
                    >
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
                      <Loader2 className="mr-2 h-4 w-4 animate-spin rtl:ml-2 rtl:mr-0" />
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
        <CardFooter className="block border-t px-6 text-center text-sm">
          {" "}
          {/* Added border and padding */}
          {currentStep === "request" ? (
            <Link href={PATHS.HOME} className="text-primary hover:underline">
              {tAuth("forgotPasswordBackToLogin")}{" "}
              {/* Changed text for login context */}
            </Link>
          ) : (
            <Link href={PATHS.HOME} className="text-primary hover:underline">
              {tAuth("forgotPasswordBackToLogin")}
            </Link>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
