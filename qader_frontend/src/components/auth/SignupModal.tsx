"use client";
import React, { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { User, Mail, Lock, XIcon, Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  SignupSchema,
  type SignupFormValues,
  type ApiSignupData,
} from "@/types/forms/auth.schema"; // Ensure this type matches form fields
import { signupUser } from "@/services/auth.service"; // Ensure service function expects correct data type
import { PATHS } from "@/constants/paths";
import { QUERY_KEYS } from "@/constants/queryKeys";

// For i18n
// import { useTranslations } from 'next-intl';

interface SignupModalProps {
  show: boolean;
  onClose: () => void;
  onSwitchToLogin?: () => void;
}

const SignupModal: React.FC<SignupModalProps> = ({
  show,
  onClose,
  onSwitchToLogin,
}) => {
  // const t = useTranslations('Auth');
  const router = useRouter();
  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
    reset,
    control,
  } = useForm<SignupFormValues>({
    // Use the Zod inferred type for the form
    resolver: zodResolver(SignupSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      password_confirm: "",
      termsAccepted: false,
    },
  });

  const signupMutation = useMutation({
    mutationKey: [QUERY_KEYS.SIGNUP],
    mutationFn: (data: SignupFormValues) => {
      // The API expects data without 'termsAccepted'
      // The SignupData type in auth.schema.ts already reflects this for the service
      const apiData: ApiSignupData = {
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        password_confirm: data.password_confirm,
      };
      return signupUser(apiData);
    },
    onSuccess: (data) => {
      toast.success(
        data.detail ||
          "تم إرسال رابط التفعيل إلى بريدك الإلكتروني. يرجى التحقق من بريدك الوارد والمجلدات الأخرى."
      ); // t('signupSuccessEmailSent')
      reset();
      onClose();
      // The backend API doc says: "The user must click the link in the email to activate their account and log in."
      // So, no automatic redirect to complete-profile yet, unless your flow has changed.
      // If you want to guide them, maybe a message on the page they are on, or redirect to a "check your email" page.
      // For now, we just close the modal.
      // router.push(PATHS.CHECK_EMAIL_NOTICE); // Example: If you have such a page
    },
    onError: (error: any) => {
      if (error.status === 400 && error.data) {
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof SignupFormValues;
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : error.data[key];
          if (
            field === "email" ||
            field === "full_name" ||
            field === "password"
          ) {
            // Add other fields if backend returns errors for them
            setFormError(field, { type: "server", message });
          }
        });
        if (error.data.detail) {
          toast.error(error.data.detail);
        } else {
          toast.error("فشل التسجيل. الرجاء التحقق من البيانات المدخلة."); // t('signupFailedCheckData')
        }
      } else {
        toast.error(error.message || "فشل الاتصال بالخادم. حاول لاحقاً."); // t('signupErrorServer')
      }
    },
  });

  const onSubmit = (data: SignupFormValues) => {
    signupMutation.mutate(data);
  };

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      // Dialog is closing
      reset(); // Reset React Hook Form state
      signupMutation.reset(); // Reset TanStack Query mutation state
      onClose(); // Call the passed onClose handler
    }
  };

  if (!show && !signupMutation.isPending) {
    return null;
  }

  return (
    <Dialog open={show} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-md md:max-w-3xl flex flex-col md:flex-row p-0 overflow-hidden">
        <div className="w-full md:w-1/2 flex items-center justify-center p-6 sm:p-8">
          <div className="w-full space-y-6">
            <DialogHeader className="text-center">
              <DialogTitle className="text-3xl font-bold">
                {/*t('welcome')*/}أهلاً بك!
              </DialogTitle>
              <p className="text-muted-foreground">
                {/*t('qaderWelcomesYou')*/}قادر ترحب بك.
              </p>
            </DialogHeader>

            {signupMutation.error && !signupMutation.error.data?.detail && (
              <Alert variant="destructive">
                <AlertTitle>خطأ في التسجيل</AlertTitle>
                <AlertDescription>
                  {(signupMutation.error as any)?.message ||
                    "فشل التسجيل. الرجاء التحقق من البيانات المدخلة."}
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="signup-fullname">
                  {/*t('fullName')*/}الاسم الكامل
                </Label>
                <div className="relative mt-1">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
                  <Input
                    id="signup-fullname"
                    type="text"
                    placeholder="الاسم الثلاثي" //{t('fullNamePlaceholder')}
                    {...register("full_name")}
                    className="pl-10 rtl:pr-10 rtl:pl-4"
                    aria-invalid={errors.full_name ? "true" : "false"}
                  />
                </div>
                {errors.full_name && (
                  <p className="mt-1 text-xs text-red-500">
                    {errors.full_name.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="signup-email">
                  {/*t('email')*/}البريد الإلكتروني
                </Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="you@example.com"
                    {...register("email")}
                    className="pl-10 rtl:pr-10 rtl:pl-4"
                    aria-invalid={errors.email ? "true" : "false"}
                  />
                </div>
                {errors.email && (
                  <p className="mt-1 text-xs text-red-500">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="signup-password">
                  {/*t('password')*/}كلمة المرور
                </Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
                  <Input
                    id="signup-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="********"
                    {...register("password")}
                    className="pl-10 pr-10 rtl:pr-10 rtl:pl-10"
                    aria-invalid={errors.password ? "true" : "false"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rtl:left-3 rtl:right-auto"
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
                {errors.password && (
                  <p className="mt-1 text-xs text-red-500">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="signup-confirm-password">
                  {/*t('confirmPassword')*/}تأكيد كلمة المرور
                </Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
                  <Input
                    id="signup-confirm-password"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="********"
                    {...register("password_confirm")}
                    className="pl-10 pr-10 rtl:pr-10 rtl:pl-10"
                    aria-invalid={errors.password_confirm ? "true" : "false"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rtl:left-3 rtl:right-auto"
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
                {errors.password_confirm && (
                  <p className="mt-1 text-xs text-red-500">
                    {errors.password_confirm.message}
                  </p>
                )}
              </div>

              <div className="flex items-start space-x-2 rtl:space-x-reverse">
                <Controller
                  name="termsAccepted" // Name from your Zod schema
                  control={control} // control object from useForm
                  render={({ field }) => (
                    <Checkbox
                      id="termsAccepted"
                      checked={field.value} // Use field.value for checked state
                      onCheckedChange={field.onChange} // Use field.onChange for updates
                      aria-invalid={errors.termsAccepted ? "true" : "false"}
                      className={errors.termsAccepted ? "border-red-500" : ""} // Optional: add error styling
                    />
                  )}
                />
                <Label
                  htmlFor="termsAccepted"
                  className="text-sm font-normal text-muted-foreground leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {/*t('agreeTo')*/}أوافق على{" "}
                  <Link
                    href={PATHS.TERMS_AND_CONDITIONS || "/conditions"}
                    className="font-medium text-primary hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {/*t('termsAndConditions')*/}الشروط والأحكام
                  </Link>
                </Label>
              </div>
              {errors.termsAccepted && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.termsAccepted.message}
                </p>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={signupMutation.isPending}
              >
                {signupMutation.isPending ? "جاري التسجيل..." : "إنشاء حساب"}
              </Button>
            </form>

            <p className="text-center text-sm text-muted-foreground">
              {/*t('alreadyHaveAccount')*/} لديك حساب بالفعل؟{" "}
              {onSwitchToLogin ? (
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onSwitchToLogin();
                  }}
                  className="font-medium text-primary hover:underline"
                >
                  {/*t('login')*/}تسجيل الدخول
                </button>
              ) : (
                <Link
                  href={PATHS.LOGIN}
                  className="font-medium text-primary hover:underline"
                  onClick={onClose}
                >
                  {/*t('login')*/}تسجيل الدخول
                </Link>
              )}
            </p>
          </div>
        </div>

        <div className="hidden md:block w-full md:w-1/2 h-64 md:h-auto">
          <img
            src="/images/login.jpg" // Re-use or use a different signup image
            alt="Signup Visual"
            className="h-full w-full object-cover"
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SignupModal;
