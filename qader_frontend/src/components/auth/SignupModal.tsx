"use client";
import React, { useState } from "react";
import { XMarkIcon } from "@heroicons/react/24/solid";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";
import { useRouter } from "next/navigation";

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
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!show) return null;

  const handleStartSignup = async () => {
    setError(null);
    setSuccessMessage(null);

    if (password !== confirmPassword) {
      setError("كلمتا المرور غير متطابقتين.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch("https://qader.vip/ar/api/v1/auth/signup/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          password_confirm: confirmPassword,
        }),
      });

      const data = await res.json();

      if (res.status === 201) {
        setSuccessMessage(data.detail || "تم إرسال رابط التفعيل إلى بريدك الإلكتروني.");
        // optional: احفظ المعلومات مؤقتًا
        localStorage.setItem("signup-step1", JSON.stringify({ full_name: fullName, email, password }));
        // يمكنك إعادة التوجيه بعد ثوانٍ إن أردت
        setTimeout(() => {
          router.push("/completsignup");
        }, 2000);
      } else if (res.status === 400) {
        if (data.email) setError(data.email[0]);
        else if (data.detail) setError(data.detail);
        else setError("حدث خطأ ما أثناء التسجيل.");
      } else {
        setError("فشل في إرسال البريد الإلكتروني. الرجاء المحاولة لاحقًا.");
      }
    } catch (e) {
      setError("حدث خطأ غير متوقع. الرجاء المحاولة لاحقًا.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]" onClick={onClose} />
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div
          className="relative w-full max-w-md lg:max-w-3xl bg-background rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onClose}
            className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors z-10"
            aria-label="Close popup"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>

          {/* Form Content */}
          <div className="w-full md:w-1/2 flex items-center justify-center">
            <div className="w-full p-6 sm:p-8 space-y-6">
              <div>
                <h2 className="text-3xl font-bold text-center">أهلاً بك!!</h2>
                <p className="text-xl text-gray-600 text-center">قادر ترحب بك.</p>
              </div>
              <div className="space-y-4">
                {/* Full Name */}
                <div className="space-y-1">
                  <label htmlFor="signup-fullname" className="block text-sm font-medium text-foreground mr-3">
                    الاسم الكامل
                  </label>
                  <div className="relative">
                    <input
                      id="signup-fullname"
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="الاسم الكامل"
                    />
                    <UserIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                {/* Email */}
                <div className="space-y-1">
                  <label htmlFor="signup-email" className="block text-sm font-medium text-foreground mr-3">
                    البريد الإلكتروني
                  </label>
                  <div className="relative">
                    <input
                      id="signup-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="you@example.com"
                    />
                    <EnvelopeIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-1">
                  <label htmlFor="signup-password" className="block text-sm font-medium text-foreground mr-3">
                    كلمة المرور
                  </label>
                  <div className="relative">
                    <input
                      id="signup-password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="********"
                    />
                    <LockClosedIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                {/* Confirm Password */}
                <div className="space-y-1">
                  <label htmlFor="signup-confirm-password" className="block text-sm font-medium text-foreground mr-3">
                    تأكيد كلمة المرور
                  </label>
                  <div className="relative">
                    <input
                      id="signup-confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="********"
                    />
                    <LockClosedIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                {/* Terms */}
                <div className="flex items-start text-sm">
                  <label className="flex items-center gap-2 text-muted-foreground">
                    <input type="checkbox" className="accent-primary" required />
                    <span>
                      أوافق على{" "}
                      <Link href="/conditions" className="text-primary hover:underline">
                        الشروط والأحكام
                      </Link>
                    </span>
                  </label>
                </div>

                {/* Error Message */}
                {error && <p className="text-red-500 text-sm text-center">{error}</p>}

                {/* Success Message */}
                {successMessage && <p className="text-green-600 text-sm text-center">{successMessage}</p>}

                {/* Submit Button */}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleStartSignup}
                  disabled={isLoading}
                >
                  {isLoading ? "جاري التسجيل..." : "إنشاء حساب"}
                </Button>
              </div>

              {/* Login Prompt */}
              <p className="text-center text-sm text-muted-foreground">
                لديك حساب بالفعل؟{" "}
                {onSwitchToLogin ? (
                  <button onClick={onSwitchToLogin} className="text-primary hover:underline font-medium">
                    تسجيل الدخول
                  </button>
                ) : (
                  <Link href="/login" className="text-primary hover:underline font-medium">
                    تسجيل الدخول
                  </Link>
                )}
              </p>
            </div>
          </div>

          {/* Image */}
          <div className="w-full md:w-1/2 h-64 md:h-auto hidden md:block">
            <img
              src="/images/login.jpg"
              alt="إنشاء حساب"
              className="h-full w-full object-cover"
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default SignupModal;
