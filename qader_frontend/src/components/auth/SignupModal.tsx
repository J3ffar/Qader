"use client";
import React from "react";
import { XMarkIcon } from "@heroicons/react/24/solid";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";

interface SignupModalProps {
  show: boolean;
  onClose: () => void;
  // Add prop to switch to login modal if needed
  onSwitchToLogin?: () => void;
}

const SignupModal: React.FC<SignupModalProps> = ({
  show,
  onClose,
  onSwitchToLogin,
}) => {
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
                <p className="text-xl text-gray-600 text-center">
                  قادر ترحب بك.
                </p>
              </div>
              <div className="space-y-4">
                {/* Full Name */}
                <div className="space-y-1">
                  <label
                    htmlFor="signup-fullname"
                    className="block text-sm font-medium text-foreground mr-3"
                  >
                    الاسم الكامل
                  </label>
                  <div className="relative">
                    <input
                      id="signup-fullname"
                      type="text"
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="الاسم الكامل"
                    />{" "}
                    {/* Added placeholder */}
                    <UserIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />{" "}
                    {/* Changed side */}
                  </div>
                </div>

                {/* Email */}
                <div className="space-y-1">
                  <label
                    htmlFor="signup-email"
                    className="block text-sm font-medium text-foreground mr-3"
                  >
                    البريد الإلكتروني
                  </label>
                  <div className="relative">
                    <input
                      id="signup-email"
                      type="email"
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="you@example.com"
                    />{" "}
                    {/* Added placeholder */}
                    <EnvelopeIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />{" "}
                    {/* Changed side */}
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-1">
                  <label
                    htmlFor="signup-password"
                    className="block text-sm font-medium text-foreground mr-3"
                  >
                    كلمة المرور
                  </label>
                  <div className="relative">
                    <input
                      id="signup-password"
                      type="password"
                      className="w-full mt-1 pr-10 p-2 border rounded-md bg-input border-border focus:outline-none focus:ring focus:ring-primary"
                      placeholder="********"
                    />{" "}
                    {/* Added placeholder */}
                    <LockClosedIcon className="w-5 h-5 absolute top-1/2 right-3 transform -translate-y-1/2 text-gray-400" />{" "}
                    {/* Changed side */}
                  </div>
                  {/* Removed error message example */}
                  {/* <p className="text-xs text-red-500 mt-1 mr-1">* كلمة المرور ضعيفة</p> */}
                </div>

                {/* Terms agreement - Example */}
                <div className="flex items-start text-sm">
                  <label className="flex items-center gap-2 text-muted-foreground">
                    <input
                      type="checkbox"
                      className="accent-primary"
                      required
                    />
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
                {/* The Link inside Button might not be semantically ideal, but works for navigation */}
                <Button variant={"outline"} className="w-full" asChild>
                  <Link href={"/completsignup"}>
                    {" "}
                    {/* Navigate on click */}
                    إنشاء حساب
                  </Link>
                </Button>
                {/* OR if you want to handle signup logic here first:
                 <Button variant={"outline"} className="w-full" onClick={handleSignup}>
                   إنشاء حساب
                 </Button>
                 */}
              </div>

              {/* Login Prompt - Use onSwitchToLogin if provided */}
              <p className="text-center text-sm text-muted-foreground">
                لديك حساب بالفعل؟{" "}
                {onSwitchToLogin ? (
                  <button
                    onClick={onSwitchToLogin}
                    className="text-primary hover:underline font-medium"
                  >
                    تسجيل الدخول
                  </button>
                ) : (
                  <Link
                    href="/login"
                    className="text-primary hover:underline font-medium"
                  >
                    تسجيل الدخول
                  </Link>
                )}
              </p>
            </div>
          </div>

          {/* Image */}
          <div className="w-full md:w-1/2 h-64 md:h-auto hidden md:block">
            {" "}
            {/* Hide on small screens */}
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
