"use client";
import React, { useState } from "react";
import { XMarkIcon } from "@heroicons/react/24/solid";
import { EnvelopeIcon, LockClosedIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";
import Link from "next/link";

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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!show) return null;

  const handleLogin = async () => {
    if (!email || !password) {
      setError("يرجى إدخال البريد الإلكتروني وكلمة المرور");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch("https://qader.vip/ar/api/v1/auth/login/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          username: email,
          password: password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 400) {
          setError(data.detail || "بيانات الدخول غير صحيحة");
        } else if (res.status === 401) {
          setError("أنت غير مصرح لك. يرجى التحقق من بيانات الدخول.");
        } else {
          setError("حدث خطأ غير متوقع. حاول مرة أخرى.");
        }
        setIsSubmitting(false);
        return;
      }

      // Store tokens and user info
      localStorage.setItem("accessToken", data.access);
      localStorage.setItem("refreshToken", data.refresh);
      localStorage.setItem("user", JSON.stringify(data.user));

      // Optionally: log success or redirect
      console.log("تم تسجيل الدخول بنجاح", data.user);

      onClose();

      // TODO: navigate to dashboard or refresh auth context
    } catch (err) {
      console.error(err);
      setError("فشل الاتصال بالخادم. حاول لاحقاً.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div
          className="relative w-full max-w-sm lg:max-w-3xl bg-background rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onClose}
            className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors z-10"
            aria-label="Close popup"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>

          <div className="w-full md:w-1/2 flex items-center justify-center max-md:flex-col">
            <div className="w-full p-4 sm:p-6 lg:p-8 space-y-6">
              <div>
                <h2 className="text-3xl font-bold text-center">أهلاً بعودتك!!!</h2>
                <p className="text-xl text-gray-600 text-center">اكمل السير معنا...</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="login-email" className="block text-sm font-medium mr-3">
                    البريد الإلكتروني
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      id="login-email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="you@example.com"
                    />
                    <EnvelopeIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                <div>
                  <label htmlFor="login-password" className="block text-sm font-medium mr-3">
                    كلمة المرور
                  </label>
                  <div className="relative">
                    <input
                      type="password"
                      id="login-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="********"
                    />
                    <LockClosedIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                {error && <p className="text-sm text-red-500 text-center">{error}</p>}

                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <label className="flex items-center space-x-2 rtl:space-x-reverse">
                    <input type="checkbox" className="accent-primary" />
                    <span>حفظ الجلسة</span>
                  </label>
                  <Link href="/forgot-password" className="text-[#2f80ed] underline">
                    نسيت كلمة السر؟
                  </Link>
                </div>

                <Button
                  variant={"outline"}
                  className="w-full"
                  onClick={handleLogin}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "جارٍ الدخول..." : "دخول"}
                </Button>
              </div>

              <p className="text-center text-sm text-muted-foreground">
                ليس لديك حساب؟{" "}
                {onSwitchToSignup ? (
                  <button
                    onClick={onSwitchToSignup}
                    className="text-primary hover:underline font-medium"
                  >
                    إنشاء حساب
                  </button>
                ) : (
                  <Link href="/signup" className="text-primary hover:underline font-medium">
                    إنشاء حساب
                  </Link>
                )}
              </p>
            </div>
          </div>

          <div className="w-full md:w-1/2 h-64 md:h-auto hidden md:block">
            <img
              src="/images/login.jpg"
              alt="تسجيل الدخول"
              className="h-full w-full object-cover"
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default LoginModal;
