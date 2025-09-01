"use client";
import React, { useEffect, useMemo } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { User, Mail, Lock, Eye, EyeOff } from "lucide-react"; // XIcon not used here
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  // DialogClose, // Not explicitly used for a button, Shadcn Dialog handles X icon
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  createSignupSchema, // Using the factory function
  type SignupFormValues,
  type ApiSignupData,
} from "@/types/forms/auth.schema"; // Adjust path
import { signupUser } from "@/services/auth.service"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import { queryKeys } from "@/constants/queryKeys";

interface SignupModalProps {
  show: boolean;
  onClose: () => void;
  onSwitchToLogin?: () => void;
}

const signupDefaultValues: SignupFormValues = {
  full_name: "",
  email: "",
  password: "",
  password_confirm: "",
  termsAccepted: false,
};

const SignupModal: React.FC<SignupModalProps> = ({
  show,
  onClose,
  onSwitchToLogin,
}) => {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common"); // For generic texts like show/hide password
  const router = useRouter(); // next-intl router
  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);

  // Create the schema instance with the translation function
  const CurrentSignupSchema = useMemo(() => createSignupSchema(tAuth), [tAuth]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
    reset,
    control,
  } = useForm<SignupFormValues>({
    resolver: zodResolver(CurrentSignupSchema), // Pass the memoized schema instance
    defaultValues: signupDefaultValues,
  });

  const signupMutation = useMutation({
    mutationKey: queryKeys.auth.signup(),
    mutationFn: (data: SignupFormValues) => {
      const apiData: ApiSignupData = {
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        password_confirm: data.password_confirm,
      };
      return signupUser(apiData);
    },
    onSuccess: (data) => {
      toast.success(data.detail || tAuth("signupSuccessEmailSent"));
      reset();
      onClose();
      // Consider redirecting to a specific "check your email" page if you have one
      // Example: router.push(PATHS.CHECK_EMAIL_NOTICE);
    },
    onError: (error: any) => {
      if (error.status === 400 && error.data) {
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof SignupFormValues;
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : String(error.data[key]); // Ensure message is a string for setFormError

          // Check if the field is actually part of the form to avoid errors
          if (Object.keys(signupDefaultValues).includes(field)) {
            setFormError(field, { type: "server", message });
          }
        });
        if (error.data.detail) {
          toast.error(String(error.data.detail));
        } else {
          // Fallback if no specific field errors were set from backend data and no detail message
          let hasFieldErrors = false;
          Object.keys(signupDefaultValues).forEach((formKey) => {
            if (error.data[formKey]) hasFieldErrors = true;
          });
          if (!hasFieldErrors) {
            toast.error(tAuth("signupFailedCheckData"));
          }
        }
      } else {
        toast.error(error.message || tAuth("signupErrorServer"));
      }
    },
  });

  const onSubmit = (data: SignupFormValues) => {
    signupMutation.mutate(data);
  };

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      reset();
      signupMutation.reset();
      onClose();
    }
  };

  // Conditional rendering: if modal is not shown and mutation isn't pending, return null
  if (!show && !signupMutation.isPending) {
    return null;
  }

  return (
    <Dialog open={show} onOpenChange={handleOpenChange}>
      <DialogContent className="flex max-w-md flex-col overflow-hidden p-0 md:max-w-3xl md:flex-row">
        {/* Form Side */}
        <div className="flex w-full items-center justify-center p-6 sm:p-8 md:w-1/2">
          {/* <div className="w-full space-y-6">
            <DialogHeader className="text-center">
              <DialogTitle className="text-3xl font-bold">
                {tAuth("welcome")}
              </DialogTitle>
              <p className="text-muted-foreground">
                {tAuth("qaderWelcomesYou")}
              </p>
            </DialogHeader>

            {signupMutation.error &&
              !(signupMutation.error as any).data?.detail &&
              !Object.keys(signupDefaultValues).some(
                (key) => (signupMutation.error as any).data?.[key]
              ) && (
                <Alert variant="destructive">
                  <AlertTitle>{tAuth("errorAlertTitle")}</AlertTitle>
                  <AlertDescription>
                    {(signupMutation.error as any)?.message ||
                      tAuth("signupFailedCheckData")}
                  </AlertDescription>
                </Alert>
              )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="signup-modal-fullname">
                  {tAuth("fullName")}
                </Label>{" "}
                <div className="relative mt-1">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                  <Input
                    id="signup-modal-fullname"
                    type="text"
                    placeholder={tAuth("fullNamePlaceholder")}
                    {...register("full_name")}
                    className="pl-10 rtl:pl-4 rtl:pr-10"
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
                <Label htmlFor="signup-modal-email">{tAuth("email")}</Label>{" "}
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                  <Input
                    id="signup-modal-email"
                    type="email"
                    placeholder={tAuth("emailPlaceholder")}
                    {...register("email")}
                    className="pl-10 rtl:pl-4 rtl:pr-10"
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
                <Label htmlFor="signup-modal-password">
                  {tAuth("password")}
                </Label>{" "}
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                  <Input
                    id="signup-modal-password"
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

              <div>
                <Label htmlFor="signup-modal-confirm-password">
                  {tAuth("confirmPassword")}
                </Label>{" "}
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                  <Input
                    id="signup-modal-confirm-password"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder={tAuth("passwordPlaceholder")} 
                    {...register("password_confirm")}
                    className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
                    aria-invalid={errors.password_confirm ? "true" : "false"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
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
                {errors.password_confirm && (
                  <p className="mt-1 text-xs text-red-500">
                    {errors.password_confirm.message}
                  </p>
                )}
              </div>

              <div className="flex items-start space-x-2 gap-2 pt-1 rtl:space-x-reverse">
                <Controller
                  name="termsAccepted"
                  control={control}
                  render={({ field }) => (
                    <Checkbox
                      id="termsAcceptedSignupModal" // Unique ID
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      aria-invalid={errors.termsAccepted ? "true" : "false"}
                      className={`mt-0.5 ${
                        errors.termsAccepted ? "border-red-500" : ""
                      }`}
                    />
                  )}
                />
                <Label
                  htmlFor="termsAcceptedSignupModal"
                  className="cursor-pointer text-sm font-normal leading-snug text-muted-foreground"
                >
                  {tAuth("agreeTo")}{""}
                  <Link
                    href={"/terms-and-conditions"} 
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
                  {" "}
                  {errors.termsAccepted.message}
                </p>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={signupMutation.isPending}
              >
                {signupMutation.isPending
                  ? tAuth("creatingAccountLoading")
                  : tAuth("createAccount")}
              </Button>
            </form>

          
            <p className="text-center text-sm text-muted-foreground">
              {tAuth("alreadyHaveAccount")}{" "}
              {onSwitchToLogin ? (
                <button
                  type="button"
                  onClick={() => {
                    onClose(); 
                    if (onSwitchToLogin) onSwitchToLogin(); 
                  }}
                  className="font-medium text-primary hover:underline"
                >
                  {tAuth("login")}
                </button>
              ) : (
                <Link
                  href={PATHS.LOGIN} 
                  className="font-medium text-primary hover:underline"
                  onClick={onClose} 
                >
                  {tAuth("login")}
                </Link>
              )}
            </p>
          </div> */}

          <div className="w-full space-y-6">
            <div className="font-bold md:text-3xl text-xl text-[#074182] text-center">
              نعتذر حاليا !
            </div>
            <div className="font-bold md:text-2xl text-xl  text-center ">
              لا يمكن إنشاء حساب إلا من خلال التعاقدات مع المدارس
            </div>

            <div className=" flex justify-center items-center">
              <a href="/partners" className="flex justify-center gap-2 min-[1120px]:py-3 sm:w-[180px] w-[100px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer hover:scale-105 active:scale-95 transform-gpu">
              صفحة التعاقد
            </a>
            </div>
          </div>


        </div>

        {/* Image Side */}
        <div className="hidden h-64 w-full md:block md:h-auto md:w-1/2">
          <img
            src="/images/login.jpg" // Ensure this path is correct from /public
            alt={tAuth("signupVisualAltText")}
            className="h-full w-full object-cover"
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SignupModal;
