"use client";
<<<<<<< HEAD
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
=======
import React from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";
>>>>>>> ba611a48ecd8a169d38393a4a292bc8f8814af57

// This is the PAGE component for the /signup route
const SignupPage: React.FC = () => {
  return (
<<<<<<< HEAD
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
=======
    // Main container for the page, centers content
    <div className="flex min-h-screen items-center justify-center p-4">
      {/* Re-using the modal's inner structure for layout */}
      <div className="relative w-full max-w-md lg:max-w-3xl bg-background rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row">
        {/* Form Content */}
        <div className="w-full md:w-1/2 flex items-center justify-center">
          <div className="w-full p-6 sm:p-8 space-y-6">
            <div>
              <h2 className="text-3xl font-bold text-center">أهلاً بك!!</h2>
              <p className="text-xl text-gray-600 text-center">قادر ترحب بك.</p>
>>>>>>> ba611a48ecd8a169d38393a4a292bc8f8814af57
            </div>
            <div className="space-y-4">
              {/* Full Name */}
              <div className="space-y-1">
                <label
                  htmlFor="signup-page-fullname"
                  className="block text-sm font-medium text-foreground mr-3"
                >
                  الاسم الكامل
                </label>
                <div className="relative">
                  <input
                    id="signup-page-fullname"
                    type="text"
                    className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                    placeholder="الاسم الكامل"
                  />
                  <UserIcon className="w-5 h-5 absolute top-1/2 left-3 transform -translate-y-1/2 text-gray-400" />
                </div>
              </div>

              {/* Email */}
              <div className="space-y-1">
                <label
                  htmlFor="signup-page-email"
                  className="block text-sm font-medium text-foreground mr-3"
                >
                  البريد الإلكتروني
                </label>
                <div className="relative">
                  <input
                    id="signup-page-email"
                    type="email"
                    className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                    placeholder="you@example.com"
                  />
                  <EnvelopeIcon className="w-5 h-5 absolute top-1/2 left-3 transform -translate-y-1/2 text-gray-400" />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1">
                <label
                  htmlFor="signup-page-password"
                  className="block text-sm font-medium text-foreground mr-3"
                >
                  كلمة المرور
                </label>
                <div className="relative">
                  <input
                    id="signup-page-password"
                    type="password"
                    className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                    placeholder="********"
                  />
                  <LockClosedIcon className="w-5 h-5 absolute top-1/2 left-3 transform -translate-y-1/2 text-gray-400" />
                </div>
              </div>

              {/* Terms agreement */}
              <div className="flex items-start text-sm">
                <label className="flex items-center gap-2 text-muted-foreground">
                  <input type="checkbox" className="accent-primary" required />
                  <span>
                    أوافق على{" "}
                    <Link
                      href="/conditions"
                      className="text-primary hover:underline"
                    >
                      الشروط والأحكام
                    </Link>
                  </span>
                </label>
              </div>

              {/* Signup Button */}
              <Button variant={"outline"} className="w-full" asChild>
                <Link href={"/completsignup"}>إنشاء حساب</Link>
              </Button>
            </div>

            {/* Link to Login Page */}
            <p className="text-center text-sm text-muted-foreground">
              لديك حساب بالفعل؟{" "}
              <Link
                href="/login"
                className="text-primary hover:underline font-medium"
              >
                تسجيل الدخول
              </Link>
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
  );
};

export default SignupPage; // Export the page component
