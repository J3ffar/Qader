import React from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-muted/40 dark:bg-gradient-to-br dark:from-slate-900 dark:to-slate-800 p-4">
      {/* The children will be the login or signup page component */}
      {children}
    </div>
  );
}
