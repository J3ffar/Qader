"use client";
<<<<<<< HEAD
import React, { useState } from "react";
import { XMarkIcon, EyeIcon, EyeSlashIcon } from "@heroicons/react/24/solid";
=======
import React from "react";
>>>>>>> ba611a48ecd8a169d38393a4a292bc8f8814af57
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { EnvelopeIcon, LockClosedIcon } from "@heroicons/react/24/outline";

<<<<<<< HEAD
interface LoginModalProps {
  show: boolean;
  onClose: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ show, onClose }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState("");

  if (!show) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
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

          {/* Form Wrapper */}
          <div className="w-full md:w-1/2 flex items-center justify-center max-md:flex-col">
            <div className="w-full p-4 sm:p-6 lg:p-8 space-y-6">
              <div>
                <h2 className="text-3xl font-bold text-center">أهلاً بعودتك!!!</h2>
                <p className="text-xl text-gray-600 text-center">اكمل السير معنا...</p>
              </div>
              <div className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-bold">
                    البريد الإلكتروني
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      id="email"
                      className="w-full mt-1 pl-10 p-2 rounded-md bg-gray-100 focus:border focus:outline-none"
                      placeholder="you@example.com"
                    />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <label htmlFor="password" className="block text-sm font-bold">
                    كلمة المرور
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      id="password"
                      className="w-full mt-1 pl-10 pr-10 p-2 rounded-md bg-gray-100 focus:border focus:outline-none"
                      placeholder="********"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 left-2 flex items-center text-gray-500"
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? (
                        <EyeSlashIcon className="w-5 h-5" />
                      ) : (
                        <EyeIcon className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {password && (
                    <p className="text-sm text-red-500 mt-1">* كلمة المرور خاطئة</p>
                  )}
                </div>

                {/* Checkbox and forgot password */}
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <label className="flex items-center space-x-2 rtl:space-x-reverse">
                    <input type="checkbox" className="accent-primary" />
                    <span>حفظ الجلسة</span>
                  </label>
                  <Link href="/forgot-password" className="text-[#2f80ed] underline">
                    نسيت كلمة السر؟
                  </Link>
                </div>

                <Button variant={"outline"} className="w-full">دخول</Button>
              </div>

              <p className="text-center text-sm text-muted-foreground">
                ليس لديك حساب؟{" "}
                <Link href="/signup" className="text-primary hover:underline">
                  إنشاء حساب
                </Link>
=======
// This is the PAGE component for the /login route
const LoginPage: React.FC = () => {
  return (
    // Main container for the page, centers content
    <div className="flex min-h-screen items-center justify-center p-4">
      {/* Re-using the modal's inner structure for layout */}
      <div className="relative w-full max-w-sm lg:max-w-3xl bg-background rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row">
        {/* Form Wrapper */}
        <div className="w-full md:w-1/2 flex items-center justify-center max-md:flex-col">
          <div className="w-full p-4 sm:p-6 lg:p-8 space-y-6">
            <div>
              <h2 className="text-3xl font-bold text-center">
                أهلاً بعودتك!!!
              </h2>
              <p className="text-xl text-gray-600 text-center">
                اكمل السير معنا...
>>>>>>> ba611a48ecd8a169d38393a4a292bc8f8814af57
              </p>
            </div>
            <div className="space-y-4">
              {/* Email */}
              <div>
                <label
                  htmlFor="login-page-email"
                  className="block text-sm font-medium mr-3"
                >
                  البريد الإلكتروني
                </label>
                <div className="relative">
                  <input
                    type="email"
                    id="login-page-email" // Unique ID for the page
                    className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                    placeholder="you@example.com"
                  />
                  <EnvelopeIcon className="w-5 h-5 absolute top-1/2 left-3 transform -translate-y-1/2 text-gray-400" />
                </div>
              </div>
              {/* Password */}
              <div>
                <label
                  htmlFor="login-page-password"
                  className="block text-sm font-medium mr-3"
                >
                  كلمة المرور
                </label>
                <div className="relative">
                  <input
                    type="password"
                    id="login-page-password" // Unique ID for the page
                    className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                    placeholder="********"
                  />
                  <LockClosedIcon className="w-5 h-5 absolute top-1/2 left-3 transform -translate-y-1/2 text-gray-400" />
                </div>
              </div>

              {/* Checkbox and forgot password */}
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <label className="flex items-center space-x-2 rtl:space-x-reverse">
                  <input type="checkbox" className="accent-primary" />
                  <span>حفظ الجلسة</span>
                </label>
                <Link
                  href="/forgot-password"
                  className="text-[#2f80ed] underline"
                >
                  نسيت كلمة السر؟
                </Link>
              </div>

              <Button variant={"outline"} className="w-full">
                دخول
              </Button>
            </div>
            {/* Link to Signup Page */}
            <p className="text-center text-sm text-muted-foreground">
              ليس لديك حساب؟{" "}
              <Link
                href="/signup"
                className="text-primary hover:underline font-medium"
              >
                إنشاء حساب
              </Link>
            </p>
          </div>
        </div>

        {/* Image Wrapper */}
        <div className="w-full md:w-1/2 h-64 md:h-auto hidden md:block">
          <div className="h-full w-full">
            <img
              src="/images/login.jpg"
              alt="تسجيل الدخول"
              className="h-full w-full object-cover"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; // Export the page component
