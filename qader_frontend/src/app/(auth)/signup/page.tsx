"use client";

import React, { useEffect, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import Image from "next/image"; // For the side image
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  User as UserIconLucide,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  SignupSchema,
  type SignupFormValues,
  type ApiSignupData,
} from "@/types/forms/auth.schema";
import { signupUser } from "@/services/auth.service";
import { PATHS } from "@/constants/paths";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { useAuthStore } from "@/store/auth.store"; // For redirect if already logged in
// import { useTranslations } from 'next-intl';

export default function SignupPage() {
  // const t = useTranslations('Auth.Signup');
  // const tCommon = useTranslations('Common');
  const router = useRouter();
  const { isAuthenticated, user: authUser } = useAuthStore(); // Check if already logged in
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
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      password_confirm: "",
      termsAccepted: false,
    },
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && authUser) {
      toast.info("أنت مسجل الدخول بالفعل."); // tCommon('alreadyLoggedIn')
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
          "تم إرسال رابط التفعيل إلى بريدك الإلكتروني. يرجى التحقق من بريدك الوارد والمجلدات الأخرى."
      ); // t('signupSuccessEmailSent')
      reset();
      // Display a message on the page or redirect to a "check your email" page
      // For now, we can show a success message within the card or redirect
      // router.push(PATHS.LOGIN + "?message=confirmEmailSent"); // Example redirect
      toast.info(
        "تم إرسال رابط التفعيل بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل حسابك ثم تسجيل الدخول.",
        { duration: 10000 }
      );
      // router.push(PATHS.LOGIN || "/login"); // Optionally redirect to login after a delay or user action
    },
    onError: (error: any) => {
      if (error.status === 400 && error.data) {
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof SignupFormValues; // Use SignupFormValues
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : String(error.data[key]);
          // Check if field exists in SignupFormValues before setting error
          if (Object.keys(SignupSchema.shape).includes(field)) {
            setFormError(field, { type: "server", message });
          }
        });
        if (error.data.detail) {
          toast.error(String(error.data.detail));
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

  if (isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background p-6">
        <Sparkles className="w-12 h-12 text-primary animate-pulse mb-4" />
        <p className="text-muted-foreground">جاري التوجيه...</p>
      </div>
    );
  }

  return (
    <div className="w-full lg:grid lg:min-h-screen lg:grid-cols-2 xl:min-h-screen">
      <div className="flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <Card className="mx-auto w-full max-w-md shadow-xl border">
          <CardHeader className="space-y-1 text-center">
            <Link href={PATHS.HOME} className="inline-block mb-4">
              <Image
                src="/images/logo.svg"
                alt="Qader Logo"
                width={120}
                height={40}
              />
            </Link>
            <CardTitle className="text-3xl font-bold">
              إنشاء حساب جديد
            </CardTitle>{" "}
            {/* t('createAccountTitle') */}
            <CardDescription>
              {/* t('signupPrompt') */}املأ النموذج أدناه لإنشاء حسابك.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {signupMutation.error &&
              !(signupMutation.error as any).data?.detail &&
              !(signupMutation.error as any).data
                ?.email /* and other fields */ && (
                <Alert variant="destructive" className="mb-4">
                  <AlertTitle>خطأ في التسجيل</AlertTitle>
                  <AlertDescription>
                    {(signupMutation.error as any)?.message ||
                      "فشل التسجيل. الرجاء التحقق من البيانات المدخلة."}
                  </AlertDescription>
                </Alert>
              )}
            {signupMutation.isSuccess && (
              <Alert
                variant="default"
                className="mb-4 bg-green-50 border-green-300 text-green-700"
              >
                <Sparkles className="h-5 w-5 text-green-600" />
                <AlertTitle className="font-semibold">تم بنجاح!</AlertTitle>
                <AlertDescription>
                  {signupMutation.data?.detail ||
                    "تم إرسال رابط التفعيل. يرجى التحقق من بريدك الإلكتروني."}
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="signup-fullname">الاسم الكامل</Label>
                {/* t('fullName') */}
                <div className="relative mt-1">
                  <UserIconLucide className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="signup-fullname"
                    type="text"
                    placeholder="الاسم الثلاثي" //{t('fullNamePlaceholder')}
                    {...register("full_name")}
                    className="pl-10 rtl:pr-10"
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
                <Label htmlFor="signup-email">البريد الإلكتروني</Label>
                {/* t('email') */}
                <div className="relative mt-1">
                  <Mail className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="you@example.com"
                    {...register("email")}
                    className="pl-10 rtl:pr-10"
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
                <Label htmlFor="signup-password">كلمة المرور</Label>
                {/* t('password') */}
                <div className="relative mt-1">
                  <Lock className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="signup-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="********"
                    {...register("password")}
                    className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
                    aria-invalid={errors.password ? "true" : "false"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 rtl:left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
                  تأكيد كلمة المرور
                </Label>
                {/* t('confirmPassword') */}
                <div className="relative mt-1">
                  <Lock className="absolute left-3 rtl:right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="signup-confirm-password"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="********"
                    {...register("password_confirm")}
                    className="pl-10 rtl:pr-10 pr-10 rtl:pl-10"
                    aria-invalid={errors.password_confirm ? "true" : "false"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 rtl:left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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

              <div className="flex items-start space-x-2 rtl:space-x-reverse pt-2">
                <Controller
                  name="termsAccepted"
                  control={control}
                  render={({ field }) => (
                    <Checkbox
                      id="termsAccepted"
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      aria-invalid={errors.termsAccepted ? "true" : "false"}
                    />
                  )}
                />
                <Label
                  htmlFor="termsAccepted"
                  className="text-sm font-normal text-muted-foreground leading-snug"
                >
                  أوافق على {/* t('agreeTo') */}
                  <Link
                    href={PATHS.TERMS_AND_CONDITIONS || "/conditions"}
                    className="font-medium text-primary hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    الشروط والأحكام {/* t('termsAndConditions') */}
                  </Link>
                </Label>
              </div>
              {errors.termsAccepted && (
                <p className="text-xs text-red-500 -mt-2">
                  {" "}
                  {/* Adjusted margin for tighter spacing */}
                  {errors.termsAccepted.message}
                </p>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={signupMutation.isPending || signupMutation.isSuccess} // Disable after successful submission too
              >
                {signupMutation.isPending ? (
                  <>
                    <Sparkles className="mr-2 h-4 w-4 animate-spin" /> جارٍ
                    التسجيل...
                  </> /* t('signingUp') */
                ) : (
                  "إنشاء حساب" /* t('createAccount') */
                )}
              </Button>
            </form>
            <div className="mt-6 text-center text-sm">
              لديك حساب بالفعل؟ {/* t('alreadyHaveAccount') */}
              <Link
                href={PATHS.LOGIN || "/login"}
                className="font-medium text-primary hover:underline"
              >
                تسجيل الدخول {/* t('login') */}
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="hidden bg-muted lg:block">
        <Image
          src="/images/signup-visual.jpg" // Use a different image for signup page
          alt="Signup Visual"
          width={1920}
          height={1080}
          className="h-full w-full object-cover dark:brightness-[0.7]"
        />
      </div>
    </div>
  );
}
