"use client";

import React, { useState } from "react";
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
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSeparator,
  InputOTPSlot,
} from "@/components/ui/input-otp"; // Shadcn UI component for OTP

import {
  RequestOtpSchema,
  type RequestOtpFormValues,
  VerifyOtpSchema,
  type VerifyOtpFormValues,
  ResetPasswordSchema,
  type ResetPasswordFormValues,
} from "@/types/forms/auth.schema";
import {
  requestOtp,
  verifyOtp,
  resetPasswordWithOtp,
} from "@/services/auth.service";
import { PATHS } from "@/constants/paths";
import Link from "next/link";
// import { useTranslations } from 'next-intl';

type Step = "request" | "verify" | "reset";

const REQUEST_OTP_KEY = ["requestPasswordOtp"];
const VERIFY_OTP_KEY = ["verifyPasswordOtp"];
const RESET_PASSWORD_KEY = ["resetPasswordWithOtp"];

export default function ForgotPasswordPage() {
  // const t = useTranslations('Auth.ForgotPassword');
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>("request");
  const [identifier, setIdentifier] = useState<string>(""); // To pass to verify and reset steps
  const [resetToken, setResetToken] = useState<string>(""); // From verify step
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Form for Requesting OTP
  const requestOtpForm = useForm<RequestOtpFormValues>({
    resolver: zodResolver(RequestOtpSchema),
    defaultValues: { identifier: "" },
  });

  // Form for Verifying OTP
  const verifyOtpForm = useForm<VerifyOtpFormValues>({
    resolver: zodResolver(VerifyOtpSchema),
    defaultValues: { identifier: "", otp: "" },
  });

  // Form for Resetting Password
  const resetPasswordForm = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(ResetPasswordSchema),
    defaultValues: {
      reset_token: "",
      new_password: "",
      new_password_confirm: "",
    },
  });

  // Mutations
  const requestOtpMutation = useMutation({
    mutationKey: REQUEST_OTP_KEY,
    mutationFn: requestOtp,
    onSuccess: (data, variables) => {
      toast.success(data.detail); // API gives generic success message
      setIdentifier(variables.identifier);
      verifyOtpForm.setValue("identifier", variables.identifier); // Pre-fill for next step
      setCurrentStep("verify");
      requestOtpForm.reset(); // Reset this form
    },
    onError: (error: any) => {
      if (error.data?.identifier) {
        requestOtpForm.setError("identifier", {
          type: "server",
          message: error.data.identifier.join(", "),
        });
      } else {
        toast.error(error.message || "فشل طلب رمز OTP. حاول لاحقًا.");
      }
    },
  });

  const verifyOtpMutation = useMutation({
    mutationKey: VERIFY_OTP_KEY,
    mutationFn: verifyOtp,
    onSuccess: (data) => {
      toast.success(data.detail);
      setResetToken(data.reset_token);
      resetPasswordForm.setValue("reset_token", data.reset_token); // Pre-fill for next step
      setCurrentStep("reset");
      verifyOtpForm.reset(); // Reset this form
    },
    onError: (error: any) => {
      if (error.data?.otp) {
        verifyOtpForm.setError("otp", {
          type: "server",
          message: error.data.otp.join(", "),
        });
      } else if (error.data?.identifier) {
        // This might indicate an issue if identifier changed between steps, though unlikely here
        toast.error(`خطأ في المعرف: ${error.data.identifier.join(", ")}`);
      } else {
        toast.error(error.message || "فشل التحقق من رمز OTP. حاول لاحقًا.");
      }
    },
  });

  const resetPasswordMutation = useMutation({
    mutationKey: RESET_PASSWORD_KEY,
    mutationFn: resetPasswordWithOtp,
    onSuccess: (data) => {
      toast.success(data.detail);
      router.push(PATHS.HOME || "/"); // Redirect to login page
      resetPasswordForm.reset();
      setCurrentStep("request"); // Reset flow
      setIdentifier("");
      setResetToken("");
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
          `خطأ في رمز إعادة التعيين: ${error.data.reset_token.join(
            ", "
          )}. الرجاء البدء من جديد.`
        );
        // Optionally force back to step 1
        // setCurrentStep("request");
      } else {
        toast.error(
          error.message || "فشل إعادة تعيين كلمة المرور. حاول لاحقًا."
        );
      }
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
      // Do not reset resetToken here as it's needed if user just wants to re-enter passwords
      resetPasswordForm.reset({
        reset_token: resetToken,
        new_password: "",
        new_password_confirm: "",
      });
    }
  };

  return (
    <div className="flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        {currentStep !== "request" && (
          <Button
            variant="ghost"
            size="sm"
            onClick={goBack}
            className="absolute top-4 left-4 rtl:right-4 rtl:left-auto"
          >
            <ArrowLeft className="w-4 h-4 mr-1 rtl:ml-1 rtl:mr-0" />
            رجوع
          </Button>
        )}
        {currentStep === "request" && (
          <>
            <CardHeader>
              <CardTitle className="text-2xl">نسيت كلمة المرور؟</CardTitle>{" "}
              {/*t('title')*/}
              <CardDescription>
                {/*t('requestSubtitle')*/}أدخل بريدك الإلكتروني أو اسم المستخدم
                لإرسال رمز إعادة التعيين.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={requestOtpForm.handleSubmit(onRequestOtpSubmit)}
                className="space-y-4"
              >
                <div>
                  <Label htmlFor="identifier">
                    البريد الإلكتروني / اسم المستخدم
                  </Label>
                  {/*t('identifierLabel')*/}
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="identifier"
                      placeholder="you@example.com أو username" //{t('identifierPlaceholder')}
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
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />{" "}
                      {/*t('sending')*/}جارٍ الإرسال...
                    </>
                  ) : (
                    //t('sendOtpButton')
                    "إرسال الرمز"
                  )}
                </Button>
              </form>
            </CardContent>
          </>
        )}

        {currentStep === "verify" && (
          <>
            <CardHeader>
              <CardTitle className="text-2xl">التحقق من الرمز</CardTitle>{" "}
              {/*t('verifyTitle')*/}
              <CardDescription>
                {/*t('verifySubtitle', { identifier })*/}تم إرسال رمز OTP إلى{" "}
                {identifier}. الرجاء إدخاله أدناه.
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
                    <div dir="ltr">
                      <Label htmlFor="otp" className="sr-only">
                        رمز OTP
                      </Label>
                      <InputOTP maxLength={6} {...field}>
                        <InputOTPGroup dir="ltr">
                          {" "}
                          {/* OTP usually LTR */}
                          <InputOTPSlot index={0} />
                          <InputOTPSlot index={1} />
                          <InputOTPSlot index={2} />
                        </InputOTPGroup>
                        <InputOTPSeparator />
                        <InputOTPGroup dir="ltr">
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
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />{" "}
                      {/*t('verifying')*/}جارٍ التحقق...
                    </>
                  ) : (
                    //t('verifyOtpButton')
                    "التحقق من الرمز"
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
                إعادة تعيين كلمة المرور
              </CardTitle>{" "}
              {/*t('resetTitle')*/}
              <CardDescription>
                {/*t('resetSubtitle')*/}أدخل كلمة المرور الجديدة.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={resetPasswordForm.handleSubmit(onResetPasswordSubmit)}
                className="space-y-4"
              >
                <div>
                  <Label htmlFor="new_password">كلمة المرور الجديدة</Label>
                  {/*t('newPasswordLabel')*/}
                  <div className="relative mt-1">
                    <KeyRound className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="new_password"
                      type={showPassword ? "text" : "password"}
                      placeholder="********"
                      {...resetPasswordForm.register("new_password")}
                      className="pl-10 rtl:pr-10 pr-10 rtl:pl-10" // Space for both icons
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
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
                  <Label htmlFor="new_password_confirm">
                    تأكيد كلمة المرور الجديدة
                  </Label>
                  {/*t('confirmNewPasswordLabel')*/}
                  <div className="relative mt-1">
                    <ShieldCheck className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="new_password_confirm"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="********"
                      {...resetPasswordForm.register("new_password_confirm")}
                      className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      aria-label={
                        showConfirmPassword ? "Hide password" : "Show password"
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
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />{" "}
                      {/*t('resetting')*/}جارٍ التعيين...
                    </>
                  ) : (
                    //t('resetPasswordButton')
                    "إعادة تعيين كلمة المرور"
                  )}
                </Button>
              </form>
            </CardContent>
          </>
        )}
        <CardFooter className="text-sm text-center block pt-6">
          <Link
            href={PATHS.HOME || "/"}
            className="text-primary hover:underline"
          >
            {/* t('backToLogin') */}العودة إلى تسجيل الدخول
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
