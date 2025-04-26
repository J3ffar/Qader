"use client";
import React from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";

// This is the PAGE component for the /signup route
const SignupPage: React.FC = () => {
  return (
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
