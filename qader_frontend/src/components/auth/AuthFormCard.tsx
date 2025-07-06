// src/components/auth/AuthFormCard.tsx
import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PATHS } from "@/constants/paths"; // Assuming PATHS.HOME is defined

interface AuthFormCardProps {
  title: string;
  description: string;
  children: React.ReactNode; // The form elements
  footerLinkHref: string;
  footerLinkText: string;
  footerPromptText: string;
  showLogo?: boolean;
  logoSrc?: string;
  logoAlt?: string;
  logoWidth?: number;
  logoHeight?: number;
}

export function AuthFormCard({
  title,
  description,
  children,
  footerLinkHref,
  footerLinkText,
  footerPromptText,
  showLogo = false,
  logoSrc = "/images/logo.svg", // Default logo
  logoAlt = "Qader Logo",
  logoWidth = 120,
  logoHeight = 40,
}: AuthFormCardProps) {
  return (
    <Card className="mx-auto w-full max-w-md shadow-xl border">
      <CardHeader className="space-y-2 text-center">
        <CardTitle className="text-3xl font-bold">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {children} {/* Form elements and general error alerts will go here */}
        <div className="mt-6 text-center text-sm">
          {footerPromptText}{" "}
          <Link
            href={footerLinkHref}
            className="font-medium text-primary hover:underline"
          >
            {footerLinkText}
          </Link>{" "}
          او عود الي{" "}
          <Link
            href={PATHS.HOME}
            className="font-medium text-primary hover:underline"
          >
            الصفحة الرئيسة{" "}
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
