"use client";
import React, { useState } from "react";
import { XMarkIcon, EyeIcon, EyeSlashIcon } from "@heroicons/react/24/solid";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { UserIcon, EnvelopeIcon, LockClosedIcon } from "@heroicons/react/24/outline";

interface SignupModalProps {
  show: boolean;
  onClose: () => void;
}

const SignupModal: React.FC<SignupModalProps> = ({ show, onClose }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState("");

  if (!show) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]"
        onClick={onClose}
        aria-hidden="true"
      />
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
                  <label className="block text-sm font-bold text-foreground mr-3">الاسم الكامل</label>
                  <div className="relative">
                    <input type="text" className="input-style p-2 bg-gray-100 w-full rounded-lg mt-1 pr-9 focus:outline-none focus:border" />
                    <UserIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                {/* Email */}
                <div className="space-y-1">
                  <label className="block text-sm font-bold text-foreground mr-3">البريد الإلكتروني</label>
                  <div className="relative">
                    <input type="email" className="input-style p-2 bg-gray-100 w-full rounded-lg mt-1 pr-9 focus:outline-none focus:border" />
                    <EnvelopeIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-1">
                  <label className="block text-sm font-bold text-foreground mr-3">كلمة المرور</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      className="input-style p-2 bg-gray-100 w-full rounded-lg mt-1 pr-9 pl-9 focus:outline-none focus:border"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <LockClosedIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />
                    <button
                      type="button"
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeSlashIcon className="w-5 h-5" />
                      ) : (
                        <EyeIcon className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {password.length > 0 && (
                    <p className="text-xs text-red-500 mt-1 mr-1">* كلمة المرور ضعيفة</p>
                  )}
                </div>

                {/* Remember me and Forgot password */}
                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="accent-primary" />
                    تذكر كلمة المرور
                  </label>
                  <Link href="#" className="text-[#2f80ed] underline">نسيت كلمة المرور؟</Link>
                </div>

                {/* Signup Button */}
                <Button variant={"outline"} className="w-full">
                  <Link href={"/completsignup"}>
                    إنشاء حساب
                  </Link>
                </Button>
              </div>

              {/* Login Prompt */}
              <p className="text-center text-sm text-muted-foreground">
                لديك حساب بالفعل؟{" "}
                <button onClick={onClose} className="text-primary hover:underline">
                  تسجيل الدخول
                </button>
              </p>
            </div>
          </div>

          {/* Image */}
          <div className="w-full md:w-1/2 h-64 md:h-auto">
            <img src="/images/login.jpg" alt="إنشاء حساب" className="h-full w-full object-cover" />
          </div>
        </div>
      </div>
    </>
  );
};

export default SignupModal;
