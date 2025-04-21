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
  title: "إنشاء حساب | منصة قادر",
  description: "أنشئ حساباً جديداً في منصة قادر التعليمية لتبدأ رحلتك.",
};

export default function SignupPage() {
  // TODO: Add state management (useState) and form submission logic (handleSubmit)

  return (
    <Card className="w-full max-w-sm shadow-lg">
      <CardHeader className="space-y-1 text-center">
        {/* Optional: Add Logo Here */}
        {/* <Image src="/images/logo.svg" alt="Qader Logo" width={120} height={40} className="mx-auto mb-4" /> */}
        <CardTitle className="text-2xl font-bold">إنشاء حساب جديد</CardTitle>
        <CardDescription>
          املأ البيانات التالية للانضمام إلى منصة قادر
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">الاسم الكامل</Label>
          <Input id="name" type="text" placeholder="اسمك الثلاثي" required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">البريد الإلكتروني</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">كلمة المرور</Label>
          <Input id="password" type="password" required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirmPassword">تأكيد كلمة المرور</Label>
          <Input id="confirmPassword" type="password" required />
        </div>
      </CardContent>
      <CardFooter className="flex flex-col gap-4">
        <Button type="submit" className="w-full">
          إنشاء الحساب
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          لديك حساب بالفعل؟{" "}
          <Link
            href="/login"
            className="font-medium text-primary hover:underline"
          >
            تسجيل الدخول
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
