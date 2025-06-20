"use client";
import React, { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation"; // Use next-intl's router
import Link from "next/link"; // Use next-intl's Link
import { toast } from "sonner";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  createLoginSchema,
  type LoginCredentials,
} from "@/types/forms/auth.schema"; // Adjust path
import { loginUser } from "@/services/auth.service"; // Adjust path
import { useAuthActions, useAuthStore } from "@/store/auth.store"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import { queryKeys } from "@/constants/queryKeys";

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
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common");
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { login: storeLogin } = useAuthActions();
  const [showPassword, setShowPassword] = React.useState(false);

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

  const loginMutation = useMutation({
    mutationKey: queryKeys.auth.login(),
    mutationFn: loginUser,
    onSuccess: (data) => {
      storeLogin({ access: data.access, refresh: data.refresh }, data.user);
      toast.success(tAuth("loginSuccess"));
      onClose();
      reset();
      if (data.user?.is_super || data.user?.is_staff) {
        router.push(PATHS.ADMIN_DASHBOARD);
      } else if (!data.user.profile_complete) {
        router.push(PATHS.COMPLETE_PROFILE);
      } else {
        router.push(PATHS.STUDY.HOME);
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

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      reset();
      loginMutation.reset();
      onClose();
    }
  };

  useEffect(() => {
    if (isAuthenticated && show) {
      onClose();
    }
  }, [isAuthenticated, show, onClose]);

  const onSubmit = (data: LoginCredentials) => loginMutation.mutate(data);

  if (!show && !loginMutation.isPending) return null;

  return (
    <Dialog open={show} onOpenChange={handleOpenChange}>
      <DialogContent className="flex max-w-sm flex-col overflow-hidden p-0 md:max-w-3xl md:flex-row">
        <div className="flex w-full items-center justify-center p-6 sm:p-8 md:w-1/2">
          <div className="w-full space-y-6">
            <DialogHeader className="text-center">
              <DialogTitle className="text-3xl font-bold">
                {tAuth("welcomeBack")}
              </DialogTitle>
              <p className="text-muted-foreground">
                {tAuth("continueJourney")}
              </p>
            </DialogHeader>

            {loginMutation.error && !loginMutation.error.data?.detail && (
              <Alert variant="destructive">
                <AlertTitle>{tAuth("loginErrorAlertTitle")}</AlertTitle>
                <AlertDescription>
                  {(loginMutation.error as any)?.message ||
                    tAuth("loginFailed")}
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="login-username">
                  {tAuth("emailOrUsername")}
                </Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                  <Input
                    id="login-username"
                    type="text"
                    placeholder={tAuth("emailOrUsernamePlaceholder")}
                    {...register("username")}
                    className="pl-10 rtl:pl-4 rtl:pr-10"
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
                <Label htmlFor="login-password">{tAuth("password")}</Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                  <Input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    placeholder={tAuth("passwordPlaceholder")}
                    {...register("password")}
                    className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
                    aria-invalid={errors.password ? "true" : "false"}
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
                {errors.password && (
                  <p className="mt-1 text-xs text-red-500">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <Checkbox
                    id="rememberMeLoginModal"
                    {...register("rememberMe")}
                  />{" "}
                  {/* Unique ID for modal context */}
                  <Label
                    htmlFor="rememberMeLoginModal"
                    className="font-normal text-muted-foreground"
                  >
                    {tAuth("rememberMe")}
                  </Label>
                </div>
                <Link
                  href={PATHS.FORGOT_PASSWORD}
                  className="text-primary hover:underline"
                  onClick={onClose}
                >
                  {tAuth("forgotPassword")}
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending
                  ? tAuth("loggingInLoading")
                  : tAuth("login")}
              </Button>
            </form>

            <p className="text-center text-sm text-muted-foreground">
              {tAuth("noAccount")}{" "}
              {onSwitchToSignup ? (
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onSwitchToSignup();
                  }}
                  className="font-medium text-primary hover:underline"
                >
                  {tAuth("createAccount")}
                </button>
              ) : (
                <Link
                  href={PATHS.SIGNUP}
                  className="font-medium text-primary hover:underline"
                  onClick={onClose}
                >
                  {tAuth("createAccount")}
                </Link>
              )}
            </p>
          </div>
        </div>
        <div className="hidden h-64 w-full md:block md:h-auto md:w-1/2">
          <img
            src="/images/login.jpg"
            alt={tAuth("loginVisualAltText")}
            className="h-full w-full object-cover"
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};
export default LoginModal;
