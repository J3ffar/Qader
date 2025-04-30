"use client";
import React from "react";
import { XMarkIcon } from "@heroicons/react/24/solid";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { EnvelopeIcon, LockClosedIcon } from "@heroicons/react/24/outline"; // Added icons

interface LoginModalProps {
  show: boolean;
  onClose: () => void;
  // Add prop to switch to signup modal if needed
  onSwitchToSignup?: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({
  show,
  onClose,
  onSwitchToSignup,
}) => {
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
          onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
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
                <h2 className="text-3xl font-bold text-center">
                  أهلاً بعودتك!!!
                </h2>
                <p className="text-xl text-gray-600 text-center">
                  اكمل السير معنا...
                </p>
              </div>
              <div className="space-y-4">
                {/* Email */}
                <div>
                  <label
                    htmlFor="login-email"
                    className="block text-sm font-medium mr-3"
                  >
                    {" "}
                    {/* Added mr-3 */}
                    البريد الإلكتروني
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      id="login-email" // Unique ID
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary" // Adjusted padding
                      placeholder="you@example.com"
                    />
                    <EnvelopeIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />{" "}
                    {/* Added Icon */}
                  </div>
                </div>
                {/* Password */}
                <div>
                  <label
                    htmlFor="login-password"
                    className="block text-sm font-medium mr-3"
                  >
                    {" "}
                    {/* Added mr-3 */}
                    كلمة المرور
                  </label>
                  <div className="relative">
                    {" "}
                    {/* Added relative container */}
                    <input
                      type="password"
                      id="login-password" // Unique ID
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary" // Adjusted padding
                      placeholder="********"
                    />
                    <LockClosedIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />{" "}
                    {/* Added Icon */}
                  </div>
                  {/* Removed error message example */}
                  {/* <p className="text-sm text-red-500 mt-1">
                    * كلمة المرور خاطئة
                  </p> */}
                </div>

                {/* Checkbox and forgot password */}
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <label className="flex items-center space-x-2 rtl:space-x-reverse">
                    <input type="checkbox" className="accent-primary" />
                    <span>حفظ الجلسة</span>
                  </label>
                  <Link
                    href="/forgot-password" // Assuming you have this route
                    className="text-[#2f80ed] underline"
                  >
                    نسيت كلمة السر؟
                  </Link>
                </div>

                <Button variant={"outline"} className="w-full">
                  دخول
                </Button>
              </div>
              {/* Signup Prompt - Use onSwitchToSignup if provided */}
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
                  <Link
                    href="/signup"
                    className="text-primary hover:underline font-medium"
                  >
                    إنشاء حساب
                  </Link>
                )}
              </p>
            </div>
          </div>

          {/* Image Wrapper */}
          <div className="w-full md:w-1/2 h-64 md:h-auto hidden md:block">
            {" "}
            {/* Hide on small screens */}
            <div className="h-full w-full">
              <img
                src="/images/login.jpg" // Ensure you have this image
                alt="تسجيل الدخول"
                className="h-full w-full object-cover"
              />
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default LoginModal;
