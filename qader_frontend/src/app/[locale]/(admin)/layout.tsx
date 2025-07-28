"use client";

import { useState } from "react";
import AdminHeader from "@/components/features/admin/layout/AdminHeader";
import AdminSidebar from "@/components/features/admin/layout/AdminSidebar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="flex min-h-screen">
      <AdminSidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
      <main className="flex flex-1 flex-col">
        <AdminHeader />
        <div className="flex-1 p-6">{children}</div>
      </main>
    </div>
  );
}
