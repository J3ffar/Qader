"use client";
import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Mail, Lock, XIcon, Eye, EyeOff } from "lucide-react"; // Replaced Eye icons

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose, // For explicit close button if needed outside of X
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox"; // For "Remember me"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"; // For general error messages

import { LoginSchema, type LoginCredentials } from "@/types/forms/auth.schema";
import { loginUser } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";
import { QUERY_KEYS } from "@/constants/queryKeys";

// For i18n (assuming you have next-intl setup)
// import { useTranslations } from 'next-intl';

interface LoginModalProps {
  show: boolean;
  onClose: () => void;
  onSwitchToSignup?: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({
  show,
  onClose,
  onSwitchToSignup,
}) => {
  // const t = useTranslations('Auth'); // Example for i18n
  const router = useRouter();
  const { login: storeLogin, isAuthenticated } = useAuthStore();
  const [showPassword, setShowPassword] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError, // For API errors related to specific fields
    reset,
  } = useForm<LoginCredentials>({
    resolver: zodResolver(LoginSchema),
    defaultValues: {
      username: "",
      password: "",
      rememberMe: false,
    },
  });

  const loginMutation = useMutation({
    mutationKey: [QUERY_KEYS.LOGIN],
    mutationFn: loginUser,
    onSuccess: (data) => {
      storeLogin({ access: data.access, refresh: data.refresh }, data.user);
      toast.success("تم تسجيل الدخول بنجاح!"); // t('loginSuccess')
      onClose(); // Close modal on success
      reset(); // Reset form
      // Redirect based on profile completion or other logic
      if (data.user?.is_super || data.user?.is_staff) {
        router.push(PATHS.ADMIN_DASHBOARD);
      } else if (!data.user.profile_complete) {
        router.push(PATHS.COMPLETE_PROFILE); // Or your specific path
      } else {
        router.push(PATHS.STUDY_HOME); // Or user's last visited page
      }
    },
    onError: (error: any) => {
      // Handle API errors
      if (error.status === 400 && error.data) {
        // Example: if backend returns { username: ["error"], password: ["error"] }
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof LoginCredentials;
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : error.data[key];
          if (field === "username" || field === "password") {
            setFormError(field, { type: "server", message });
          }
        });
        if (error.data.detail) {
          // General non-field error from backend
          toast.error(error.data.detail);
        } else {
          toast.error("بيانات الدخول غير صحيحة أو حساب غير مفعل."); // t('loginFailed')
        }
      } else {
        toast.error(error.message || "فشل الاتصال بالخادم. حاول لاحقاً."); // t('loginErrorServer')
      }
    },
  });

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      // This means the dialog is about to close
      reset(); // Reset React Hook Form state (fields and errors)
      loginMutation.reset(); // Reset TanStack Query mutation state
      onClose(); // Call the passed onClose handler to update parent state
    } else {
      // Dialog is opening. If `show` is managed by parent,
      // `onClose` (which sets parent's show to false) isn't called here.
      // The `show` prop directly controls the open state.
    }
  };

  // Close modal if user is already authenticated and modal tries to show
  useEffect(() => {
    if (isAuthenticated && show) {
      onClose();
    }
  }, [isAuthenticated, show, onClose]);

  const onSubmit = (data: LoginCredentials) => {
    loginMutation.mutate(data);
  };

  if (!show && !loginMutation.isPending) {
    // Also ensure not to return null if a mutation is in progress after close (edge case)
    return null;
  }

  return (
    <Dialog open={show} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-sm md:max-w-3xl flex flex-col md:flex-row p-0 overflow-hidden"
        onInteractOutside={(e) => e.preventDefault()} // Prevents closing on outside click if needed
      >
        <div className="w-full md:w-1/2 flex items-center justify-center p-6 sm:p-8">
          <div className="w-full space-y-6">
            <DialogHeader className="text-center">
              <DialogTitle className="text-3xl font-bold">
                {/*t('welcomeBack')*/}أهلاً بعودتك!
              </DialogTitle>
              <p className="text-muted-foreground">
                {/*t('continueJourney')*/}اكمل السير معنا...
              </p>
            </DialogHeader>

            {loginMutation.error && !loginMutation.error.data?.detail && (
              <Alert variant="destructive">
                <AlertTitle>خطأ في تسجيل الدخول</AlertTitle>
                <AlertDescription>
                  {(loginMutation.error as any)?.message ||
                    "بيانات الدخول غير صحيحة أو حساب غير مفعل."}
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="login-username">
                  {/*t('emailOrUsername')*/}البريد الإلكتروني أو اسم المستخدم
                </Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
                  <Input
                    id="login-username"
                    type="text"
                    placeholder="you@example.com" //{t('emailOrUsernamePlaceholder')}
                    {...register("username")}
                    className="pl-10 rtl:pr-10 rtl:pl-4"
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
                <Label htmlFor="login-password">
                  {/*t('password')*/}كلمة المرور
                </Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
                  <Input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="********"
                    {...register("password")}
                    className="pl-10 pr-10 rtl:pr-10 rtl:pl-10" // Space for both icons
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

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <Checkbox id="rememberMe" {...register("rememberMe")} />
                  <Label
                    htmlFor="rememberMe"
                    className="font-normal text-muted-foreground"
                  >
                    {/*t('rememberMe')*/}حفظ الجلسة
                  </Label>
                </div>
                <Link
                  href={PATHS.FORGOT_PASSWORD}
                  className="text-primary hover:underline"
                  onClick={onClose} // Close modal when navigating
                >
                  {/*t('forgotPassword')*/}نسيت كلمة السر؟
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending ? "جارٍ الدخول..." : "دخول"}
              </Button>
            </form>

            <p className="text-center text-sm text-muted-foreground">
              {/*t('noAccount')*/}ليس لديك حساب؟{" "}
              {onSwitchToSignup ? (
                <button
                  type="button"
                  onClick={() => {
                    onClose(); // Close current modal first
                    onSwitchToSignup(); // Then open signup
                  }}
                  className="font-medium text-primary hover:underline"
                >
                  {/*t('createAccount')*/}إنشاء حساب
                </button>
              ) : (
                <Link
                  href={PATHS.SIGNUP} // Fallback if it's a page route
                  className="font-medium text-primary hover:underline"
                  onClick={onClose}
                >
                  {/*t('createAccount')*/}إنشاء حساب
                </Link>
              )}
            </p>
          </div>
        </div>

        {/* Image Section - remains the same */}
        <div className="hidden md:block w-full md:w-1/2 h-64 md:h-auto">
          <img
            src="/images/login.jpg" // Ensure this path is correct from /public
            alt="Login Visual"
            className="h-full w-full object-cover"
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default LoginModal;
