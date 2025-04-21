import React from "react";
import Link from "next/link";
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
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "تسجيل الدخول | منصة قادر",
  description: "قم بتسجيل الدخول إلى حسابك في منصة قادر التعليمية.",
};

export default function LoginPage() {
  // TODO: Add state management (useState) and form submission logic (handleSubmit)

  return (
    <Card className="w-full max-w-sm shadow-lg">
      <CardHeader className="space-y-1 text-center">
        {/* Optional: Add Logo Here */}
        {/* <Image src="/images/logo.svg" alt="Qader Logo" width={120} height={40} className="mx-auto mb-4" /> */}
        <CardTitle className="text-2xl font-bold">تسجيل الدخول</CardTitle>
        <CardDescription>
          أدخل بريدك الإلكتروني وكلمة المرور للوصول لمنصة قادر
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">البريد الإلكتروني</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            required
            // value={email} onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">كلمة المرور</Label>
            <Link
              href="/forgot-password" // Add a forgot password link if needed
              className="text-sm text-primary hover:underline"
            >
              نسيت كلمة المرور؟
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            required
            // value={password} onChange={(e) => setPassword(e.target.value)}
          />
        </div>
      </CardContent>
      <CardFooter className="flex flex-col gap-4">
        <Button type="submit" className="w-full">
          دخول
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          ليس لديك حساب؟{" "}
          <Link
            href="/signup"
            className="font-medium text-primary hover:underline"
          >
            إنشاء حساب جديد
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
