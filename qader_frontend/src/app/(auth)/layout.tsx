import React from "react";
import Image from "next/image";
import Link from "next/link";
import { PATHS } from "@/constants/paths";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-muted/40 p-4">
      <div className="mb-8">
        <Link href={PATHS.HOME || "/"}>
          <Image
            src="/images/logo.svg"
            alt="Qader Logo"
            width={150}
            height={60}
            priority
          />
        </Link>
      </div>
      <main className="w-full max-w-xl">{children}</main>
    </div>
  );
}
