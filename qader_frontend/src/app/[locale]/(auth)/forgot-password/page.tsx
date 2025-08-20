"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
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
import { gsap } from "gsap";

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
  const [identifier, setIdentifier] = useState<string>("");
  const [resetTokenState, setResetTokenState] = useState<string>("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // GSAP Animation Refs
  const cardRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const footerRef = useRef<HTMLDivElement>(null);
  const backButtonRef = useRef<HTMLButtonElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

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

  // GSAP Animation Functions
  const animateStepTransition = (direction: 'forward' | 'backward' = 'forward') => {
    const tl = gsap.timeline();
    
    // Animate out current content
    tl.to([headerRef.current, contentRef.current], {
      opacity: 0,
      x: direction === 'forward' ? -30 : 30,
      duration: 0.3,
      ease: "power2.inOut",
    })
    .to(formRef.current, {
      scale: 0.95,
      opacity: 0,
      duration: 0.2,
      ease: "power2.inOut",
    }, "-=0.1")
    .call(() => {
      // Content will update here due to React re-render
    })
    .to([headerRef.current, contentRef.current], {
      opacity: 1,
      x: 0,
      duration: 0.4,
      ease: "power2.out",
    }, "+=0.1")
    .to(formRef.current, {
      scale: 1,
      opacity: 1,
      duration: 0.3,
      ease: "back.out(1.7)",
    }, "-=0.2");
  };

  const animateBackButton = (show: boolean) => {
    if (!backButtonRef.current) return;
    
    if (show) {
      gsap.fromTo(backButtonRef.current, 
        { 
          scale: 0,
          opacity: 0,
          rotation: -180 
        },
        {
          scale: 1,
          opacity: 1,
          rotation: 0,
          duration: 0.5,
          ease: "back.out(1.7)",
        }
      );
    } else {
      gsap.to(backButtonRef.current, {
        scale: 0,
        opacity: 0,
        duration: 0.3,
        ease: "power2.inOut",
      });
    }
  };

  const animateFormElements = () => {
    const formElements = formRef.current?.querySelectorAll('.form-element');
    if (formElements) {
      gsap.fromTo(formElements,
        { 
          opacity: 0, 
          y: 20,
          scale: 0.95
        },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.5,
          stagger: 0.1,
          ease: "power2.out",
        }
      );
    }
  };

  const animateOTPSlots = () => {
    const otpSlots = document.querySelectorAll('[data-slot]');
    if (otpSlots.length > 0) {
      gsap.fromTo(otpSlots,
        { 
          scale: 0,
          opacity: 0,
          rotation: 180
        },
        {
          scale: 1,
          opacity: 1,
          rotation: 0,
          duration: 0.6,
          stagger: 0.1,
          ease: "back.out(1.7)",
          delay: 0.2
        }
      );
    }
  };

  // Initial page load animation
  useEffect(() => {
    const tl = gsap.timeline();
    
    // Set initial states
    gsap.set(cardRef.current, { scale: 0.8, opacity: 0, y: 50 });
    gsap.set([headerRef.current, contentRef.current, footerRef.current], { 
      opacity: 0, 
      y: 30 
    });
    
    // Animate in
    tl.to(cardRef.current, {
      scale: 1,
      opacity: 1,
      y: 0,
      duration: 0.6,
      ease: "back.out(1.7)",
    })
    .to([headerRef.current, contentRef.current, footerRef.current], {
      opacity: 1,
      y: 0,
      duration: 0.5,
      stagger: 0.1,
      ease: "power2.out",
    }, "-=0.3")
    .call(() => {
      animateFormElements();
    });

  }, []);

  // Animate step changes
  useEffect(() => {
    if (currentStep !== "request") {
      animateBackButton(true);
    }
    
    // Animate form elements when step changes
    const timer = setTimeout(() => {
      animateFormElements();
      if (currentStep === "verify") {
        animateOTPSlots();
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [currentStep]);

  const requestOtpMutation = useMutation({
    mutationKey: REQUEST_OTP_KEY,
    mutationFn: requestOtp,
    onSuccess: (data, variables) => {
      toast.success(data.detail || tAuth("activationLinkSent"));
      setIdentifier(variables.identifier);
      verifyOtpForm.setValue("identifier", variables.identifier);
      verifyOtpForm.setValue("otp", "");
      
      // Animate transition
      animateStepTransition('forward');
      setTimeout(() => {
        setCurrentStep("verify");
        requestOtpForm.reset();
      }, 300);
    },
    onError: (error: any) => {
      // Error shake animation gsap.to(
      gsap.to(formRef.current, {
         x: 0,
        duration: 0.5,
        ease: "power2.inOut",
        keyframes: [
          { x: -10 },
          { x: 10 },
          { x: -10 },
          { x: 10 },
          { x: 0 },]
      });
      
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
      
      // Animate transition
      animateStepTransition('forward');
      setTimeout(() => {
        setCurrentStep("reset");
        verifyOtpForm.reset();
      }, 300);
    },
    onError: (error: any) => {
      // Error shake animation
      gsap.to(formRef.current, {
         x: 0,
        duration: 0.5,
        ease: "power2.inOut",
        keyframes: [
          { x: -10 },
          { x: 10 },
          { x: -10 },
          { x: 10 },
          { x: 0 },]
      });
      
      if (error.data?.otp) {
        verifyOtpForm.setError("otp", {
          type: "server",
          message: error.data.otp.join(", "),
        });
      } else if (error.data?.identifier) {
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
      
      // Success animation
      gsap.to(cardRef.current, {
        scale: 1.05,
        duration: 0.2,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut",
        onComplete: () => {
          router.push(PATHS.LOGIN);
        }
      });
      
      // Reset all forms and states {
      scale:
      requestOtpForm.reset();
      verifyOtpForm.reset();
      resetPasswordForm.reset();
      setCurrentStep("request");
      setIdentifier("");
      setResetTokenState("");
    },
    onError: (error: any) => {
      // Error shake animation
      gsap.to(formRef.current, {
         x: 0,
        duration: 0.5,
        ease: "power2.inOut",
        keyframes: [
          { x: -10 },
          { x: 10 },
          { x: -10 },
          { x: 10 },
          { x: 0 },]
      });
      
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

  const onRequestOtpSubmit = (data: RequestOtpFormValues) => {
    requestOtpMutation.mutate(data);
  };

  const onVerifyOtpSubmit = React.useCallback(
    (data: VerifyOtpFormValues) => {
      verifyOtpMutation.mutate(data);
    },
    [verifyOtpMutation]
  );

  const onResetPasswordSubmit = (data: ResetPasswordFormValues) => {
    resetPasswordMutation.mutate(data);
  };

  const goBack = () => {
    animateStepTransition('backward');
    
    setTimeout(() => {
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
    }, 300);
  };

  const dir = tCommon("dir") as "ltr" | "rtl";

  return (
    <div className="flex items-center justify-center p-4" dir={dir}>
      <Card ref={cardRef} className="w-full max-w-md bg-background shadow">
        {currentStep !== "request" && (
          <Button
            ref={backButtonRef}
            variant="ghost"
            size="icon"
            onClick={goBack}
            className="absolute left-4 top-4 m-2 h-8 w-8 rtl:left-auto rtl:right-4"
            aria-label={tAuth("goBack")}
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1.1,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
        )}
        
        {currentStep === "request" && (
          <>
            <CardHeader ref={headerRef}>
              <CardTitle className="text-2xl font-semibold">
                {tAuth("forgotPasswordTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordRequestSubtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent ref={contentRef}>
              <form
                ref={formRef}
                onSubmit={requestOtpForm.handleSubmit(onRequestOtpSubmit)}
                className="space-y-6"
              >
                <div className="form-element">
                  <Label htmlFor="fp-identifier" className="font-medium">
                    {tAuth("forgotPasswordIdentifierLabel")}
                  </Label>
                  <div className="relative mt-1.5">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:left-auto rtl:right-3" />
                    <Input
                      id="fp-identifier"
                      placeholder={tAuth("forgotPasswordIdentifierPlaceholder")}
                      {...requestOtpForm.register("identifier")}
                      className="pl-10 rtl:pr-10"
                      aria-describedby="identifier-error"
                      onFocus={(e) => {
                        gsap.to(e.currentTarget, {
                          scale: 1.02,
                          duration: 0.2,
                          ease: "power2.out"
                        });
                      }}
                      onBlur={(e) => {
                        gsap.to(e.currentTarget, {
                          scale: 1,
                          duration: 0.2,
                          ease: "power2.out"
                        });
                      }}
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
                  className="form-element w-full"
                  disabled={requestOtpMutation.isPending}
                  onMouseEnter={(e) => {
                    if (!requestOtpMutation.isPending) {
                      gsap.to(e.currentTarget, {
                        scale: 1.05,
                        duration: 0.2,
                        ease: "power2.out"
                      });
                    }
                  }}
                  onMouseLeave={(e) => {
                    gsap.to(e.currentTarget, {
                      scale: 1,
                      duration: 0.2,
                      ease: "power2.out"
                    });
                  }}
                  onClick={(e) => {
                    // Button press animation
                    gsap.to(e.currentTarget, {
                      scale: 0.95,
                      duration: 0.1,
                      yoyo: true,
                      repeat: 1,
                      ease: "power2.inOut"
                    });
                  }}
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
            <CardHeader ref={headerRef}>
              <CardTitle className="text-2xl font-semibold">
                {tAuth("forgotPasswordVerifyTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordVerifySubtitle", {
                  identifier: identifier,
                })}
              </CardDescription>
            </CardHeader>
            <CardContent ref={contentRef}>
              <form
                ref={formRef}
                className="flex flex-col items-center space-y-6"
              >
                <Controller
                  name="otp"
                  control={verifyOtpForm.control}
                  render={({ field, fieldState }) => (
                    <div
                      dir="ltr"
                      className="form-element flex w-full flex-col items-center"
                    >
                      <Label htmlFor="fp-otp" className="sr-only">
                        {tAuth("forgotPasswordOtpLabel")}
                      </Label>
                      <InputOTP
                        id="fp-otp"
                        maxLength={6}
                        value={field.value}
                        onChange={(value) => {
                          field.onChange(value);
                          // Animate slots on input
                          const activeSlot = document.querySelector(`[data-slot="${value.length}"]`);
                          if (activeSlot) {
                            gsap.fromTo(activeSlot, 
                              { scale: 1.2 }, 
                              { scale: 1, duration: 0.2, ease: "power2.out" }
                            );
                          }
                        }}
                        onBlur={field.onBlur}
                        onComplete={() => {
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
                <Button
                  type="button"
                  onClick={verifyOtpForm.handleSubmit(onVerifyOtpSubmit)}
                  className="form-element w-full"
                  disabled={
                    verifyOtpMutation.isPending ||
                    verifyOtpForm.watch("otp")?.length !== 6
                  }
                  onMouseEnter={(e) => {
                    if (!verifyOtpMutation.isPending && verifyOtpForm.watch("otp")?.length === 6) {
                      gsap.to(e.currentTarget, {
                        scale: 1.05,
                        duration: 0.2,
                        ease: "power2.out"
                      });
                    }
                  }}
                  onMouseLeave={(e) => {
                    gsap.to(e.currentTarget, {
                      scale: 1,
                      duration: 0.2,
                      ease: "power2.out"
                    });
                  }}
                  onClickCapture={(e) => {
                    // Button press animation
                    if (!verifyOtpMutation.isPending && verifyOtpForm.watch("otp")?.length === 6) {
                      gsap.to(e.currentTarget, {
                        scale: 0.95,
                        duration: 0.1,
                        yoyo: true,
                        repeat: 1,
                        ease: "power2.inOut"
                      });
                    }
                  }}
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
            <CardHeader ref={headerRef}>
              <CardTitle className="text-2xl font-semibold">
                {tAuth("forgotPasswordResetTitle")}
              </CardTitle>
              <CardDescription>
                {tAuth("forgotPasswordResetSubtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent ref={contentRef}>
              <form
                ref={formRef}
                onSubmit={resetPasswordForm.handleSubmit(onResetPasswordSubmit)}
                className="space-y-4"
              >
                <div className="form-element">
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
                      className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
                      aria-describedby="new-password-error"
                      onFocus={(e) => {
                        gsap.to(e.currentTarget, {
                          scale: 1.02,
                          duration: 0.2,
                          ease: "power2.out"
                        });
                      }}
                      onBlur={(e) => {
                        gsap.to(e.currentTarget, {
                          scale: 1,
                          duration: 0.2,
                          ease: "power2.out"
                        });
                      }}
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        setShowPassword(!showPassword);
                        // Animate eye icon
                        gsap.to(e.currentTarget, {
                          scale: 1.2,
                          duration: 0.1,
                          yoyo: true,
                          repeat: 1,
                          ease: "power2.inOut"
                        });
                      }}
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
                <div className="form-element">
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
                      placeholder={tAuth("passwordPlaceholder")}
                      {...resetPasswordForm.register("new_password_confirm")}
                      className="pl-10 pr-10 rtl:pl-10 rtl:pr-10"
                      aria-describedby="confirm-password-error"
                      onFocus={(e) => {
                        gsap.to(e.currentTarget, {
                          scale: 1.02,
                          duration: 0.2,
                          ease: "power2.out"
                        });
                      }}
                      onBlur={(e) => {
                        gsap.to(e.currentTarget, {
                          scale: 1,
                          duration: 0.2,
                          ease: "power2.out"
                        });
                      }}
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        setShowConfirmPassword(!showConfirmPassword);
                        // Animate eye icon
                        gsap.to(e.currentTarget, {
                          scale: 1.2,
                          duration: 0.1,
                          yoyo: true,
                          repeat: 1,
                          ease: "power2.inOut"
                        });
                      }}
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
                  className="form-element w-full"
                  disabled={resetPasswordMutation.isPending}
                  onMouseEnter={(e) => {
                    if (!resetPasswordMutation.isPending) {
                      gsap.to(e.currentTarget, {
                        scale: 1.05,
                        duration: 0.2,
                        ease: "power2.out"
                      });
                    }
                  }}
                  onMouseLeave={(e) => {
                    gsap.to(e.currentTarget, {
                      scale: 1,
                      duration: 0.2,
                      ease: "power2.out"
                    });
                  }}
                  onClick={(e) => {
                    // Button press animation
                    if (!resetPasswordMutation.isPending) {
                      gsap.to(e.currentTarget, {
                        scale: 0.95,
                        duration: 0.1,
                        yoyo: true,
                        repeat: 1,
                        ease: "power2.inOut"
                      });
                    }
                  }}
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
        
        <CardFooter ref={footerRef} className="block border-t px-6 text-center text-sm">
          {currentStep === "request" ? (
            <Link 
              href={PATHS.HOME} 
              className="text-primary hover:underline transition-colors duration-200"
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1.05,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
            >
              {tAuth("forgotPasswordBackToLogin")}
            </Link>
          ) : (
            <Link 
              href={PATHS.HOME} 
              className="text-primary hover:underline transition-colors duration-200"
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1.05,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
            >
              {tAuth("forgotPasswordBackToLogin")}
            </Link>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
